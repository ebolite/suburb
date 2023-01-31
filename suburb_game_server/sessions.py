import json
import hashlib
import random
import os
from copy import deepcopy

import util
import config

maptiles = {}

def mapfromfile(file, folder=None):
    if folder == None:
        os.chdir(f"{util.homedir}\\maps")
    else:
        os.chdir(f"{util.homedir}\\maps\\{folder}")
    with open(f"{file}", "r") as f:
        content = f.read()
    content = content.split("\n") #split y axis
    for index, line in enumerate(content):
        content[index] = list(line) # split each string in content into a list of letters
    return content

def allmapsinfolder(folder): # returns a list of all of the maps in a folder
    maps = []
    for filename in os.listdir(f"{util.homedir}\\maps\\{folder}"):
        maps.append(mapfromfile(filename, folder))
    return maps

maptiles["house"] = allmapsinfolder("house")
maptiles["land"] = allmapsinfolder("land")
maptiles["gateframe"] = allmapsinfolder("gateframe")

class Session():
    def __init__(self, name):
        if name not in util.sessions:
            util.sessions[name] = {}
        self.__dict__["session"] = name
        if self.players == None:
            self.players = {}
        if self.overmaps == None:
            self.overmaps = {}

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session"]][attr] = value

    def __getattr__(self, attr):
        if attr in util.sessions[self.__dict__["session"]]:
            return util.sessions[self.__dict__["session"]][attr]
        else:
            return None

    @property
    def name(self):
        return self.__dict__["session"]

class Overmap(): # name is whatever, for player lands it's "{Player.name}{Player.session}"
    def __init__(self, name, Session, Player=None):
        if name not in util.sessions[Session.name]["overmaps"]:
            util.sessions[Session.name]["overmaps"][name] = {}
        self.__dict__["session"] = Session.name
        self.__dict__["name"] = name
        if self.maps == None:
            self.maps = {}
        if self.specials == None:
            self.specials = []
        if Player != None:
            self.__dict__["player"] = Player.name
            self.gristcategory = Player.gristcategory
            self.genovermap()
            self.genlandname()

    def genovermap(self):
        islands = config.categoryproperties[self.gristcategory]["islands"]
        landrate = config.categoryproperties[self.gristcategory]["landrate"]
        lakes = config.categoryproperties[self.gristcategory]["lakes"]
        lakerate = config.categoryproperties[self.gristcategory]["lakerate"]
        if "special" in config.categoryproperties[self.gristcategory]:
            special = config.categoryproperties[self.gristcategory]["special"]
        else:
            special = None
        if "extralands" in config.categoryproperties[self.gristcategory]:
            extralands = config.categoryproperties[self.gristcategory]["extralands"]
        else:
            extralands = None
        if "extrarate" in config.categoryproperties[self.gristcategory]:
            extrarate = config.categoryproperties[self.gristcategory]["extrarate"]
        else:
            extrarate = None
        if "extraspecial" in config.categoryproperties[self.gristcategory]:
            extraspecial = config.categoryproperties[self.gristcategory]["extraspecial"]
        else:
            extraspecial = None
        self.map = generateoverworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial)
        for line in self.map:
            print("".join(line))
        #house
        if self.housemap == None:
            y = random.randint(0, len(self.map)-1)
            x = random.randint(0, len(self.map[0])-1)
            while self.map[y][x] == "~":
                y = random.randint(0, len(self.map)-1)
                x = random.randint(0, len(self.map[0])-1)
            housemap = self.getmap(x, y)
            housemap.genmap("house")
            self.housemap = housemap.name
            self.specials.append(housemap.name)
            # we're not doing this right now
            # housemap.genrooms()

    def genlandname(self):
        print(f"{self.gristcategory} {self.Player.aspect}")
        print(f"Player {self.Player} {self.Player.name} {self.player}")
        print(f"grist {self.gristcategory} aspect {self.Player.aspect}")
        bases = config.landbases[self.gristcategory] + config.aspectbases[self.Player.aspect]
        random.seed(self.Player.name)
        random.shuffle(bases)
        self.base1 = bases[0]
        if self.Player.aspect != "space":
            self.base2 = bases[1]
        else:
            self.base2 = "frogs"
        self.title = f"Land of {self.base1.capitalize()} and {self.base2.capitalize()}"
        words = self.title.split(" ")
        acronym = ""
        for word in words:
            acronym += f"{word[0].upper()}"
        self.acronym = acronym

    def getmap(self, x, y):
        m = Map(f"{x}, {y}", self.Session, self)
        return m

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        if attr in util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["name"]]:
            return util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["name"]][attr]
        else:
            return None

    @property
    def Session(self):
        return Session(self.__dict__["session"])

    @property
    def Player(self):
        return Player(self.__dict__["player"], self.Session)

    @property
    def name(self):
        return self.__dict__["name"]

