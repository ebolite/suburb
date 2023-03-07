from copy import deepcopy
from typing import Optional, Union

import util
import sessions
import npcs

vials: dict[str, "Vial"] = {}

def stats_from_ratios(stat_ratios: dict[str, int], power: int):
    total_ratios = 0
    for stat_name in stat_ratios:
        total_ratios += stat_ratios[stat_name]
    stats = {}
    for stat_name in stat_ratios:
        if total_ratios != 0: stat_mult = (stat_ratios[stat_name]/total_ratios)
        else: stat_mult = 1/len(stat_ratios)
        stats[stat_name] = int(power * stat_mult)
    remainder = power - sum(stats.values())
    for stat_name in stats:
        if remainder == 0: break
        if stats[stat_name] == 0: continue
        stats[stat_name] += 1
        remainder -= 1
    return stats

class Vial():
    def __init__(self, name):
        vials[name] = self
        self.maximum_formula = "0"
        self.starting_formula = "0"
        # hidden vials don't display unless they change from their starting value
        self.hidden_vial = False
        # optional vials do not exist for every griefer
        self.optional_vial = False
        # gel vials are fucked and weird
        self.gel_vial = False

    def get_maximum(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.maximum_formula)
        return int(eval(formula))
    
    def get_starting(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.starting_formula)
        if "{maximum}" in formula: formula = formula.replace("{maximum}", str(self.get_maximum(griefer)))
        return int(eval(formula))
    
hp = Vial("hp")
hp.maximum_formula = "{power} + {vig}*6"
hp.starting_formula = "{maximum}"
hp.gel_vial = True

vim = Vial("vim")
vim.maximum_formula = "{power} + {tac}*6"
vim.starting_formula = "{maximum}"

aspect = Vial("aspect")
aspect.maximum_formula = "{power}*2"
aspect.starting_formula = "{maximum}"
aspect.optional_vial = True

hope = Vial("hope")
hope.maximum_formula = "{power}*3"
hope.starting_formula = "{maximum}//2"
hope.hidden_vial = True

rage = Vial("rage")
rage.maximum_formula = "{power}*3"
rage.starting_formula = "{maximum}//2"
rage.hidden_vial = True

mangrit = Vial("mangrit")
mangrit.maximum_formula = "{power} + {tac}*6"
mangrit.starting_formula = "0"
mangrit.optional_vial = True

imagination = Vial("imagination")
imagination.maximum_formula = "{power} + {tac}*6"
imagination.starting_formula = "0"
imagination.optional_vial = True

horseshitometer = Vial("horseshitometer")
horseshitometer.maximum_formula = "{power} + {tac}*6"
horseshitometer.starting_formula = "{maximum}//2"
horseshitometer.optional_vial = True

gambit = Vial("gambit")
gambit.maximum_formula = "{power} + {tac}*6"
gambit.starting_formula = "{maximum}//2"
gambit.optional_vial = True

