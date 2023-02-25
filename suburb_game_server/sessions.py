import json
import hashlib
import random
import os
from typing import Optional, Union
from copy import deepcopy

import util
import config
import tiles
import alchemy
import binaryoperations

map_tiles = {}

def map_from_file(file, folder=None):
    if folder == None:
        os.chdir(f"{util.homedir}\\maps")
    else:
        os.chdir(f"{util.homedir}\\maps\\{folder}")
    with open(f"{file}", "r") as f:
        content = f.read()
    content = content.split("\n") #split y axis
    map = []
    for line in content:
        map.append(list(line)) # split each string in content into a list of letters
    return map

def all_maps_in_folder(folder): # returns a list of all of the maps in a folder
    maps = []
    for filename in os.listdir(f"{util.homedir}\\maps\\{folder}"):
        maps.append(map_from_file(filename, folder))
    return maps

map_tiles["house"] = all_maps_in_folder("house")
map_tiles["land"] = all_maps_in_folder("land")
map_tiles["gateframe"] = all_maps_in_folder("gateframe")

class Session():
    def __init__(self, name):
        self.__dict__["session_name"] = name
        if name not in util.sessions:
            util.sessions[name] = {}
            self.starting_players = []
            self.connected = []
            # atheneum is a list of items that have been alchemized by all players in the session
            self.atheneum = []
            self.overmaps = {}          

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session_name"]][attr] = value
        self.__dict__[attr] = value
        
    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               [attr])
        return self.__dict__[attr]

    @property
    def current_grist_types(self) -> list:
        available_types = []
        for player_name in self.starting_players:
            player = Player(player_name)
            gristcategory = player.gristcategory
            for grist_name in config.gristcategories[gristcategory]:
                if grist_name not in available_types:
                    available_types.append(grist_name)
        return available_types

    @property
    def name(self):
        return self.__dict__["session_name"]

class Overmap(): # name is whatever, for player lands it's "{Player.name}{Player.session}"
    def __init__(self, name, session: Session, player: Optional["Player"] = None):
        self.__dict__["session_name"] = session.name
        self.__dict__["name"] = name
        if name not in util.sessions[session.name]["overmaps"]:
            util.sessions[session.name]["overmaps"][name] = {}
            self.maps = {}
            self.specials = []
        if player != None:
            self.__dict__["player_name"] = player.name
            self.gristcategory = player.gristcategory
            self.gen_overmap()
            self.gen_land_name()

    def gen_overmap(self):
        islands = config.categoryproperties[self.gristcategory]["islands"]
        landrate = config.categoryproperties[self.gristcategory]["landrate"]
        lakes = config.categoryproperties[self.gristcategory]["lakes"]
        lakerate = config.categoryproperties[self.gristcategory]["lakerate"]
        special = config.categoryproperties[self.gristcategory].get("special", None)
        extralands = config.categoryproperties[self.gristcategory].get("extralands", None)
        extrarate = config.categoryproperties[self.gristcategory].get("extrarate", None)
        extraspecial = config.categoryproperties[self.gristcategory].get("extraspecial", None)
        self.map_tiles = gen_overworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial)
        for line in self.map_tiles:
            print("".join(line))
        y = random.randint(0, len(self.map_tiles)-1)
        x = random.randint(0, len(self.map_tiles[0])-1)
        while self.map_tiles[y][x] == "~":
            y = random.randint(0, len(self.map_tiles)-1)
            x = random.randint(0, len(self.map_tiles[0])-1)
        housemap = self.find_map(x, y)
        housemap.gen_map("house")
        self.housemap_name = housemap.name
        self.specials.append(housemap.name)
        # todo: we're not doing this right now
        # housemap.gen_rooms()

    def gen_land_name(self):
        print(f"{self.gristcategory} {self.player.aspect}")
        print(f"Player {self.player} {self.player.name} {self.player_name}")
        print(f"grist {self.gristcategory} aspect {self.player.aspect}")
        bases = config.landbases[self.gristcategory] + config.aspectbases[self.player.aspect]
        random.seed(self.player.name)
        random.shuffle(bases)
        self.base1 = bases[0]
        if self.player.aspect != "space":
            self.base2 = bases[1]
        else:
            self.base2 = "frogs"
        self.title = f"Land of {self.base1.capitalize()} and {self.base2.capitalize()}"
        words = self.title.split(" ")
        acronym = ""
        for word in words:
            acronym += f"{word[0].upper()}"
        self.acronym = acronym

    def get_map(self, name:str) -> "Map":
        return Map(name, self.session, self)

    def find_map(self, x, y) -> "Map":
        return Map(f"{x}, {y}", self.session, self)

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.sessions[self.__dict__["session_name"]]["overmaps"][self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["name"]]
                               [attr])
        return self.__dict__[attr]

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def player(self) -> "Player":
        return Player(self.__dict__["player_name"])

    @property
    def name(self):
        return self.__dict__["name"]
    
    @property
    def housemap(self) -> "Map":
        return Map(self.housemap_name, self.session, self)

