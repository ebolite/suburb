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
        spoils_dict[self.grist_type] = self.power // tier
        for i in reversed(range(grist_index)):
            next_grist = grist_list[i]
            tier = config.grists[next_grist]["tier"]
            amount = (self.power // (tier)) // (i + 2)
            if amount == 0: break
            spoils_dict[next_grist] = amount
        for grist_name, amount in spoils_dict.copy().items():
            new_amount = amount * (0.5 + random.random())
            new_amount = math.ceil(new_amount/num_players)
            spoils_dict[grist_name] = new_amount
        return spoils_dict

if __name__ == "__main__":
    ...