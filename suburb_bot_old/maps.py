import os
import sys
import random
import discord
import asyncio
from copy import deepcopy
from discord.ext import tasks, commands

import util
import config
import explore
import alchemy
import npcs

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

class Overmap():
    def __init__(self, session, name, player=None): #name of overmap is "{ID}{sessionname}" for lands or "{prospit/derse}{sessionname}" for other locations
        if name not in util.sessions[session]["overmaps"]: util.sessions[session]["overmaps"][name] = {}
        self.__dict__["session"] = session
        self.__dict__["name"] = name
        if player != None and self.setup == None: # this is a land
            print(f"PLAYER GRIST CATEGORY {player.gristcategory} PLAYER ASPECT {player.aspect}")
            self.gristcategory = player.gristcategory
            self.player = player.id
            self.aspect = player.aspect
            self.genlandname()
            self.setup = True
        if self.maps == None:
            self.maps = {}
        if self.specials == None:
            self.specials = []
        if self.map == None:
            print("TRYING TO GENERATE OVERMAP, NOT FOUND")
            self.genovermap()
        if self.gates == None: self.gates = {}
        if self.gates == {}: self.gengates()
        if self.difficultymap == None:
            self.gendifficultymap()
        if self.houseentered == None: self.houseentered = []
        if self.landentered == None: self.landentered = []

    def getmap(self, x=None, y=None, name=None):
        if name == None:
            return Map(self, x, y)
        else:
            name = name.replace(",", "")
            name = name.split(" ")
            x = int(name[0])
            y = int(name[1])
            return Map(self, x, y)

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
            housemap.genrooms()

    def gendifficultymap(self): #difficulty map, 1-6 difficulty
        self.difficultymap = deepcopy(self.map)
        for y, line in enumerate(self.difficultymap):
            for x, char in enumerate(self.difficultymap[y]):
                self.difficultymap[y][x] = "6"
        housemap = self.getmap(name=self.housemap)
        x = housemap.x
        y = housemap.y
        for i in range(6, 0, -1):
            for h in range(y-(i), y+(i)+1): #y
                for w in range(x-(3*i), x+(3*i)+1): #x
                    height = h
                    width = w
                    while height >= len(self.difficultymap):
                        height -= len(self.difficultymap)
                    while height < 0:
                        height += len(self.difficultymap)
                    while width >= len(self.difficultymap[0]):
                        width -= len(self.difficultymap[0])
                    while height < 0:
                        width += len(self.difficultymap[0])
                    self.difficultymap[height][width] = str(i)
        for gate in self.gates:
            coords = self.gates[gate].split(", ")
            self.difficultybubble(int(coords[1]), int(coords[0]), 3, gate)
        #random pockets of 7
        for i in range(4): # 4 random pockets
            distx = random.randint(6, 15)
            if random.random() < 0.5:
                distx *= -1
            disty = random.randint(3, 7)
            if random.random() < 0.5:
                disty *= -1
            self.difficultybubble(x+distx, y+disty, i+1, "7")
        # for line in self.difficultymap:
        #     print("".join(line))

    def difficultybubble(self, x, y, r, difficulty):
        for n in range(r): # basically this creates a circle by creating rings of various sizes
            coords = []
            for m in range(n):
                coords.append([m, n-m])
                coords.append([-1*m, n-m])
                coords.append([m, -1*n-m])
                coords.append([-1*m, -1*n-m])
            for coord in coords:
                height = y + coord[1]
                width = x + coord[0]
                while height >= len(self.difficultymap):
                    height -= len(self.difficultymap)
                while height < 0:
                    height += len(self.difficultymap)
                while width >= len(self.difficultymap[0]):
                    width -= len(self.difficultymap[0])
                while height < 0:
                    width += len(self.difficultymap[0])
                self.difficultymap[height][width] = str(difficulty)

    def genlandname(self):
        print(f"{self.gristcategory} {self.aspect}")
        print(f"Player {self.Player} {self.Player.name} {self.player}")
        print(f"grist {self.gristcategory} aspect {self.aspect}")
        if self.gristcategory == None:
            self.gristcategory == self.Player.gristcategory
        if self.aspect == None:
            self.aspect == self.Player.aspect
        bases = config.landbases[self.gristcategory] + config.aspectbases[self.aspect]
        random.seed(self.Player.name)
        random.shuffle(bases)
        self.base1 = bases[0]
        if self.aspect != "space":
            self.base2 = bases[1]
        else:
            self.base2 = "frogs"
        self.title = f"Land of {self.base1.capitalize()} and {self.base2.capitalize()}"
        words = self.title.split(" ")
        acronym = ""
        for word in words:
            acronym += f"{word[0].upper()}"
        self.acronym = acronym

    def gengates(self):
        housemap = self.getmap(name=self.housemap)
        x = housemap.x
        y = housemap.y
        for num in range(1,8): # gates 1-7
            if num % 2 == 1: #even number gates should be close to odd numbered gates before them
                loc = self.chooselocation(x, y, 2*num)
                oddloc = loc
            else:
                loc = self.chooselocation(oddloc[0], oddloc[1], 2)
            map = self.getmap(loc[0], loc[1])
            map.genmap(type=f"gate{num}")
            self.gates[num] = map.name
            self.specials.append(map.name)

    def chooselocation(self, x, y, distance): # chooses a random location that's distance away from x, y
        possiblelocs = []
        for num in range(0, distance+1):
            possiblelocs.append([num, distance-num])
            possiblelocs.append([num * -1, distance-num])
            possiblelocs.append([num, (distance-num) * -1])
            possiblelocs.append([num * -1, (distance-num) * -1])
        random.shuffle(possiblelocs)
        for loc in possiblelocs:
            xplus = loc[0]
            yplus = loc[1] # this creates a sort of ring of valid targets around x, y
            newx = x + xplus
            newy = y + yplus
            while newx >= len(self.map[0]):
                newx -= len(self.map[0]) # loop around to the other side
            while newx < 0:
                newx = len(self.map[0]) + newx # loop around to the other side
            while newy >= len(self.map):
                newy -= len(self.map) # loop around to the other side
            while newy < 0:
                newy = len(self.map) + newy # loop around to the other side
            if self.map[newy][newx] == "#" and f"{newx}, {newy}" not in self.specials:
                return [newx, newy]
        else: # if there is no valid location around the tile
            return self.chooselocation(x, y, distance+1) # recurse, find loc further away

    def displaymap(self, player=None, flash=False):
        out = ""
        mapdisplay = deepcopy(self.map)
        if flash == True:
            for map in self.maps:
                m = self.getmap(name=map)
                x = m.x
                y = m.y
                if m.overmaptile != None:
                    mapdisplay[y][x] = m.overmaptile
            if player != None:
                mapdisplay[player.opos[1]][player.opos[0]] = "@"
        out += "```"
        for line in mapdisplay:
            for char in line:
                out += char
            out+="\n"
        out += "```"
        return out

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        if attr in util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["name"]]:
            return util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["name"]][attr]
        else:
            print(f"could not find {attr}")
            return None

    @property
    def Player(self):
        player = explore.Player(self.player)
        return player

    @property
    def color(self):
        return config.aspectcolors[self.aspect]

