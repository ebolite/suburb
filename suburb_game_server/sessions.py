import json
import hashlib
import random
import os
from typing import Optional, Union
from copy import deepcopy

import util
import config

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
        if name not in util.sessions:
            util.sessions[name] = {}
        self.__dict__["session_name"] = name
        if self.players == None:
            self.players = {}
        if self.overmaps == None:
            self.overmaps = {}

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.sessions[self.__dict__["session_name"]][attr] = value
        

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               .get(attr, self.__dict__[attr]))
        return self.__dict__[attr]

    @property
    def name(self):
        return self.__dict__["session_name"]

class Overmap(): # name is whatever, for player lands it's "{Player.name}{Player.session}"
    def __init__(self, name, session: Session, player: Optional["Player"] = None):
        if name not in util.sessions[session.name]["overmaps"]:
            util.sessions[session.name]["overmaps"][name] = {}
        self.__dict__["session_name"] = session.name
        self.__dict__["name"] = name
        if self.maps == None:
            self.maps = {}
        if self.specials == None:
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
        self.map = gen_overworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial)
        for line in self.map:
            print("".join(line))
        #house
        if self.housemap == None:
            y = random.randint(0, len(self.map)-1)
            x = random.randint(0, len(self.map[0])-1)
            while self.map[y][x] == "~":
                y = random.randint(0, len(self.map)-1)
                x = random.randint(0, len(self.map[0])-1)
            housemap = self.find_map(x, y)
            housemap.gen_map("house")
            self.housemap = housemap.name
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

    def find_map(self, x, y) -> "Map":
        return Map(f"{x}, {y}", self.Session, self)

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.sessions[self.__dict__["session_name"]]["overmaps"][self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["name"]]
                               .get(attr, self.__dict__[attr]))
        return self.__dict__[attr]

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def player(self) -> "Player":
        return Player(self.__dict__["player_name"], self.Session)

    @property
    def name(self):
        return self.__dict__["name"]

class Map():
    def __init__(self, name, session: Session, overmap: Overmap):
        if name not in util.sessions[session.name]["overmaps"][overmap.name]["maps"]:
            util.sessions[session.name]["overmaps"][overmap.name]["maps"][name] = {}
        self.__dict__["session_name"] = session.name
        self.__dict__["overmap_name"] = overmap.name
        self.__dict__["name"] = name
        if self.rooms == None:
            self.rooms = {}
        if self.overmaptile == None:
            self.overmaptile = "~"
        if self.x == None or self.y == None:
            coords = name.replace(",", "")
            coords = name.split(" ")
            x = int(name[0])
            y = int(name[1])
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
        self.map = map

    def gen_rooms(self):
        for y, line in enumerate(self.map):
            for x, char in enumerate(line):
                if char != ".":
                    r = self.find_room(x, y)

    def find_room(self, x, y) -> "Room":
        return Room(f"{x}, {y}", self.session, self.overmap, self)

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
                               .get(attr, None))
        return self.__dict__[attr]

    def get_tile(self, x, y) -> str:
        return self.map[y][x]

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def overmap(self) -> Overmap:
        return Overmap(self.__dict__["session_name"], self.__dict__["overmap_name"])

    @property
    def player(self) -> "Player":
        return Player(self.__dict__["player_name"], self.Session)

    @property
    def name(self):
        return self.__dict__["name"]

class Room():
    def __init__(self, name, session: Session, overmap: Overmap, map: Map):
        if name not in util.sessions[session.name]["overmaps"][overmap.name]["maps"][map.name]["rooms"]:
            util.sessions[session.name]["overmaps"][overmap.name]["maps"][map.name]["rooms"][name] = {}
        self.__dict__["session_name"] = session.name
        self.__dict__["overmap_name"] = overmap.name
        self.__dict__["map_name"] = map.name
        self.__dict__["name_name"] = name
        if self.x == None or self.y == None:
            coords = name.replace(",", "")
            coords = coords.split(" ")
            x = int(coords[0])
            y = int(coords[1])
            self.x = x
            self.y = y

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["overmaps"][self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["map_name"]]
         ["rooms"][self.__dict__["name"]]
         [attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session"]]
                               ["overmaps"][self.__dict__["overmap"]]
                               ["maps"][self.__dict__["map"]]
                               ["rooms"][self.__dict__["name"]]
                               .get(attr, self.__dict__[attr]))
        return self.__dict__[attr]

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def overmap(self) -> Overmap:
        return Overmap(self.__dict__["session_name"], self.__dict__["overmap_name"])

    @property
    def player(self) -> "Player":
        return self.overmap.player

    @property
    def name(self):
        return self.__dict__["name"]

    @property
    def tile(self) -> str:
        return self.Map.get_tile(self.x, self.y)


class Player():
    def __init__(self, name, session: Session):
        if name not in util.sessions[session.name]["players"]:
            util.sessions[session.name]["players"][name] = {}
        self.__dict__["session_name"] = session.name
        self.__dict__["name"] = name
        if self.setup == None: self.setup = False

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["players"][self.__dict__["name"]]
         [attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = util.sessions[self.__dict__["session_name"]]["players"][self.__dict__["name"]].get(attr, self.__dict__[attr])
        return self.__dict__[attr]

    @property
    def session(self) -> Session:
        return Session(self.__dict__["session_name"])

    @property
    def name(self):
        return self.__dict__["name"]

    @property
    def calledby(self):
        return self.nickname

    @property
    def land(self) -> Overmap:
        return Overmap(self.land_name, Session(self.landsession))

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