class Map():
    def __init__(self, name, Session, Overmap):
        if name not in util.sessions[Session.name]["overmaps"][Overmap.name]["maps"]:
            util.sessions[Session.name]["overmaps"][Overmap.name]["maps"][name] = {}
        self.__dict__["session"] = Session.name
        self.__dict__["overmap"] = Overmap.name
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

    def genmap(self, type=None):
        map = None
        if type == "house":
            map = mapfromfile("gates.txt")
            map += deepcopy(random.choice(maptiles["house"]))
            self.overmaptile = "H"
        elif type == "gate1":
            map = deepcopy(random.choice(maptiles["gateframe"]))
            self.overmaptile = "1"
        elif type == "gate2":
            map = deepcopy(random.choice(maptiles["gateframe"]))
            self.overmaptile = "2"
        elif type == "gate3":
            map = deepcopy(random.choice(maptiles["gateframe"]))
            self.overmaptile = "3"
        elif type == "gate4":
            map = deepcopy(random.choice(maptiles["gateframe"]))
            self.overmaptile = "4"
        elif type == "gate5":
            map = deepcopy(random.choice(maptiles["gateframe"]))
            self.overmaptile = "5"
        elif type == "gate6":
            map = deepcopy(random.choice(maptiles["gateframe"]))
            self.overmaptile = "6"
        elif type == "gate7":
            map = deepcopy(random.choice(maptiles["gateframe"]))
            self.overmaptile = "7"
        else:
            map = deepcopy(random.choice(maptiles["land"]))
            self.overmaptile = "#"
        print("genmap")
        self.map = map

    def genrooms(self):
        for y, line in enumerate(self.map):
            for x, char in enumerate(self.map[y]):
                if char != ".":
                    r = self.getroom(x, y)

    def getroom(self, x, y):
        r = Room(f"{x}, {y}", self.Session, self.Overmap, self)
        return r

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["overmap"]]["maps"][self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        if attr in util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["overmap"]]["maps"][self.__dict__["name"]]:
            return util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["overmap"]]["maps"][self.__dict__["name"]][attr]
        else:
            return None

    def gettile(self, x, y):
        return self.map[y][x]

    @property
    def Session(self):
        return Session(self.__dict__["session"])

    @property
    def Overmap(self):
        return Overmap(self.__dict__["session"], self.__dict__["overmap"])

    @property
    def Player(self):
        return Player(self.__dict__["player"], self.Session)

    @property
    def name(self):
        return self.__dict__["name"]

class Room():
    def __init__(self, name, Session, Overmap, Map):
        if name not in util.sessions[Session.name]["overmaps"][Overmap.name]["maps"][Map.name]["rooms"]:
            util.sessions[Session.name]["overmaps"][Overmap.name]["maps"][Map.name]["rooms"][name] = {}
        self.__dict__["session"] = Session.name
        self.__dict__["overmap"] = Overmap.name
        self.__dict__["map"] = Map.name
        self.__dict__["name"] = name
        if self.x == None or self.y == None:
            coords = name.replace(",", "")
            coords = name.split(" ")
            x = int(name[0])
            y = int(name[1])
            self.x = x
            self.y = y

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["overmap"]]["maps"][self.__dict__["map"]]["rooms"][self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        if attr in util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["overmap"]]["maps"][self.__dict__["map"]]["rooms"][self.__dict__["name"]]:
            return util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["overmap"]]["maps"][self.__dict__["map"]]["rooms"][self.__dict__["name"]][attr]
        else:
            return None

    @property
    def Session(self):
        return Session(self.__dict__["session"])

    @property
    def Overmap(self):
        return Overmap(self.__dict__["session"], self.__dict__["overmap"])

    @property
    def Player(self):
        return Player(self.__dict__["player"], self.Session)

    @property
    def name(self):
        return self.__dict__["name"]

    @property
    def tile(self):
        return self.Map.gettile(self.x, self.y)


class Player():
    def __init__(self, name, Session):
        if name not in util.sessions[Session.name]["players"]:
            util.sessions[Session.name]["players"][name] = {}
        self.__dict__["session"] = Session.name
        self.__dict__["name"] = name
        if self.setup == None: self.setup = False

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session"]]["players"][self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        if attr in util.sessions[self.__dict__["session"]]["players"][self.__dict__["name"]]:
            return util.sessions[self.__dict__["session"]]["players"][self.__dict__["name"]][attr]
        else:
            return None

    @property
    def Session(self):
        return Session(self.__dict__["session"])

    @property
    def name(self):
        return self.__dict__["name"]

    @property
    def calledby(self):
        return self.nickname

    @property
    def Land(self):
        l = Overmap(self.land, Session(self.landsession))
        return l

    def verify(self, hash): # returns True if hash is valid
        if hash == self.character_pass_hash:
            return True
        else:
            return False

def generateterrain(x, y, map, replacetile, terrain, depth=0):
    if map[y][x] == "*":
        for coordinate in [(-1, 0), (1, 0), (0, 1), (0, -1)]: # up down left right
            try:
                tile = map[y+coordinate[1]][x+coordinate[0]]
                rng = random.random()
                if rng < terrain - (0.1 * depth * terrain): # chance to generate more terrain lowers with depth
                    map[y+coordinate[1]][x+coordinate[0]] = "*"
                    map = generateterrain(x+coordinate[0], y+coordinate[1], map, tile, terrain, depth+1)
            except IndexError:
                pass
    if depth == 0:
        for y, line in enumerate(map):
            for x, char in enumerate(line):
                if char == "*":
                    map[y][x] = replacetile
    return map

def blockmodify(map, checktile, replacetile):
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
                valid = blockcheck(x, y, newmap, checktile)
                if valid == False:
                    newmap[y][x] = replacetile
                    removed += 1
        if removed == 0:
            break
    return newmap

def blockcheck(x, y, map, checktile):
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

def generateoverworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial):
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
        map = generateterrain(x, y, map, "#", landrate)
    for i in range(0, lakes): # generate lakes
        y = random.randint(0, len(map)-1)
        x = random.randint(0, len(map[0])-1)
        map[y][x] = "*" # placeholder terrain tile
        map = generateterrain(x, y, map, "~", lakerate)
    if special == "block":
        print("block special")
        map = blockmodify(map, "#", "~")
        map = blockmodify(map, "~", "#")
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
            map = generateterrain(x, y, map, "#", extrarate)
    return map
