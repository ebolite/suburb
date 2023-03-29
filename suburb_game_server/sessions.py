import json
import hashlib
import random
import os
import time
import numpy as np
from string import ascii_letters
from typing import Optional, Union
from copy import deepcopy

import util
import config
import tiles
import alchemy
import binaryoperations
import npcs
import strife
import skills
import stateseffects
import suburbserver
from strife import Strife


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
    def __new__(cls, name) -> Optional["Session"]:
        if name not in util.memory_sessions:
            print("session does not exist")
            return None
        else: return super().__new__(cls)

    def __init__(self, name):
        self.__dict__["_id"] = name

    @classmethod
    def create_session(cls, name, password) -> Optional["Session"]:
        if name in util.memory_sessions: return None
        util.memory_sessions[name] = {}
        session = cls(name)
        session.setup_defaults(name, password)

    def setup_defaults(self, name, password):
        self._id = name
        # username: {"normal_self": blah, "dream_self": blah1}
        self.user_players: dict[str, dict[str, str]] = {}
        self.user_current_players: dict[str, Optional[str]] = {}
        self.current_players: list[str] = []
        self.starting_players: list[str] = []
        self.connected: list[str] = []
        self.entered_players: list[str] = []
        self.excursus = ["captchalogue card", "perfectly generic object"]
        self.overmaps = {}
        self.prototypes: list[Optional[str]] = []
        self.set_password(password)

    def add_to_excursus(self, item_name):
        if item_name not in self.excursus:
            self.excursus.append(item_name)

    def get_best_seeds(self):
        best_seeds = {}
        for player in self.players_list:
            for grist_name, rate in player.seeds.items():
                if grist_name not in best_seeds: best_seeds[grist_name] = rate
                elif best_seeds[grist_name] < rate: best_seeds[grist_name] = rate
        return best_seeds

    def __setattr__(self, attr, value):
        util.memory_sessions[self.__dict__["session_name"]][attr] = value
        self.__dict__[attr] = value
        
    def __getattr__(self, attr):
        self.__dict__[attr] = (util.memory_sessions[self.__dict__["session_name"]]
                               [attr])
        return self.__dict__[attr]
    
    def set_password(self, password: str):
        self.salt = os.urandom(32).hex()
        plaintext = password.encode()
        digest = hashlib.pbkdf2_hmac("sha256", plaintext, bytes.fromhex(self.salt), 10000)
        hex_hash = digest.hex()
        self.hashed_password = hex_hash
    
    def verify_password(self, password: str):
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(self.salt), 10000)
        new_hash = digest.hex()
        if new_hash == self.hashed_password: return True
        else: return False

    def get_current_player(self, user: "suburbserver.User") -> Optional["Player"]:
        player_type = self.user_current_players[user.name]
        if player_type is None: return None
        player_name = self.user_players[user.name][player_type]
        return Player(player_name)

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
    def players_list(self) -> list["Player"]:
        return [Player(name) for name in self.current_players]

    @property
    def name(self) -> str:
        return self.__dict__["session_name"]

