from copy import deepcopy
from typing import Optional, Union
import random
import math

import util
import sessions
import npcs
import skills
import config
import stateseffects
import alchemy

vials: dict[str, "Vial"] = {}
secondary_vials: dict[str, str] = {}


def stats_from_ratios(stat_ratios: dict[str, int], power: int):
    total_ratios = 0
    for stat_name in stat_ratios:
        total_ratios += stat_ratios[stat_name]
    stats = {}
    for stat_name in stat_ratios:
        if total_ratios != 0:
            stat_mult = stat_ratios[stat_name] / total_ratios
        else:
            stat_mult = 1 / len(stat_ratios)
        stats[stat_name] = int(power * stat_mult)
    remainder = power - sum(stats.values())
    for stat_name in stats:
        if remainder == 0:
            break
        if stat_ratios[stat_name] == 0:
            continue
        stats[stat_name] += 1
        remainder -= 1
    return stats


class Vial:
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
        if self.name in griefer.vials:
            current = griefer.vials[self.name]["current"]
            griefer.vials[self.name]["current"] += amount
            maximum = griefer.get_vial_maximum(self.name)
            if griefer.vials[self.name]["current"] > maximum:
                griefer.vials[self.name]["current"] = maximum
            if griefer.vials[self.name]["current"] < 0:
                griefer.vials[self.name]["current"] = 0
            return griefer.vials[self.name]["current"] - current
        else:
            return 0

    def get_current(self, griefer: "Griefer") -> int:
        return griefer.get_vial(self.name)

    def get_maximum(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.maximum_formula)
        return int(eval(formula))

    def get_starting(self, griefer: "Griefer") -> int:
        formula = griefer.format_formula(self.starting_formula)
        if "{maximum}" in formula:
            formula = formula.replace("{maximum}", str(self.get_maximum(griefer)))
        starting_value = int(eval(formula))
        return starting_value

    def difference_from_starting(self, griefer: "Griefer") -> int:
        return self.get_current(griefer) - self.get_starting(griefer)

    def initialize_vial(self, griefer: "Griefer"):
        pass

    def modify_damage_received(self, damage: int, griefer: "Griefer") -> int:
        return damage

    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        return damage

    def modify_stat(self, stat_name: str, value: int, griefer: "Griefer") -> int:
        return value

    def extra_actions(self, griefer: "Griefer") -> int:
        return 0

    def parry_roll_modifier(self, griefer: "Griefer") -> float:
        return 1.0

    def new_turn(self, griefer: "Griefer"):
        pass

    def on_parry(self, griefer: "Griefer", damage_parried: int):
        pass

    def on_hit(self, griefer: "Griefer", damage_dealt: int):
        pass

    def use_skill(self, griefer: "Griefer", skill: "skills.Skill"):
        pass


class SecondaryVial(Vial):
    def __init__(self, name: str, description: str):
        super().__init__(name)
        secondary_vials[name] = description
        self.optional_vial = True


class HpVial(Vial):
    def new_turn(self, griefer: "Griefer"):
        regen_mult = 0.025 + 0.15 * (
            griefer.get_stat("tact") / griefer.get_stat("power")
        )
        regen = griefer.get_vial_maximum("hp") * regen_mult
        regen = int(regen)
        griefer.change_vial("hp", regen)


hp = Vial("hp")
hp.maximum_formula = "{power}*3 + {vig}*18"
hp.starting_formula = "{maximum}"
hp.gel_vial = True

vim = Vial("vim")
vim.maximum_formula = "{power} + {tac}*6"
vim.starting_formula = "{maximum}"
vim.tact_vial = True


