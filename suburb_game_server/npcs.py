from string import ascii_letters
from typing import Optional, Callable
from copy import deepcopy
import random
import math

import util
import config
import sessions
import strife
import skills

underlings: dict[str, "Underling"] = {}
griefer_ai: dict[str, "GrieferAI"] = {}

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
        self.actions = 1
        self.cluster_size = 1
        self.difficulty = 1
        self.variance = 0
        self.additional_skills = []
        self.onhit_states = {}
        self.wear_states = {}
        self.immune_states = []
        self.ai_type: str = "random"

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
        npc.actions = self.actions
        npc.ai_type = self.ai_type
        npc.additional_skills = self.additional_skills
        npc.hostile = True
        npc.onhit_states = self.onhit_states
        npc.wear_states = self.wear_states
        room.add_npc(npc)
        return npc

class GrieferAI():
    name = "random"
    def __init__(self):
        griefer_ai[self.name] = self

    def ai_choose_skill(self, user: "strife.Griefer") -> str:
        return user.get_random_submittable_skill()
GrieferAI()

imp = Underling("imp")
imp.stat_ratios["luck"] = 3
imp.cluster_size = 3
imp.difficulty = 1
imp.variance = 4
imp.ai_type = "imp"

class ImpAI(GrieferAI):
    name = "imp"
    def ai_choose_skill(self, user: "strife.Griefer") -> str:
        if skills.skills["abuse"].is_submittable_by(user): return "abuse"
        return super().ai_choose_skill(user)
ImpAI()

ogre = Underling("ogre")
ogre.base_power = 16
ogre.stat_ratios["vigor"] = 3
ogre.stat_ratios["mettle"] = 2
ogre.stat_ratios["spunk"] = 2
ogre.stat_ratios["savvy"] = 0
ogre.wear_states = {
    "triggered": 1.0
}
ogre.cluster_size = 2
ogre.difficulty = 1
ogre.ai_type = "ogre"

class OgreAI(GrieferAI):
    name = "ogre"
    def ai_choose_skill(self, user: "strife.Griefer") -> str:
        damaging_skills = [skill for skill in user.known_skills_list if skill.damage_formula != "0"]
        sorted_skills = sorted(damaging_skills, key=lambda skill: skill.evaluate_theoretical_damage(user), reverse=True)
        for skill in sorted_skills:
            if skill.is_submittable_by(user): return skill.name
        else:
            return super().ai_choose_skill(user)
OgreAI()

lich = Underling("lich")
lich.base_power = 20
lich.stat_ratios["savvy"] = 2
lich.stat_ratios["luck"] = 2
lich.stat_ratios["spunk"] = 2
lich.immune_states = ["bleed", "poison", "blind"]
lich.cluster_size = 1
lich.difficulty = 3
lich.additional_skills = ["abhor"]
lich.ai_type = "lich"

class LichAI(GrieferAI):
    name = "lich"
    def ai_choose_skill(self, user: "strife.Griefer") -> str:
        if skills.skills["abhor"].is_submittable_by(user): return "abhor"
        return super().ai_choose_skill(user)
LichAI()

basilisk = Underling("basilisk")
basilisk.base_power = 26
basilisk.stat_ratios["savvy"] = 3
basilisk.stat_ratios["spunk"] = 2
basilisk.stat_ratios["vigor"] = 2
basilisk.onhit_states = {
    "poison": 0.5
}
basilisk.cluster_size = 2
basilisk.actions = 2
basilisk.difficulty = 4

giclops = Underling("giclops")
giclops.base_power = 68
giclops.stat_ratios["mettle"] = 4
giclops.stat_ratios["vigor"] = 2
giclops.stat_ratios["spunk"] = 2
giclops.cluster_size = 1
giclops.difficulty = 6
giclops.additional_skills = ["awreak", "abstain"]

class GiclopsAI(GrieferAI):
    name = "giclops"
    def ai_choose_skill(self, user: "strife.Griefer") -> str:
        if skills.skills["awreak"].is_submittable_by(user): return "awreak"
        if random.random() < 0.5:
            return super().ai_choose_skill(user)
        else: return "abstain"

acheron = Underling("acheron")
acheron.base_power = 111
acheron.stat_ratios["tact"] = 4
acheron.stat_ratios["spunk"] = 2
acheron.stat_ratios["mettle"] = 2
acheron.onhit_states = {
    "demoralize": 1.2
}
acheron.cluster_size = 1
acheron.difficulty = 7
acheron.actions = 2
acheron.ai_type = "ogre"

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
            self.ai_type: str = "random"
            self.stat_ratios: dict[str, int] = {
                "spunk": 1,
                "vigor": 1,
                "tact": 1,
                "luck": 1,
                "savvy": 1,
                "mettle": 1,
            }
            self.actions = 1
            self.additional_skills: list[str] = []
            self.onhit_states = {}
            self.wear_states = {}
            self.immune_states = []
            self.invulnerable = False

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
            if num_players == 0: continue
            new_amount = amount * (0.5 + random.random())
            new_amount = math.ceil(new_amount/num_players)
            spoils_dict[grist_name] = new_amount
        return spoils_dict

class KernalAI(GrieferAI):
    name = "kernel"
    def ai_choose_skill(self, user: "strife.Griefer") -> str:
        return "abstain"

class KernelSprite(Npc):
    @classmethod
    def spawn_new(cls):
        name = Npc.make_valid_name("kernel")
        sprite = cls(name)
        sprite.type = "kernel"
        sprite.hostile = False
        sprite.power = 1
        sprite.nickname = "kernel"
        sprite.invulnerable = True
        sprite.additional_skills.append("abstain")
        return sprite

if __name__ == "__main__":
    print(griefer_ai)