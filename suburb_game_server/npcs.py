from string import ascii_letters
from typing import Optional
from copy import deepcopy
import random
import math

import util
import config
import sessions

underlings: dict[str, "Underling"] = {}

class Underling():
    def __init__(self, monster_type: str):
        underlings[monster_type] = self
        self.monster_type: str = monster_type
        self.base_power: int = 1
        self.stat_ratios: dict[str, int] = {
            "spunk": 1,
            "vigor": 1,
            "tact": 1,
            "luck": 1,
            "savvy": 1,
            "mettle": 1,
        }
        self.cluster_size = 1
        self.difficulty = 1
        self.variance = 0

    def make_npc(self, grist_name: str, grist_category: str, room: "sessions.Room") -> "Npc":
        tier: int = config.grists[grist_name]["tier"]
        power = self.base_power * (tier**2)
        nickname = f"{grist_name} {self.monster_type}"
        name = Npc.make_valid_name(nickname)
        npc = Npc(name)
        npc.type = self.monster_type
        npc.grist_type = grist_name
        npc.grist_category = grist_category
        npc.power = power
        npc.nickname = nickname
        npc.stat_ratios = self.stat_ratios
        npc.hostile = True
        room.add_npc(npc)
        return npc

imp = Underling("imp")
imp.stat_ratios["luck"] = 3
imp.cluster_size = 3
imp.difficulty = 1
imp.variance = 4

ogre = Underling("ogre")
ogre.base_power = 16
ogre.stat_ratios["vigor"] = 3
ogre.stat_ratios["mettle"] = 2
ogre.stat_ratios["spunk"] = 2
ogre.stat_ratios["savvy"] = 0
ogre.cluster_size = 2
ogre.difficulty = 1

lich = Underling("lich")
lich.base_power = 20
lich.stat_ratios["savvy"] = 2
lich.stat_ratios["luck"] = 2
lich.stat_ratios["spunk"] = 2
lich.cluster_size = 1
lich.difficulty = 4

basilisk = Underling("basilisk")
basilisk.base_power = 26
basilisk.stat_ratios["savvy"] = 3
basilisk.stat_ratios["spunk"] = 2
basilisk.stat_ratios["vigor"] = 2
basilisk.cluster_size = 2
basilisk.difficulty = 4

giclops = Underling("giclops")
giclops.base_power = 68
giclops.stat_ratios["mettle"] = 4
giclops.stat_ratios["vigor"] = 2
giclops.stat_ratios["spunk"] = 2
giclops.cluster_size = 1
giclops.difficulty = 6

class Npc():
    @staticmethod
    def make_valid_name(name):
        new_name = name
        while new_name in util.npcs:
            new_name += random.choice(ascii_letters)
        return new_name

    def __init__(self, name: str):
        self.__dict__["name"] = name
        self.name: str
        if name not in util.npcs:
            util.npcs[name] = {}
            self.power: int = 0
            self.nickname: str = name
            self.type: str = ""
            self.grist_category: Optional[str] = None
            self.grist_type: Optional[str] = None
            self.hostile = True
            self.stat_ratios: dict[str, int] = {
                "spunk": 1,
                "vigor": 1,
                "tact": 1,
                "luck": 1,
                "savvy": 1,
                "mettle": 1,
            }

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.npcs[self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = util.npcs[self.__dict__["name"]][attr]
        return self.__dict__[attr]
    
    def get_dict(self) -> dict:
        out = deepcopy(util.npcs[self.__dict__["name"]])
        return out
    
    def make_spoils(self, num_players: int) -> dict:
        if self.grist_category is None or self.grist_type is None: return {}
        spoils_dict = {}
        grist_list = config.gristcategories[self.grist_category]
        grist_index = grist_list.index(self.grist_type)
        tier = config.grists[self.grist_type]["tier"]
        spoils_dict["build"] = self.power
        spoils_dict[self.grist_type] = self.power
        for i in reversed(range(grist_index)):
            next_grist = grist_list[i]
            tier = config.grists[next_grist]["tier"]
            amount = (self.power // (tier)) // (i*0.5 + 2)
            if amount == 0: break
            spoils_dict[next_grist] = amount
        for grist_name, amount in spoils_dict.copy().items():
            new_amount = amount * (0.5 + random.random())
            new_amount = math.ceil(new_amount/num_players)
            spoils_dict[grist_name] = new_amount
        return spoils_dict

class KernelSprite(Npc):
    @classmethod
    def spawn_new(cls):
        name = Npc.make_valid_name("kernel")
        sprite = cls(name)
        sprite.type = "kernel"
        sprite.hostile = False
        sprite.power = 1
        sprite.nickname = "kernel"
        return sprite

if __name__ == "__main__":
    ...