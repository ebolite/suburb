from copy import deepcopy
from typing import Optional

import util
import sessions

vials: dict[str, "Vial"] = {}

class Vial():
    def __init__(self, name):
        vials[name] = self
        self.maximum_formula = "0"
        self.starting_formula = "0"
        # hidden vials don't display unless they change from their starting value
        self.hidden_vial = False
        # optional vials do not exist for every griefer
        self.optional_vial = False

    def get_maximum(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.maximum_formula)
        return int(eval(formula))
    
    def get_starting(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.starting_formula)
        formula = formula.format("maximum", self.get_maximum(griefer))
        return int(eval(formula))
    
hp = Vial("hp")
hp.maximum_formula = "{power} + {vig}*6"
hp.starting_formula = "{maximum}"

vigor = Vial("vigor")
vigor.maximum_formula = "{power} + {tac}*6"
vigor.starting_formula = "{maximum}"

aspect = Vial("aspect")
aspect.maximum_formula = "{power}*2"
aspect.starting_formula = "{maximum}"

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
            self.maximum_vial_bonuses: dict[str, int] = {}
            self.player_name: Optional[str] = None
            self.vials: dict[str, dict] = {}
            # vials still need to be initialized
            for vial_name in vials:
                vial = vials[vial_name]
                if not vial.optional_vial:
                    self.add_vial(vial_name)
            self.maximum_vial_bonuses: dict[str, int] = {}

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
        if vial_name in self.maximum_vial_bonuses:
            maximum += self.maximum_vial_bonuses[vial_name]
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
            if game_attr not in self.maximum_vial_bonuses: self.maximum_vial_bonuses[game_attr] = 0
            self.maximum_vial_bonuses[game_attr] += amount
            self.change_vial(game_attr, amount)
        else:
            raise AttributeError
        
    def add_permanent_bonus(self, game_attr: str, amount: int):
        if self.player is not None: self.player.add_permanent_bonus(game_attr, amount)
        self.add_bonus(game_attr, amount)

    @property
    def power(self) -> int:
        return self.base_power
    
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
            "tac": self.get_stat("grief"),
            "luk": self.get_stat("luck"),
            "sav": self.get_stat("savvy"),
            "met": self.get_stat("mettle"),
        }
        return formula.format(**terms)

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
        if "strife_dict" not in util.sessions[room.session.name]["overmaps"][room.overmap.name]["maps"][room.map.name]["rooms"][room.name]:
            room.strife_dict = {}
            self.griefers = {}
            self.turn_num: int = 0
            # key: griefer name value: list of Skill dict (skill name and target/s)
            self.submitted_actions: dict[str, list[dict]] = {}

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