class AspectVial(Vial):
    def add_value(self, griefer: "Griefer", amount: int) -> int:
        difference = super().add_value(griefer, amount)
        # imagination increases when aspect vial decreases
        if difference < 0 and griefer.has_vial("imagination"):
            griefer.change_vial("imagination", -difference // 2)
        return difference


aspect = AspectVial("aspect")
aspect.maximum_formula = "{power}*2"
aspect.starting_formula = "{maximum}"
aspect.optional_vial = True
aspect.tact_vial = True


class HopeVial(Vial):
    def new_turn(self, griefer: "Griefer"):
        diff_from_starting = self.difference_from_starting(griefer)
        flat_add = self.difference_from_starting(griefer) // 36
        old_vials = {
            vial_name: griefer.get_vial_maximum(vial_name)
            for vial_name in griefer.vials
        }
        for stat_name in griefer.base_stats:
            griefer.add_bonus(stat_name, flat_add)
        if flat_add > 0:
            griefer.strife.log(
                f"{griefer.nickname} gained +{flat_add} to all stats from {griefer.their} HOPE!"
            )
        elif flat_add < 0:
            griefer.strife.log(
                f"{griefer.nickname} lost {-flat_add} in all stats from {griefer.their} HOPE!"
            )
        new_vials = {
            vial_name: griefer.get_vial_maximum(vial_name)
            for vial_name in griefer.vials
        }
        for vial_name in old_vials:
            if old_vials[vial_name] != new_vials[vial_name]:
                griefer.change_vial(
                    vial_name, new_vials[vial_name] - old_vials[vial_name]
                )
        # decay back to starting value
        if diff_from_starting != 0:
            change = diff_from_starting * -0.05
            change = int(change)
            if change < 0:
                change = min(change, -1)
            else:
                change = max(change, 1)
            griefer.change_vial(self.name, change)


hope = HopeVial("hope")
hope.maximum_formula = "{power}*3"
hope.starting_formula = "{maximum}//2"
hope.hidden_vial = True


class RageVial(Vial):
    def modify_damage_received(self, damage: int, griefer: "Griefer") -> int:
        if damage <= 0:
            return damage
        flat_add = self.difference_from_starting(griefer)
        return max(damage + flat_add, 0)

    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        if damage <= 0:
            return damage
        flat_add = self.difference_from_starting(griefer)
        return max(damage + flat_add, 0)

    def new_turn(self, griefer: "Griefer"):
        # decay back to starting value
        diff_from_starting = self.difference_from_starting(griefer)
        if diff_from_starting != 0:
            change = diff_from_starting * -0.05
            change = int(change)
            if change < 0:
                change = min(change, -1)
            else:
                change = max(change, 1)
            griefer.change_vial(self.name, change)


rage = RageVial("rage")
rage.maximum_formula = "{power}*3"
rage.starting_formula = "{maximum}//2"
rage.hidden_vial = True


class MangritVial(SecondaryVial):
    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        value = self.get_current(griefer)
        power = griefer.power
        mod = value / (value + power)
        mod += 1
        return int(damage * mod)


mangrit = MangritVial(
    "mangrit", "Starts empty, but increases steadily.\nIncreases damage."
)
mangrit.maximum_formula = "{power} + {tac}*6"
mangrit.starting_formula = "0"
mangrit.tact_vial = True


class ImaginationVial(SecondaryVial):
    def new_turn(self, griefer: "Griefer"):
        griefer.change_vial("aspect", self.get_current(griefer) // 2)

    # increasing as ASPECT is drained is hard coded


imagination = ImaginationVial(
    "imagination",
    "Starts empty, increases as ASPECT vial is drained.\nIncreases ASPECT vial regeneration.",
)
imagination.maximum_formula = "{power} + {tac}*6"
imagination.starting_formula = "0"


class HorseshitometerVial(SecondaryVial):
    def parry_roll_modifier(self, griefer: "Griefer") -> float:
        diff = self.difference_from_starting(griefer)
        power = griefer.power
        mod = (power**2) / (power + diff)
        return mod

    def on_hit(self, griefer: "Griefer", damage_dealt: int):
        self.add_value(griefer, -damage_dealt // 4)


horseshitometer = HorseshitometerVial(
    "horseshitometer",
    "Increases overtime, dealing damage decreases.\nIncreases or decreases chance to AUTO-PARRY.",
)
horseshitometer.maximum_formula = "{power} + {tac}*6"
horseshitometer.starting_formula = "{maximum}//2"
horseshitometer.tact_vial = True


class GambitVial(SecondaryVial):
    def initialize_vial(self, griefer: "Griefer"):
        if "gambit_skill_name" not in griefer.misc_data:
            griefer.misc_data["gambit_skill_name"] = None
        if "picked_gambit_skills" not in griefer.misc_data:
            griefer.misc_data["picked_gambit_skills"] = []
        if "gambit_combob" not in griefer.misc_data:
            griefer.misc_data["gambit_combob"] = 0
        return super().initialize_vial(griefer)

    def choose_random_skill(self, griefer: "Griefer") -> str:
        pickable_skills = [skill_name for skill_name in griefer.known_skills]
        return random.choice(pickable_skills)

    def new_turn(self, griefer: "Griefer"):
        if griefer.misc_data["gambit_skill_name"] is not None:
            value = griefer.power // 12 + griefer.get_stat("tact") // 2
            if self.used_gambit_skill(griefer):
                self.add_value(griefer, value)
                value = self.difference_from_starting(griefer)
                griefer.change_vial("hp", value)
                griefer.strife.log(
                    f"{griefer.nickname} recovered {value} hp from {griefer.their} GAMBIT!"
                )
            else:
                self.add_value(griefer, -value)
                combob = griefer.misc_data["gambit_combob"]
                if combob > 1:
                    griefer.strife.log(f"GAMBIT COMBOB BROKEN D: {combob*'!'}")
                griefer.misc_data["gambit_combob"] = 0
        gambit_skill_name = self.choose_random_skill(griefer)
        griefer.misc_data["gambit_skill_name"] = gambit_skill_name
        griefer.strife.log(
            f"{griefer.nickname}'s GAMBIT skill is {gambit_skill_name.upper()}!"
        )
        if "used_gambit_skill" in griefer.tags:
            griefer.tags.remove("used_gambit_skill")

    def use_skill(self, griefer: "Griefer", skill: "skills.Skill"):
        super().use_skill(griefer, skill)
        if self.used_gambit_skill(griefer):
            return
        if skill.name == griefer.misc_data["gambit_skill_name"]:
            griefer.tags.append("used_gambit_skill")
            griefer.misc_data["gambit_combob"] += 1
            combob = griefer.misc_data["gambit_combob"]
            if combob == 1:
                griefer.strife.log("The crowd goes wild!")
            else:
                griefer.strife.log(f"{combob}x GAMBIT COMBOB{combob*'!'}")

    def used_gambit_skill(self, griefer: "Griefer"):
        if "used_gambit_skill" in griefer.tags:
            return True
        else:
            return False


gambit = GambitVial(
    "gambit",
    "Get a prompt for a GAMBIT skill each turn.\nHeals you each turn you comply.",
)
gambit.maximum_formula = "{power} + {tac}*6"
gambit.starting_formula = "{maximum}//2"


class FistometerVial(SecondaryVial):
    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        if damage <= 0:
            return damage
        current_amount = self.get_current(griefer)
        damage += current_amount
        griefer.change_vial(self.name, -current_amount)
        return damage

    def new_turn(self, griefer: "Griefer"):
        current_amount = self.get_current(griefer)
        griefer.change_vial(self.name, current_amount // 10)


fistometer = FistometerVial(
    "fistometer",
    "Starts at 0, increases over time exponentially.\nDealing damage consumes the vial as additional damage.",
)
fistometer.maximum_formula = "{power}*6 + {tac}*36"
fistometer.starting_formula = "0"
fistometer.tact_vial = True


class FakenessVial(SecondaryVial):
    def new_turn(self, griefer: "Griefer"):
        vial_change = -(griefer.power // 6 + griefer.get_stat("tact"))
        griefer.change_vial(self.name, vial_change)

    def extra_actions(self, griefer: "Griefer") -> int:
        if self.get_current(griefer) > 0:
            return 0
        else:
            return 1


fakeness = FakenessVial(
    "fakeness",
    "Starts full and gradually reduces.\nGives you an extra action when it's empty.",
)
fakeness.maximum_formula = "{power}*1.5"
fakeness.starting_formula = "{maximum}"


class RealnessVial(SecondaryVial):
    def modify_damage_received(self, damage: int, griefer: "Griefer") -> int:
        current_percent = self.get_current(griefer) / self.get_maximum(griefer)
        reduction = 0.75 * current_percent
        mod = 1 - reduction
        return int(damage * mod)

    def new_turn(self, griefer: "Griefer"):
        vial_change = -griefer.power // 2
        griefer.change_vial(self.name, vial_change)


realness = RealnessVial(
    "realness",
    "Starts full, and gradually reduces.\nGives you damage reduction the more you have.",
)
realness.maximum_formula = "{power} + {tac}*6"
realness.starting_formula = "{maximum}"


class HysteriaVial(SecondaryVial):
    def modify_damage_dealt(self, damage: int, griefer: "Griefer") -> int:
        if self.get_current(griefer) != self.get_maximum(griefer):
            return damage
        else:
            return damage * 2

    def new_turn(self, griefer: "Griefer"):
        if self.get_current(griefer) == self.get_maximum(griefer):
            griefer.change_vial(self.name, -self.get_maximum(griefer))
        vial_change = griefer.get_stat("tact") + griefer.power // 6
        vial_change = max(vial_change, 0)
        griefer.change_vial(self.name, vial_change)


hysteria = HysteriaVial(
    "hysteria",
    "Starts empty, gradually increases. Does nothing until full.\nDoubles damage when full before depleting completely next turn.",
)
hysteria.maximum_formula = "{power}"
hysteria.starting_formula = "0"


class Griefer:
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
            self.color: Optional[list] = None
            self.actions = 1
            self.ready: bool = False
            self.base_power: int = 0
            self.pronouns: list[str] = ["it", "it", "its", "its"]
            self.base_stats: dict[str, int] = {
                "spunk": 0,
                "vigor": 0,
                "tact": 0,
                "luck": 0,
                "savvy": 0,
                "mettle": 0,
            }
            self.stat_bonuses: dict[str, int] = {}
            self.skill_cooldowns: dict[str, int] = {}
            self.known_skills: list[str] = skills.base_skills.copy()
            # submitted_skills: [{"skill_name": "aggrieve", "targets": ["jet impq", "shale ogrea"]}]
            self.submitted_skills: list[dict] = []
            self.player_name: Optional[str] = None
            self.npc_name: Optional[str] = None
            self.ai_type: str = "random"
            self.vials: dict[str, dict] = {}
            self.states: dict[str, dict] = {}
            self.tags = []
            self.misc_data = {}
            self.wielded_item_name: Optional[str] = None
            self.worn_item_name: Optional[str] = None
            self.onhit_states: dict[str, float] = {}
            self.wear_states: dict[str, float] = {}
            self.immune_states = []
            # vials still need to be initialized
            for vial_name in vials:
                vial = vials[vial_name]
                if not vial.optional_vial:
                    self.add_vial(vial_name)

    def new_turn(self):
        self.ready = False
        if self.death_break():
            return
        for vial in self.vials_list:
            if vial.tact_vial:
                vial_change = self.get_stat("tact") + self.power // 6
                vial_change = max(vial_change, 0)
                self.change_vial(vial.name, vial_change)
            vial.new_turn(self)
        for state in self.states_list.copy():
            state.new_turn(self)
            if state.passive:
                continue
            self.add_state_duration(state.name, -1)
            if self.get_state_duration(state.name) <= 0:
                self.remove_state(state.name)
        for state_name in self.wear_states:
            self.apply_state(state_name, self, self.wear_states[state_name], 1)
        for skill_name in self.skill_cooldowns.copy():
            self.skill_cooldowns[skill_name] -= 1
            if self.skill_cooldowns[skill_name] <= 0:
                self.skill_cooldowns.pop(skill_name)
        if self.player is None:
            self.ai_use_skills()
        self.death_break()

    def take_damage(
        self,
        damage: int,
        coin: Optional[bool] = None,
        source: Optional[str] = None,
        log=True,
    ) -> int:
        if damage > 0:
            damage = skills.modify_damage(damage, self)
            for vial in self.vials_list:
                damage = vial.modify_damage_received(damage, self)
            for state in self.states_list:
                damage = state.modify_damage_received(damage, self)
        # if self.player is not None:
        #     threshold = self.get_vial_maximum("hp") / 3
        #     if damage > threshold:
        #         modified_damage = damage - threshold
        #         modified_damage *= config.player_hp_threshold_damage_mult
        #         damage = int(threshold + modified_damage)
        self.change_vial("hp", -damage)
        if log:
            if coin is None:
                self.strife.log(
                    f"{self.nickname} takes {damage} damage!{ f' ({source})' if source is not None else ''}"
                )
            else:
                self.strife.log(
                    f"{self.nickname} takes {damage} damage! ({'heads' if coin else 'scratch'}){ f' ({source})' if source is not None else ''}"
                )
        return damage

    def death_break(self) -> bool:
        if self.dead:
            return True
        if self.get_vial("hp") <= 0:
            self.die()
            return True
        else:
            return False

    def die(self):
        # todo: explode into grist
        if self.npc is not None and self.npc.invulnerable:
            self.strife.log(f"{self.nickname} absconds!")
        elif self.npc is not None:
            self.strife.log(f"The {self.nickname} explodes into grist!")
            self.room.remove_npc(self.npc)
            spoils_dict = self.npc.make_spoils(len(self.strife.player_griefers))
            for player_griefer in self.strife.player_griefers:
                if player_griefer.player is None:
                    raise AttributeError
                player_griefer.player.add_unclaimed_grist(spoils_dict)
                player_griefer.player.add_rungs(self.power)
                player_griefer.player.add_gutter_and_leech()
        elif self.player is not None:
            self.strife.log(f"{self.nickname}: DEAD.")
            self.strife.banned_players.append(self.player.name)
        self.strife.remove_griefer(self)
        self.strife.verify_strife()

    def get_skill_cooldown(self, skill_name) -> int:
        if skill_name not in self.skill_cooldowns:
            return 0
        else:
            return self.skill_cooldowns[skill_name]

    def add_cooldown(self, skill_name: str, cooldown: int):
        if cooldown == 0:
            return
        if skill_name not in self.skill_cooldowns:
            self.skill_cooldowns[skill_name] = 0
        self.skill_cooldowns[skill_name] += cooldown

    def submit_skill(self, skill_name, targets: list[str]) -> bool:
        skill = skills.skills[skill_name]
        if not skill.is_usable_by(self):
            return False
        if len(targets) > skill.num_targets:
            return False
        for target_name in targets:
            if target_name not in self.strife.griefers:
                return False
        if self.remaining_actions < skill.action_cost:
            return False
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
            if self.dead:
                return
            skill.use(self, targets_list)
            if self.dead:
                return

    def get_random_submittable_skill(self) -> Optional[str]:
        def is_usable_skill(skill: "skills.Skill"):
            if skill.name in skills.illegal_ai_skills:
                return False
            valid_targets = [
                self.strife.get_griefer(griefer_name)
                for griefer_name in skill.get_valid_targets(self)
            ]
            if skill.beneficial:
                valid_targets = [
                    griefer for griefer in valid_targets if griefer.team == self.team
                ]
            else:
                valid_targets = [
                    griefer for griefer in valid_targets if griefer.team == self.team
                ]
            if len(valid_targets) > 0:
                return True

        usable_skills = [
            skill.name
            for skill in self.known_skills_list
            if skill.is_submittable_by(self) and is_usable_skill(skill)
        ]
        if usable_skills:
            return random.choice(usable_skills)
        else:
            return None

    def submit_random_skill(self):
        if self.dead:
            return
        random_skill_name = self.get_random_submittable_skill()
        if random_skill_name is None:
            return None
        skill = skills.skills[random_skill_name]
        valid_targets = [
            self.strife.get_griefer(griefer_name)
            for griefer_name in skill.get_valid_targets(self)
        ]
        if skill.beneficial:
            valid_targets = [
                griefer.name for griefer in valid_targets if griefer.team == self.team
            ]
        else:
            valid_targets = [
                griefer.name for griefer in valid_targets if griefer.team != self.team
            ]
        targets = []
        for i in range(skill.num_targets):
            targets.append(random.choice(valid_targets))
        self.submit_skill(random_skill_name, targets)

    def ai_use_skills(self):
        while self.remaining_actions:
            assert self.ai_type in npcs.griefer_ai
            ai = npcs.griefer_ai[self.ai_type]
            chosen_skill_name = ai.ai_choose_skill(self)
            if chosen_skill_name is None:
                return
            skill = skills.skills[chosen_skill_name]
            valid_targets = [
                self.strife.get_griefer(griefer_name)
                for griefer_name in skill.get_valid_targets(self)
            ]
            if skill.beneficial:
                valid_targets = [
                    griefer.name
                    for griefer in valid_targets
                    if griefer.team == self.team
                ]
            else:
                valid_targets = [
                    griefer.name
                    for griefer in valid_targets
                    if griefer.team != self.team
                ]
            if len(valid_targets) == 0:
                return
            targets = []
            for i in range(skill.num_targets):
                targets.append(random.choice(valid_targets))
            self.submit_skill(chosen_skill_name, targets)

    @classmethod
    def from_player(
        cls, strife: "Strife", player: "sessions.SubPlayer"
    ) -> Optional["Griefer"]:
        if player.name in strife.banned_players:
            return None
        griefer = cls(player.name, strife)
        griefer.player_name = player.name
        griefer.type = "player"
        # todo: add player symbol dict here
        griefer.symbol_dict = player.symbol_dict.copy()
        griefer.nickname = player.nickname
        griefer.base_power = player.power
        griefer.team = "blue"
        base_stats = {
            stat_name: player.get_base_stat(stat_name)
            for stat_name in player.stat_ratios
        }
        griefer.base_stats = base_stats.copy()
        griefer.stat_bonuses = player.permanent_stat_bonuses.copy()
        if player.echeladder_rung >= 100:
            griefer.actions = 2
        griefer.known_skills = player.get_known_skills()
        griefer.pronouns = player.pronouns.copy()
        if player.wielded_instance is not None:
            griefer.wielded_item_name = player.wielded_instance.item.name
            griefer.onhit_states = player.wielded_instance.item.onhit_states.copy()
        if player.worn_instance is not None:
            griefer.worn_item_name = player.worn_instance_name
            griefer.wear_states = player.worn_instance.item.wear_states.copy()
        griefer.add_vial("aspect")
        griefer.add_vial(player.secondaryvial)
        griefer.initialize_vials()
        for passive_name in player.get_current_passives():
            griefer.apply_state(passive_name, griefer, 1.0, 99)
        return griefer

    @classmethod
    def from_npc(cls, strife: "Strife", npc: "npcs.Npc") -> "Griefer":
        griefer = cls(npc.name, strife)
        griefer.type = npc.type
        griefer.grist_type = npc.grist_type
        griefer.grist_category = npc.grist_category
        griefer.color = npc.color
        griefer.nickname = npc.nickname.upper()
        griefer.base_power = npc.power
        griefer.base_stats = stats_from_ratios(npc.stat_ratios, npc.power)
        for stat in griefer.base_stats:
            if stat in npc.permanent_stat_bonuses:
                griefer.base_stats[stat] += npc.permanent_stat_bonuses[stat]
        griefer.known_skills += npc.additional_skills
        griefer.actions = npc.actions
        griefer.npc_name = npc.name
        griefer.ai_type = npc.ai_type
        griefer.onhit_states.update(npc.onhit_states)
        griefer.wear_states.update(npc.wear_states)
        griefer.immune_states = npc.immune_states.copy()
        if npc.hostile:
            griefer.team = "red"
        else:
            griefer.team = "blue"
        griefer.initialize_vials()
        return griefer

    def apply_state(
        self, state_name: str, applier: "Griefer", potency: float, duration: int
    ):
        if state_name in self.immune_states:
            if f"immune{state_name}" not in self.tags:
                self.strife.log(f"{self.nickname} is immune to {state_name.upper()}!")
                self.tags.append(f"immune{state_name}")
            return
        if state_name not in self.states:
            self.states[state_name] = {
                "applier_stats": applier.stats_dict,
                "potency": potency,
                "duration": 0,
            }
        if potency > self.get_state_potency(state_name):
            self.states[state_name]["potency"] = potency
            self.states[state_name]["applier_stats"] = applier.stats_dict
        self.states[state_name]["duration"] += duration
        state = stateseffects.states[state_name]
        state.on_apply(self)
        coin = skills.flip_coin(applier, self)
        if coin or state.beneficial:
            self.add_state_potency(state_name, potency / 10)

    def remove_state(self, state_name):
        if state_name in self.states:
            self.states.pop(state_name)

    def get_state_potency(self, state_name: str) -> float:
        return self.states[state_name]["potency"]

    def get_state_duration(self, state_name: str) -> int:
        return self.states[state_name]["duration"]

    def get_applier_stats(self, state_name: str) -> dict:
        return self.states[state_name]["applier_stats"]

    def add_state_duration(self, state_name: str, duration: int):
        if state_name in self.states:
            self.states[state_name]["duration"] += duration

    def add_state_potency(self, state_name: str, potency_change: float):
        if state_name in self.states:
            self.states[state_name]["potency"] += potency_change

    def change_vial(self, vial_name: str, amount: int) -> int:
        vial = vials[vial_name]
        return vial.add_value(self, amount)

    def add_vial(self, vial_name: str):
        self.vials[vial_name] = {}
        vials[vial_name].initialize_vial(self)

    def get_vial(self, vial_name: str) -> int:
        if vial_name not in self.vials:
            return 0
        return self.vials[vial_name]["current"]

    def get_vial_maximum(self, vial_name: str):
        vial = vials[vial_name]
        maximum = vial.get_maximum(self)
        if vial_name in self.stat_bonuses:
            maximum += self.stat_bonuses[vial_name]
        return maximum

    def has_vial(self, vial_name: str) -> bool:
        if vial_name in self.vials:
            return True
        else:
            return False

    def can_pay_vial_costs(self, costs: dict) -> bool:
        for vial_name in costs:
            if self.get_vial(vial_name) < costs[vial_name]:
                return False
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
            if vial_name in self.stat_bonuses:
                # to account for the maximum bonus plus some initial starting for 1/2 vials
                self.vials[vial_name]["current"] += self.stat_bonuses[vial_name] * 2
                self.vials[vial_name]["current"] = min(
                    self.vials[vial_name]["current"], self.get_vial_maximum(vial_name)
                )

    def add_bonus(self, game_attr: str, amount: int):
        if game_attr in self.base_stats:
            if game_attr not in self.stat_bonuses:
                self.stat_bonuses[game_attr] = 0
            self.stat_bonuses[game_attr] += amount
        elif game_attr in vials:
            if game_attr not in self.stat_bonuses:
                self.stat_bonuses[game_attr] = 0
            self.stat_bonuses[game_attr] += amount
            self.change_vial(game_attr, amount)
        else:
            print(f"bonus does not exist {game_attr}")

    def add_permanent_bonus(self, game_attr: str, amount: int):
        if self.player is not None:
            self.player.add_permanent_bonus(game_attr, amount)
        self.add_bonus(game_attr, amount)

    @property
    def speed(self) -> int:
        speed = self.get_stat("savvy")
        for state in self.states_list:
            speed = state.modify_speed(speed, self)
        speed = int(speed)
        return speed

    @property
    def dead(self) -> bool:
        return not self.name in self.strife.griefers

    @property
    def wielded_item(self) -> Optional["alchemy.Item"]:
        if self.wielded_item_name is None:
            return None
        else:
            return alchemy.Item(self.wielded_item_name)

    @property
    def worn_item(self) -> Optional["alchemy.Item"]:
        if self.worn_item_name is None:
            return None
        else:
            return alchemy.Item(self.worn_item_name)

    @property
    def team_members(self) -> list["Griefer"]:
        return [
            griefer for griefer in self.strife.griefer_list if griefer.team == self.team
        ]

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
                "gel": vials[vial].gel_vial,
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
                "tooltip": stateseffects.states[state_name].tooltip,
                "passive": stateseffects.states[state_name].passive,
            }
        return out

    @property
    def states_list(self) -> list["stateseffects.State"]:
        return [stateseffects.states[state_name] for state_name in self.states]

    @property
    def known_skills_list(self) -> list["skills.Skill"]:
        return [skills.skills[skill_name] for skill_name in self.known_skills]

    @property
    def submitted_skills_list(self) -> list["skills.Skill"]:
        return [
            skills.skills[skill_dict["skill_name"]]
            for skill_dict in self.submitted_skills
        ]

    def get_stat(self, stat_name) -> int:
        if stat_name == "power":
            return self.power
        stat = self.base_stats[stat_name]
        if stat_name in self.stat_bonuses:
            stat += self.stat_bonuses[stat_name]
        for vial in self.vials_list:
            stat = vial.modify_stat(stat_name, stat, self)
        return stat

    def format_formula(self, formula: str, identifier: Optional[str] = None) -> str:
        terms: dict[str, Union[int, float]] = {
            "base_damage": self.power // 2 + max(self.get_stat("spunk") * 3, 0),
            "power": self.power,
            "spk": self.get_stat("spunk"),
            "vig": self.get_stat("vigor"),
            "tac": self.get_stat("tact"),
            "luk": self.get_stat("luck"),
            "sav": self.get_stat("savvy"),
            "met": self.get_stat("mettle"),
        }
        for aspect_name in skills.aspects:
            if f"{aspect_name}.ratio" in formula:
                terms[f"{aspect_name}.ratio"] = self.get_aspect_ratio(aspect_name)
            if f"{aspect_name}.inverse_ratio" in formula:
                terms[f"{aspect_name}.inverse_ratio"] = self.get_inverse_aspect_ratio(
                    aspect_name
                )
        for term in terms:
            if identifier is None:
                if f"{{{term}}}" in formula:
                    formula = formula.replace(f"{{{term}}}", str(terms[term]))
            else:
                if f"{identifier}.{term}" in formula:
                    formula = formula.replace(f"{identifier}.{term}", str(terms[term]))
        return formula

    def get_aspect_ratio(self, aspect_name: str) -> float:
        return skills.aspects[aspect_name].ratio(self)

    def get_inverse_aspect_ratio(self, aspect_name: str) -> float:
        return skills.aspects[aspect_name].inverse_ratio(self)

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
    def player(self) -> Optional["sessions.SubPlayer"]:
        try:
            if self.player_name is None:
                return None
        except KeyError:
            return None
        return sessions.SubPlayer.from_name(self.player_name)

    @property
    def npc(self) -> Optional["npcs.Npc"]:
        if self.npc_name is None:
            return None
        return npcs.Npc(self.npc_name)

    @property
    def power(self) -> int:
        return self.base_power

    @property
    def total_actions(self) -> int:
        actions = self.actions
        for state in self.states_list:
            actions += state.extra_actions(self)
        for vial in self.vials_list:
            actions += vial.extra_actions(self)
        return actions

    @property
    def remaining_actions(self) -> int:
        actions = self.total_actions
        for skill_dict in self.submitted_skills:
            skill = skills.skills[skill_dict["skill_name"]]
            actions -= skill.action_cost
        return actions

    @property
    def they(self) -> str:
        return self.pronouns[0]

    @property
    def them(self) -> str:
        return self.pronouns[1]

    @property
    def their(self) -> str:
        return self.pronouns[2]

    @property
    def theirs(self) -> str:
        return self.pronouns[3]

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
        out["known_skills"] = {
            skill_name: skills.skills[skill_name].get_dict(self)
            for skill_name in self.known_skills
        }
        out["actions"] = self.total_actions
        return out


# each room can only have one Strife in it
class Strife:
    def __init__(self, room: "sessions.Room"):
        self.__dict__["session_name"] = room.session.name
        self.__dict__["overmap_name"] = room.overmap.name
        self.__dict__["map_name"] = room.map.name
        self.__dict__["room_name"] = room.name
        try:
            self.griefers
            self.turn_num
            self.strife_log
            self.banned_players
        except KeyError:
            self.griefers = {}
            self.turn_num: int = 0
            self.strife_log = ["STRIFE BEGIN!"]
            self.banned_players = []

    def add_griefer(self, identifier: Union["sessions.SubPlayer", "npcs.Npc"]):
        if isinstance(identifier, sessions.SubPlayer):
            Griefer.from_player(self, identifier)
        elif isinstance(identifier, npcs.Npc):
            Griefer.from_npc(self, identifier)

    def remove_griefer(self, griefer: Griefer):
        self.griefers.pop(griefer.name)

    def ready_check(self):
        if not self.ready:
            return
        self.resolve_skills()
        self.clear_submitted_skills()
        self.increase_turn()

    def resolve_skills(self):
        # sorted by savvy in descending order
        for griefer_name in sorted(
            self.griefers.keys(), key=lambda x: self.get_griefer(x).speed, reverse=True
        ):
            # mf died
            if griefer_name not in self.griefers:
                continue
            self.get_griefer(griefer_name).use_skills()

    def increase_turn(self):
        self.turn_num += 1
        for griefer in self.griefer_list:
            griefer.new_turn()
        message = f"TURN {self.turn_num}!"
        self.log("{:-^30}".format(message))
        self.verify_strife()

    def verify_strife(self):
        teams = []
        players = []
        for griefer in self.griefer_list:
            if griefer.team not in teams:
                teams.append(griefer.team)
            if griefer.player is not None:
                players.append(griefer)
        if len(teams) <= 1 or len(players) == 0:
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
        (
            self.session.overmaps[self.__dict__["overmap_name"]]["maps"][
                self.__dict__["map_name"]
            ]["rooms"][self.__dict__["room_name"]]["strife_dict"][attr]
        ) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = self.session.overmaps[self.__dict__["overmap_name"]][
            "maps"
        ][self.__dict__["map_name"]]["rooms"][self.__dict__["room_name"]][
            "strife_dict"
        ][
            attr
        ]
        return self.__dict__[attr]

    def get_dict(self) -> dict:
        out = deepcopy(
            self.session.overmaps[self.__dict__["overmap_name"]]["maps"][
                self.__dict__["map_name"]
            ]["rooms"][self.__dict__["room_name"]]["strife_dict"]
        )
        for griefer_name in self.griefers:
            out["griefers"][griefer_name] = self.get_griefer(griefer_name).get_dict()
        return out

    def get_griefer(self, name: str) -> "Griefer":
        return Griefer(name, self)

    @property
    def ready(self) -> bool:
        for griefer in self.griefer_list:
            if griefer.player is None:
                continue  # debug, enemies cant submit actions yet
            if not griefer.ready:
                return False
        return True

    @property
    def griefer_list(self) -> list[Griefer]:
        return [self.get_griefer(griefer_name) for griefer_name in self.griefers]

    @property
    def player_griefers(self) -> list[Griefer]:
        out = []
        for griefer in self.griefer_list:
            if griefer.player is not None:
                out.append(griefer)
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
        return sessions.Room(
            self.__dict__["room_name"], self.session, self.overmap, self.map
        )