class Griefer():
    def __init__(self, name, strife: "Strife"):
        self.__dict__["name"] = name
        self.__dict__["session_name"] = strife.session.name
        self.__dict__["overmap_name"] = strife.overmap.name
        self.__dict__["map_name"] = strife.map.name
        self.__dict__["room_name"] = strife.room.name
        if name not in util.sessions[strife.session.name]["overmaps"][strife.overmap.name]["maps"][strife.map.name]["rooms"][strife.room.name]["strife_dict"]["griefers"]:
            strife.griefers[name] = {}
            self.nickname = name
            # blue: players, red: enemies
            self.team = "red"
            self.type = ""
            self.symbol_dict = {}
            self.grist_type: Optional[str] = None
            self.base_power: int = 0
            self.base_stats: dict[str, int] = {
                "spunk": 0,
                "vigor": 0,
                "tact": 0,
                "luck": 0,
                "savvy": 0,
                "mettle": 0,
            }
            self.stat_bonuses: dict[str, int] = {}
            self.player_name: Optional[str] = None
            self.vials: dict[str, dict] = {}
            # vials still need to be initialized
            for vial_name in vials:
                vial = vials[vial_name]
                if not vial.optional_vial:
                    self.add_vial(vial_name)

    @classmethod
    def from_player(cls, strife: "Strife", player: "sessions.Player") -> "Griefer":
        griefer = cls(player.name, strife)
        griefer.player_name = player.name
        griefer.type = "player"
        # todo: add player symbol dict here
        griefer.symbol_dict = {
            "base": "kid",
            "hair": "egbert",
            "mouth": "egbert",
            "eyes": "egbert",
            "shirt": "egbert",
            "pants": "egbert",
            "shoes": "egbert",
        }
        griefer.nickname = player.nickname
        griefer.base_power = player.power
        griefer.team = "blue"
        base_stats = {stat_name:player.get_base_stat(stat_name) for stat_name in player.stat_ratios}
        griefer.base_stats = base_stats
        griefer.stat_bonuses = player.permanent_stat_bonuses
        griefer.add_vial("aspect")
        griefer.add_vial(player.secondaryvial)
        griefer.initialize_vials()
        return griefer
    
    @classmethod
    def from_npc(cls, strife: "Strife", npc: "npcs.Npc") -> "Griefer":
        griefer = cls(npc.name, strife)
        griefer.type = npc.type
        griefer.grist_type = npc.grist_type
        griefer.nickname = npc.nickname
        griefer.base_power = npc.power
        griefer.base_stats = stats_from_ratios(npc.stat_ratios, npc.power)
        if npc.hostile: griefer.team = "red"
        else: griefer.team = "blue"
        griefer.initialize_vials()
        return griefer

    def change_vial(self, vial_name: str, amount: int):
        self.vials[vial_name]["current"] += amount
        maximum = self.get_vial_maximum(vial_name)
        if self.vials[vial_name]["current"] > maximum:
            self.vials[vial_name]["current"] = maximum
        if self.vials[vial_name]["current"] < 0:
            self.vials[vial_name]["current"] = 0

    def add_vial(self, vial_name: str):
        self.vials[vial_name] = {}

    def get_vial(self, vial_name: str) -> int:
        if vial_name not in self.vials: return 0
        return self.vials[vial_name]["current"]

    def get_vial_maximum(self, vial_name: str):
        vial = vials[vial_name]
        maximum = vial.get_maximum(self)
        if vial_name in self.stat_bonuses:
            maximum += self.stat_bonuses[vial_name]
        return maximum

    def initialize_vials(self):
        for vial_name in self.vials:
            vial = vials[vial_name]
            self.vials[vial_name] = {
                "starting": vial.get_starting(self),
                "current": vial.get_starting(self),
            }

    def add_bonus(self, game_attr: str, amount: int):
        if game_attr in self.base_stats:
            if game_attr not in self.stat_bonuses: self.stat_bonuses[game_attr] = 0
            self.stat_bonuses[game_attr] += amount
        elif game_attr in vials:
            if game_attr not in self.stat_bonuses: self.stat_bonuses[game_attr] = 0
            self.stat_bonuses[game_attr] += amount
            self.change_vial(game_attr, amount)
        else:
            raise AttributeError
        
    def add_permanent_bonus(self, game_attr: str, amount: int):
        if self.player is not None: self.player.add_permanent_bonus(game_attr, amount)
        self.add_bonus(game_attr, amount)

    @property
    def power(self) -> int:
        return self.base_power
    
    @property
    def stats_dict(self) -> dict:
        out = {}
        for stat in self.base_stats:
            out[stat] = self.get_stat(stat)
        out["power"] = self.get_stat("power")
        return out
    
    @property
    def vials_dict(self) -> dict:
        out = {}
        for vial in self.vials:
            out[vial] = {"current": self.get_vial(vial), 
                         "maximum": self.get_vial_maximum(vial),
                         "starting": self.vials[vial]["starting"],
                         "hidden": vials[vial].hidden_vial,
                         "gel": vials[vial].gel_vial
                         }
        return out
    
    def get_stat(self, stat_name) -> int:
        if stat_name == "power": return self.power
        stat = self.base_stats[stat_name]
        if stat_name in self.stat_bonuses:
            stat += self.stat_bonuses[stat_name]
        return stat

    def format_formula(self, formula: str) -> str:
        terms = {
            "power": self.power,
            "spk": self.get_stat("spunk"),
            "vig": self.get_stat("vigor"),
            "tac": self.get_stat("tact"),
            "luk": self.get_stat("luck"),
            "sav": self.get_stat("savvy"),
            "met": self.get_stat("mettle"),
        }
        for term in terms:
            if f"{{{term}}}" in formula: formula = formula.replace(f"{{{term}}}", str(terms[term]))
        return formula

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["overmaps"][self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["map_name"]]
         ["rooms"][self.__dict__["room_name"]]
         ["strife_dict"]["griefers"]
         [self.__dict__["name"]][attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["map_name"]]
                               ["rooms"][self.__dict__["room_name"]]
                               ["strife_dict"]["griefers"]
                               [self.__dict__["name"]][attr])
        return self.__dict__[attr]
    
    def get_dict(self) -> dict:
        out = deepcopy(util.sessions[self.__dict__["session_name"]]
                        ["overmaps"][self.__dict__["overmap_name"]]
                        ["maps"][self.__dict__["map_name"]]
                        ["rooms"][self.__dict__["room_name"]]
                        ["strife_dict"]["griefers"]
                        [self.__dict__["name"]])
        out["stats_dict"] = self.stats_dict
        out["vials_dict"] = self.vials_dict
        return out

    @property
    def session(self) -> "sessions.Session":
        return sessions.Session(self.__dict__["session_name"])
    
    @property
    def overmap(self) -> "sessions.Overmap":
        return sessions.Overmap(self.__dict__["overmap_name"], self.session)
    
    @property
    def map(self) -> "sessions.Map":
        return sessions.Map(self.__dict__["map_name"], self.session, self.overmap)
    
    @property
    def room(self) -> "sessions.Room":
        return sessions.Room(self.__dict__["room_name"], self.session, self.overmap, self.map)
    
    @property
    def strife(self) -> "Strife":
        return Strife(self.room)
    
    @property
    def player(self) -> Optional["sessions.Player"]:
        if self.player_name is None: return None
        return sessions.Player(self.player_name)