class Map(): #
    def __init__(self, overmap, x, y):
        if f"{x}, {y}" not in util.sessions[overmap.session]["overmaps"][overmap.name]["maps"]:
            print("NOT FOUND!")
            util.sessions[overmap.session]["overmaps"][overmap.name]["maps"][f"{x}, {y}"] = {}
        self.__dict__["session"] = overmap.session
        self.__dict__["overmap"] = overmap.name
        self.__dict__["x"] = x
        self.__dict__["y"] = y
        if self.map == None:
            print("TRYING TO GENERATE MAP, NOT FOUND")
            self.genmap()
        if self.rooms == None:
            self.rooms = {}

    def __setattr__(self, attr, value):
        util.sessions[self.__dict__["session"]]["overmaps"][self.__dict__["overmap"]]["maps"][f"{self.__dict__['x']}, {self.__dict__['y']}"][attr] = value

    def __getattr__(self, attr):
        session = self.__dict__["session"]
        overmap = self.__dict__["overmap"]
        x = self.__dict__['x']
        y = self.__dict__['y']
        # print(f"{x}, {y} {util.sessions[session]['overmaps'][overmap]['maps'][f'{x}, {y}']}")
        if attr in util.sessions[session]["overmaps"][overmap]["maps"][f"{x}, {y}"]:
            return util.sessions[session]["overmaps"][overmap]["maps"][f"{x}, {y}"][attr]
        else:
            return None

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

    def mapembed(self, player, flash=False):
        room = player.Room
        color = player.Overmap.color
        desc = f"{displayregion(player, flash=flash)}"
        desc += f"{player.name} {room.roomdescribe()}. "
        desc += f"{room.describe(player)}"
        foot = ""
        foot += f"w a s d to move.\nType `update` to update the room and `none` to close it.\n"
        if len(room.items) > 0:
            foot += f"Type `>captcha` to captchalogue an item.\n"
        if room.tile in ["0","1","2","3","4","5","6","7"] or player.Map.overmaptile in ["0","1","2","3","4","5","6","7"]:
            foot += f"Type `>enter` to enter the gate."
        embed = discord.Embed(title=f"{room.roomname} [{player.pos[0]}, {player.pos[1]}]", description = desc, color=color) #title should be the type of room they are in
        embed.set_footer(text=foot)
        return embed

    def genrooms(self):
        for y, line in enumerate(self.map):
            for x, char in enumerate(self.map[y]):
                if char != ".":
                    self.getroom(x, y, gen=True)

    def tile(self, x, y): # return the symbol of the tile at coordinates
        try:
            t = self.map[y][x]
        except IndexError:
            print("CAUGHT ERROR IN TILE SYMBOL")
            print(f"y {y}")
            print(f"y {y} length {len(self.map)} x {x} length {len(self.map[y])}")
            for line in self.map:
                print("".join(line))
            t = "."
        return t

    def validspawns(self):
        spawns = [] # list of lists [x, y]
        for y, line in enumerate(self.map):
            for x, char in enumerate(line):
                if char in ["B", "S"]:
                    spawns.append([x, y])
        if len(spawns) == 0: spawns = [[0,0]]
        return spawns

    def validtile(self):
        spawns = [] # list of lists [x, y]
        for y, line in enumerate(self.map):
            if self.map[y][0] == ".":
                if self.map[y+1] in config.impassible + config.infallible:
                    spawns.append([y, 0])
        return spawns

    def findtile(self, tile): # returns a list of coordinates with the specified tile
        spawns = []
        for y, line in enumerate(self.map):
            for x, char in enumerate(line):
                if char == tile:
                    spawns.append([x, y])
        return spawns

    def getroom(self, x=None, y=None, name=None, gen=False): # returns the room at coordinates
        if name == None:
            return Room(self, x, y, gen)
        else:
            name = name.replace(",", "")
            name = name.split(" ")
            x = int(name[0])
            y = int(name[1])
            return Room(self, x, y, gen)

    @property
    def Overmap(self):
        overmap = Overmap(self.session, self.overmap)
        return overmap

    @property
    def name(self):
        return f"{self.__dict__['x']}, {self.__dict__['y']}"

    @property
    def x(self):
        return self.__dict__['x']

    @property
    def y(self):
        return self.__dict__['y']