class Overmap(): # name is whatever, for player lands it's "{Player.name}{Player.session}"
    def __init__(self, name, session: Session, player: Optional["Player"] = None):
        self.__dict__["session_name"] = session.name
        self.__dict__["name"] = name
        if name not in session.overmaps:
            print("overmap not in session")
            session.overmaps[name] = {}
            self.maps = {}
            self.specials = []
        if player != None:
            self.player_name = player.name
            self.gristcategory = player.gristcategory
            self.theme = "default"
            self.gate_maps: dict[str, str] = {}
            self.gen_overmap()
            self.gen_land_name()
            print(f"{self.title.upper()}")
            print_map(self.map_tiles)

    def gen_overmap(self):
        islands = config.categoryproperties[self.gristcategory]["islands"]
        landrate = config.categoryproperties[self.gristcategory]["landrate"]
        lakes = config.categoryproperties[self.gristcategory]["lakes"]
        lakerate = config.categoryproperties[self.gristcategory]["lakerate"]
        special = config.categoryproperties[self.gristcategory].get("special", None)
        extralands = config.categoryproperties[self.gristcategory].get("extralands", None)
        extrarate = config.categoryproperties[self.gristcategory].get("extrarate", None)
        extraspecial = config.categoryproperties[self.gristcategory].get("extraspecial", None)
        steepness = config.categoryproperties[self.gristcategory].get("steepness", 1.0)
        smoothness = config.categoryproperties[self.gristcategory].get("smoothness", 0.5)
        self.map_tiles = gen_overworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial)
        housemap_x, housemap_y = get_random_land_coords(self.map_tiles)
        housemap = self.find_map(housemap_x, housemap_y)
        housemap.gen_map("house")
        housemap.special_type = "house"
        self.housemap_name = housemap.name
        self.specials.append(housemap.name)
        last_gate_x, last_gate_y = 0, 0
        for gate_num in range(1, 8): # gates 1-7
            if gate_num % 2 == 1: # even numbered gates should be close to odd numbered gates before them
                gate_x, gate_y = get_tile_at_distance(self.map_tiles, housemap_x, housemap_y, gate_num*9, self.specials)
                last_gate_x, last_gate_y = gate_x, gate_y
            else:
                gate_x, gate_y = get_tile_at_distance(self.map_tiles, last_gate_x, last_gate_y, gate_num*4, self.specials)
            gate_map = self.find_map(gate_x, gate_y)
            gate_map.gen_map(f"gate{gate_num}")
            gate_map.special_type = "gate"
            self.gate_maps[str(gate_num)] = gate_map.name
            if gate_num == 1 or gate_num == 2:
                # first and second gates are in a bowl
                self.map_tiles = set_height(self.map_tiles, gate_x, gate_y, 2, 4, 2)
            self.map_tiles = set_height(self.map_tiles, gate_x, gate_y, gate_num, 3)
        self.map_tiles = make_height_map(self.map_tiles, steepness, smoothness)
        self.map_tiles = set_height(self.map_tiles, housemap_x, housemap_y, 1, 3)
        self.map_tiles = set_height(self.map_tiles, housemap_x, housemap_y, 9)

    def gen_land_name(self):
        assert self.player is not None
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

    def get_view(self, target_x: int, target_y: int, view_tiles: int) -> tuple[list, dict, dict]:
        if not self.is_tile_in_bounds(target_x, target_y): return ([], {}, {})
        out_map_tiles = []
        out_specials = {}
        map_types = {}
        map_tiles = self.map_tiles
        for map_tile_y, real_y in enumerate(range(target_y-view_tiles, target_y+view_tiles+1)):
            new_line = []
            for map_tile_x, real_x in enumerate(range(target_x-view_tiles, target_x+view_tiles+1)):
                map_x, map_y = real_x, real_y
                if map_y < 0: map_y += len(map_tiles)
                if map_y >= len(map_tiles): map_y -= len(map_tiles) # loop if out of bounds
                if map_x < 0: map_x += len(map_tiles[0])
                if map_x >= len(map_tiles[0]): map_x -= len(map_tiles[0])
                new_line.append(map_tiles[map_y][map_x])
                map = self.find_map(map_x, map_y)
                specials = map.specials
                if len(specials) > 0: out_specials[f"{map_tile_x}, {map_tile_y}"] = specials
                if map.special_type: map_types[f"{map_tile_x}, {map_tile_y}"] = map.special_type
            out_map_tiles.append(new_line)
        return out_map_tiles, out_specials, map_types

    def is_tile_in_bounds(self, x: int, y: int) -> bool:
        if y < 0: return False
        if x < 0: return False
        if y >= len(self.map_tiles): return False
        if x >= len(self.map_tiles[0]): return False
        return True

    def get_map(self, name:str) -> "Map":
        return Map(name, self.session, self)

    def find_map(self, x, y) -> "Map":
        if y < 0: y += len(self.map_tiles)
        if y >= len(self.map_tiles): y -= len(self.map_tiles) # loop if out of bounds
        if x < 0: x += len(self.map_tiles[0])
        if x >= len(self.map_tiles[0]): x -= len(self.map_tiles[0])
        return Map(f"{x}, {y}", self.session, self)

    def clientdepth(self, depth):
        output_player = self.player
        if output_player is None: return None
        for i in range(depth):
            if output_player.client_player is not None:
                output_player = output_player.client_player
            else:
                output_player = None
                return output_player
        return output_player
    
    def serverdepth(self, depth):
        output_player = self.player
        if output_player is None: return None
        for i in range(depth):
            if output_player.server_player is not None:
                output_player = output_player.server_player
            else:
                output_player = None
                return output_player
        return output_player

    def gate_location(self, gate_num: int, at_house: bool) -> Optional["Player"]:
        landowner = self.player
        gates = { # left: housegate right: landgate
            0: [landowner, landowner], # return gate
            1: [landowner, landowner],
            2: [self.clientdepth(1), self.serverdepth(1)],
            3: [landowner, landowner],
            4: [self.clientdepth(2), self.serverdepth(2)],
            5: [landowner, landowner],
            6: [self.clientdepth(3), self.serverdepth(3)],
            7: [landowner, landowner] # not implemented, second gate leads to denizen
            }
        if at_house: return gates[gate_num][0]
        else: return gates[gate_num][1]

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        session = Session(self.__dict__["session_name"])
        session.overmaps[self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        session = Session(self.__dict__["session_name"])
        self.__dict__[attr] = session.overmaps[self.__dict__["name"]][attr]
        return self.__dict__[attr]

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def player(self) -> Optional["Player"]:
        try:
            return Player(self.player_name)
        except KeyError: return None

    @property
    def name(self) -> str:
        return self.__dict__["name"]
    
    @property
    def housemap(self) -> "Map":
        return Map(self.housemap_name, self.session, self)

class Map():
    def __init__(self, name, session: Session, overmap: Overmap):
        self.__dict__["session_name"] = session.name
        self.__dict__["overmap_name"] = overmap.name
        self.__dict__["name"] = name  
        if name not in session.overmaps[overmap.name]["maps"]:
            session.overmaps[overmap.name]["maps"][name] = {}
            self.special: Optional[str] = None
            self.discovered = False
            self.rooms = {}
            self.overmaptile = "~"
            coords = name.replace(",", "")
            coords = coords.split(" ")
            x = int(coords[0])
            y = int(coords[1])
            self.x = x
            self.y = y
            self.map_tiles = []
            self.special_type = ""

    def gen_map(self, type=None):
        map = None
        match type:
            case "house":
                map = map_from_file("gates.txt")
                map += deepcopy(random.choice(map_tiles["house"]))
            case "gate1":
                map = map_from_file(f"frame1.txt", "gateframe")
            case "gate2":
                map = map_from_file(f"frame2.txt", "gateframe")
            case "gate3":
                map = map_from_file(f"frame3.txt", "gateframe")
            case "gate4":
                map = map_from_file(f"frame4.txt", "gateframe")
            case "gate5":
                map = map_from_file(f"frame5.txt", "gateframe")
            case "gate6":
                map = map_from_file(f"frame6.txt", "gateframe")
            case "gate7":
                map = map_from_file(f"frame7.txt", "gateframe")
            case _:
                map = deepcopy(random.choice(map_tiles["land"]))
                self.overmaptile = "#"
        self.map_tiles = map

    def gen_rooms(self):
        for y, line in enumerate(self.map_tiles):
            for x, char in enumerate(line):
                if char != ".":
                    r = self.find_room(x, y)

    def get_room(self, name: str) -> "Room":
        return Room(name, self.session, self.overmap, self)
    
    def get_alchemiter_location(self) -> Optional[tuple[int, int]]:
        # reversed so we look bottom to top
        for y, line in reversed(list(enumerate(self.map_tiles))):
            for x, char in enumerate(line):
                checking_room = self.find_room(x, y)
                for instance_name in checking_room.instances:
                    if alchemy.Instance(instance_name).item.name == "alchemiter":
                        return (x, y)
        else:
            return None

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
    
    def get_starting_room(self, direction) -> "Room":
        if direction == "right": x = len(self.map_tiles[0]) - 1
        else: x = 0
        for y in reversed(range(len(self.map_tiles))):
            room = self.find_room(x, y)
            if room.tile.impassible: continue
            if room.tile.ramp: continue
            return room
        else: raise AssertionError


    def populate_with_underlings(self, underling_type: str, cluster_size: int, number: int, min_tier:int, max_tier: int):
        valid_rooms: list[Room] = []
        for y, line in enumerate(self.map_tiles):
            for x, char in enumerate(line):
                if not self.is_tile_in_bounds(x, y+1): continue
                if self.map_tiles[y+1][x] == ".": continue
                room = self.find_room(x, y)
                if room.tile.impassible: continue
                if room.tile.ramp: continue
                if room.tile.automove: continue
                if room.tile.stair: continue
                if not room.above_solid_ground(): continue
                valid_rooms.append(room)
        remaining_spawns = number
        while remaining_spawns:
            room = random.choice(valid_rooms)
            underling = npcs.underlings[underling_type]
            for i in range(random.randint(1, min(cluster_size, remaining_spawns))):
                grist_tier = random.randint(min_tier, max_tier)
                grist_name = config.gristcategories[self.overmap.gristcategory][grist_tier-1]
                underling.make_npc(grist_name, self.overmap.gristcategory, room)
                remaining_spawns -= 1

    def populate_with_scaled_underlings(self):
        difficulty = self.height
        valid_underlings: list["npcs.Underling"] = []
        for underling in npcs.underlings.values():
            if underling.difficulty <= difficulty: valid_underlings.append(underling)
        num_clusters = 8 + difficulty*2
        if len(valid_underlings) == 0: return
        for i in range(num_clusters):
            underling = random.choice(valid_underlings)
            cluster_size = underling.cluster_size
            diff_difference = difficulty - underling.difficulty
            num_to_spawn = underling.cluster_size + underling.cluster_size*(diff_difference//2)
            min_tier = min(1 + diff_difference, 9)
            max_tier = min(3 + difficulty + underling.variance, 9)
            self.populate_with_underlings(underling.monster_type, cluster_size, num_to_spawn, min_tier, max_tier)

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (self.session.overmaps[self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["name"]]
         [attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (self.session.overmaps[self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["name"]]
                               [attr])
        return self.__dict__[attr]

    def get_tile(self, x: int, y: int) -> tiles.Tile:
        try:
            return tiles.tiles[self.map_tiles[y][x]]
        except KeyError: return tiles.tiles["."]
    
    def change_tile(self, x: int, y: int, tile_char: str):
        self.map_tiles[y][x] = tile_char
    
    def is_tile_in_bounds(self, x: int, y: int) -> bool:
        if y < 0: return False
        if x < 0: return False
        if y >= len(self.map_tiles): return False
        if x >= len(self.map_tiles[0]): return False
        return True

    def get_view(self, target_x: int, target_y: int, view_tiles: int) -> tuple[list, dict]:
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
                    if len(specials) > 0: out_specials[f"{map_tile_x}, {map_tile_y}"] = specials
            out_map_tiles.append(new_line)
        return out_map_tiles, out_specials

    @property
    def specials(self) -> dict[str, tuple]:
        special_dict = {}
        for player_name in self.session.current_players:
            player = Player(player_name)
            if player.overmap.name == self.overmap.name and player.map.name == self.name:
                special_dict[player.name] = ("player", player.symbol_dict["color"])
        # todo: other specials
        return special_dict

    @property
    def height(self) -> int:
        tile_char = self.overmap.map_tiles[self.y][self.x]
        try: return int(tile_char)
        except ValueError: return 0

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
    def name(self) -> str:
        return self.__dict__["name"]

class Room():
    def __init__(self, name, session: Session, overmap: Overmap, map: Map):
        self.__dict__["session_name"] = session.name
        self.__dict__["overmap_name"] = overmap.name
        self.__dict__["map_name"] = map.name
        self.__dict__["name"] = name
        if name not in session.overmaps[overmap.name]["maps"][map.name]["rooms"]:
            session.overmaps[overmap.name]["maps"][map.name]["rooms"][name] = {}
            coords = name.replace(",", "")
            coords = coords.split(" ")
            x = int(coords[0])
            y = int(coords[1])
            self.x = x
            self.y = y
            self.players: list[str] = []
            self.npcs: list[str] = []
            self.instances: list[str] = []
            self.strife_dict: dict = {}
            self.generate_loot()

    def start_strife(self):
        if self.strife is None:
            new_strife = Strife(self)
            for player_name in self.players:
                player = Player(player_name)
                new_strife.add_griefer(player)
            for npc_name in self.npcs:
                npc = npcs.Npc(npc_name)
                new_strife.add_griefer(npc)
            new_strife.increase_turn()
            return True
        else: return False

    def add_npc(self, npc: "npcs.Npc"):
        if npc.name not in self.npcs:
            self.npcs.append(npc.name)

    def remove_npc(self, npc: "npcs.Npc"):
        if npc.name in self.npcs:
            self.npcs.remove(npc.name)

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
    
    def get_npcs(self) -> dict:
        out_dict = {}
        for npc_name in self.npcs:
            npc = npcs.Npc(npc_name)
            out_dict[npc_name] = npc.get_dict()
        return out_dict
    
    def get_players(self) -> list:
        return [Player(player_name).nickname for player_name in self.players if player_name != self.name]

    def deploy_phernalia(self, client: "Player", item_name: str) -> bool:
        if item_name not in client.available_phernalia: print("not in phernalia"); return False
        if not self.tile.deployable: print("undeployable tile"); return False
        below_room = self.map.find_room(self.x, self.y+1)
        if not below_room.tile.infallible and not below_room.tile.impassible: print("below room not suitable"); return False
        if item_name == "pre-punched card":
            item = alchemy.Item("punched card")
            instance = alchemy.Instance(item)
            instance.punched_code = "I11w1a11"
            instance.punched_item_name = "entry item"
            self.add_instance(instance.name)
        else:
            item = alchemy.Item(item_name)
            instance = alchemy.Instance(item)
            cost = item.true_cost
            if not client.pay_costs(cost): print("couldn't pay cost"); return False
            self.add_instance(instance.name)
        client.deployed_phernalia.append(item_name)
        return True
    
    def deploy_atheneum(self, client: "Player", instance_name: str) -> bool:
        if instance_name not in client.atheneum: return False
        if not self.tile.deployable: print("undeployable tile"); return False
        below_room = self.map.find_room(self.x, self.y+1)
        if not below_room.tile.infallible and not below_room.tile.impassible: print("below room not suitable"); return False
        self.add_instance(instance_name)
        client.atheneum.remove(instance_name)
        return True
    
    def above_solid_ground(self) -> bool:
        if not self.map.is_tile_in_bounds(self.x, self.y+1): return False
        below_room = self.map.find_room(self.x, self.y+1)
        return below_room.tile.infallible or below_room.tile.impassible

    def get_surrounding_tiles(self) -> list[tiles.Tile]:
        out_tiles = []
        for y in range(-1, 2):
            for x in range(-1, 2):
                if x == 0 and y == 0: continue
                if self.map.is_tile_in_bounds(self.x+x, self.y+y):
                    out_tiles.append(self.map.find_room(self.x+x, self.y+y).tile)
        return out_tiles
    
    def get_orthogonal_tiles(self) -> list[tiles.Tile]:
        out_tiles = []
        for coords in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            x, y = coords
            if self.map.is_tile_in_bounds(self.x+x, self.y+y):
                out_tiles.append(self.map.find_room(self.x+x, self.y+y).tile)
        return out_tiles

    def revise(self, client: "Player", new_tile_char: str) -> bool:
        if self.tile.forbidden: return False 
        new_tile = tiles.tiles[new_tile_char]
        if new_tile.forbidden: return False 
        if self.players: return False
        # todo: return False if NPCs are in the room as well
        # can't place an impassible tile where instances of items are
        if new_tile.impassible and self.instances: return False
        surrounding_tiles = self.get_orthogonal_tiles()
        supported_from_above = False
        if new_tile.below_allowed and self.map.find_room(self.x, self.y-1).tile.tile_char == new_tile.tile_char:
            pass
        else:
            for tile in surrounding_tiles:
                if tile.solid: break
            else: return False
        if new_tile.supported and not self.map.find_room(self.x, self.y+1).tile.solid: return False
        # todo: some supported tile system beyond this
        # you can't build unsupported tiles directly right now but you can create them with "erasing" with air
        old_cost = self.tile.build_cost
        new_cost = new_tile.build_cost
        if old_cost > new_cost:
            build_cost = 0
            refund = (old_cost-new_cost)//2
            client.add_grist("build", refund)
        else:
            build_cost = new_cost - old_cost
        cost = {"build": build_cost}
        if not client.pay_costs(cost): return False 
        self.map.change_tile(self.x, self.y, new_tile_char)
        # todo: add item falling if this tile is no longer solid
        return True

    @property
    def specials(self) -> dict[str, tuple]:
        special_dict = {}
        for player_username in self.players:
            player = Player(player_username)
            special_dict[player.calledby] = ("player", player.symbol_dict["color"])
        for instance_name in self.instances:
            instance = alchemy.Instance(instance_name)
            if instance.item.name in config.special_items:
                special_dict[instance_name] = (instance.item.name, None)
        for npc_name in self.npcs:
            npc = npcs.Npc(npc_name)
            if npc.color is not None:
                special_dict[npc_name] = (npc.type, npc.color)
            else:
                special_dict[npc_name] = (npc.type, npc.grist_type)
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
    def player(self) -> Optional["Player"]:
        return self.overmap.player
    
    @property
    def strife(self) -> Optional["Strife"]:
        if self.strife_dict:
            return Strife(self)
        else: return None

    @property
    def name(self) -> str:
        return self.__dict__["name"]

    @property
    def tile(self) -> tiles.Tile:
        return self.map.get_tile(self.x, self.y)
    
    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (self.session.overmaps[self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["map_name"]]
         ["rooms"][self.__dict__["name"]]
         [attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (self.session.overmaps[self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["map_name"]]
                               ["rooms"][self.__dict__["name"]]
                               [attr])
        return self.__dict__[attr]

def does_player_exist(name):
    if name not in util.memory_players:
        if util.db_players.find_one({"_id": name}) is None:
            return False
    return True

class Player():
    def __init__(self, name):
        self.__dict__["_id"] = name
        if name not in util.memory_players:
            raise KeyError

    @classmethod
    def create_player(cls, name, owner_username) -> "Player":
        while name in util.memory_players:
            name += random.choice(ascii_letters)
        util.memory_players[name] = {}
        player = cls(name)
        player.setup_defaults(name, owner_username)
        return player

    def setup_defaults(self, name, owner_username):
        self._id = name
        self.session_name = None
        self.overmap_name = None
        self.map_name = None
        self.room_name = None
        self.owner_username = owner_username
        self.sylladex: list[str] = []
        self.moduses: list[str] = []
        self.strife_portfolio: dict[str, list] = {}
        self.current_strife_deck: Optional[str] = None
        self.empty_cards = 5
        self.unassigned_specibi = 1
        self.echeladder_rung: int = 1
        self.grist_cache = {grist_name:0 for grist_name in config.grists}
        self.grist_gutter: list[list] = []
        self.leeching: list[str] = []
        self.wielding: Optional[str] = None
        self.worn_instance_name: Optional[str] = None
        self.symbol_dict = {}
        self.stat_ratios = {
            "spunk": 1,
            "vigor": 1,
            "tact": 1,
            "luck": 1,
            "savvy": 1,
            "mettle": 1,
        }
        self.npc_followers = []
        self.permanent_stat_bonuses = {}
        # phernalia registry is a default list of deployable objects minus the deployed phernalia
        self.deployed_phernalia = []
        # atheneum is the list of stored instances
        self.atheneum = []
        # key: grist value: amount
        self.unclaimed_grist = {}
        self.unclaimed_rungs = 0
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
        self.prototyped_before_entry = False

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.memory_players[self.__dict__["_id"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = util.memory_players[self.__dict__["_id"]][attr]
        return self.__dict__[attr]
    
    def get_dict(self):
        out = deepcopy(util.memory_players[self.__dict__["_id"]])
        out["grist_cache_limit"] = self.grist_cache_limit
        out["total_gutter_grist"] = self.total_gutter_grist
        out["available_phernalia"] = self.available_phernalia
        for kind_name in self.strife_portfolio:
            out["strife_portfolio"][kind_name] = {instance_name:alchemy.Instance(instance_name).get_dict() for instance_name in self.strife_portfolio[kind_name]}
        out["power"] = self.power
        out["entered"] = self.entered
        out["atheneum"] = {instance.name:instance.get_dict() for instance in [alchemy.Instance(instance_name) for instance_name in self.atheneum]}
        out["seeds"] = self.seeds
        if self.worn_instance_name is not None:
            out["worn_instance_dict"] = alchemy.Instance(self.worn_instance_name).get_dict()
        else:
            out["worn_instance_dict"] = None
        best_seeds = self.session.get_best_seeds()
        leeching = self.leeching
        out["leeching"] = {grist_name:(best_seeds[grist_name]//len(leeching)) for grist_name in leeching}
        return out
    
    def add_unclaimed_grist(self, spoils_dict: dict):
        for grist_name, amount in spoils_dict.items():
            if grist_name in self.unclaimed_grist:
                self.unclaimed_grist[grist_name] += amount
            else:
                self.unclaimed_grist[grist_name] = amount

    def add_rungs(self, power_defeated: int):
        combined_rungs = self.echeladder_rung + self.unclaimed_rungs
        min_for_advancement = np.power(combined_rungs, 1.2)
        if combined_rungs > 50 and power_defeated < min_for_advancement: return 0
        rung_reached = np.power(power_defeated, 1/1.2)
        additional_rungs = (rung_reached-combined_rungs)//10
        additional_rungs = max(additional_rungs, 0)
        additional_rungs += 1
        self.unclaimed_rungs += additional_rungs
        self.unclaimed_rungs = int(self.unclaimed_rungs)
    
    def claim_spoils(self):
        self.echeladder_rung += self.unclaimed_rungs
        self.unclaimed_rungs = 0
        for grist_name, amount in self.unclaimed_grist.items():
            self.add_grist(grist_name, amount)
        self.unclaimed_grist = {}

    def add_permanent_bonus(self, game_attr: str, amount: int):
        if game_attr in self.stat_ratios or game_attr in strife.vials:
            if game_attr not in self.permanent_stat_bonuses: self.permanent_stat_bonuses[game_attr] = 0
            self.permanent_stat_bonuses[game_attr] += amount
        else:
            raise AttributeError

    def assign_specibus(self, kind_name) -> bool:
        if kind_name not in util.kinds: return False
        if self.unassigned_specibi <= 0: return False
        if kind_name in self.strife_portfolio: return False
        self.strife_portfolio[kind_name] = []
        self.unassigned_specibi -= 1
        if self.current_strife_deck is None: self.current_strife_deck = kind_name
        return True
    
    def move_to_strife_deck(self, instance_name, kind_name) -> bool:
        if instance_name not in self.sylladex: return False
        if kind_name not in self.strife_portfolio: return False
        self.sylladex.remove(instance_name)
        self.strife_portfolio[kind_name].append(instance_name)
        return True
    
    def eject_from_strife_deck(self, instance_name):
        for kind_name in self.strife_portfolio:
            if instance_name in self.strife_portfolio[kind_name]:
                self.strife_portfolio[kind_name].remove(instance_name)
                self.room.add_instance(instance_name)
                return True
        return False
    
    def wield(self, instance_name: str) -> bool:
        instance = alchemy.Instance(instance_name)
        if instance.item.size > config.max_wielded_size: return False
        for deck in self.strife_portfolio.values():
            if instance.name not in deck: return False
        if self.wielding is not None: self.unwield()
        self.wielding = instance.name
        return True

    def unwield(self):
        if self.wielding is None: return False
        instance = alchemy.Instance(self.wielding)
        self.wielding = None
        return True
    
    def wear(self, instance_name: str) -> bool:
        instance = alchemy.Instance(instance_name)
        if instance.item.size > config.max_worn_size: return False
        if self.worn_instance_name is not None: self.unwield()
        for deck in self.strife_portfolio.values():
            if instance.name in deck: 
                self.eject_from_strife_deck(instance.name)
        if instance_name in self.room.instances:
            self.room.remove_instance(instance_name)
            self.worn_instance_name = instance_name
            return True
        elif instance_name in self.sylladex:
            self.sylladex.remove(instance_name)
            self.worn_instance_name = instance_name
            return True
        else:
            for kind_name, deck in self.strife_portfolio.items():
                if instance_name in deck:
                    self.eject_from_strife_deck(instance_name)
                    self.worn_instance_name = instance_name
                    return True
            else:
                return False
            
    def unwear(self):
        if self.worn_instance_name is None: return False
        else:
            self.room.add_instance(self.worn_instance_name)
            self.worn_instance_name = None
            return True

    @property
    def wielded_instance(self) -> Optional[alchemy.Instance]:
        if self.wielding is None: return None
        else: return alchemy.Instance(self.wielding)

    @property
    def worn_instance(self) -> Optional[alchemy.Instance]:
        if self.worn_instance_name is None: return None
        else: return alchemy.Instance(self.worn_instance_name)

    @property
    def power(self) -> int:
        base_power = self.echeladder_rung
        if self.wielded_instance is not None:
            base_power += self.wielded_instance.item.power
        if self.worn_instance is not None:
            base_power += self.worn_instance.item.power//2
        return base_power

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
        if instance_name in self.room.instances:
            self.room.remove_instance(instance_name)
            return True
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
        
    # deploys an item to this user's map at the specified coordinates
    def deploy_phernalia(self, item_name, target_x, target_y) -> bool:
        room = self.land.housemap.find_room(target_x, target_y)
        return room.deploy_phernalia(self, item_name)
    
    def deploy_atheneum(self, instance_name, target_x, target_y) -> bool:
        room = self.land.housemap.find_room(target_x, target_y)
        return room.deploy_atheneum(self, instance_name)
    
    def revise(self, tile_char, target_x, target_y) -> bool:
        room = self.land.housemap.find_room(target_x, target_y)
        return room.revise(self, tile_char)
    
    def add_grist(self, grist_name: str, amount: int):
        current_grist = self.grist_cache[grist_name]
        if current_grist + amount <= self.grist_cache_limit:
            self.grist_cache[grist_name] = current_grist + amount
            return
        else:
            if self.grist_cache[grist_name] < self.grist_cache_limit: 
                self.grist_cache[grist_name] = self.grist_cache_limit
            overflow = amount - (self.grist_cache[grist_name] - current_grist)
            if len(self.grist_gutter) != 0 and self.grist_gutter[-1][0] == grist_name:
                self.grist_gutter[-1] = [grist_name, self.grist_gutter[-1][1] + overflow]
            else:
                self.grist_gutter.append([grist_name, overflow])

    def pay_costs(self, true_cost: dict) -> bool:
        for grist_name, value in true_cost.items():
            if self.grist_cache[grist_name] < value: return False
        for grist_name, value in true_cost.items():
            self.grist_cache[grist_name] -= value
        return True

    def get_seed_rate(self, grist_name: str, amount: int) -> int:
        rate = 0
        tier = config.grists[grist_name]["tier"]
        tier = max(tier, 1)
        if "exotic" not in config.grists[grist_name]:
            rate += self.echeladder_rung//2//tier
        if self.gristcategory in config.gristcategories and grist_name in config.gristcategories[self.gristcategory]:
            rate += self.echeladder_rung//2//tier
        rate += int(amount//25)
        return rate

    @property
    def seeds(self) -> dict[str, int]:
        seeds = {grist_name:0 for grist_name in config.grists}
        for grist_name, value in self.grist_cache.items():
            rate = self.get_seed_rate(grist_name, value)
            seeds[grist_name] = rate
        return seeds

    @property
    def total_gutter_grist(self) -> int:
        total = 0
        for grist_name, amount in self.grist_gutter:
            total += amount
        return total

    def add_gutter_and_leech(self):
        spoils_dict = {}
        if self.leeching == []: leeching = ["build"]
        else: leeching = self.leeching
        best_seeds = self.session.get_best_seeds()
        for grist_type in leeching:
            value = best_seeds[grist_type]//len(leeching)
            spoils_dict[grist_type] = value
        possible_players = [player_name for player_name in self.session.current_players if Player(player_name).grist_gutter and player_name is not self.name]
        if not possible_players: return self.add_unclaimed_grist(spoils_dict)
        random.shuffle(possible_players)
        for player_name in possible_players:
            if player_name == self.name: continue
            player = Player(player_name)
            grist_name, amount = player.grist_gutter.pop()
            if grist_name in spoils_dict: spoils_dict[grist_name] += amount
            else: spoils_dict[grist_name] = amount
        self.add_unclaimed_grist(spoils_dict)

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
    
    def get_illegal_overmap_moves(self) -> list[str]:
        player_x = self.map.x
        player_y = self.map.y
        illegal_moves = []
        for direction in ["north", "south", "east", "west"]:
            if direction == "north":
                target_x = player_x
                target_y = player_y - 1
            elif direction == "south":
                target_x = player_x
                target_y = player_y + 1
            elif direction == "east":
                target_x = player_x + 1
                target_y = player_y
            else: # west
                target_x = player_x - 1
                target_y = player_y
            target_map = self.overmap.find_map(target_x, target_y)
            if abs(target_map.height - self.map.height) > 1 or target_map.height == 0: illegal_moves.append(direction)
        return illegal_moves

    def attempt_overmap_move(self, direction: str) -> bool:
        if self.strife is not None: return False
        if direction in self.get_illegal_overmap_moves(): return False
        player_x = self.map.x
        player_y = self.map.y
        match direction:
            case "north":
                target_x = player_x
                target_y = player_y - 1
            case "south":
                target_x = player_x
                target_y = player_y + 1
            case "east":
                target_x = player_x + 1
                target_y = player_y
            case "west":
                target_x = player_x - 1
                target_y = player_y
            case _:
                return False
        target_map = self.overmap.find_map(target_x, target_y)
        if not target_map.map_tiles:
            target_map.gen_map()
            target_map.populate_with_scaled_underlings()
        entry_direction = "left"
        # if direction == "north" or direction == "east": entry_direction = "left"
        # else: entry_direction = "right"
        self.goto_room(target_map.get_starting_room(entry_direction))
        return True

    def attempt_move(self, direction: str) -> bool:
        if self.strife is not None: return False
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
            if fall_tile.ramp and fall_tile.ramp_direction == "left": 
                target_x += 1
                target_y += 1
            elif fall_tile.ramp and fall_tile.ramp_direction == "right": 
                target_x -= 1
                target_y += 1
            elif fall_tile.ramp and fall_tile.ramp_direction == "both":
                if direction == "right": target_x += 1
                if direction == "left": target_x -= 1
            else:
                target_y += 1
            target_tile = map.get_tile(target_x, target_y)
        new_room = map.find_room(target_x, target_y)
        # check if entered gate room
        try: 
            gate_num = int(new_room.tile.tile_char)
            entered_gate = self.enter_gate(gate_num)
            if not entered_gate: self.goto_room(new_room)
        except ValueError:
            self.goto_room(new_room)
        return True

    def enter_gate(self, gate_num: int) -> bool:
        if self.overmap.housemap.name == self.map.name:
            at_house = True
        else:
            at_house = False
        if gate_num == 0: # return gate
            destination_player = self.overmap.player
            if destination_player is None: return False
            destination_map = destination_player.land.housemap
            room = destination_map.random_valid_room([str(1)]) # go back to first gate
            self.goto_room(room)
            return True
        destination_player = self.overmap.gate_location(gate_num, at_house)
        if destination_player is None: return False
        if not destination_player.entered: return False
        if at_house:
            destination_map = destination_player.land.get_map(destination_player.land.gate_maps[str(gate_num)])
            room = destination_map.random_valid_room([str(gate_num)])
        else:
            destination_map = destination_player.land.housemap
            room = destination_map.random_valid_room([str(gate_num)])
            if not room.above_solid_ground(): return False
        self.goto_room(room)
        return True

    def get_base_stat(self, stat):
        stats = strife.stats_from_ratios(self.stat_ratios, self.power)
        amount = stats[stat]
        if stat in self.permanent_stat_bonuses:
            amount += self.permanent_stat_bonuses[stat]
        return amount
    
    def get_known_skills(self):
        known_skills = skills.base_skills + skills.player_skills
        if self.aspect in skills.aspect_skills:
            for skill_name, required_rung in skills.aspect_skills[self.aspect].items():
                if self.echeladder_rung >= required_rung: known_skills.append(skill_name)
        if self.gameclass in skills.class_skills:
            if self.aspect in skills.class_skills[self.gameclass]:
                for skill_name, required_rung in skills.class_skills[self.gameclass][self.aspect].items():
                    if self.echeladder_rung >= required_rung: known_skills.append(skill_name)
        abstratus = self.current_strife_deck
        if abstratus in skills.abstratus_skills:
            for skill_name, required_rung in skills.abstratus_skills[abstratus].items():
                if self.echeladder_rung >= required_rung: known_skills.append(skill_name)
        else:
            print(f"{abstratus} needs skills doofus!!!")
        return known_skills
    
    def get_current_passives(self):
        current_passives = []
        if self.gameclass in stateseffects.class_passives:
            if self.aspect in stateseffects.class_passives[self.gameclass]:
                for passive_name, required_rung in stateseffects.class_passives[self.gameclass][self.aspect].items():
                    if self.echeladder_rung >= required_rung: current_passives.append(passive_name)
        return current_passives

    @property
    def session(self) -> Session:
        return Session(self.session_name)
    
    @property
    def overmap(self) -> Overmap:
        return Overmap(self.overmap_name, self.session)
    
    @property
    def map(self) -> Map:
        return Map(self.map_name, self.session, self.overmap)
    
    def get_view(self, view_tiles=6) -> tuple[list, dict, dict, dict, list, dict]:
        map_tiles, map_specials = self.map.get_view(self.room.x, self.room.y, view_tiles)
        room_instances = self.room.get_instances()
        room_npcs = self.room.get_npcs()
        room_players = self.room.get_players()
        if self.nickname in room_players: room_players.remove(self.nickname)
        if self.strife is None: strife = {}
        else: strife = self.strife.get_dict()
        return map_tiles, map_specials, room_instances, room_npcs, room_players, strife
    
    def get_overmap_view(self, view_tiles=12):
        view_tiles = view_tiles + self.map.height*2
        theme = self.overmap.theme
        map_tiles, map_specials, map_types = self.overmap.get_view(self.map.x, self.map.y, view_tiles)
        return map_tiles, map_specials, map_types, theme

    @property
    def room(self) -> Room:
        return Room(self.room_name, self.session, self.overmap, self.map)
    
    def goto_room(self, room: Room):
        if self.session is not None and self.session != room.session:
            if self.name in self.session.current_players:
                self.session.current_players.remove(self.name)
        if self.room_name is not None: self.room.remove_player(self)
        self.session_name = room.session.name
        self.overmap_name = room.overmap.name
        self.map_name = room.map.name
        self.room_name = room.name
        if self.name not in self.session.current_players: self.session.current_players.append(self.name)
        room.add_player(self)
        for npc_name in self.npc_followers:
            npc = npcs.Npc(npc_name)
            npc.goto_room(room)

    @property
    def strife(self) -> Optional["Strife"]:
        if self.room.strife is None: return None
        for griefer in self.room.strife.griefer_list:
            if griefer.player is None: continue
            if griefer.player.name == self.name: return self.room.strife
        else:
            return None

    @property
    def grist_cache_limit(self):
        mult = 1 + self.echeladder_rung//50
        if self.echeladder_rung > 10: mult += 1
        return 10*self.echeladder_rung*mult
    
    @property
    def available_phernalia(self):
        connected = self.session.connected
        available_phernalia = ["sealed cruxtruder", "totem lathe", "alchemiter", "pre-punched card"]
        if len(connected) >= 2:
            available_phernalia.append("gristTorrent disc")
            available_phernalia.append("punch designix")
        for item in self.deployed_phernalia:
            available_phernalia.remove(item)
        phernalia_dict = {}
        for item_name in available_phernalia:
            phernalia_dict[item_name] = alchemy.Item(item_name).get_dict()
        return phernalia_dict

    @property
    def entered(self):
        return self.name in self.land.session.entered_players

    @property
    def title(self) -> str:
        return f"{self.gameclass.capitalize()} of {self.aspect.capitalize()}"

    @property
    def coords(self):
        return self.room.x, self.room.y

    @property
    def name(self) -> str:
        return self.__dict__["_id"]
    
    @property
    def username(self):
        return self.__dict__["_id"]

    @property
    def calledby(self):
        return self.nickname
    
    @property
    def color(self):
        return self.symbol_dict["color"]

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

def gen_terrain(x, y, map, replacetile, terrain_rate, depth=0):
    if map[y][x] == "*":
        for coordinate in [(-1, 0), (1, 0), (0, 1), (0, -1)]: # up down left right
            try:
                tile = map[y+coordinate[1]][x+coordinate[0]]
                if tile == "*": continue
                rng = random.random()
                if rng < terrain_rate - (config.terrain_decay * depth * terrain_rate): # chance to generate more terrain lowers with depth
                    map[y+coordinate[1]][x+coordinate[0]] = "*"
                    map = gen_terrain(x+coordinate[0], y+coordinate[1], map, tile, terrain_rate, depth+1)
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
        for line in newmap:
            ln = ""
            for char in line:
                ln += char
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

def make_water_height_0(map_tiles: list[list[str]]) -> list[list[str]]:
    out = [list(map(lambda tile: tile.replace("~", "0"), line)) for line in map_tiles]
    return out

def generate_height(target_x: int, target_y: int, map_tiles: list[list[str]], steepness: float, smoothness: float) -> Optional[int]:
    current_tile:str = map_tiles[target_y][target_x]
    try:
        return int(current_tile)
    except ValueError: pass
    if current_tile == "0": return 0
    surrounding_values: list[int] = []
    for x, y in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
        new_x = target_x+x
        new_y = target_y+y
        if new_x >= len(map_tiles[0]): new_x -= (len(map_tiles[0]) - 1)
        if new_y >= len(map_tiles): new_y -= (len(map_tiles) - 1)
        new_tile = map_tiles[new_y][new_x]
        if new_tile == "#": continue
        tile_value = int(new_tile)
        surrounding_values.append(tile_value)
    if len(surrounding_values) == 0: return None
    if 0 in surrounding_values: return 1 + round(random.uniform(0, steepness))
    # get mode of surrounding values
    average_height = round(sum(surrounding_values) / len(surrounding_values))
    if random.random() < smoothness: 
        possible_values = [random.choice(surrounding_values) for i in range(1)]
        mode_height = max(set(surrounding_values), key=surrounding_values.count)
        possible_values.append(mode_height)
        for i in range(1): possible_values.append(average_height)
        return random.choice(possible_values)
    new_height = average_height + round(random.uniform(-steepness, steepness))
    new_height = max(new_height, 1)
    return new_height

def height_map_pass(map_tiles: list[list[str]], steepness: float, smoothness: float) -> list[list[str]]:
    y_values = list(range(len(map_tiles)))
    x_values = list(range(len(map_tiles[0])))
    random.shuffle(x_values)
    random.shuffle(y_values)
    for y in y_values:
        line = map_tiles[y]
        for x in x_values:
            char = line[x]
            if char != "#": continue
            height = generate_height(x, y, map_tiles, steepness, smoothness)
            if height is None: continue
            map_tiles[y][x] = str(height)
    # for y, line in enumerate(map_tiles):
    #     for x, char in enumerate(line):
    #         if char != "#": continue
    #         height = generate_height(x, y, map_tiles, steepness)
    #         if height is None: continue
    #         map_tiles[y][x] = str(height)
    return map_tiles

def smooth_height_pits(map_tiles: list[list[str]], aggressiveness: int=1) -> list[list[str]]:
    new_map = deepcopy(map_tiles)
    for y, line in enumerate(map_tiles):
        for x, char in enumerate(line):
            height = int(char)
            surrounding_tiles = []
            # check surrounding tiles
            for x_diff, y_diff in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                new_x = x+x_diff
                new_y = y+y_diff
                if new_x >= len(map_tiles[0]): new_x -= (len(map_tiles[0]) - 1)
                if new_y >= len(map_tiles): new_y -= (len(map_tiles) - 1)
                surrounding_tiles.append(map_tiles[new_y][new_x])
            surrounding_tiles = [int(tile) for tile in surrounding_tiles]
            different_tiles = []
            # if this tile is significantly different than surrounding tiles, set it to the minimum of surrounding tiles
            for surrounding_height in surrounding_tiles.copy():
                if surrounding_height != height:
                    different_tiles.append(surrounding_height)
            if len(different_tiles) > 4 - aggressiveness:
                new_map[y][x] = str(random.choice(different_tiles))
    return new_map


def make_height_map(map_tiles: list[list[str]], steepness: float=1.0, smoothness: float=0.5):
    t = time.time()
    # we want to keep any pre-defined heights from being smoothed
    old_map_tiles = deepcopy(map_tiles)
    map_tiles = make_water_height_0(map_tiles)
    while True:
        map_tiles = height_map_pass(map_tiles, steepness, smoothness)
        for line in map_tiles:
            if "#" not in line: continue
            else: break
        else:
            break
    print(f"height map generation took {time.time()-t} seconds")
    t = time.time()
    if smoothness >= 0.5:
        if smoothness > 0.75: aggressiveness = 2
        else: aggressiveness = 1
        map_tiles = smooth_height_pits(map_tiles, aggressiveness)
        # any heights pre-defined by old map tiles will be replaced here to undo smoothing
        for y, line in enumerate(old_map_tiles):
            for x, char in enumerate(line):
                if char in ["~", "#"]: continue
                map_tiles[y][x] = char
    print(f"smooth map took {time.time()-t} seconds")
    return map_tiles

default_map_tiles = [["~" for i in range(config.overmap_width)] for i in range(config.overmap_width)]

def gen_overworld(islands, landrate, lakes, lakerate, special=None, extralands=None, extrarate=None, extraspecial=None):
    t = time.time()
    map_tiles = deepcopy(default_map_tiles)
    for i in range(0, islands): # generate islands
        if special == "center":
            y = int(len(map_tiles)/2)
            x = int(len(map_tiles[0])/2)
        elif special == "dual":
            if i % 2 == 0:
                x = int(len(map_tiles[0])/7)
                y = int(len(map_tiles)/4) * 3
            else:
                x = int(len(map_tiles[0])/7) * 6
                y = int(len(map_tiles)/4)
        else:
            y = random.randint(0, len(map_tiles)-1)
            x = random.randint(0, len(map_tiles[0])-1)
        map_tiles[y][x] = "*" # placeholder terrain tile
        map_tiles = gen_terrain(x, y, map_tiles, "#", landrate)
    for i in range(0, lakes): # generate lakes
        y = random.randint(0, len(map_tiles)-1)
        x = random.randint(0, len(map_tiles[0])-1)
        map_tiles[y][x] = "*" # placeholder terrain tile
        map_tiles = gen_terrain(x, y, map_tiles, "~", lakerate)
    if special == "block":
        print("block special")
        map_tiles = modify_block(map_tiles, "#", "~")
        map_tiles = modify_block(map_tiles, "~", "#")
    if extralands != None:
        for i in range(0, extralands): # generate extra islands
            if extraspecial == "center":
                y = int(len(map_tiles)/2)
                x = int(len(map_tiles[0])/2)
            elif extraspecial == "dual":
                if i % 2 == 0:
                    x = int(len(map_tiles[0])/7)
                    y = int(len(map_tiles)/4) * 3
                else:
                    x = int(len(map_tiles[0])/7) * 6
                    y = int(len(map_tiles)/4)
            else:
                y = random.randint(0, len(map_tiles)-1)
                x = random.randint(0, len(map_tiles[0])-1)
            map_tiles[y][x] = "*" # placeholder terrain tile
            map_tiles = gen_terrain(x, y, map_tiles, "#", extrarate)
    print(f"terrain gen took {time.time()-t} seconds")
    return map_tiles

def set_height(map_tiles: list[list[str]], target_x, target_y, height: int, hill_radius=1, min_height=1) -> list[list[str]]:
        for i in reversed(range(hill_radius)):
            for x in range(-i, i+1):
                for y in range(-i, i+1):
                    dest_y = target_y+y
                    dest_x = target_x+x
                    if dest_y > len(map_tiles)-1: dest_y -= len(map_tiles)-1
                    if dest_x > len(map_tiles[0])-1: dest_x -= len(map_tiles[0])-1
                    if map_tiles[dest_y][dest_x] == "~": continue
                    map_tiles[dest_y][dest_x] = str(max(height-i, min_height))
        map_tiles[target_y][target_x] = str(height)
        return map_tiles

def get_tile_at_distance(map_tiles, x: int, y: int, distance: int, specials: list=[]) -> tuple[int, int]: # chooses a random location that's distance away from x, y
    possiblelocs = []
    # make a ring of valid targets around x, y
    for num in range(0, distance+1):
        possiblelocs.append((num, distance-num))
        possiblelocs.append((num*-1, distance-num))
        possiblelocs.append((num, (distance-num)*-1))
        possiblelocs.append((num*-1, (distance-num)*-1))
    random.shuffle(possiblelocs)
    for xplus, yplus in possiblelocs:
        newx = x + xplus
        newy = y + yplus
        while newx >= len(map_tiles[0]):
            newx -= len(map_tiles[0]) # loop around to the other side
        while newx < 0:
            newx = len(map_tiles[0]) + newx # loop around to the other side
        while newy >= len(map_tiles):
            newy -= len(map_tiles) # loop around to the other side
        while newy < 0:
            newy = len(map_tiles) + newy # loop around to the other side
        if map_tiles[newy][newx] != "~" and f"{newx}, {newy}" not in specials:
            return newx, newy
    else: # if there is no valid location around the tile
        return get_tile_at_distance(map_tiles, x, y, distance+1, specials) # recurse, find loc further away

def get_random_land_coords(map_tiles) -> tuple[int, int]:
    y = random.randint(0, len(map_tiles)-1)
    x = random.randint(0, len(map_tiles[0])-1)
    while map_tiles[y][x] == "~":
        y = random.randint(0, len(map_tiles)-1)
        x = random.randint(0, len(map_tiles[0])-1)
    return x, y

def print_map(map_tiles: list[list[str]]):
    str_list = ["".join(chars) for chars in map_tiles]
    print("\n".join(str_list).replace("0", "~"))

if __name__ == "__main__":
    type = input("land type: ")
    category: dict = config.categoryproperties[type]
    islands = category.get("islands")
    landrate = category.get("landrate")
    lakes = category.get("lakes")
    lakerate = category.get("lakerate")
    special = category.get("special", None)
    extralands = category.get("extralands", None)
    extrarate = category.get("extrarate", None)
    extraspecial = category.get("extraspecial", None)
    steepness = category.get("steepness", 1.0)
    smoothness = category.get("smoothness", 0.5)
    test_map = gen_overworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial)
    housemap_x, housemap_y = get_random_land_coords(test_map)
    last_gate_x, last_gate_y = 0, 0
    for gate_num in range(1, 8): # gates 1-7
        if gate_num % 2 == 1: # even numbered gates should be close to odd numbered gates before them
            gate_x, gate_y = get_tile_at_distance(test_map, housemap_x, housemap_y, gate_num*9)
            last_gate_x, last_gate_y = gate_x, gate_y
        else:
            gate_x, gate_y = get_tile_at_distance(test_map, last_gate_x, last_gate_y, gate_num*4)
        if gate_num == 1 or gate_num == 2:
            test_map = set_height(test_map, gate_x, gate_y, 2, 4, 2)
        test_map = set_height(test_map, gate_x, gate_y, gate_num, 3)
    test_map = make_height_map(test_map, steepness, smoothness)
    test_map = set_height(test_map, housemap_x, housemap_y, 1, 3)
    test_map = set_height(test_map, housemap_x, housemap_y, 9)
    print_map(test_map)