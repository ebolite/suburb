import socket
import os
from _thread import start_new_thread
import json
import hashlib
import time
import datetime
import random
import ssl
import uuid
from typing import Optional

import sessions
import alchemy
import util
import config
import tiles
import binaryoperations
import npcs

conns = []

class User():
    def __new__(cls, name) -> Optional["User"]:
        if name not in util.memory_users:
            return None
        else: return super().__new__(cls)

    def __init__(self, name):
        self.__dict__["_id"] = name

    @classmethod
    def create_user(cls, name, password) -> Optional["User"]:
        if name in util.memory_users: return None
        util.memory_users[name] = {}
        user = cls(name)
        user.setup_defaults(name, password)
        return user

    def setup_defaults(self, name, password):
        self._id = name
        self.sessions: list[str] = []
        self.set_password(password)

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.memory_users[self.__dict__["_id"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = util.memory_users[self.__dict__["_id"]][attr]
        return self.__dict__[attr]
    
    def set_password(self, password: str):
        self.salt = os.urandom(32).hex()
        plaintext = password.encode()
        digest = hashlib.pbkdf2_hmac("sha256", plaintext, bytes.fromhex(self.salt), 10000)
        hex_hash = digest.hex()
        self.hashed_password = hex_hash
    
    def verify_password(self, password: str):
        if self.hashed_password == None: 
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(self.salt), 10000)
        new_hash = digest.hex()
        if new_hash == self.hashed_password: 
            return True
        else: return False

    def make_token(self, password: str, expires=True):
        if not self.verify_password(password): return None
        else:
            token = str(uuid.uuid4())
            if expires:
                expiration_time = datetime.datetime.now() + datetime.timedelta(hours=1)
                self.token = token, expiration_time.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                expiration_time = None
                self.token = token, expiration_time
            return token
            
    def verify_token(self, token: str, refresh_token=True):
        current_token, expiry = self.token
        if token != current_token: 
            return False
        if expiry is None: return True
        else:
            if datetime.datetime.strptime(expiry, "%m/%d/%Y, %H:%M:%S") < datetime.datetime.now(): 
                return False
            else: 
                if refresh_token:
                    new_expiration_time = datetime.datetime.now() + datetime.timedelta(hours=1)
                    self.token = token, new_expiration_time.strftime("%m/%d/%Y, %H:%M:%S")
                return True

    @property
    def name(self) -> str:
        return self.__dict__["_id"]

for user_name in util.memory_users:
    user = User(user_name)
    for session_name in user.sessions.copy():
        if sessions.Session(session_name) is None:
            user.sessions.remove(session_name)

def threaded_client(connection):
    try:
        conns.append(connection)
        print(f"Connections: {len(conns)}")
        while True:
            data = connection.recv(2048)
            reply = ""
            if not data:
                break
            decoded = data.decode("utf-8")
            dict = json.loads(decoded)
            reply = handle_request(dict)
            connection.sendall(str.encode(str(reply)+"\n"))
        conns.remove(connection)
        connection.close()
    except (ConnectionResetError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"\nExcepted error!\n{e}\n")
        conns.remove(connection)
        connection.close()

def handle_request(dict):
    intent = dict["intent"]
    if intent == "connect":
        return "Successfully connected."
    if intent == "server_tiles":
        return json.dumps({"server_tiles": tiles.server_tiles, "labels": {tile.tile_char:tile.name for tile in tiles.tiles.values()}})
    username = dict["username"]
    password = dict["password"]
    content = dict["content"]
    if intent == "create_account":
        if len(username) == 0 or len(password) == 0: return "Can you please just be fucking normal"
        user = User.create_user(username, password)
        if user is None: return f"`{username}` is already taken."
        return f"Successfully created your account. You may now log in."
    user = User(username)
    if User(username) is None: return f"Account does not exist."
    if intent == "login":
        return user.verify_password(password)
    token = dict["token"]
    if intent == "verify_token":
        verified = user.verify_token(token)
        return verified
    if intent == "get_token":
        token = user.make_token(password)
        if token is None: return False
        else: return token
    if not user.verify_token(token): return "Invalid authorization token."
    if intent == "all_session_characters":
        out_dict = {}
        for session_name in user.sessions:
            session = sessions.Session(session_name)
            if session is None: continue
            session_player = session.get_current_subplayer(user.name)
            if session_player is None: out_dict[session_name] = None
            else: out_dict[session_name] = session_player.get_dict()
        return json.dumps(out_dict)
    if intent == "interests":
        return json.dumps(config.interests)
    # session verification
    session_name = dict["session_name"]
    if session_name in user.sessions and intent == "join_session": return "You are already in that session!"
    if session_name not in user.sessions:
        session_password = dict["session_password"]
        if intent == "create_session":
            if len(session_name) > 32: return "fuck you"
            session = sessions.Session.create_session(session_name, session_password)
            if session is None: return f"The session `{session_name}` is already registered."
            print(f"session created {session_name}")
            return f"The session `{session_name}` has been successfully registered."
        elif intent == "join_session":
            session = sessions.Session(session_name)
            if session is None: return f"Session `{session_name}` does not exist."
            if not session.verify_password(session_password): return f"Incorrect session password."
            user.sessions.append(session_name)
            session.user_players[user.name] = None
            return f"Successfully joined `{session_name}`!"
        else: return "No session."
    session = sessions.Session(session_name)
    if session is None: return f"Session `{session_name}` no longer exists."
    if intent == "session_info":
        out = {}
        out["current_grist_types"] = session.current_grist_types
        return json.dumps(out)
    if intent == "create_character":
        if session.get_current_subplayer(user.name) is not None: return "Character was already created."
        desired_name = content["name"]
        # create player
        new_player = sessions.Player.create_player(desired_name, username)
        new_player.nickname = content["name"]
        new_player.noun = content["noun"]
        new_player.pronouns = content["pronouns"]
        new_player.interests = content["interests"]
        new_player.aspect = content["aspect"]
        new_player.gameclass = content["class"]
        new_player.gristcategory = content["gristcategory"]
        new_player.secondaryvial = content["secondaryvial"]
        new_player.symbol_dict = content["symbol_dict"]
        # todo: moon selection
        new_player.moon_name = random.choice(["prospit", "derse"])
        new_player.starting_session_name = session.name
        new_player.add_modus(content["modus"])
        land = sessions.Land.create(f"{new_player.id}{session.name}", session, new_player)
        new_player.land_name = land.name
        new_player.land_session = session.name
        housemap = land.get_map(land.housemap_name)
        room = housemap.random_valid_room(config.starting_tiles)
        room.add_instance(alchemy.Instance(alchemy.Item("Sburb disc")).name)
        # create subplayers (real and dream)
        real_self = sessions.SubPlayer.create_subplayer(new_player, "real")
        real_self.goto_room(room)
        dream_self = sessions.SubPlayer.create_subplayer(new_player, "dream")
        dream_self.sleeping = True
        dream_room = new_player.kingdom.moon.spawn_player_in_tower(dream_self)
        dream_room.map.special_type = "dreamer_tower"
        new_player.current_subplayer_type = "real"
        for interest in new_player.interests:
            room.generate_loot(tiles.get_tile(interest).get_loot_list())
            dream_room.generate_loot(tiles.get_tile(interest).get_loot_list())
        # session
        session.starting_players.append(new_player.id)
        session.user_players[user.name] = new_player.id
        new_player.setup = True
        return f"Your land is the {land.title}! ({land.acronym})"
    # verify character
    player = session.get_current_subplayer(user.name)
    if player is None: return False
    # process commands todo: clean this up
    match intent:
        case "current_map":
            return map_data(player)
        case "current_overmap":
            map_tiles, map_specials, map_types, theme = player.get_overmap_view()
            illegal_moves = player.get_illegal_overmap_moves()
            overmap_title = player.overmap.title
            overmap_type = player.overmap.overmap_type
            return json.dumps({"map_tiles": map_tiles, "map_specials": map_specials, "map_types": map_types, 
                               "title": overmap_title, "theme": theme, "illegal_moves": illegal_moves, "overmap_type": overmap_type})
        case "player_info":
            return json.dumps(player.get_dict())
        case "strife_data":
            if player.strife is None: 
                if player.room.strife is not None:
                    griefer = player.room.strife.add_griefer(player)
                    if griefer is None: return json.dumps({})
                    else: return json.dumps(player.room.strife.get_dict())
                else: return json.dumps({})
            else: return json.dumps(player.strife.get_dict())
        # todo: this is not optional
        case "start_strife":
            if not player.room.start_strife():
                if player.room.strife is not None:
                    player.room.strife.add_griefer(player)
                    for npc_name in player.npc_followers:
                        npc = npcs.Npc(npc_name)
                        player.room.strife.add_griefer(npc)
        case "carved_item_info":
            dowel_name = content["dowel_name"]
            if not alchemy.does_instance_exist(dowel_name): print("dowel does not exist"); return {}
            dowel_instance = alchemy.Instance(dowel_name)
            carved_code = dowel_instance.carved
            if carved_code in util.codes:
                carved_item_name = util.codes[carved_code]
                carved_item = alchemy.Item(carved_item_name)
                carved_dict = carved_item.get_dict()
                carved_dict["name"] = carved_item.name
                return json.dumps(carved_dict)
            else:
                return {}
        case "sylladex":
            return json.dumps(player.sylladex_instances())
        case "use_item":
            instance_name = content["instance_name"]
            action_name = content["action_name"]
            target_name = content["target_name"]
            if "additional_data" in content:
                additional_data = content["additional_data"]
            else: additional_data = None
            if not alchemy.does_instance_exist(instance_name): return False
            instance = alchemy.Instance(instance_name)
            if target_name is not None: target_instance = alchemy.Instance(target_name)
            else: target_instance = None
            return use_item(player, instance, action_name, target_instance, additional_data)
        case "interact_npc":
            npc_name = content["npc_name"]
            interaction_name = content["interaction_name"]
            additional_data = content["additional_data"]
            if npc_name not in player.room.npcs: return False
            if interaction_name not in npcs.npc_interactions: return False
            if interaction_name not in npcs.Npc(npc_name).interactions: return False
            return npcs.npc_interactions[interaction_name].use(player, npcs.Npc(npc_name), additional_data)
        case "computer":
            return computer_shit(player, content, session)
        case "assign_specibus":
            kind_name = content["kind_name"]
            return player.assign_specibus(kind_name)
        case "move_to_strife_deck":
            instance_name = content["instance_name"]
            kind_name = content["kind_name"]
            return player.move_to_strife_deck(instance_name, kind_name)
        case "eject_from_strife_deck":
            instance_name = content["instance_name"]
            if player.wielding == instance_name: player.unwield()
            return player.eject_from_strife_deck(instance_name)
        case "wield":
            instance_name = content["instance_name"]
            return player.wield(instance_name)
        case "wear":
            instance_name = content["instance_name"]
            return player.wear(instance_name)
        case "unwear":
            return player.unwear()
        case "set_stat_ratios":
            ratios = content["ratios"]
            for stat in player.stat_ratios:
                player.stat_ratios[stat] = int(ratios[stat])
            return True
        case "drop_empty_card":
            return player.drop_empty_card()
        case "captchalogue":
            instance_name = content["instance_name"]
            modus_name = content["modus_name"]
            success = player.captchalogue(instance_name, modus_name)
            return "success" if success else "failure"
        case "uncaptchalogue":
            instance_name = content["instance_name"]
            success = player.uncaptchalogue(instance_name)
            return "success" if success else "failure"
        case "eject":
            instance_name = content["instance_name"]
            modus_name = content["modus_name"]
            velocity = content["velocity"]
            success = player.eject(instance_name, modus_name, velocity)
            return "success" if success else "failure"
        case "valid_use_targets":
            instance_name = content["instance_name"]
            action_name = content["action_name"]
            instances_dict = {}
            valid_names = valid_use_targets(player, alchemy.Instance(instance_name), action_name)
            for name in valid_names:
                if not alchemy.does_instance_exist(instance_name): return {}
                instances_dict[name] = alchemy.Instance(name).get_dict()
            return json.dumps(instances_dict)
        case "move":
            player.attempt_move(content)
            return
        case "overmap_move":
            player.attempt_overmap_move(content)
            return overmap_data(player)
        case "console_command":
            # try:
                console_commands(player, content)
            # except Exception as e:
            #     print(f"Error in command {content}", e)
        case "get_client_server_chains":
            server_client = {player_username:sessions.Player(player_username).client_player_name for player_username in session.starting_players}
            player_names = {player_username:sessions.Player(player_username).nickname for player_username in session.starting_players}
            no_server = []
            chained = []
            chains = []
            # find which players don't have servers
            for player_username in session.starting_players:
                player = sessions.Player(player_username)
                if player.server_player_name is None: no_server.append(player_username)
            # find which players are in a chain and which aren't
            for player_username in session.starting_players:
                if player_username in chained: continue
                first_member_of_chain = get_first_member_of_chain(player_username)
                chain = construct_chain(first_member_of_chain)
                if len(chain) == 1: 
                    continue
                chains.append(chain)
                for username in chain: chained.append(username)
            return json.dumps({"chains": chains, "no_server": no_server, "server_client": server_client, "player_names": player_names})
        case "strife_info":
            if player.strife is None: return json.dumps({})
            player.strife.ready_check()
            if player.strife is None: return json.dumps({})
            else: return json.dumps(player.strife.get_dict())
        case "submit_strife_action":
            skill_name = content["skill_name"]
            targets = content["targets"]
            if player.strife is None: print("strife is none"); return json.dumps({})
            success = player.strife.get_griefer(player.name).submit_skill(skill_name, targets)
            if success: return json.dumps(player.strife.get_dict())
            else: return json.dumps({})
        case "unsubmit_skill":
            if player.strife is None: return json.dumps({})
            player.strife.get_griefer(player.name).unsubmit_skill()
            return json.dumps(player.strife.get_dict())
        case "strife_ready":
            if player.strife is None: return json.dumps({})
            player.strife.get_griefer(player.name).ready = True
            player.strife.ready_check()
            if player.strife is None: return json.dumps({})
            else: return json.dumps(player.strife.get_dict())
        case "strife_unready":
            if player.strife is None: return json.dumps({})
            player.strife.get_griefer(player.name).ready = False
            return json.dumps(player.strife.get_dict())
        case "collect_spoils":
            unclaimed_grist = player.unclaimed_grist.copy()
            unclaimed_rungs = player.unclaimed_rungs
            player.claim_spoils()
            return json.dumps({"unclaimed_grist": unclaimed_grist, "unclaimed_rungs": unclaimed_rungs})
        case "get_resulting_alchemy":
            code_1 = content["code_1"]
            code_2 = content["code_2"]
            operation = content["operation"]
            if code_1 in util.codes and code_2 in util.codes:
                item_1 = alchemy.Item(util.codes[code_1])
                item_2 = alchemy.Item(util.codes[code_2])
                alchemized_item_name = alchemy.alchemize(item_1.name, item_2.name, operation)
                alchemized_item = alchemy.Item(alchemized_item_name)
            else:
                alchemized_item = None
            if alchemized_item is not None:
                return json.dumps(alchemized_item.get_dict())
            else:
                return json.dumps({})
        case "session_seeds":
            return json.dumps(player.session.get_best_seeds())
        case "prototype_targets":
            valid_targets = {instance_name:alchemy.Instance(instance_name).get_dict() for instance_name in player.room.instances}
            valid_targets.update({instance_name:alchemy.Instance(instance_name).get_dict() for instance_name in player.sylladex})
            return json.dumps(valid_targets)

def map_data(player: "sessions.SubPlayer"):
    map_tiles, map_specials, room_instances, room_npcs, room_players, strife = player.get_view()
    return json.dumps({"map": map_tiles, "specials": map_specials, "instances": room_instances, "npcs": room_npcs, "players": room_players,
                       "strife": strife,
                       "room_name": player.room.tile.name, "theme": player.overmap.theme})

def overmap_data(player: "sessions.SubPlayer"):
    map_tiles, map_specials, map_types, theme = player.get_overmap_view()
    illegal_moves = player.get_illegal_overmap_moves()
    overmap_title = player.overmap.title
    overmap_type = player.overmap.overmap_type
    formatted_map_tiles = ["".join(line) for line in map_tiles]
    return json.dumps({"map_tiles": formatted_map_tiles, "map_specials": map_specials, "map_types": map_types, 
                        "title": overmap_title, "theme": theme, "illegal_moves": illegal_moves, "overmap_type": overmap_type})

def get_viewport(x: int, y: int, client: Optional[sessions.Player]) -> str:
    if client is None: print("no client"); return "No client dumpass"
    map_tiles, map_specials = client.land.housemap.get_view(x, y, 8)
    room = client.land.housemap.find_room(x, y)
    room_instances = room.get_instances()
    room_npcs = room.get_npcs()
    room_players = room.get_players()
    client_grist_cache = client.grist_cache
    client_available_phernalia = client.available_phernalia
    excursus_contents = {item.name:item.get_dict() for item in [alchemy.Item(item_name) for item_name in client.starting_session.excursus]}
    atheneum = {instance.name:instance.get_dict() for instance in [alchemy.Instance(instance_name) for instance_name in client.atheneum]}
    return json.dumps({"map": map_tiles, "specials": map_specials, "instances": room_instances, "npcs": room_npcs, "room_name": room.tile.name, 
                       "players": room_players,
                       "client_grist_cache": client_grist_cache, "client_available_phernalia": client_available_phernalia,
                       "client_cache_limit": client.grist_cache_limit, "atheneum": atheneum, "excursus": excursus_contents,
                       "theme": client.land.theme, "player_color": client.symbol_dict["color"]})

def computer_shit(player: sessions.SubPlayer, content: dict, session:sessions.Session):
    for instance_name in player.sylladex + player.room.instances:
        instance = alchemy.Instance(instance_name)
        if "computer" in instance.item.use:
            break
    else:
        print("No computer")
        return "You don't have a computer, idiot!"
    command = content["command"]
    match command:
        case "starting_sburb_coords":
            client = player.client_player
            if client is None: return "No client dumpass"
            housemap = client.land.housemap
            x = len(housemap.map_tiles[0]) // 2
            y = len(housemap.map_tiles) - 6
            return json.dumps({"x": x, "y": y})
        case "viewport":
            viewport_x = content["viewport_x"]
            viewport_y = content["viewport_y"]
            client = player.client_player
            return get_viewport(viewport_x, viewport_y, client)
        case "is_tile_in_bounds":
            x_coord = content["x"]
            y_coord = content["y"]
            client = player.client_player
            if client is None: return "No client dumpass"
            return client.land.housemap.is_tile_in_bounds(int(x_coord), int(y_coord))
        case "leech":
            grist_type = content["grist_type"]
            if grist_type not in config.grists: return "fuck you"
            if grist_type in player.leeching: player.leeching.remove(grist_type)
            else: player.leeching.append(grist_type)
        case "connect":
            client_player_username = content["client_player_username"]
            if not sessions.does_player_exist(client_player_username): return "Player does not exist."
            client_player = sessions.Player(client_player_username)
            if client_player.server_player_name is not None: return "Client already has server."
            if player.client_player_name is not None: return "You already have a client."
            player.client_player_name = client_player_username
            client_player.server_player_name = player.player.id
            client_player.starting_session.connected.append(client_player_username)
            client_player.grist_cache["build"] += min(2 * (10 ** len(client_player.starting_session.connected)), 2000)
            return "Successfully connected."
        case "deploy_phernalia":
            if player.client_player is None: return "No client."
            x_coord = content["x"]
            y_coord = content["y"]
            viewport_x = content["viewport_x"]
            viewport_y = content["viewport_y"]
            item_name = content["item_name"]
            if player.client_player.deploy_phernalia(item_name, x_coord, y_coord):
                return get_viewport(viewport_x, viewport_y, player.client_player)
                # return get_viewport(viewport_x, viewport_y, player.client_player)
            else:
                return json.dumps({})
        case "deploy_atheneum":
            if player.client_player is None: return "No client."
            x_coord = content["x"]
            y_coord = content["y"]
            viewport_x = content["viewport_x"]
            viewport_y = content["viewport_y"]
            instance_name = content["instance_name"]
            if player.client_player.deploy_atheneum(instance_name, x_coord, y_coord):
                return get_viewport(viewport_x, viewport_y, player.client_player)
                # return get_viewport(viewport_x, viewport_y, player.client_player)
            else:
                return json.dumps({})
        case "revise":
            if player.client_player is None: return "No client."
            x_coord = content["x"]
            y_coord = content["y"]
            viewport_x = content["viewport_x"]
            viewport_y = content["viewport_y"]
            tile_char = content["tile_char"]
            if player.client_player.revise(tile_char, x_coord, y_coord):
                return get_viewport(viewport_x, viewport_y, player.client_player)
            else:
                return json.dumps({})
        case "add_to_atheneum":
            if player.client_player is None: return "No client."
            viewport_x = content["viewport_x"]
            viewport_y = content["viewport_y"]
            instance_name = content["instance_name"]
            target_room = player.client_player.land.housemap.find_room(viewport_x, viewport_y)
            if instance_name not in target_room.instances: return False
            target_room.remove_instance(instance_name)
            player.client_player.atheneum.append(instance_name)
            instance = alchemy.Instance(instance_name)
            player.client_player.starting_session.add_to_excursus(instance.item.name)
            return True
        case "recycle":
            if player.client_player is None: return "No client."
            instance_name = content["instance_name"]
            if instance_name not in player.client_player.atheneum: return False
            instance = alchemy.Instance(instance_name)
            player.client_player.atheneum.remove(instance_name)
            for grist_name, amount in instance.item.true_cost.items():
                player.client_player.add_grist(grist_name, amount)
            return True
        case "get_alchemiter_location":
            if player.client_player is None: return "No client."
            alchemiter_location = player.client_player.land.housemap.get_alchemiter_location()
            return json.dumps({"alchemiter_location": alchemiter_location})
        case "server_alchemy":
            if player.client_player is None: return "No client."
            alchemiter_loc = player.client_player.land.housemap.get_alchemiter_location()
            if alchemiter_loc is None: return "No alchemiter."
            code = content["code"]
            roomx, roomy = alchemiter_loc
            room = player.client_player.land.housemap.find_room(roomx, roomy)
            return alchemy.alchemize_instance(code, player.client_player, room)

def console_commands(player: sessions.SubPlayer, content: str):
    args = content.split(" ")
    command = args.pop(0)
    match command:
        case "harlify":
            item = alchemy.Item(" ".join(args))
            instance = alchemy.Instance(item)
            player.room.add_instance(instance.name)
        case "card":
            item = alchemy.Item("captchalogue card")
            instance = alchemy.Instance(item)
            player.room.add_instance(instance.name)
        case "gristify":
            grist_name = args[0]
            amount = int(args[1])
            player.add_grist(grist_name, amount)
        case "impify":
            if args: num = int(args[0])
            else: num = 1
            if len(args) > 1:
                tier = int(args[1])
            else:
                tier = random.randint(0,8)
            grist_name = config.gristcategories[player.gristcategory][tier]
            imp = npcs.underlings["imp"]
            for i in range(num):
                imp.make_npc(grist_name, player.land.gristcategory, player.room)
        case "enemify":
            underling_type = args[0]
            if len(args) > 1: num = int(args[1])
            else: num = 1
            if len(args) > 2:
                tier = int(args[2])
            else:
                tier = random.randint(0,8)
            grist_name = config.gristcategories[player.gristcategory][tier]
            underling = npcs.underlings[underling_type]
            for i in range(num):
                underling.make_npc(grist_name, player.land.gristcategory, player.room)
        case "overmap_move":
            direction = args[0]
            player.attempt_overmap_move(direction)
            return overmap_data(player)
        case "change_vial":
            vial = args[0]
            player.secondaryvial = vial
        case "change_class":
            class_name = args[0]
            player.gameclass = class_name
        case "change_aspect":
            aspect = args[0]
            player.aspect = aspect
        case "add_rungs":
            rungs = int(args[0])
            player.echeladder_rung += rungs
        case "enter_gate":
            gate_num = int(args[0])
            player.enter_gate(gate_num)
        case "set_rung":
            rung = int(args[0])
            player.echeladder_rung = rung
        case "reset_permanent_bonuses":
            player.permanent_stat_bonuses = {}
        case "enter_imps":
            player.map.populate_with_underlings("imp", 3, random.randint(40, 60), 1, 5)
        case "gushoverload":
            try:
                args_amount = int(args[0])
            except IndexError: args_amount = 0
            for grist_name in player.grist_cache:
                amount = args_amount or random.randint(0, player.grist_cache_limit)
                player.add_grist(grist_name, amount)
        case "bankgushry":
            for grist_name in player.grist_cache:
                player.grist_cache[grist_name] = 0
        case "homestuck":
            player.goto_room(player.land.housemap.random_valid_room(config.starting_tiles))
        case "tp":
            target_name = " ".join(args)
            if sessions.does_player_exist(target_name):
                target = sessions.Player(target_name).current_subplayer
                player.goto_room(target.room)
        case "unchain":
            if player.server_player is not None:
                player.server_player.client_player_name = None
                player.server_player_name = None
            if player.client_player is not None:
                player.client_player.server_player_name = None
                player.client_player_name = None
        case "summon":
            target_name = " ".join(args)
            if sessions.does_player_exist(target_name):
                target = sessions.Player(target_name).current_subplayer
                target.goto_room(player.room)
        case "sleep":
            player.sleep()

# return True on success, return False on failure
def use_item(player: sessions.SubPlayer, instance: alchemy.Instance, action_name, target_instance: Optional[alchemy.Instance] = None, additional_data: Optional[str]=None) -> bool:
    if instance.name not in player.sylladex and instance.name not in player.room.instances: return False
    if target_instance is not None and target_instance.name not in player.room.instances and target_instance.name not in player.sylladex: print("not in room"); return False
    if action_name not in instance.item.use: return False
    match action_name:
        case "add_card":
            if player.empty_cards >= 10: return False
            player.empty_cards += 1
            if instance.contained != "":
                contained_instance = alchemy.Instance(instance.contained)
                player.sylladex.append(contained_instance.name)
            return player.consume_instance(instance.name)
        case "computer":
            return True
        case "install_sburb":
            if target_instance is None: return False
            if "computer" not in target_instance.item.use: return False
            if "Sburb" not in target_instance.computer_data["installed_programs"]: target_instance.computer_data["installed_programs"].append("Sburb")
            return True
        case "install_gristtorrent":
            if target_instance is None: return False
            if "computer" not in target_instance.item.use: return False
            if "gristTorrent" not in target_instance.computer_data["installed_programs"]: target_instance.computer_data["installed_programs"].append("gristTorrent")
            return True
        case "combine_card":
            if target_instance is None: return False
            if target_instance.name not in player.sylladex: return False
            if target_instance.punched_code == "" or instance.punched_code == "": return False
            if target_instance.item.name != "punched card" or instance.item.name != "punched card": return False
            # if both items are real and not just bullshit
            new_code = ""
            if target_instance.punched_code in util.codes and instance.punched_code in util.codes:
                currently_punched_item = alchemy.Item(util.codes[instance.punched_code])
                additional_item = alchemy.Item(util.codes[target_instance.punched_code])
                alchemized_item_name = alchemy.alchemize(currently_punched_item.name, additional_item.name, "&&")
                alchemized_item = alchemy.Item(alchemized_item_name)
                new_code = alchemized_item.code
            else:
                # otherwise the code is just bullshit
                new_code = binaryoperations.codeor(target_instance.punched_code, instance.punched_code)
                alchemized_item = alchemy.Item.from_code(new_code)
            # make a new item containing the data of the old instance, the new instance becomes a container
            # for the old instance and the target
            if not player.consume_instance(target_instance.name): return False
            old_instance = alchemy.Instance(alchemy.Item("punched card"))
            old_instance.contained = instance.contained
            old_instance.combined = instance.combined
            old_instance.punched_code = instance.punched_code
            old_instance.punched_item_name = instance.punched_item_name
            instance.punched_code = new_code
            instance.punched_item_name = alchemized_item.displayname
            instance.combined = [old_instance.name, target_instance.name]
            return True
        case "uncombine_card":
            if instance.combined == []: print("not combined"); return False
            if not player.consume_instance(instance.name): print("couldnt consume"); return False
            card_1 = alchemy.Instance(instance.combined[0])
            card_2 = alchemy.Instance(instance.combined[1])
            player.room.add_instance(card_1.name)
            player.room.add_instance(card_2.name)
            return True
        case "enter":
            if not player.entered:
                if not player.consume_instance(instance.name): return False
                player.land.session.entered_players.append(player.player.id)
                player.land.theme = player.aspect
                player.map.populate_with_underlings("imp", 4, random.randint(40, 60), 1, 7)
                player.map.populate_with_underlings("ogre", 1, random.randint(1, 4), 1, 2)
                if not player.prototyped_before_entry: player.session.prototypes.append(None)
                return True
            else: return False
        case "alchemize":
            if not instance.inserted: print("nothing inserted"); return False
            inserted_instance = alchemy.Instance(instance.inserted)
            code = inserted_instance.carved
            return alchemy.alchemize_instance(code, player, player.room)
        case "unseal":
            instance.item_name = "cruxtruder"
            sprite = npcs.KernelSprite.spawn_new(player)
            player.room.add_npc(sprite)
            dowel_instance = alchemy.Instance(alchemy.Item("cruxite dowel"))
            dowel_instance.color = player.symbol_dict["color"]
            player.room.add_instance(dowel_instance.name)
            return True
        case "cruxtrude":
            dowel_instance = alchemy.Instance(alchemy.Item("cruxite dowel"))
            dowel_instance.color = player.symbol_dict["color"]
            player.room.add_instance(dowel_instance.name)
            return True
        case "insert_card":
            if target_instance is None: return False
            if target_instance.name not in player.sylladex: return False
            if instance.inserted != "": return False
            if not player.consume_instance(target_instance.name): return False
            player.empty_cards -= 1
            if target_instance.item.name != "captchalogue card" and target_instance.item.name != "punched card":
                card_instance = target_instance.to_card()
                instance.inserted = card_instance.name
            else:
                instance.inserted = target_instance.name
            return True
        case "remove_card":
            if instance.inserted == "": return False
            player.room.add_instance(instance.inserted)
            instance.inserted = ""
            return True
        case "punch_card":
            if instance.inserted == "": print("no instance inserted"); return False
            if additional_data is None:
                if target_instance is None: print("no target"); return False
                code_to_punch = target_instance.item.code
            else:
                code_to_punch = additional_data
            if len(code_to_punch) != 8: print("invalid code"); return False
            for char in code_to_punch:
                if char not in binaryoperations.bintable: print("invalid code"); return False
            if code_to_punch == "00000000": return True # no holes would be made
            if code_to_punch not in util.codes:
                paradox_item = alchemy.Item.from_code(code_to_punch)
                player.session.add_to_excursus(paradox_item.name)
            inserted_instance = alchemy.Instance(instance.inserted)
            if inserted_instance.item_name != "punched card": inserted_instance.item_name = "punched card"
            if inserted_instance.punched_code == "":
                inserted_instance.punched_code = code_to_punch
                if target_instance is not None: 
                    inserted_instance.punched_item_name = target_instance.item.displayname
                    player.session.add_to_excursus(target_instance.item.name)
                else:
                    new_item = alchemy.Item(util.codes[code_to_punch])
                    player.session.add_to_excursus(new_item.name)
                    inserted_instance.punched_item_name = new_item.displayname
                return True
            # if both items are real and not just bullshit
            if inserted_instance.punched_code in util.codes and code_to_punch in util.codes:
                currently_punched_item = alchemy.Item(util.codes[inserted_instance.punched_code])
                additional_item = alchemy.Item(util.codes[code_to_punch])
                alchemized_item_name = alchemy.alchemize(currently_punched_item.name, additional_item.name, "||")
                alchemized_item = alchemy.Item(alchemized_item_name)
                inserted_instance.punched_code = alchemized_item.code
                inserted_instance.punched_item_name = alchemized_item.displayname
                player.session.add_to_excursus(alchemized_item.name)
                return True
            else:
                print("This should not happen")
                raise AssertionError
        case "insert_dowel":
            if instance.inserted != "": print("something is already inserted"); return False
            if target_instance is None: print("no target"); return False
            if target_instance.item.name != "cruxite dowel": print("not a dowel"); return False
            if target_instance.carved != "00000000": print("dowel already carved"); return False
            if target_instance.name in player.sylladex:
                if not player.consume_instance(target_instance.name): print("couldn't consume"); return False
            else:
                if target_instance.name not in player.room.instances: print("couldn't find dowel in room"); return False
                player.room.remove_instance(target_instance.name)
            instance.inserted = target_instance.name
            return True
        case "remove_dowel":
            if instance.inserted == "": print("nothing in machine"); return False
            player.room.add_instance(instance.inserted)
            instance.inserted = ""
            return True
        case "insert_carved_dowel":
            if instance.inserted != "": print("something is already inserted"); return False
            if target_instance is None: print("no target"); return False
            if target_instance.item.name != "cruxite dowel": print("not a dowel"); return False
            if target_instance.name in player.sylladex:
                if not player.consume_instance(target_instance.name): print("couldn't consume"); return False
            else:
                if target_instance.name not in player.room.instances: print("couldn't find dowel in room"); return False
                player.room.remove_instance(target_instance.name)
            instance.inserted = target_instance.name
            return True
        case "lathe":
            if instance.inserted == "": print("nothing in machine"); return False
            if target_instance is None: print("no target"); return False
            if target_instance.item.name != "punched card": print("not punched card"); return False
            inserted_instance = alchemy.Instance(instance.inserted)
            inserted_instance.carved = target_instance.punched_code
            inserted_instance.carved_item_name = target_instance.punched_item_name
            # eject dowel
            player.room.add_instance(inserted_instance.name)
            instance.inserted = ""
            return True
        case "sleep":
            player.sleep()
            return True
        case _:
            return False

# can't check if these items are accessible by client modus, must be checked client side
def valid_use_targets(player: sessions.Player, instance: alchemy.Instance, action_name) -> list[str]:
    valid_target_names = []
    match action_name:
        case "install_sburb":
            def filter_func(name):
                if "computer" not in alchemy.Instance(name).item.use: return False
                return True
        case "install_gristtorrent":
            def filter_func(name):
                if "computer" not in alchemy.Instance(name).item.use: return False
                return True
        case "insert_card":
            def filter_func(name):
                if name not in player.sylladex: return False
                return True
        case "punch_card":
            def filter_func(name):
                if name not in player.sylladex: return False
                if alchemy.Instance(name).item.forbiddencode: return False
                return True
        case "combine_card":
            def filter_func(name):
                if name == instance.name: return False
                if name not in player.sylladex: return False
                if alchemy.Instance(name).punched_code == "": return False
                return True
        case "insert_dowel":
            def filter_func(name):
                filter_instance = alchemy.Instance(name)
                if filter_instance.item.name != "cruxite dowel": return False
                if filter_instance.carved != "00000000": return False
                return True
        case "insert_carved_dowel":
            def filter_func(name):
                filter_instance = alchemy.Instance(name)
                if filter_instance.item.name != "cruxite dowel": return False
                return True
        case "lathe":
            def filter_func(name):
                if name not in player.sylladex: return False
                filter_instance = alchemy.Instance(name)
                if filter_instance.item.name != "punched card": return False
                return True
        case _:
            return []
    valid_target_names = filter(filter_func, player.sylladex+player.room.instances)
    return list(valid_target_names)

def get_first_member_of_chain(player_name: str, checked=[]):
    player = sessions.Player(player_name)
    if player.server_player_name is None: return player_name
    # we're in a closed server chain
    elif player_name in checked: return player_name
    else:
        checked.append(player_name)
        return get_first_member_of_chain(player.server_player_name, checked)

# constructs chain from first member, or any member in a loop
def construct_chain(player_name: str) -> list:
    chain = [player_name]
    current_player = sessions.Player(player_name)
    while True:
        client_player_name = current_player.client_player_name
        # end of chain
        if client_player_name is None: return chain
        # we are in a closed chain
        elif client_player_name in chain:
            chain.append(client_player_name)
            return chain
        # add client to loop and loop again
        else: 
            chain.append(client_player_name)
            current_player = sessions.Player(client_player_name)

def autosave():
    last_save = time.time()
    util.saveall()
    while True:
        if time.time() - last_save > 60:
            util.saveall()
            last_save = time.time()

def console():
    while True:
        console_input = input()
          
def main():  
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(util.path_to_cert, util.path_to_key)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.bind((util.ip, util.port))
    with context.wrap_socket(sock, server_side=True) as ServerSocket:

        start_new_thread(autosave, ())
        start_new_thread(console, ())

        print("Waiting for connections...")
        ServerSocket.listen(5)

        threads = 0

        while True:
            try:
                Client, address = ServerSocket.accept()
                print(f"Connected to: {address[0]} : {str(address[1])}")
                start_new_thread(threaded_client, (Client, ))
                threads += 1
                print(f"Thread Number: {str(threads)}")
            except ConnectionResetError as e:
                print(e)
            except ssl.SSLError as e:
                print(e)
    
if __name__ == "__main__":
    main()