class Room():
    def __init__(self, map, x, y, gen=False):
        self.__dict__["session"] = map.session
        self.__dict__["map"] = map.name
        self.__dict__["overmap"] = map.overmap
        self.__dict__["x"] = x
        self.__dict__["y"] = y
        if f"{x}, {y}" not in map.rooms:
            map.rooms[f"{x}, {y}"] = {}
        if self.npcs == None:
            self.npcs = []
        if self.items == None:
            #generate items in tile
            #temporarily just choosing random garbage in each tile
            self.items = []
            t = map.tile(x, y)
            if gen == True and t not in config.special and t in config.maptiles and t != ".":
                if config.maptiles[t] in config.itemcategoryrarities:
                    r = config.maptiles[t]
                    self.addcategoryitem("anywhere", noloop=True)
                    if "always" in config.itemcategoryrarities[r]:
                        for item in config.itemcategoryrarities[r]["always"]:
                            self.additem(item)
                    itemnum = random.randint(2,6)
                    for i in range(itemnum):
                        self.addcategoryitem(r)

    def addcategoryitem(self, category, noloop=False):
        rng = random.random()
        if rng < 0.65:
            if "common" in config.itemcategoryrarities[category]:
                self.additem(random.choice(config.itemcategoryrarities[category]["common"]))
            else:
                if noloop == False:
                    self.addcategoryitem(category)
                else:
                    return None
        elif rng < 0.92:
            if "uncommon" in config.itemcategoryrarities[category]:
                self.additem(random.choice(config.itemcategoryrarities[category]["uncommon"]))
            else:
                if noloop == False:
                    self.addcategoryitem(category)
                else:
                    return None
        elif rng < 0.99:
            if "rare" in config.itemcategoryrarities[category]:
                self.additem(random.choice(config.itemcategoryrarities[category]["rare"]))
            else:
                if noloop == False:
                    self.addcategoryitem(category)
                else:
                    return None
        else:
            if "exotic" in config.itemcategoryrarities[category]:
                self.additem(random.choice(config.itemcategoryrarities[category]["exotic"]))
            else:
                if noloop == False:
                    self.addcategoryitem(category)
                else:
                    return None

    def __setattr__(self, attr, value):
        self.Map.rooms[f"{self.__dict__['x']}, {self.__dict__['y']}"][attr] = value

    def __getattr__(self, attr):
        if attr in self.Map.rooms[f"{self.__dict__['x']}, {self.__dict__['y']}"]:
            return self.Map.rooms[f"{self.__dict__['x']}, {self.__dict__['y']}"][attr]
        else:
            return None

    def additem(self, name):
        items = self.items
        item = alchemy.Item(name)
        inst = alchemy.Instance(item=name)
        items.append(inst.name)
        self.items = items

    def addinstance(self, name):
        items = self.items
        inst = alchemy.Instance(name=name)
        items.append(inst.name)
        self.items = items
        return inst

    def addnpc(self, name=None, type=None, tier=None):
        npc = npcs.Npc(name=name, type=type, tier=tier, room=self)
        return npc

    def enemycheck(self, player):
        if self.strife != None:
            return True
        else:
            for name in self.npcs:
                npc = npcs.Npc(name=name)
                if npc.team != player.team:
                    return True
            else:
                return False

    @property
    def Strife(self):
        if self.strife != None:
            return explore.strifes[self.strife]
        else:
            return None

    @property
    def map(self):
        return self.__dict__["map"]

    @property
    def Overmap(self):
        return Overmap(self.__dict__["session"], self.__dict__["overmap"])

    @property
    def Map(self):
        return self.Overmap.getmap(name=self.__dict__["map"])

    @property
    def tile(self):
        t = self.Map.tile(self.__dict__['x'], self.__dict__['y'])
        return t

    @property
    def players(self): # returns a list of player ids
        list = []
        for p in util.sessions[self.__dict__["session"]]["members"]:
            player = explore.Player(p)
            if player.setup and player.Room.name == self.name and player.Map.name == self.Map.name and player.Overmap.name == self.Overmap.name:
                list.append(p)
        return list

    @property
    def x(self):
        return self.__dict__["x"]

    @property
    def y(self):
        return self.__dict__["y"]

    @property
    def name(self):
        return f"{self.__dict__['x']}, {self.__dict__['y']}"

    @property
    def roomname(self):
        m = self.Map
        t = m.tile(self.x, self.y)
        try:
            name = config.maptiles[t]
        except KeyError:
            name = "room"
        return name

    def describe(self, player):
        if len(self.items) > 0:
            text = f"{player.they.capitalize()} can see items:\n"
            for i in self.items:
                inst = alchemy.Instance(name=i)
                text += f"`{inst.Item.calledby}` "
        else:
            text = "There are no items in the area."
        if len(self.npcs) > 0:
            text += "\nThere are NPCs in the area:\n"
            for n in self.npcs:
                npc = npcs.Npc(name=n)
                text += f"`{npc.calledby}` "
        players = self.players.copy()
        if player.id in players:
            players.remove(player.id)
        if len(players) > 0:
            text += f"\nThere are other players in the area:\n"
            for p in players:
                pobj = explore.Player(p)
                text += f"`{pobj.name}` "
        return text

    def roomdescribe(self): # gives the "stands in a" description
        if self.roomname in config.roomdescriptions:
            return config.roomdescriptions[self.roomname]
        else:
            return f"stands in a {self.roomname}"

    def namecheck(self, name):
        print(f"namecheck for room at {self.x}, {self.y}")
        for i in self.items:
            item = alchemy.Instance(name=i)
            if name.upper() == item.Item.calledby:
                name = i
                break
        return name

    def roomcheck(self, name): #same as namecheck but returns False if not found
        newname = False
        print(f"namecheck for room at {self.x}, {self.y}")
        for i in self.items:
            item = alchemy.Instance(name=i)
            if name.upper() == item.Item.calledby:
                newname = i
                break
        return newname

    def npccheck(self, name): #roomcheck for npcs
        newname = False
        print(f"npccheck for room at {self.x}, {self.y}")
        for i in self.npcs:
            npc = npcs.Npc(name=i)
            if name.upper() == npc.calledby:
                newname = i
                break
        return newname

    def playercheck(self, name): #roomcheck for players
        newname = False
        print(f"playercheck for room at {self.x}, {self.y}")
        for i in self.players:
            p = explore.Player(i)
            if name.upper() == p.name.upper():
                newname = i
                break
        return newname

