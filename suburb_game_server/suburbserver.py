import socket
import os
from _thread import start_new_thread
import json
import hashlib
import time
from typing import Optional

import sessions
import alchemy
import util
import config
import tiles
import binaryoperations

HOST_IP = "192.168.4.28"
PORT = 25565

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
            intent = dict["intent"]
            session_name = dict["session_name"]
            session_pass_hash = dict["session_pass_hash"]
            if intent == "create_session":
                if len(session_name) > 32: reply = "fuck you"
                elif session_name in util.sessions:
                    reply = f"The session `{session_name}` is already registered."
                else:
                    session = sessions.Session(session_name)
                    session.pass_hash = dict["session_pass_hash"]
                    print(f"session created {session_name}")
                    reply = f"The session `{session_name}` has been successfully registered."
            else:
                if session_name in util.sessions:
                    session = sessions.Session(session_name)
                    if session_pass_hash == session.pass_hash:
                        reply = handle_request(dict)
                    else:
                        reply = f"Incorrect session password."
                else:
                    reply = f"Invalid session name `{session_name}`."
            connection.sendall(str.encode(str(reply)))
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
    session_name = dict["session_name"]
    session = sessions.Session(session_name)
    character = dict["character"]
    character_pass_hash = dict["character_pass_hash"]
    content = dict["content"]
    if intent == "create_character":
        if character in util.players:
            return f"Character id `{character}` has already been made."
        else:
            player = sessions.Player(character)
            player.character_pass_hash = character_pass_hash
            return f"Successfully created `{character}`. You may now log in."
    if character not in util.players:
        return f"Character {character} does not exist."
    player = sessions.Player(character)
    if not player.verify(character_pass_hash):
        return f"Incorrect character password."
    match intent:
        case "login":
            return f"Successfully logged in!"
        case "interests":
            return json.dumps(config.interests)
        case "setup_character":
            if player.setup:
                return "That character has already been setup!"
            else:
                player.nickname = content["name"]
                player.noun = content["noun"]
                player.pronouns = content["pronouns"]
                player.interests = content["interests"]
                player.aspect = content["aspect"]
                player.gameclass = content["class"]
                player.gristcategory = content["gristcategory"]
                player.secondaryvial = content["secondaryvial"]
                player.add_modus(content["modus"])
                land = sessions.Overmap(f"{player.name}{session.name}", session, player)
                player.land_name = land.name
                player.land_session = session.name
                housemap = land.get_map(land.housemap_name)
                print(f"housemap {housemap.name} {housemap}")
                print(f"housemap session {housemap.session.name} {housemap.session}")
                print(f"overmap {housemap.overmap.name} {housemap.overmap}")
                room = housemap.random_valid_room(config.starting_tiles)
                for interest in player.interests:
                    room.generate_loot(tiles.get_tile(interest).get_loot_list())
                player.goto_room(room)
                player.setup = True
                return f"Your land is the {land.title}! ({land.acronym})"
        case "current_map":
            map_tiles, map_specials, room_instances = player.get_view()
            return json.dumps({"map": map_tiles, "specials": map_specials, "instances": room_instances, "room_name": player.room.tile.name})
        case "player_info":
            return json.dumps(player.get_dict())
        case "sylladex":
            return json.dumps(player.sylladex_instances())
        case "use_item":
            instance_name = content["instance_name"]
            action_name = content["action_name"]
            target_name = content["target_name"]
            instance = alchemy.Instance(instance_name)
            if target_name is not None: target_instance = alchemy.Instance(target_name)
            else: target_instance = None
            return use_item(player, instance, action_name, target_instance)
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
                instances_dict[name] = alchemy.Instance(name).get_dict()
            return json.dumps(instances_dict)
        case "move":
            player.attempt_move(content)
            return
        case "console_command":
            console_commands(player, content)


def console_commands(player: sessions.Player, content: str):
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