class Map():
    def __init__(self, name, session: Session, overmap: Overmap):
        self.__dict__["session_name"] = session.name
        self.__dict__["overmap_name"] = overmap.name
        self.__dict__["name"] = name  
        if name not in util.sessions[session.name]["overmaps"][overmap.name]["maps"]:
            util.sessions[session.name]["overmaps"][overmap.name]["maps"][name] = {}
            self.rooms = {}
            self.overmaptile = "~"
            coords = name.replace(",", "")
            coords = coords.split(" ")
            x = int(coords[0])
            y = int(coords[1])
            self.x = x
            self.y = y

    def gen_map(self, type=None):
        map = None
        match type:
            case "house":
                map = map_from_file("gates.txt")
                map += deepcopy(random.choice(map_tiles["house"]))
                self.overmaptile = "H"
            case "gate1":
                map = deepcopy(random.choice(map_tiles["gateframe"]))
                self.overmaptile = "1"
            case "gate2":
                map = deepcopy(random.choice(map_tiles["gateframe"]))
                self.overmaptile = "2"
            case "gate3":
                map = deepcopy(random.choice(map_tiles["gateframe"]))
                self.overmaptile = "3"
            case "gate4":
                map = deepcopy(random.choice(map_tiles["gateframe"]))
                self.overmaptile = "4"
            case "gate5":
                map = deepcopy(random.choice(map_tiles["gateframe"]))
                self.overmaptile = "5"
            case "gate6":
                map = deepcopy(random.choice(map_tiles["gateframe"]))
                self.overmaptile = "6"
            case "gate7":
                map = deepcopy(random.choice(map_tiles["gateframe"]))
                self.overmaptile = "7"
            case _:
                map = deepcopy(random.choice(map_tiles["land"]))
                self.overmaptile = "#"
        print("gen_map")
        self.map_tiles = map

    def gen_rooms(self):
        for y, line in enumerate(self.map_tiles):
            for x, char in enumerate(line):
                if char != ".":
                    r = self.find_room(x, y)

    def get_room(self, name: str) -> "Room":
        return Room(name, self.session, self.overmap, self)

    def find_room(self, x: int, y: int) -> "Room":
        return Room(f"{x}, {y}", self.session, self.overmap, self)
    
    def find_tiles_coords(self, valid_tiles: list) -> list:
        valid_coords = []
        for y, line in enumerate(self.map_tiles):
            for x, char in enumerate(line):
                if char in valid_tiles: valid_coords.append((x, y))
        return valid_coords
    
    def random_valid_room(self, valid_tiles: list) -> "Room":
        valid_coords = self.find_tiles_coords(valid_tiles)
        coords = random.choice(valid_coords)
        return self.find_room(coords[0], coords[1])

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["overmaps"][self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["name"]]
         [attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["name"]]
                               [attr])
        return self.__dict__[attr]

    def get_tile(self, x: int, y: int) -> tiles.Tile:
        return tiles.tiles[self.map_tiles[y][x]]
    
    def is_tile_in_bounds(self, x: int, y: int) -> bool:
        if y < 0: return False
        if x < 0: return False
        if y >= len(self.map_tiles): return False
        if x >= len(self.map_tiles[0]): return False
        return True

    def get_view(self, target_x: int, target_y: int, view_tiles: int, server_view=False) -> tuple[list, dict]:
        if not self.is_tile_in_bounds(target_x, target_y): return ([], {})
        out_map_tiles = []
        out_specials = {}
        map_tiles = self.map_tiles
        # we need both the y of the real map(real_y) and the y of the output tile(map_tile_y)
        for map_tile_y, real_y in enumerate(range(target_y-view_tiles, target_y+view_tiles+1)):
            new_line = []
            for map_tile_x, real_x in enumerate(range(target_x-view_tiles, target_x+view_tiles+1)):
                if real_y < 0 or real_y >= len(map_tiles): new_line.append("?") # out of bounds
                elif real_x < 0 or real_x >= len(map_tiles[0]): new_line.append("?") # out of bounds
                else: 
                    new_line.append(map_tiles[real_y][real_x])
                    specials = self.find_room(real_x, real_y).specials
                    if server_view and real_x == target_x and real_y == target_y: specials["cursor"] = "cursor"
                    if len(specials) > 0: out_specials[f"{map_tile_x}, {map_tile_y}"] = specials
            out_map_tiles.append(new_line)
        return out_map_tiles, out_specials

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def overmap(self) -> Overmap:
        return Overmap(self.__dict__["overmap_name"], self.session)

    @property
    def player(self) -> "Player":
        return Player(self.__dict__["player_name"])

    @property
    def name(self):
        return self.__dict__["name"]