def displayregion(player, width=8, height=4, flash=False):
    minx = player.pos[0] - (width//2)
    maxx = player.pos[0] + (width//2)
    miny = player.pos[1] - (height//2)
    maxy = player.pos[1] + (height//2)
    if maxy > len(player.Map.map) - 1:
        maxy = len(player.Map.map) - 1
    if miny < 0:
        miny = 0
    if maxx > len(player.Map.map[maxy]) - 1:
        maxx = len(player.Map.map[maxy]) - 1
    if minx < 0:
        minx = 0
    out = ""
    for y in range(miny, maxy+1):
        out += "`"
        for x in range(minx, maxx+1):
            if x < 0 or y < 0:
                continue
            if flash == True:
                if player.pos[0] == x and player.pos[1] == y:
                    out += "@"
                    continue
                elif len(player.Map.getroom(x=x, y=y).players) > 0:
                    out += "@"
                    continue
                elif player.Map.getroom(x=x, y=y).npcs != []:
                    players = False
                    for name in player.Map.getroom(x=x, y=y).npcs:
                        npc = npcs.Npc(name)
                        if npc.team == "ENEMIES":
                            out += "!"
                            break
                    else:
                        out += "?"
                        continue
                    continue
            try:
                out += player.Map.map[y][x]
            except IndexError:
                pass
        out += "`\n"
    out = out.replace("``", "")
    return out

class Maps(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="harlify") # debugs anything into the room you're in
    async def harlify(self, ctx, *target):
        player = explore.Player(ctx.author)
        room = player.Room
        print(f"harlify for {room.x}, {room.y}")
        name = " ".join(target)
        inst = alchemy.Instance(item=name)
        player.Room.addinstance(inst.name)
        m = await ctx.send(f"Poof! Your {name.upper()} plot-appearifies conveniently in your room. It's a good thing you're a mysterious and interesting character.")
        await asyncio.sleep(3)
        await m.delete()

    @commands.command(name="npcify") # debugs an npc into the room you're in
    async def npcify(self, ctx, type, tier):
        player = explore.Player(ctx.author)
        room = player.Room
        print(f"npcify for {room.x}, {room.y}")
        npc = player.Room.addnpc(type=type, tier=int(tier))
        m = await ctx.send(f"Wait, where did that {npc.calledby} come from?")
        await asyncio.sleep(3)
        await m.delete()

    @commands.command(name="difficultymap") # generate difficulty map for overworld
    async def difficultymapcmd(self, ctx):
        player = explore.Player(ctx.author)
        player.Overmap.gendifficultymap()
        await ctx.send("Generated")

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
            print("break")
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

if __name__ == "__main__":
    while True:
        islands = int(input("Islands: "))
        landrate = float(input("Land Rate: "))
        lakes = int(input("Lakes: "))
        lakerate = float(input("Lake Rate: "))
        special = input("Special: ")
        extralands = int(input("Extra Islands: "))
        extrarate = float(input("Extra Land Rate: "))
        extraspecial = input("Extra Special: ")
        while True:
            m = generateoverworld(islands, landrate, lakes, lakerate, special, extralands, extrarate, extraspecial)
            for line in m:
                ln = ""
                for char in line:
                    ln += char
                print(ln)
            repeat = input("Repeat? (y/n) ")
            if repeat == "n":
                break
