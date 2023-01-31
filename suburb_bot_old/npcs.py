import explore
import skills
import alchemy
import maps
import util
import config
import string
import random
import math

class Npc():
    def __init__(self, name=None, type=None, tier=None, room=None, map=None):
        if name != None and name not in util.npcs:
            return None
        if type != None:
            name = type
            while name in util.npcs:
                name += random.choice(string.ascii_letters).upper()
            self.__dict__["name"] = name
            util.npcs[name] = {}
            self.type = type
            if tier == None:
                self.tier = 0
            else:
                self.tier = tier
            if self.skills == None:
                self.skills = skills.defaults.copy()
                for s in skills.noenemy:
                    self.skills.remove(s)
            for skill in npcs[type]["skills"]:
                self.skills.append(skill)
        else:
            self.__dict__["name"] = name
            if self.skills == None:
                self.skills = skills.defaults.copy()
                for s in skills.noenemy:
                    self.skills.remove(s)
        if room != None:
            self.gotoroom(room)
        if map != None:
            self.map = map.name
            self.overmap = map.Overmap.name
            if self.originalovermap == None:
                self.originalovermap = self.overmap
            self.session = map.Overmap.session
            if self.originalsession == None:
                self.originalsession = self.session
        if self.adjectives == None:
            self.adjectives = []
        if self.vials == None:
            self.vials = ["health", "vim", "hope", "blood", "rage"]
        if self.stats == None:
            self.stats = npcs[self.type]["stats"].copy()
            if self.tier != 0:
                self.stats["POWER"] *= self.tier
            self.stats["RUNG"] = self.power
            if "noprototype" not in npcs[self.type]:
                self.prototypeadjs()
            for stat in self.stats:
                if stat != "POWER" and stat != "RUNG":
                    self.stats[stat] = self.stats["POWER"] * self.stats[stat]
            self.power = self.stats["POWER"]
        if self.passives == None:
            self.passives = []
        if self.team == None:
            self.team = "ENEMIES"

    def gotoroom(self, room):
        if self.room != None:
            self.Room.npcs.remove(self.name)
        self.room = room.name
        self.map = room.Map.name
        self.overmap = room.Overmap.name
        if self.originalovermap == None:
            self.originalovermap = self.overmap
        self.session = room.Overmap.session
        if self.originalsession == None:
            self.originalsession = self.session
        self.Room.npcs.append(self.name)

    async def interact(self, ctx):
        if npcs[self.type]["interact"] != None:
            return await npcs[self.type]["interact"](self, ctx)
        else:
            return f"{self.calledby} does not want to be interacted with!"

    def prototypeadjs(self):
        print(f"session {self.originalsession}")
        if util.sessions[self.originalsession]["prototypes"] != {}:
            name = random.choice(list(util.sessions[self.originalsession]["prototypes"]))
            instname = random.choice(util.sessions[self.originalsession]["prototypes"][name])
            inst = alchemy.Instance(name=instname)
            adj = inst.Item.randomadj()
            self.adjectives.append(adj)
            power = inst.Item.power + inst.Item.inheritpower
            self.stats["POWER"] *= math.log(power, 10)
            self.stats["POWER"] = int(self.stats["POWER"])

    def die(self):
        if "dies" in npcs[self.type]:
            pass
        else:
            if self.following != None:
                p = explore.Player(self.following)
                if self.name in p.followers:
                    p.followers.remove(self.name)
            if self.room != None:
                self.Room.npcs.remove(self.name)
            self.room = None

    def follow(self, player):
        if self.following != player.name:
            if self.following != None:
                p = explore.Player(self.following)
                if self.name in p.followers:
                    p.followers.remove(self.name)
            if self.name not in player.followers:
                self.following = player.name
                player.followers.append(self.name)
        else:
            if self.name in player.followers:
                player.followers.remove(self.name)
            self.following = None

    @property
    def calledby(self):
        if self.nickname != None:
            return self.nickname
        name = ""
        if self.originalovermap == None:
            name = self.type.upper()
        else:
            if self.tier != 0:
                name = f"{config.gristcategories[self.OriginalOvermap.gristcategory][self.tier-1].upper()} {self.type.upper()}"
            else:
                name = self.type.upper()
        for adj in self.adjectives:
            name = f"{adj.upper()} {name}"
        return name

    @property
    def OriginalOvermap(self):
        return maps.Overmap(self.originalsession, self.originalovermap)

    @property
    def Overmap(self):
        return maps.Overmap(self.session, self.overmap)

    @property
    def Map(self):
        return self.Overmap.getmap(name=self.map)

    @property
    def Room(self):
        return self.Map.getroom(name=self.room)

    def __getattr__(self, attr):
        if attr in util.npcs[self.__dict__["name"]]:
            return util.npcs[self.__dict__["name"]][attr]
        else:
            return None

    def __setattr__(self, attr, value):
        util.npcs[self.__dict__["name"]][attr] = value