# return True on success, return False on failure
def use_item(player: sessions.Player, instance: alchemy.Instance, action_name, target_instance: Optional[alchemy.Instance] = None, additional_data: Optional[str]=None) -> bool:
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
            if instance.name in player.sylladex:
                return player.consume_instance(instance.name)
            else:
                player.room.remove_instance(instance.name)
                return True
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
                alchemized_item = None
            # make a new item containing the data of the old instance, the new instance becomes a container
            # for the old instance and the target
            if not player.consume_instance(target_instance.name): return False
            old_instance = alchemy.Instance(alchemy.Item("punched card"))
            old_instance.contained = instance.contained
            old_instance.combined = instance.combined
            old_instance.punched_code = instance.punched_code
            old_instance.punched_item_name = instance.punched_item_name
            instance.punched_code = new_code
            if alchemized_item is not None:
                instance.punched_item_name = alchemized_item.displayname
            instance.combined = [old_instance.name, target_instance.name]
            return True
        case "uncombine_card":
            if instance.combined == []: print("not combined"); return False
            if instance.name in player.sylladex:
                if not player.consume_instance(instance.name): print("couldnt consume"); return False
            else:
                if instance.name not in player.room.instances: print("item not in room"); return False
                player.room.remove_instance(instance.name)
            card_1 = alchemy.Instance(instance.combined[0])
            card_2 = alchemy.Instance(instance.combined[1])
            player.room.add_instance(card_1.name)
            player.room.add_instance(card_2.name)
            return True
        case "cruxtrude":
            dowel_instance = alchemy.Instance(alchemy.Item("cruxite dowel"))
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
            inserted_instance = alchemy.Instance(instance.inserted)
            if inserted_instance.item_name != "punched card": inserted_instance.item_name = "punched card"
            if inserted_instance.punched_code == "":
                inserted_instance.punched_code = code_to_punch
                if target_instance is not None: 
                    inserted_instance.punched_item_name = target_instance.item.displayname
                    print(f"punching {inserted_instance.name} with {target_instance.name}")
                return True
            # if both items are real and not just bullshit
            if inserted_instance.punched_code in util.codes and code_to_punch in util.codes:
                currently_punched_item = alchemy.Item(util.codes[inserted_instance.punched_code])
                additional_item = alchemy.Item(util.codes[code_to_punch])
                alchemized_item_name = alchemy.alchemize(currently_punched_item.name, additional_item.name, "||")
                alchemized_item = alchemy.Item(alchemized_item_name)
                inserted_instance.punched_code = alchemized_item.code
                inserted_instance.punched_item_name = alchemized_item.displayname
                print(f"punching {currently_punched_item.name} with {additional_item.name} makes {alchemized_item.displayname}")
                return True
            # otherwise the code is just bullshit
            inserted_instance.punched_code = binaryoperations.codeor(inserted_instance.punched_code, code_to_punch)
            inserted_instance.punched_item_name = ""
            print("bullshit code")
            return True
        case "insert_dowel":
            if instance.inserted != "": print("something is already inserted"); return False
            if target_instance is None: print("no target"); return False
            if target_instance.item.name != "cruxite dowel": print("not a dowel"); return False
            if target_instance.carved != "00000000": print("dowel already carved"); return False
            if target_instance.name in player.sylladex:
                if not player.consume_instance(target_instance.name): print("couldn't consume"); return False
            else:
                if target_instance.name not in player.room: print("couldn't find dowel in room"); return False
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
                if target_instance.name not in player.room: print("couldn't find dowel in room"); return False
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
            
    
if __name__ == "__main__":
    ServerSocket = socket.socket()
    try:
        ServerSocket.bind((HOST_IP, PORT))
    except socket.error as e:
        print(str(e))

    start_new_thread(autosave, ())
    start_new_thread(console, ())

    print("Waiting for connections...")
    ServerSocket.listen(5)

    conns = []
    threads = 0
    

    while True:
        Client, address = ServerSocket.accept()
        print(f"Connected to: {address[0]} : {str(address[1])}")
        start_new_thread(threaded_client, (Client, ))
        threads += 1
        print(f"Thread Number: {str(threads)}")