class Room():
    def __init__(self, name, session: Session, overmap: Overmap, map: Map):
        self.__dict__["session_name"] = session.name
        self.__dict__["overmap_name"] = overmap.name
        self.__dict__["map_name"] = map.name
        self.__dict__["name"] = name
        if name not in util.sessions[session.name]["overmaps"][overmap.name]["maps"][map.name]["rooms"]:
            util.sessions[session.name]["overmaps"][overmap.name]["maps"][map.name]["rooms"][name] = {}
            coords = name.replace(",", "")
            coords = coords.split(" ")
            x = int(coords[0])
            y = int(coords[1])
            self.x = x
            self.y = y
            self.players: list[str] = []
            self.instances: list[str] = []
            self.generate_loot()

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["overmaps"][self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["map_name"]]
         ["rooms"][self.__dict__["name"]]
         [attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["map_name"]]
                               ["rooms"][self.__dict__["name"]]
                               [attr])
        return self.__dict__[attr]

    def add_player(self, player: "Player"):
        if player.username not in self.players:
            self.players.append(player.username)

    def remove_player(self, player: "Player"):
        if player.username in self.players:
            self.players.remove(player.username)

    def generate_loot(self, spawns: Optional[list[str]] = None):
        if not self.tile.generate_loot: return
        if spawns is None:
            spawns = self.tile.get_loot_list()
        for item_name in spawns:
            item = alchemy.Item(item_name)
            instance = alchemy.Instance(item)
            self.add_instance(instance.name)
        
    def add_instance(self, instance_name: str):
        if instance_name not in self.instances:
            self.instances.append(instance_name)
    
    def remove_instance(self, instance_name: str):
        if instance_name in self.instances:
            self.instances.remove(instance_name)

    def get_instances(self) -> dict:
        out_dict = {}
        for instance_name in self.instances:
            instance = alchemy.Instance(instance_name)
            out_dict[instance_name] = instance.get_dict()
        return out_dict

    @property
    def specials(self) -> dict:
        special_dict = {}
        for player_username in self.players:
            player = Player(player_username)
            special_dict[player.calledby] = "player"
        for instance_name in self.instances:
            instance = alchemy.Instance(instance_name)
            if instance.item.name in config.special_items:
                special_dict[instance_name] = instance.item.name
        # todo: other specials
        return special_dict

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def overmap(self) -> Overmap:
        return Overmap(self.__dict__["overmap_name"], self.session)
    
    @property
    def map(self) -> Map:
        return Map(self.__dict__["map_name"], self.session, self.overmap)

    @property
    def player(self) -> "Player":
        return self.overmap.player

    @property
    def name(self):
        return self.__dict__["name"]

    @property
    def tile(self) -> tiles.Tile:
        return self.map.get_tile(self.x, self.y)


