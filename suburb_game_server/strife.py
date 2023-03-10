from copy import deepcopy
from typing import Optional, Union
import random

import util
import sessions
import npcs
import skills
import config

vials: dict[str, "Vial"] = {}
states: dict[str, "State"] = {}

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
        if stat_ratios[stat_name] == 0: continue
        stats[stat_name] += 1
        remainder -= 1
    return stats

class State():
    def __init__(self, name):
        states[name] = self
        self.name = name
        self.beneficial = False
        self.tooltip = ""

    def potency(self, griefer: "Griefer") -> float:
        return griefer.get_state_potency(self.name)

    def modify_damage_received(self, damage: int, griefer: "Griefer") -> int:
        return damage

    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        return damage
    
    def new_turn(self, griefer: "Griefer"):
        pass

class AbjureState(State):
    def modify_damage_received(self, damage: int, griefer: "Griefer") -> int:
        new_damage = damage - griefer.get_stat("mettle")*3*self.potency(griefer)
        new_damage *= 0.75
        new_damage = int(new_damage)
        return max(new_damage, 0)
    
abjure = AbjureState("abjure")
abjure.beneficial = True
abjure.tooltip = "Reducing damage based on mettle."

class Vial():
    def __init__(self, name):
        vials[name] = self
        self.name = name
        self.maximum_formula = "0"
        self.starting_formula = "0"
        # hidden vials don't display unless they change from their starting value
        self.hidden_vial = False
        # optional vials do not exist for every griefer
        self.optional_vial = False
        # gel vials are fucked and weird
        self.gel_vial = False
        # tact vials regenerate by tact each turn
        self.tact_vial = False

    def add_value(self, griefer: "Griefer", amount: int) -> int:
        current = griefer.vials[self.name]["current"]
        griefer.vials[self.name]["current"] += amount
        maximum = griefer.get_vial_maximum(self.name)
        if griefer.vials[self.name]["current"] > maximum:
            griefer.vials[self.name]["current"] = maximum
        if griefer.vials[self.name]["current"] < 0:
            griefer.vials[self.name]["current"] = 0
        return griefer.vials[self.name]["current"] - current

    def get_current(self, griefer: "Griefer") -> int:
        return griefer.get_vial(self.name)

    def get_maximum(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.maximum_formula)
        return int(eval(formula))
    
    def get_starting(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.starting_formula)
        if "{maximum}" in formula: formula = formula.replace("{maximum}", str(self.get_maximum(griefer)))
        return int(eval(formula))
    
    def difference_from_starting(self, griefer: "Griefer") -> int:
        return self.get_current(griefer) - self.get_starting(griefer)
    
    def modify_damage_received(self, damage: int, griefer: "Griefer") -> int:
        return damage

    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        return damage
    
    def modify_stat(self, stat_name: str, value: int, griefer: "Griefer") -> int:
        return value
    
    def parry_roll_modifier(self, griefer: "Griefer") -> float:
        return 1.0
    
    def new_turn(self, griefer: "Griefer"):
        pass

    def on_parry(self, griefer: "Griefer", damage_parried: int):
        pass
    
hp = Vial("hp")
hp.maximum_formula = "{power}*3 + {vig}*18"
hp.starting_formula = "{maximum}"
hp.gel_vial = True
hp.tact_vial = True

vim = Vial("vim")
vim.maximum_formula = "{power} + {tac}*6"
vim.starting_formula = "{maximum}"
vim.tact_vial = True

