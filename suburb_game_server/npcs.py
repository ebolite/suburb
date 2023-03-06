from string import ascii_letters
from copy import deepcopy
import random

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

    def make_npc(self, grist_name: str, room: "sessions.Room") -> "Npc":
        tier: int = config.grists[grist_name]["tier"]
        power = self.base_power * (tier**2)
        nickname = f"{grist_name} {self.monster_type}"
        name = Npc.make_valid_name(nickname)
        npc = Npc(name)
        npc.type = self.monster_type
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

if __name__ == "__main__":
    ...