class Player():
    def __init__(self, username):
        self.__dict__["username"] = username
        if username not in util.players:
            util.players[username] = {}
            self.session_name = None
            self.overmap_name = None
            self.map_name = None
            self.room_name = None
            self.sylladex: list[str] = []
            self.moduses: list[str] = []
            self.empty_cards = 5
            self.echeladder_rung = 1
            self.grist_cache = {grist_name:0 for grist_name in config.grists}
            self.grist_gutter: list[list] = []
            self.leeching: list[str] = []
            # phernalia registry is a default list of deployable objects minus the deployed phernalia
            self.deployed_phernalia = []
            self.server_storage = []
            self.client_player_name: Optional[str] = None
            self.server_player_name: Optional[str] = None
            self.setup = False
            self.nickname = ""
            self.noun = ""
            self.pronouns = []
            self.interests = []
            self.aspect = ""
            self.gameclass = ""
            self.gristcategory = ""
            self.secondaryvial = ""
            self.land_name = ""
            self.land_session = ""

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.players[self.__dict__["username"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = util.players[self.__dict__["username"]][attr]
        return self.__dict__[attr]
    
    def get_dict(self):
        out = deepcopy(util.players[self.__dict__["username"]])
        out["grist_cache_limit"] = self.grist_cache_limit
        out["total_gutter_grist"] = self.total_gutter_grist
        out["available_phernalia"] = self.available_phernalia
        return out
    
    def captchalogue(self, instance_name: str, modus_name: str) -> bool:
        if instance_name not in self.room.instances: return False
        if modus_name not in self.moduses: return False
        if instance_name in self.sylladex: return False
        if len(self.sylladex) + 1 > self.empty_cards: return False
        max_size = config.modus_max_sizes.get(modus_name, 30)
        instance = alchemy.Instance(instance_name)
        if instance.item.size > max_size: return False
        self.sylladex.append(instance_name)
        self.room.remove_instance(instance_name)
        return True
    
    def eject(self, instance_name: str, modus_name: str, velocity: int) -> bool:
        if instance_name not in self.sylladex: return False
        # todo: make this shit fly based on its velocity
        self.sylladex.remove(instance_name)
        self.room.add_instance(instance_name)
        return True
    
    def uncaptchalogue(self, instance_name: str) -> bool:
        if instance_name not in self.sylladex: return False
        self.sylladex.remove(instance_name)
        self.room.add_instance(instance_name)
        return True
    
    def consume_instance(self, instance_name: str) -> bool:
        if instance_name not in self.sylladex: return False
        self.sylladex.remove(instance_name)
        print(f"consuming {instance_name}")
        return True
    
    def drop_empty_card(self) -> bool:
        if self.empty_cards - len(self.sylladex) > 0:
            self.empty_cards -= 1
            self.room.add_instance(alchemy.Instance(alchemy.Item("captchalogue card")).name)
            return True
        else:
            return False
    
    def add_grist(self, grist_name: str, amount: int):
        current_grist = self.grist_cache[grist_name]
        if current_grist + amount <= self.grist_cache_limit:
            self.grist_cache[grist_name] = current_grist + amount
            return
        else:
            self.grist_cache[grist_name] = self.grist_cache_limit
            overflow = self.grist_cache[grist_name] - current_grist
            if self.grist_gutter[-1][0] == grist_name:
                self.grist_gutter[-1] = [grist_name, self.grist_gutter[-1][1] + overflow]
            else:
                self.grist_gutter.append([grist_name, overflow])

    @property
    def total_gutter_grist(self) -> int:
        total = 0
        for grist_name, amount in self.grist_gutter:
            total += amount
        return total

    def sylladex_instances(self) -> dict:
        out_dict = {}
        for instance_name in self.sylladex:
            instance = alchemy.Instance(instance_name)
            out_dict[instance_name] = instance.get_dict()
        return out_dict

    def add_modus(self, modus_name: str) -> bool:
        if modus_name in self.moduses: return False
        if modus_name not in self.moduses: self.moduses.append(modus_name)
        return True
    
    def attempt_move(self, direction: str) -> bool:
        player_x = self.room.x
        player_y = self.room.y
        map = self.map
        target_x: int = 0
        target_y: int = 0
        if direction == "up": target_x, target_y = player_x, player_y-1
        if direction == "down": target_x, target_y = player_x, player_y+1
        if direction == "left": target_x, target_y = player_x-1, player_y
        if direction == "right": target_x, target_y = player_x+1, player_y
        if not map.is_tile_in_bounds(target_x, target_y): return False
        current_tile = map.get_tile(player_x, player_y)
        while True:
            target_tile = map.get_tile(target_x, target_y)
            if target_tile.impassible: return False
            if direction == "up":
                if not target_tile.stair and not current_tile.stair: return False    # obey gravity
                if target_tile.automove:
                    target_y -= 1
                    continue
                else:
                    break
            if direction == "down":
                if target_tile.automove:
                    target_y += 1
                    continue
                else:
                    break
            if direction in ["right", "left"] and target_tile.ramp:
                if direction == "right" and target_tile.ramp_direction in ["right", "both"]:
                    target_x += 1
                    target_y -= 1
                    continue
                elif direction == "left" and target_tile.ramp_direction in ["left", "both"]:
                    target_x -= 1
                    target_y -= 1
                    continue
            break
        # fall
        while not target_tile.stair:
            fall_tile = map.get_tile(target_x, target_y+1)
            if fall_tile.infallible or fall_tile.impassible: break
            # fall in opposite direction that ramps face
            if fall_tile.ramp and fall_tile.ramp_direction == "left": target_x += 1
            if fall_tile.ramp and fall_tile.ramp_direction == "right": target_x -= 1
            target_y += 1
        new_room = map.find_room(target_x, target_y)
        self.goto_room(new_room)
        return True

    @property
    def session(self) -> Session:
        return Session(self.session_name)
    
    @property
    def overmap(self) -> Overmap:
        return Overmap(self.overmap_name, self.session)
    
    @property
    def map(self) -> Map:
        return Map(self.map_name, self.session, self.overmap)
    
    def get_view(self, view_tiles=6) -> tuple[list, dict, dict]:
        map_tiles, map_specials = self.map.get_view(self.room.x, self.room.y, view_tiles)
        room_instances = self.room.get_instances()
        return map_tiles, map_specials, room_instances

    @property
    def room(self) -> Room:
        return Room(self.room_name, self.session, self.overmap, self.map)
    
    def goto_room(self, room: Room):
        if self.room_name is not None: self.room.remove_player(self)
        self.session_name = room.session.name
        self.overmap_name = room.overmap.name
        self.map_name = room.map.name
        self.room_name = room.name
        room.add_player(self)

    @property
    def grist_cache_limit(self):
        mult = 1 + self.echeladder_rung//100
        return 10*self.echeladder_rung*mult
    
    @property
    def available_phernalia(self):
        connected = self.session.connected
        available_phernalia = ["cruxtruder", "totem lathe", "alchemiter", "punch designix", "pre-punched card"]
        if len(connected) >= 2:
            # todo: add more phernalia with more connections
            ...
        for item in self.deployed_phernalia:
            available_phernalia.remove(item)
        phernalia_dict = {}
        for item_name in available_phernalia:
            phernalia_dict[item_name] = alchemy.Item(item_name).get_dict()
        return phernalia_dict


    @property
    def coords(self):
        return self.room.x, self.room.y

    @property
    def name(self):
        return self.__dict__["username"]
    
    @property
    def username(self):
        return self.__dict__["username"]

    @property
    def calledby(self):
        return self.nickname

    @property
    def land(self) -> Overmap:
        return Overmap(self.land_name, Session(self.land_session))
    
    @property
    def server_player(self) -> Optional["Player"]:
        if self.server_player_name is None: return None
        else: return Player(self.server_player_name)
    
    @property
    def client_player(self) -> Optional["Player"]:
        if self.client_player_name is None: return None
        else: return Player(self.client_player_name)

    def verify(self, hash): # returns True if hash is valid
        if hash == self.character_pass_hash:
            return True
        else:
            return False

def gen_terrain(x, y, map, replacetile, terrain, depth=0):
    if map[y][x] == "*":
        for coordinate in [(-1, 0), (1, 0), (0, 1), (0, -1)]: # up down left right
            try:
                tile = map[y+coordinate[1]][x+coordinate[0]]
                rng = random.random()
                if rng < terrain - (0.1 * depth * terrain): # chance to generate more terrain lowers with depth
                    map[y+coordinate[1]][x+coordinate[0]] = "*"
                    map = gen_terrain(x+coordinate[0], y+coordinate[1], map, tile, terrain, depth+1)
            except IndexError:
                pass
    if depth == 0:
        for y, line in enumerate(map):
            for x, char in enumerate(line):
                if char == "*":
                    map[y][x] = replacetile
    return map

def modify_block(map, checktile, replacetile):
    newmap = map.copy()
    while True:
        removed = 0
        print("-----")
        for line in newmap:
            ln = ""
            for char in line:
                ln += char
            print(ln)
        for y, line in enumerate(newmap):
            for x, char in enumerate(line):
                valid = check_block(x, y, newmap, checktile)
                if valid == False:
                    newmap[y][x] = replacetile
                    removed += 1
        if removed == 0:
            break
    return newmap

def check_block(x, y, map, checktile):
    adjacent = 0
    if map[y][x] != checktile: return True
    for coordinate in [(-1, 0), (1, 0), (0, 1), (0, -1)]: # up down left right
        try:
            tile = map[y+coordinate[1]][x+coordinate[0]]
            if tile == checktile:
                adjacent += 1
        except IndexError:
            pass
    if adjacent != 1: return True
    else: return False

def gen_overworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial):
    map = [
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
        ["~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~","~"],
    ]
    for i in range(0, islands): # generate islands
        if special == "center":
            y = int(len(map)/2)
            x = int(len(map[0])/2)
        elif special == "dual":
            if i % 2 == 0:
                x = int(len(map[0])/7)
                y = int(len(map)/4) * 3
            else:
                x = int(len(map[0])/7) * 6
                y = int(len(map)/4)
        else:
            y = random.randint(0, len(map)-1)
            x = random.randint(0, len(map[0])-1)
        map[y][x] = "*" # placeholder terrain tile
        map = gen_terrain(x, y, map, "#", landrate)
    for i in range(0, lakes): # generate lakes
        y = random.randint(0, len(map)-1)
        x = random.randint(0, len(map[0])-1)
        map[y][x] = "*" # placeholder terrain tile
        map = gen_terrain(x, y, map, "~", lakerate)
    if special == "block":
        print("block special")
        map = modify_block(map, "#", "~")
        map = modify_block(map, "~", "#")
    if extralands != None:
        for i in range(0, extralands): # generate extra islands
            if extraspecial == "center":
                y = int(len(map)/2)
                x = int(len(map[0])/2)
            elif extraspecial == "dual":
                if i % 2 == 0:
                    x = int(len(map[0])/7)
                    y = int(len(map)/4) * 3
                else:
                    x = int(len(map[0])/7) * 6
                    y = int(len(map)/4)
            else:
                y = random.randint(0, len(map)-1)
                x = random.randint(0, len(map[0])-1)
            map[y][x] = "*" # placeholder terrain tile
            map = gen_terrain(x, y, map, "#", extrarate)
    return map