class AspectVial(Vial):
    def add_value(self, griefer: "Griefer", amount: int) -> int:
        difference = super().add_value(griefer, amount)
        # imagination increases when aspect vial decreases
        if difference < 0 and griefer.has_vial("imagination"):
            griefer.change_vial("imagination", -difference//2)
        return difference

aspect = AspectVial("aspect")
aspect.maximum_formula = "{power}*2"
aspect.starting_formula = "{maximum}"
aspect.optional_vial = True
aspect.tact_vial = True

class HopeVial(Vial):
    def new_turn(self, griefer: "Griefer"):
        flat_add = self.difference_from_starting(griefer)//18
        for stat_name in griefer.base_stats:
            griefer.add_bonus(stat_name, flat_add)

hope = HopeVial("hope")
hope.maximum_formula = "{power}*3"
hope.starting_formula = "{maximum}//2"
hope.hidden_vial = True

class RageVial(Vial):
    def modify_damage_received(self, damage: int, griefer: "Griefer") -> int:
        flat_add = self.difference_from_starting(griefer)
        return damage + flat_add

    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        flat_add = self.difference_from_starting(griefer)
        return damage + flat_add

rage = RageVial("rage")
rage.maximum_formula = "{power}*3"
rage.starting_formula = "{maximum}//2"
rage.hidden_vial = True

class MangritVial(Vial):
    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        value = self.get_current(griefer)
        power = griefer.power
        mod = (value**2) / (value + power)
        mod += 1
        return int(damage * mod)

mangrit = MangritVial("mangrit")
mangrit.maximum_formula = "{power} + {tac}*6"
mangrit.starting_formula = "0"
mangrit.optional_vial = True
mangrit.tact_vial = True

class ImaginationVial(Vial):
    def new_turn(self, griefer: "Griefer"):
        griefer.change_vial("aspect", self.get_current(griefer)//2)

imagination = ImaginationVial("imagination")
imagination.maximum_formula = "{power} + {tac}*6"
imagination.starting_formula = "0"
imagination.optional_vial = True

class HorseshitometerVial(Vial):
    def parry_roll_modifier(self, griefer: "Griefer") -> float:
        diff = self.difference_from_starting(griefer)
        power = griefer.power
        mod = (power**2) / (power + diff)
        return mod

    def on_parry(self, griefer: "Griefer", damage_parried: int):
        self.add_value(griefer, damage_parried//2)

horseshitometer = HorseshitometerVial("horseshitometer")
horseshitometer.maximum_formula = "{power} + {tac}*6"
horseshitometer.starting_formula = "{maximum}//2"
horseshitometer.optional_vial = True

gambit = Vial("gambit")
gambit.maximum_formula = "{power} + {tac}*6"
gambit.starting_formula = "{maximum}//2"
gambit.optional_vial = True

class Griefer():
    strife: "Strife"
    def __init__(self, name, strife: "Strife"):
        self.__dict__["strife"] = strife
        self.__dict__["name"] = name
        if name not in strife.griefers:
            strife.griefers[name] = {}
            self.nickname = name
            # blue: players, red: enemies
            self.team = "red"
            self.type = ""
            self.symbol_dict = {}
            self.grist_type: Optional[str] = None
            self.grist_category: Optional[str] = None
            self.actions = 1
            self.ready: bool = False
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
            self.known_skills: list[str] = skills.base_skills.copy()
            # submitted_skills: [{"skill_name": "aggrieve", "targets": ["jet impq", "shale ogrea"]}]
            self.submitted_skills: list[dict] = []
            self.player_name: Optional[str] = None
            self.npc_name: Optional[str] = None
            self.vials: dict[str, dict] = {}
            self.states: dict[str, dict] = {}
            # vials still need to be initialized
            for vial_name in vials:
                vial = vials[vial_name]
                if not vial.optional_vial:
                    self.add_vial(vial_name)

    def new_turn(self):
        if self.should_be_dead(): 
            self.die()
            return
        for vial in self.vials_list:
            if vial.tact_vial:
                self.change_vial(vial.name, self.get_stat("tact"))
            vial.new_turn(self) 
        for state in self.states_list.copy():
            state.new_turn(self)
            self.add_state_duration(state.name, -1)
            if self.get_state_duration(state.name) <= 0:
                self.remove_state(state.name)
        if self.player is None: self.ai_use_skills()

    def take_damage(self, damage: int, coin: Optional[bool] = None):
        if damage > 0: 
            damage = skills.modify_damage(damage, self.get_stat("mettle"))
            for vial in self.vials_list:
                damage = vial.modify_damage_received(damage, self)
            for state in self.states_list:
                damage = state.modify_damage_received(damage, self)
        if self.player is not None:
            threshold = self.get_vial_maximum("hp") / 3
            if damage > threshold:
                modified_damage = damage - threshold
                modified_damage *= config.player_hp_threshold_damage_mult
                damage = int(threshold + modified_damage)
        self.change_vial("hp", -damage)
        if coin is None:
            self.strife.log(f"{self.nickname} takes {damage} damage!")
        else:
            self.strife.log(f"{self.nickname} takes {damage} damage! ({'heads' if coin else 'scratch'})")
        if self.should_be_dead():
            self.die()

    def should_be_dead(self) -> bool:
        if self.get_vial("hp") <= 0:
            return True
        else: return False

    def die(self):
        # todo: explode into grist
        if self.npc is not None:
            self.strife.log(f"The {self.nickname} explodes into grist!")
            self.room.remove_npc(self.npc)
            spoils_dict = self.npc.make_spoils(len(self.strife.player_griefers))
            for player_griefer in self.strife.player_griefers:
                if player_griefer.player is None: raise AttributeError
                player_griefer.player.add_unclaimed_grist(spoils_dict)
        else:
            self.strife.log(f"{self.nickname}: DEAD.")
        self.strife.remove_griefer(self)

    def submit_skill(self, skill_name, targets: list[str]) -> bool:
        skill = skills.skills[skill_name]
        if len(targets) > skill.num_targets: return False
        for target_name in targets: 
            if target_name not in self.strife.griefers: return False
        if self.remaining_actions < skill.action_cost: return False
        skill_dict = {
            "skill_name": skill_name,
            "targets": targets,
        }
        self.submitted_skills.append(skill_dict)
        return True
    
    def unsubmit_skill(self):
        if self.submitted_skills:
            self.submitted_skills.pop()

    def use_skills(self):
        for skill_dict in self.submitted_skills:
            skill = skills.skills[skill_dict["skill_name"]]
            targets_list = []
            for griefer_name in skill_dict["targets"]:
                if griefer_name in self.strife.griefers:
                    targets_list.append(self.strife.get_griefer(griefer_name))
            skill.use(self, targets_list)

    def ai_use_skills(self):
        while self.remaining_actions:
            usable_skills = list(filter(lambda skill_name: skills.skills[skill_name].is_usable_by(self), self.known_skills))
            random_skill_name = random.choice(usable_skills)
            skill = skills.skills[random_skill_name]
            valid_targets = [self.strife.get_griefer(griefer_name) for griefer_name in skill.get_valid_targets(self)]
            if skill.beneficial:
                valid_targets = filter(lambda x: x.team == self.team, valid_targets)
            else:
                valid_targets = filter(lambda x: x.team != self.team, valid_targets)
            try:
                targets = random.choices(list(valid_targets), k=skill.num_targets)
            except IndexError: return
            self.submit_skill(random_skill_name, [target.name for target in targets])

    @classmethod
    def from_player(cls, strife: "Strife", player: "sessions.Player") -> "Griefer":
        griefer = cls(player.name, strife)
        griefer.player_name = player.name
        griefer.type = "player"
        # todo: add player symbol dict here
        griefer.symbol_dict = player.symbol_dict
        griefer.nickname = player.nickname
        griefer.base_power = player.power
        griefer.team = "blue"
        base_stats = {stat_name:player.get_base_stat(stat_name) for stat_name in player.stat_ratios}
        griefer.base_stats = base_stats
        griefer.stat_bonuses = player.permanent_stat_bonuses
        griefer.known_skills = player.get_known_skills()
        griefer.add_vial("aspect")
        griefer.add_vial(player.secondaryvial)
        griefer.initialize_vials()
        return griefer
    
    @classmethod
    def from_npc(cls, strife: "Strife", npc: "npcs.Npc") -> "Griefer":
        griefer = cls(npc.name, strife)
        griefer.type = npc.type
        griefer.grist_type = npc.grist_type
        griefer.grist_category = npc.grist_category
        griefer.nickname = npc.nickname.upper()
        griefer.base_power = npc.power
        griefer.base_stats = stats_from_ratios(npc.stat_ratios, npc.power)
        griefer.npc_name = npc.name
        if npc.hostile: griefer.team = "red"
        else: griefer.team = "blue"
        griefer.initialize_vials()
        return griefer

    def apply_state(self, state_name: str, applier: "Griefer", potency: float, duration: int):
        if state_name not in self.states: self.states[state_name] = {
                "applier_stats": applier.stats_dict,
                "potency": potency,
                "duration": 0,
        }
        if potency > self.get_state_potency(state_name):
            self.states[state_name]["potency"] = potency
            self.states[state_name]["applier_stats"] = applier.stats_dict
        self.states[state_name]["duration"] += duration

    def remove_state(self, state_name):
        if state_name in self.states:
            self.states.pop(state_name)

    def get_state_potency(self, state_name: str) -> float:
        return self.states[state_name]["potency"]
    
    def get_state_duration(self, state_name: str) -> int:
        return self.states[state_name]["duration"]
    
    def add_state_duration(self, state_name: str, duration: int):
        self.states[state_name]["duration"] += duration

    def change_vial(self, vial_name: str, amount: int) -> int:
        vial = vials[vial_name]
        return vial.add_value(self, amount)

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
    
    def has_vial(self, vial_name: str) -> bool:
        if vial_name in self.vials: return True
        else: return False

    def can_pay_vial_costs(self, costs: dict) -> bool:
        for vial_name in costs:
            if self.get_vial(vial_name) < costs[vial_name]: return False
        return True
    
    def pay_costs(self, costs: dict):
        for vial_name in costs:
            self.change_vial(vial_name, -costs[vial_name])

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
            print(f"bonus does not exist {game_attr}")
        
    def add_permanent_bonus(self, game_attr: str, amount: int):
        if self.player is not None: self.player.add_permanent_bonus(game_attr, amount)
        self.add_bonus(game_attr, amount)
    
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
            out[vial] = {
                "current": self.get_vial(vial), 
                "maximum": self.get_vial_maximum(vial),
                "starting": self.vials[vial]["starting"],
                "hidden": vials[vial].hidden_vial,
                "gel": vials[vial].gel_vial
            }
        return out
    
    @property
    def vials_list(self) -> list[Vial]:
        return [vials[vial_name] for vial_name in self.vials]
    
    @property
    def states_dict(self) -> dict:
        out = {}
        for state_name in self.states:
            out[state_name] = {
                "applier_stats": self.states[state_name]["applier_stats"],
                "potency": self.get_state_potency(state_name),
                "duration": self.get_state_duration(state_name),
                "tooltip": states[state_name].tooltip,
            }
        return out

    @property
    def states_list(self) -> list[State]:
        return [states[state_name] for state_name in self.states]
    
    def get_stat(self, stat_name) -> int:
        if stat_name == "power": return self.power
        stat = self.base_stats[stat_name]
        if stat_name in self.stat_bonuses:
            stat += self.stat_bonuses[stat_name]
        for vial in self.vials_list:
            stat = vial.modify_stat(stat_name, stat, self)
        return stat

    def format_formula(self, formula: str, identifier: Optional[str] = None) -> str:
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
            if identifier is None:
                if f"{{{term}}}" in formula: formula = formula.replace(f"{{{term}}}", str(terms[term]))
            else:
                if f"{identifier}.{term}" in formula: formula = formula.replace(f"{identifier}.{term}", str(terms[term]))
        return formula

    @property
    def name(self) -> str:
        return self.__dict__["name"]

    @property
    def session(self) -> "sessions.Session":
        return self.strife.session
    
    @property
    def overmap(self) -> "sessions.Overmap":
        return self.strife.overmap
    
    @property
    def map(self) -> "sessions.Map":
        return self.strife.map
    
    @property
    def room(self) -> "sessions.Room":
        return self.strife.room
    
    @property
    def player(self) -> Optional["sessions.Player"]:
        if self.player_name is None: return None
        return sessions.Player(self.player_name)
    
    @property
    def npc(self) -> Optional["npcs.Npc"]:
        if self.npc_name is None: return None
        return npcs.Npc(self.npc_name)
    
    @property
    def power(self) -> int:
        return self.base_power
    
    @property
    def remaining_actions(self) -> int:
        actions = self.actions
        for skill_dict in self.submitted_skills:
            skill = skills.skills[skill_dict["skill_name"]]
            actions -= skill.action_cost
        return actions
    
    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        self.strife.griefers[self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = self.strife.griefers[self.__dict__["name"]][attr]
        return self.__dict__[attr]
    
    def get_dict(self) -> dict:
        out = deepcopy(self.strife.griefers[self.__dict__["name"]])
        out["stats_dict"] = self.stats_dict
        out["vials_dict"] = self.vials_dict
        out["states_dict"] = self.states_dict
        out["known_skills"] = {skill_name:skills.skills[skill_name].get_dict(self) for skill_name in self.known_skills}
        return out

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
            self.strife_log = ["STRIFE BEGIN!"]

    def add_griefer(self, identifier: Union["sessions.Player", "npcs.Npc"]):
        if isinstance(identifier, sessions.Player):
            Griefer.from_player(self, identifier)
        elif isinstance(identifier, npcs.Npc):
            Griefer.from_npc(self, identifier)

    def remove_griefer(self, griefer: Griefer):
        self.griefers.pop(griefer.name)

    def ready_check(self):
        if not self.ready: return
        self.resolve_skills()
        self.clear_submitted_skills()
        self.increase_turn()

    def resolve_skills(self):
        # sorted by savvy in descending order
        for griefer_name in sorted(self.griefers.keys(), key=lambda x: self.get_griefer(x).get_stat("savvy"), reverse=True):
            # mf died
            if griefer_name not in self.griefers:
                continue
            self.get_griefer(griefer_name).use_skills()

    def increase_turn(self):
        self.turn_num += 1
        self.log(f"TURN {self.turn_num}!")
        for griefer in self.griefer_list:
            griefer.new_turn()
        self.verify_strife()
    
    def verify_strife(self):
        teams = []
        for griefer in self.griefer_list:
            if griefer.team not in teams: teams.append(griefer.team)
        if len(teams) <= 1:
            self.end()

    def clear_submitted_skills(self):
        for griefer in self.griefer_list:
            griefer.submitted_skills = []

    def end(self):
        print(self.strife_log)
        self.room.strife_dict = {}

    def log(self, text: str):
        self.strife_log.append(text)

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
    def ready(self) -> bool:
        for griefer in self.griefer_list:
            if griefer.player is None: continue # debug, enemies cant submit actions yet
            if not griefer.ready: return False
        return True

    @property
    def griefer_list(self) -> list[Griefer]:
        return [self.get_griefer(griefer_name) for griefer_name in self.griefers]
    
    @property
    def player_griefers(self) -> list[Griefer]:
        out = []
        for griefer in self.griefer_list:
            if griefer.player is not None: out.append(griefer)
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