# each room can only have one Strife in it
class Strife():
    def __init__(self, room: "sessions.Room"):
        self.__dict__["session_name"] = room.session.name
        self.__dict__["overmap_name"] = room.overmap.name
        self.__dict__["map_name"] = room.map.name
        self.__dict__["room_name"] = room.name
        if not room.strife_dict:
            self.griefers = {}
            self.turn_num: int = 0
            # key: griefer name value: list of Skill dict (skill name and target/s)
            self.submitted_actions: dict[str, list[dict]] = {}

    def add_griefer(self, identifier: Union["sessions.Player", "npcs.Npc"]):
        if isinstance(identifier, sessions.Player):
            Griefer.from_player(self, identifier)
        elif isinstance(identifier, npcs.Npc):
            Griefer.from_npc(self, identifier)

    def end(self):
        self.room.strife_dict = {}

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["overmaps"][self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["map_name"]]
         ["rooms"][self.__dict__["room_name"]]
         ["strife_dict"][attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["map_name"]]
                               ["rooms"][self.__dict__["room_name"]]
                               ["strife_dict"][attr])
        return self.__dict__[attr]
    
    def get_dict(self) -> dict:
        out = deepcopy(util.sessions[self.__dict__["session_name"]]
                        ["overmaps"][self.__dict__["overmap_name"]]
                        ["maps"][self.__dict__["map_name"]]
                        ["rooms"][self.__dict__["room_name"]]
                        ["strife_dict"])
        for griefer_name in self.griefers:
            out["griefers"][griefer_name] = self.get_griefer(griefer_name).get_dict()
        return out
    
    def get_griefer(self, name: str) -> "Griefer":
        return Griefer(name, self)

    @property
    def session(self) -> "sessions.Session":
        return sessions.Session(self.__dict__["session_name"])
    
    @property
    def overmap(self) -> "sessions.Overmap":
        return sessions.Overmap(self.__dict__["overmap_name"], self.session)
    
    @property
    def map(self) -> "sessions.Map":
        return sessions.Map(self.__dict__["map_name"], self.session, self.overmap)
    
    @property
    def room(self) -> "sessions.Room":
        return sessions.Room(self.__dict__["room_name"], self.session, self.overmap, self.map)