async def sprite(npc, ctx):
    user = explore.Player(ctx.author)
    if npc.prototyped == None or npc.prototyped2 == None:
        embed = user.embedsylladex
        message = await ctx.send(embed=embed, content=f"What item should {user.name} use? (The item must be in {user.their} Captchalogue Deck)")
        m = await util.messagecheck(message, ctx.author, None)
        if m == None:
            return f"Canceled prototyping."
        instname = user.itemcheck(m)
        if instname != False:
            inst = alchemy.Instance(name=instname)
        else:
            await message.delete()
            return f"`{m}` is not an item {user.name} has in {user.their} Captchalogue Deck."
        user.removeinstance(inst.name)
        if npc.prototyped == None:
            npc.prototyped = inst.name
        elif npc.prototyped2 == None:
            npc.prototyped2 = inst.name
        if user.entered == False:
            if "prototypes" not in util.sessions[user.session]:
                util.sessions[user.session]["prototypes"] = {}
            if user.name not in util.sessions[user.session]["prototypes"]:
                util.sessions[user.session]["prototypes"][user.name] = []
            util.sessions[user.session]["prototypes"][user.name].append(inst.name)
        if npc.nickname == None:
            truename = inst.Item.truename.upper().replace("+", "")
            if truename in ["DVD", "POSTER", "ALBUM", "BOOK", "DISC", "BUST", "FIGURINE"]:
                truename = inst.Item.randomadj().upper().replace("+", "")
            npc.nickname = f"{truename}SPRITE"
        else:
            adj = inst.Item.randomadj().upper().replace("+", "")
            npc.nickname = f"{adj}{npc.nickname}"
        npc.power += inst.Item.power + inst.Item.inheritpower
        npc.stats["POWER"] += inst.Item.power + inst.Item.inheritpower
        return f"Successfully prototyped your sprite! Say hello to {npc.nickname}!"
    else:
        if npc.player == user.name:
            npc.follow(user)
            if npc.following == None:
                return f"{npc.calledby} is no longer following you."
            else:
                return f"{npc.calledby} is now following you."
        else:
            return f"{npc.calledby} will not listen to you, since it's not your sprite!"

def encounterfromdifficulty(dif, player): # difficulties 1-8
    difficulty = 2**int(dif) # 256 at diff 8
    possible = []
    encounternpcs = []
    for npc in npcs:
        if "difficulty" in npcs[npc]:
            if npcs[npc]["difficulty"] >= difficulty * .1 and npcs[npc]["difficulty"] <= difficulty:
                possible.append(npc)
    while difficulty > 0 and possible != []:
        choice = random.choice(possible)
        if npcs[choice]["difficulty"] <= difficulty:
            d = npcs[choice]["difficulty"]
            cost = d
            for i in range(1,10): # tiers 1-9
                if cost <= difficulty:
                    highesttier = i
                    cost = d * (1 + (0.1*i))
                else:
                    break
            tier = random.randint(1, highesttier)
            n = Npc(type=choice, tier=tier, map=player.Map)
            encounternpcs.append(n)
            difficulty -= cost
        else:
            possible.remove(choice)
    return encounternpcs

npcs = { # basic npcs stats as % of power. POWER as base power #
    "kernelsprite": {
        "stats": {
            "POWER": 5,
            "SPK": .2,
            "VIG": .2,
            "TAC": .2,
            "LUK": .2,
            "SAV": .2,
            "MET": .2
            },
        "skills": [],
        "noprototype": True,
        "interact": sprite,
        "dies": False
        },
    "imp": {
        "stats": {
            "POWER": 5,
            "SPK": .1,
            "VIG": .1,
            "TAC": .1,
            "LUK": .2,
            "SAV": .3,
            "MET": .1
            },
        "difficulty": 0.5,
        "skills": []
        },
    "ogre": {
        "stats": {
            "POWER": 100,
            "SPK": .2,
            "VIG": .25,
            "TAC": .1,
            "LUK": .1,
            "SAV": .1,
            "MET": .25
            },
        "difficulty": 2,
        "skills": []
        },
    "basilisk": {
        "stats": {
            "POWER": 1413,
            "SPK": .2,
            "VIG": .2,
            "TAC": .15,
            "LUK": .05,
            "SAV": .3,
            "MET": .1
            },
        "difficulty": 6,
        "skills": []
        },
    "octopisc": {
        "stats": {
            "POWER": 2612,
            "SPK": .2,
            "VIG": .3,
            "TAC": .1,
            "LUK": .1,
            "SAV": .1,
            "MET": .2
            },
        "difficulty": 8,
        "skills": []
        },
    "lich": {
        "stats": {
            "POWER": 11025,
            "SPK": .3,
            "VIG": .1,
            "TAC": .2,
            "LUK": .1,
            "SAV": .2,
            "MET": .1
            },
        "difficulty": 25,
        "skills": []
        },
    "titachnid": {
        "stats": {
            "POWER": 41300,
            "SPK": .2,
            "VIG": .2,
            "TAC": .2,
            "LUK": .1,
            "SAV": .1,
            "MET": .2
            },
        "difficulty": 40,
        "skills": []
        },
    "serpentipede": {
        "stats": {
            "POWER": 100000,
            "SPK": .1,
            "VIG": .1,
            "TAC": .1,
            "LUK": .4,
            "SAV": .4,
            "MET": .1
            },
        "difficulty": 80,
        "skills": []
        },
    "giclops": {
        "stats": {
            "POWER": 111111,
            "SPK": .3,
            "VIG": .4,
            "TAC": .15,
            "LUK": .05,
            "SAV": .1,
            "MET": .3
            },
        "difficulty": 90,
        "skills": []
        },
    "bicephalon": {
        "stats": {
            "POWER": 222222,
            "SPK": .7,
            "VIG": .4,
            "TAC": .15,
            "LUK": 0.01,
            "SAV": 0.01,
            "MET": .3
            },
        "difficulty": 110,
        "skills": []
        },
    "acheron": {
        "stats": {
            "POWER": 10251111,
            "SPK": .4,
            "VIG": .4,
            "TAC": .15,
            "LUK": .05,
            "SAV": .15,
            "MET": .4
            },
        "difficulty": 134,
        "skills": []
        }
    }
