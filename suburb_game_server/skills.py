from typing import Optional, Union, Callable
from copy import deepcopy

import strife
import random
import config
import sessions
import util

aspects: dict["str", "Aspect"] = {}
skills: dict["str", "Skill"] = {}
base_skills: list[str] = [] # everyone has these
player_skills: list[str] = [] # only players get these
aspect_skills: dict[str, dict[str, int]] = {}
# aspect_skills looks like this
# aspect_skills = {
#     "time": {
#         "tick": 10,
#         "tock": 50,
#     },
#     "space": {
#         "expand": 10,
#         "big bang": 250,
#     }
# }
class_skills: dict[str, dict[str, dict[str, int]]] = {}
# class_skills looks like this
# class_skills = {
#     "knight": {
#         "time": {
#             "timeblade": 20, # where the int is the echeladder rung needed to access the skill
#             "timebreak": 100,
#         },
#         "space": {
#             "spaceblade": 20,
#             "spacebreak": 100,
#         }
#     },
#     "seer": {
#         "time": {
#             "timesight": 15,
#             "timemap": 50,
#         },
#         "space": {
#             "spacesight": 15,
#             "spacemap": 50,
#         },
#     },
# }
abstratus_skills = {}

SECONDARY_VIALS = ["horseshitometer", "gambit", "imagination", "mangrit"]

SKILL_CATEGORIES = ["aggressive", "abstinent", "aspected", "accolades", "arsenal", "none"]

def modify_damage(damage: int, griefer: "strife.Griefer"):
    mettle = griefer.get_stat("mettle")
    if damage == 0 and mettle == 0: return 0
    mod = griefer.power / (griefer.power + 6*mettle)
    new_damage = int(damage * mod)
    return int(new_damage)

def stat_edge(user_stat: int, target_stat: int) -> float:
    if user_stat == 0 and target_stat == 0: return 1.0
    if user_stat < 0: user_stat = 0
    if target_stat < 0: target_stat = 0
    try:
        edge = (user_stat - target_stat) / (user_stat + target_stat)
        edge += 1
        return max(edge, 0.1)
    except ZeroDivisionError: return 1.0

def flip_coin(user: "strife.Griefer", target: "strife.Griefer") -> bool:
    user_luck = user.get_stat("luck")
    target_luck = target.get_stat("luck")
    edge = (stat_edge(user_luck, target_luck) - 1)*2
    if edge >= 0:
        roll = random.uniform(0-edge, 1)
    else:
        roll = random.uniform(0, 1+-edge)
    for state in user.states_list:
        roll *= state.coinflip_modifier(user)
    if roll < 0.5: return True
    else: return False

class Skill():
    def __init__(self, name):
        self.name: str = name
        skills[name] = self
        self.category = "none"
        self.description = ""
        self.target_self = False
        self.target_team = False
        self.beneficial = False
        self.parryable = True
        self.display_message = True
        self.action_cost = 1
        self.num_targets = 1
        self.cooldown = 1
        self.damage_formula = "0"
        self.apply_states = {}
        self.state_potency_changes = {}
        self.need_damage_to_apply_states = False
        self.vial_change_formulas = {}
        self.vial_cost_formulas = {}
        self.aspect_change_formulas = {}
        self.stat_bonus_formulas = {}
        self.user_skill: Optional[str] = None
        self.additional_skill: Optional[str] = None
        self.special_effect: Optional[Callable[[strife.Griefer, strife.Griefer], Optional[str]]] = None

    def add_vial_cost(self, vial_name: str, formula: str):
        self.vial_cost_formulas[vial_name] = formula

    def add_vial_change(self, vial_name: str, formula: str):
        self.vial_change_formulas[vial_name] = formula

    def add_apply_state(self, state_name: str, duration: int, potency_formula: str):
        self.apply_states[state_name] = {
            "duration": duration,
            "potency_formula": potency_formula,
        }

    def add_state_potency_change(self, state_name: str, potency_change_formula: str):
        self.state_potency_changes[state_name] = potency_change_formula

    def add_aspect_change(self, aspect_name: str, formula: str):
        self.aspect_change_formulas[aspect_name] = formula
    
    def add_stat_bonus(self, stat_name: str, formula: str):
        self.stat_bonus_formulas[stat_name] = formula

    def get_costs(self, user: "strife.Griefer") -> dict[str, int]:
        true_costs = {}
        for vial_name, formula in self.vial_cost_formulas.items():
            true_cost = user.format_formula(formula, "user")
            true_costs[vial_name] = int(eval(true_cost))
        return true_costs
    
    def get_valid_targets(self, user: "strife.Griefer") -> list[str]:
        if self.target_self: return [user.name]
        valid_targets = [griefer.name for griefer in user.strife.griefer_list]
        return valid_targets

    def format_formula(self, formula: str, user: "strife.Griefer", target: "strife.Griefer") -> str:
        formula = user.format_formula(formula, "user")
        formula = target.format_formula(formula, "target")
        return formula
    
    def evaluate_theoretical_damage(self, user: "strife.Griefer") -> int:
        formula = self.damage_formula
        formula = user.format_formula(formula, "user")
        formula = user.format_formula(formula, "target")
        formula = formula.replace("coin", "0.5")
        return int(eval(formula))

    # affect each target in list
    def use(self, user: "strife.Griefer", targets_list: list["strife.Griefer"]):
        if self.target_team:
            if len(targets_list) != 0:
                team = targets_list[0].team
            else:
                if self.beneficial:
                    team = user.team
                else:
                    if user.team == "red": team = "blue"
                    else: team = "red"
            targets_list = [griefer for griefer in user.strife.griefer_list if griefer.team == team]
        if not self.is_usable_by(user): return
        costs = self.get_costs(user)
        user.pay_costs(costs)
        user.add_cooldown(self.name, self.cooldown)
        if self.display_message:
            message = f"->{user.nickname}: {self.name.capitalize()}."
            user.strife.log(message)
        for target in targets_list:
            self.affect(user, target)
        if self.additional_skill is not None: 
            skill = skills[self.additional_skill]
            skill.use(user, targets_list)
        if self.user_skill is not None: 
            # user_skill is not used if the target is the user
            for griefer in targets_list:
                if griefer.name == user.name:
                    break
            else:
                skill = skills[self.user_skill]
                if not skill.target_team:
                    skill.affect(user, user)
                else:
                    for griefer in user.strife.griefer_list:
                        if griefer.team == user.team:
                            skill.affect(user, griefer)
        if user.dead: return
        for vial in user.vials_list:
            vial.use_skill(user, self)

    # apply skill effects to individual target
    def affect(self, user: "strife.Griefer", target: "strife.Griefer"):
        if target.name not in self.get_valid_targets(user): return

        # damage step
        damage_formula = self.format_formula(self.damage_formula, user, target)
        # coin is 1 if user wins, 0 if target wins
        if "coin" in damage_formula:
            coin = flip_coin(user, target)
            damage_formula = damage_formula.replace("coin", str(int(coin)))
        else:
            coin = None
        damage = int(eval(damage_formula))
        for vial in user.vials_list:
            damage = vial.modify_damage_dealt(damage, user)
        for state in user.states_list:
            damage = state.modify_damage_dealt(damage, user)
        # only players can parry, enemies simply miss less with more savvy
        if self.parryable and target.player is not None:
            # higher target savvy = lower roll = more likely to parry
            edge = stat_edge(target.get_stat("savvy"), user.get_stat("savvy")) - 1
            for vial in target.vials_list: edge += vial.parry_roll_modifier(target) - 1
            for state in target.states_list: edge += state.parry_roll_modifier(target) - 1
            edge += (stat_edge(target.get_stat("luck")//4, user.get_stat("luck")//4)) - 0.25
            if edge >= 0:
                roll = random.uniform(0-edge, 1)
            else:
                roll = random.uniform(0, 1+-edge)
            if roll < config.base_parry_chance:
                target.strife.log(f"{target.nickname} AUTO-PARRIES!")
                for vial in target.vials_list:
                    vial.on_parry(target, damage)
                for state in target.states_list:
                    state.on_parry(target, damage)
                return
        if damage != 0: target.take_damage(damage, coin=coin)
        if target.death_break(): return
        if damage != 0 or not self.need_damage_to_apply_states:
            for state_name in self.apply_states:
                potency_formula = self.apply_states[state_name]["potency_formula"]
                potency_formula = self.format_formula(potency_formula, user, target)
                potency = float(eval(potency_formula))
                duration = self.apply_states[state_name]["duration"]
                target.apply_state(state_name, user, potency, duration)
            for state_name in self.state_potency_changes:
                potency_change_formula = self.state_potency_changes[state_name]
                potency_change_formula = self.format_formula(potency_change_formula, user, target)
                potency_change = float(eval(potency_change_formula))
                target.add_state_potency(state_name, potency_change)
            for vial in user.vials_list:
                vial.on_hit(user, damage)
            for state in user.states_list:
                state.on_hit
        # apply on-hits from weapon
        if damage > 0:
            for state_name, potency in user.onhit_states.items():
                # duration is 1-2 for on-hits
                coin = flip_coin(user, target)
                if state_name not in target.states:
                    duration = 2
                else:
                    if coin: duration = 2
                    else: duration = 1
                target.apply_state(state_name, user, potency, duration)
                if target.death_break(): return
        # vial change step
        for vial_name in self.vial_change_formulas:
            vial_formula = self.vial_change_formulas[vial_name]
            vial_formula = self.format_formula(vial_formula, user, target)
            if vial_name in target.vials:
                change = target.change_vial(vial_name, int(eval(vial_formula)))
                if change > 0: user.strife.log(f"{target.nickname}'s {vial_name.upper()} increased by {change}!")
                elif change < 0: user.strife.log(f"{target.nickname}'s {vial_name.upper()} decreased by {-change}!")
        
        # stat change step
        for stat_name in self.stat_bonus_formulas:
            stat_formula = self.stat_bonus_formulas[stat_name]
            stat_formula = self.format_formula(stat_formula, user, target)
            target.add_bonus(stat_name, int(eval(stat_formula)))

        #aspect change step
        for aspect_name in self.aspect_change_formulas:
            aspect_formula = self.aspect_change_formulas[aspect_name]
            aspect_formula = self.format_formula(aspect_formula, user, target)
            aspect = aspects[aspect_name]
            log_message = aspect.adjust(target, int(eval(aspect_formula)))
            user.strife.log(log_message)

        # special effect step
        if self.special_effect is not None:
            effect_log = self.special_effect(user, target)
            if effect_log is not None: user.strife.log(effect_log)

        # end step
        user.death_break()
        target.death_break()

    def is_usable_by(self, griefer: "strife.Griefer"):
        if not griefer.can_pay_vial_costs(self.get_costs(griefer)): return False
        if griefer.get_skill_cooldown(self.name) > 0: return False
        for state in griefer.states_list:
            if self.category in state.lock_categories(griefer): return False
        return True
    
    def is_submittable_by(self, griefer: "strife.Griefer"):
        if not self.is_usable_by(griefer): return False
        total_costs = self.get_costs(griefer)
        for skill in griefer.submitted_skills_list:
            if skill.name == self.name and self.cooldown > 0: return False
            for vial_name, value in skill.get_costs(griefer).items():
                if vial_name in total_costs: total_costs[vial_name] += value
                else: total_costs[vial_name] = value
        if not griefer.can_pay_vial_costs(total_costs): return False
        return True

    def get_dict(self, griefer: "strife.Griefer") -> dict:
        out = deepcopy(self.__dict__)
        if self.user_skill is not None: out["user_skill"] = skills[self.user_skill].get_dict(griefer)
        if self.additional_skill is not None: out["additional_skill"] = skills[self.additional_skill].get_dict(griefer)
        out["costs"] = self.get_costs(griefer)
        out["valid_targets"] = self.get_valid_targets(griefer)
        out["special_effect"] = ""
        out["usable"] = self.is_usable_by(griefer)
        return out

AGGRIEVE_FORMULA = "user.base_damage * (1 + 0.5*coin)"

aggrieve = Skill("aggrieve")
aggrieve.description = "Deals damage and is free. An acceptable technique."
aggrieve.damage_formula = AGGRIEVE_FORMULA
aggrieve.category = "aggressive"
aggrieve.cooldown = 0
base_skills.append("aggrieve")

ASSAIL_FORMULA = "user.base_damage * (1.5 + 0.75*coin)"

assail = Skill("assail")
assail.description = "Deals additional damage compared to aggrieve, but costs a bit of VIM."
assail.damage_formula = ASSAIL_FORMULA
assail.category = "aggressive"
assail.add_vial_cost("vim", "user.power//2")
base_skills.append("assail")

AGGRESS_FORMULA = "user.base_damage * (0.25 + 3*coin)"

aggress = Skill("aggress")
aggress.description = "An all-or-nothing attack which does either massive damage or a very pitiful amount of it."
aggress.damage_formula = AGGRESS_FORMULA
aggress.category = "aggressive"
aggress.add_vial_cost("vim", "user.power//2")
player_skills.append("aggress")

ASSAULT_FORMULA = "user.base_damage * (2 + 0.75*coin)"

assault = Skill("assault")
assault.description = "Deals a lot of extra damage, but costs a lot of VIM."
assault.damage_formula = ASSAULT_FORMULA
assault.category = "aggressive"
assault.add_vial_cost("vim", "user.power")
base_skills.append("assault")

abjure = Skill("abjure")
abjure.description = "The user ABJURES, reducing oncoming damage for 2 turns."
abjure.parryable = False
abjure.beneficial = True
abjure.target_self = True
abjure.damage_formula = "0"
abjure.cooldown = 3
abjure.category = "abstinent"
abjure.add_apply_state("abjure", 2, "1.0")
abjure.need_damage_to_apply_states = False
abjure.add_vial_cost("vim", "user.power//2")
base_skills.append("abjure")

abstain = Skill("abstain")
abstain.description = "The user ABSTAINS, regenerating some VIM but accomplishing nothing else."
abstain.parryable = False
abstain.beneficial = True
abstain.target_self = True
abstain.damage_formula = "0"
abstain.cooldown = 0
abstain.category = "abstinent"
# costs negative power... hey it works
abstain.add_vial_cost("vim", "-user.power")
player_skills.append("abstain")

abuse = Skill("abuse")
abuse.description = "The user ABUSES the enemy, causing them to become DEMORALIZED and lowering their HOPE each turn."
abuse.damage_formula = "user.base_damage * (0.5 + 1.5*coin)"
abuse.need_damage_to_apply_states = True
abuse.add_apply_state("demoralize", 3, "1.0")
abuse.add_vial_cost("vim", "user.power")
abuse.category = "aggressive"
base_skills.append("abuse")

def abscond_func(user: "strife.Griefer", target: "strife.Griefer"):
    print([griefer.name for griefer in user.strife.griefer_list])
    user.strife.remove_griefer(user)
    print([griefer.name for griefer in user.strife.griefer_list])
    user.strife.verify_strife()

abscond = Skill("abscond")
abscond.description = "Sweet abscond bro!"
abscond.parryable = False
abscond.target_self = True
abscond.special_effect = abscond_func
abscond.beneficial = True
player_skills.append("abscond")

# sprite
# todo: add 1 turn warmup
amend = Skill("amend")
amend.description = "Heals the target."
amend.beneficial = True
amend.parryable = False
amend.action_cost = 0
amend.cooldown = 2
amend.add_vial_change("hp", "max(target.power, user.power//2)")

# enemy skills

abhor = Skill("abhor")
abhor.description = "Drains the VIM and ASPECT of the target."
abhor.parryable = False
abhor.action_cost = 0
abhor.cooldown = 2
abhor.add_vial_cost("vim", "user.power//2")
abhor.add_vial_change("vim", "-user.power//2")
abhor.add_vial_change("aspect", "-user.power//2")

awreak = Skill("awreak")
awreak.description = "Does a lot of damage."
awreak.need_damage_to_apply_states = True
awreak.add_apply_state("stun", 1, "1.5")
awreak.add_vial_cost("vim", "user.power")
awreak.damage_formula = "user.base_damage * (3 + 1.5*coin)"

class Aspect():
    def __init__(self, name):
        aspects[name] = self
        self.name: str = name
        self.stat_name: str = "placeholder"
        self.vials = []
        self.is_vial = False
        self.check_vials = False
        self.compare_starting_vial = False
        # balance mult, higher means aspect is generally shittier / less useful, lower means aspect is inherently good
        self.balance_mult: float = 1.0
        # ratio mult affects the power of ratios specifically (doom, for example, is harder to get a lot of, so its ratio mult is increased)
        self.ratio_mult: float = 1.0
        self.adjustment_divisor = 3.0

    # skills that depend on how much ASPECT the target has use ratio
    # ratio should "generally" cap out at 1.0, meaning 100% ASPECT, though can get higher with perma bonuses
    def ratio(self, target: "strife.Griefer", raw=False) -> float:
        if not self.is_vial:
            stat_ratio = target.get_stat(self.stat_name) / target.get_stat("power")
        else:
            ratios = 0
            present_vials = []
            for vial_name in self.vials:
                if vial_name not in target.vials: continue
                try:
                    current = target.get_vial(vial_name)
                    maximum = target.get_vial_maximum(vial_name)
                    ratios += current / maximum
                    present_vials.append(vial_name)
                except KeyError: continue
            if len(present_vials) == 0: return 0.0
            stat_ratio = ratios / len(present_vials)         
        if not raw:
            stat_ratio *= self.balance_mult
            stat_ratio *= self.ratio_mult
        print(f"{self.name} ratio {stat_ratio}")
        return stat_ratio

    # skills that depend on how little ASPECT the target has use inverse_ratio
    # should "generally" cap out at 0.5 because usually having less of an aspect is easier than having more of it
    def inverse_ratio(self, target: "strife.Griefer") -> float:
        stat_ratio = self.ratio(target, raw=True)
        stat_ratio = 1 - stat_ratio
        stat_ratio = stat_ratio / 2
        stat_ratio *= self.balance_mult
        stat_ratio *= self.ratio_mult
        return stat_ratio
    
    def adjust(self, target: "strife.Griefer", value: int, return_value=False):
        value = int(value*self.balance_mult)
        if self.check_vials: old_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
        else: old_vials = {}
        adjustment = int(value/self.adjustment_divisor)
        if self.is_vial:
            for vial_name in self.vials:
                if vial_name in target.vials:
                    target.change_vial(vial_name, adjustment)
        else:
            target.add_bonus(self.stat_name, adjustment)
        if self.check_vials:
            new_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
            for vial_name in old_vials:
                if old_vials[vial_name] != new_vials[vial_name]:
                    target.change_vial(vial_name, new_vials[vial_name]-old_vials[vial_name])
        if isinstance(self, NegativeAspect): adjustment *= -1 # just for proper printing
        if return_value: return str(adjustment)
        return f"{target.nickname}'s {self.name.upper()} {'increased' if adjustment >= 0 else 'decreased'} by {adjustment}!"

    def maximum_adjust(self, target: "strife.Griefer", value: int, return_value=False):
        if not self.is_vial:
            return self.adjust(target, value, return_value=return_value)
        else:
            adjustment = self.calculate_adjustment(value)
            for vial_name in self.vials:
                if vial_name in target.vials:
                    target.add_bonus(vial_name, adjustment)
                    target.change_vial(vial_name, adjustment) # for half vials
            if return_value: return str(adjustment)
            else: return f"{target.nickname}'s maximum {self.name.upper()} {'increased' if adjustment >= 0 else 'decreased'} by {adjustment}!"

    def permanent_adjust(self, target: "strife.Griefer", value: int, return_value=False):
        value = int(value*self.balance_mult)
        if self.check_vials: old_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
        else: old_vials = {}
        adjustment = int(value/self.adjustment_divisor)
        if self.is_vial:
            for vial_name in self.vials:
                if vial_name in target.vials:
                    target.add_permanent_bonus(vial_name, adjustment)
        else:
            target.add_permanent_bonus(self.stat_name, adjustment)
        if self.check_vials:
            new_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
            for vial_name in old_vials:
                if old_vials[vial_name] != new_vials[vial_name]:
                    target.change_vial(vial_name, new_vials[vial_name]-old_vials[vial_name])
        if isinstance(self, NegativeAspect): adjustment *= -1 # just for proper printing
        if return_value: return str(adjustment)
        return f"{target.nickname}'s {self.name.upper()} {'increased' if adjustment >= 0 else 'decreased'} PERMANENTLY by {adjustment}!"
    
    def permanent_adjust_player(self, player: "sessions.Player", value: int):
        adjustment = self.calculate_adjustment(value)
        if self.is_vial:
            for vial_name in self.vials:
                player.add_permanent_bonus(vial_name, adjustment)
        else:
            player.add_permanent_bonus(self.stat_name, adjustment)

    def calculate_adjustment(self, value: int):
        adjustment = value * self.balance_mult
        adjustment = int(adjustment/self.adjustment_divisor)
        return adjustment
    
    @property
    def maximum_name(self) -> str:
        if self.is_vial: return f"maximum {self.name.upper()}"
        else: return self.name.upper()

class NegativeAspect(Aspect):
    def ratio(self, target: "strife.Griefer", raw=False) -> float:
        if not raw: return super().inverse_ratio(target)
        else: return super().ratio(target, raw=True)
    
    def inverse_ratio(self, target: "strife.Griefer") -> float:
        return super().ratio(target)
    
    def adjust(self, target: "strife.Griefer", value: int):
        return super().adjust(target, -value)

    def permanent_adjust(self, target: "strife.Griefer", value: int):
        return super().permanent_adjust(target, -value)
    
    def permanent_adjust_player(self, player: "sessions.Player", value: int):
        return super().permanent_adjust_player(player, -value)

space = Aspect("space")
space.stat_name = "mettle"

time = Aspect("time")
time.stat_name = "spunk"
time.balance_mult = 1

mind = Aspect("mind")
mind.stat_name = "tact"
mind.check_vials = True
mind.balance_mult = 1.3

heart = Aspect("heart")
heart.stat_name = "vigor"
heart.check_vials = True

hope = Aspect("hope")
hope.is_vial = True
hope.vials = ["hope"]
hope.adjustment_divisor = 1.5

rage = Aspect("rage")
rage.is_vial = True
rage.vials = ["rage"]
rage.adjustment_divisor = 1.5

breath = Aspect("breath")
breath.stat_name = "savvy"
breath.balance_mult = 1.2

blood = Aspect("blood")
blood.is_vial = True
blood.vials = ["vim"]
blood.adjustment_divisor = 1
blood.ratio_mult = 1.3

life = Aspect("life")
life.is_vial = True
life.vials = ["hp"]
life.adjustment_divisor = 1/3

doom = NegativeAspect("doom")
doom.is_vial = True
doom.vials = ["hp"]
doom.adjustment_divisor = 1/3
doom.ratio_mult = 2
doom.balance_mult = 1.2

light = Aspect("light")
light.stat_name = "luck"
light.balance_mult = 1.2

# void
void = NegativeAspect("void")
void.is_vial = True
void.vials = ["vim", "aspect"] + SECONDARY_VIALS
void.ratio_mult = 2
void.balance_mult = 1.5
void.adjustment_divisor = 2


# aspect skills
for aspect_name in aspects:
    aspect_skills[aspect_name] = {}

class AspectSkill(Skill):
    def __init__(self, skill_name: str, aspect: Aspect, rung_required: int):
        super().__init__(skill_name)
        aspect_skills[aspect.name][skill_name] = rung_required
        self.category = "aspected"

# time

tick = AspectSkill("tick", time, 10)
tick.description = "Perform an additional action this turn."
tick.beneficial = True
tick.parryable = False
tick.action_cost = -1
tick.cooldown = 3
tick.add_vial_cost("aspect", "user.power")
tick.target_self = True

tock = AspectSkill("tock", time, 50)
tock.description = "Deals damage and uses no actions."
tock.action_cost = 0
tock.cooldown = 2
tock.add_vial_cost("aspect", "user.power//2")
tock.damage_formula = "user.base_damage * (1 + 0.5*coin)"

# space
enlarge = AspectSkill("enlarge", space, 10)
enlarge.description = "Increases the target's SPACE (mettle) for this battle."
enlarge.beneficial = True
enlarge.parryable = False
enlarge.action_cost = 0
enlarge.cooldown = 1
enlarge.add_vial_cost("aspect", "user.power//1.5")
enlarge.add_aspect_change("space", "user.power//2")

gravity = AspectSkill("gravity", space, 50)
gravity.description = "Deals damage based on how much SPACE (mettle) the target has."
gravity.add_vial_cost("aspect", "user.power")
gravity.damage_formula = "user.base_damage * (1 + 0.5*coin) * target.space.ratio * 9"

# mind
reassess = AspectSkill("reasses", mind, 10)
reassess.description = "Recover HP, ASPECT and VIM equal to 3x your MIND (tact)."
reassess.target_self = True
reassess.beneficial = True
reassess.parryable = False
reassess.add_vial_cost("vim", "-user.tac*3")
reassess.add_vial_cost("aspect", "-user.tac*3")
reassess.add_vial_change("hp", "user.tac*3")
reassess.action_cost = 0
reassess.cooldown = 2

tactics = AspectSkill("tactics", mind, 50)
tactics.description = "Deals damage based on how much MIND (tact) you have. Unaffected by coin flips >:)."
tactics.add_vial_cost("aspect", "user.power")
tactics.damage_formula = "user.base_damage * user.mind.ratio * 9"

# heart
invigorate = AspectSkill("invigorate", heart, 10)
invigorate.description = "Increases the HEART (vigor) of the target."
invigorate.beneficial = True
invigorate.parryable = False
invigorate.action_cost = 0
invigorate.cooldown = 2
invigorate.add_vial_cost("aspect", "user.power")
invigorate.add_aspect_change("heart", "user.power")

throb = AspectSkill("throb", heart, 50)
throb.description = "Deals damage equal to the target's HEART (vigor)."
throb.add_vial_cost("aspect", "user.power")
throb.damage_formula = "target.vig * (1 + coin)"

# hope
pray = AspectSkill("pray", hope, 10)
pray.description = "Increases the target's HOPE, which gives a stat buff each turn."
pray.beneficial = True
pray.parryable = False
pray.action_cost = 0
pray.cooldown = 1
pray.add_vial_cost("aspect", "user.power//2")
pray.add_aspect_change("hope", "user.power//2")

vigil = AspectSkill("vigil", hope, 50)
vigil.description = "Deals damage based on your HOPE and lowers the target's HOPE."
vigil.cooldown = 2
vigil.add_vial_cost("aspect", "user.power*1.5")
vigil.add_vial_cost("vim", "user.power//2")
vigil.add_aspect_change("hope", "-user.power")
vigil.damage_formula = "user.base_damage * user.hope.ratio * (5 + 2*coin)"

# rage
seethe = AspectSkill("seethe", rage, 10)
seethe.description = "Increases the target's RAGE, which increases both damage dealt and taken."
seethe.parryable = False
seethe.action_cost = 0
seethe.cooldown = 1
seethe.add_vial_cost("aspect", "user.power")
seethe.add_aspect_change("rage", "user.power")

subjugate = AspectSkill("subjugate", rage, 50)
subjugate.description = "Deals a lot of fucking damage."
subjugate.cooldown = 3
subjugate.add_vial_cost("aspect", "user.power")
subjugate.add_vial_cost("vim", "user.power")
subjugate.damage_formula = "user.base_damage * (4 + 3*coin)"

# breath
aerate = AspectSkill("aerate", breath, 10)
aerate.description = "Applies AIRY based on your BREATH (savvy) for 3 turns, which increases AUTO-PARRY chance."
aerate.cooldown = 1
aerate.action_cost = 0
aerate.beneficial = True
aerate.parryable = False
aerate.need_damage_to_apply_states = False
aerate.add_vial_cost("aspect", "user.power//1.5")
aerate.add_apply_state("airy", 3, "user.breath.ratio")

whirlwind = AspectSkill("whirlwind", breath, 50)
whirlwind.description = "Deals mass damage based on your BREATH (savvy)."
whirlwind.cooldown = 2
whirlwind.target_team = True
whirlwind.add_vial_cost("aspect", "user.power*1.5")
whirlwind.add_vial_cost("vim", "user.power")
whirlwind.damage_formula = "user.base_damage * user.breath.ratio * (1 + coin)"

# blood
circulate = AspectSkill("circulate", blood, 10)
circulate.description = "Increases the BLOOD (vim) of the target and all their friends."
circulate.beneficial = True
circulate.parryable = False
circulate.action_cost = 0
circulate.cooldown = 2
circulate.target_team = True
circulate.add_vial_cost("aspect", "user.power")
circulate.add_aspect_change("blood", "user.power")

bleed = AspectSkill("bleed", blood, 50)
bleed.description = "Deals damage equal to your VIM."
bleed.add_vial_cost("aspect", "user.power")
bleed.damage_formula = "user.get_vial('vim') * (1.5 + 0.5*coin)"

# life
heal = AspectSkill("heal", life, 10)
heal.description = "Restores health to the target."
heal.beneficial = True
heal.parryable = False
heal.action_cost = 0
heal.cooldown = 1
heal.add_vial_cost("aspect", "user.power//3")
heal.add_aspect_change("life", "user.power//2")

christen = AspectSkill("christen", life, 50)
christen.description = "Deals more damage the higher the target's LIFE."
christen.add_vial_cost("aspect", "user.power//2")
christen.add_vial_cost("vim", "user.power//2")
christen.damage_formula = "user.base_damage * target.life.ratio * (5 + 2*coin)"

# doom
curse = AspectSkill("curse", doom, 10)
curse.description = "Increases the target's DOOM."
curse.action_cost = 0
curse.cooldown = 1
curse.parryable = False
curse.add_vial_cost("aspect", "user.power")
curse.add_aspect_change("doom", "user.power")

execute = AspectSkill("execute", doom, 50)
execute.description = "Deals more damage the higher the target's DOOM."
execute.add_vial_cost("aspect", "user.power//2")
execute.add_vial_cost("vim", "user.power//2")
execute.damage_formula = "user.base_damage * target.doom.ratio * (7 + 3*coin)"

# light
roll = AspectSkill("roll", light, 10)
roll.description = "Does a large amount of damage on HEADS, but 1 damage on SCRATCH."
roll.action_cost = 0
roll.cooldown = 1
roll.add_vial_cost("aspect", "user.power")
roll.damage_formula = "(user.base_damage * 3 * coin) + 1"

stack_deck = AspectSkill("stack deck", light, 50)
stack_deck.description = "Lowers the LIGHT (luck) of the target and all their friends."
stack_deck.parryable = False
stack_deck.target_team = True
stack_deck.add_vial_cost("aspect", "user.power")
stack_deck.add_aspect_change("light", "-user.power")

# void
erase = AspectSkill("erase", void, 10)
erase.description = "Increases the target's VOID, draining all their vials."
erase.parryable = False
erase.action_cost = 0
erase.cooldown = 1
erase.add_vial_cost("aspect", "user.power//2")
erase.add_aspect_change("void", "user.power")

strike_between = AspectSkill("strike between", void, 50)
strike_between.description = "Deals damage based on your VOID and increases the target's VOID."
strike_between.add_vial_cost("aspect", "user.power//2")
strike_between.add_aspect_change("void", "user.power")
strike_between.damage_formula = "user.base_damage * user.void.ratio * 4 * (1 + 0.5*coin)"

balance_changes = {
    "thief": {"doom": 3, "void": 3},
    "rogue": {"doom": 4, "void": 4},
    "page": {"doom": 5, "void": 5},
    "heir": {"doom": 2, "void": 2},
    "bard": {"time": 1.5, "life": 1.25},
}

def get_balance_mult(class_name, aspect: Aspect):
    if class_name in balance_changes and aspect.name in balance_changes[class_name]:
        return aspect.balance_mult * balance_changes[class_name][aspect.name]
    else: return aspect.balance_mult

class ClassSkill(Skill):
    def __init__(self, name: str, aspect: Aspect, class_name: str, required_rung: int):
        if class_name not in class_skills: class_skills[class_name] = {}
        if aspect.name not in class_skills[class_name]: class_skills[class_name][aspect.name] = {}
        class_skills[class_name][aspect.name][name] = required_rung
        super().__init__(name)
        self.category = "accolades"

def steal_effect_constructor(aspect: Aspect) -> Callable:
        def steal_effect(user: "strife.Griefer", target: "strife.Griefer"):
            if f"stolen{aspect.name}" in target.tags:
                return f"{target.nickname} already had {aspect.name.upper()} stolen!"
            else:
                target.tags.append(f"stolen{aspect.name}")
            value = max(target.power//6, 1)
            value *= 4
            stolen_target = aspect.permanent_adjust(target, -value, return_value=True)
            stolen = aspect.permanent_adjust(user, value//4, return_value=True)
            return f"{user.nickname} stole {stolen_target} {aspect.name.upper()} from {target.nickname} (+{stolen})!"
        return steal_effect

def robbery_effect_constructor(aspect: Aspect) -> Callable:
        def robbery_effect(user: "strife.Griefer", target: "strife.Griefer"):
            if target.npc is not None and user.player is not None:
                spoils = target.npc.make_spoils(3)
                user.player.add_unclaimed_grist(spoils)
                user.strife.log(f"{user.nickname} stole grist!")
            value = max(target.power//6, 1)
            stolen_target = aspect.maximum_adjust(target, -value, return_value=True)
            stolen = aspect.maximum_adjust(user, value//4, return_value=True)
            return f"{user.nickname} robbed {stolen_target} {aspect.name.upper()} from {target.nickname} (+{stolen})!"
        return robbery_effect

def rogue_steal_effect_constructor(aspect: Aspect) -> Callable:
        def steal_effect(user: "strife.Griefer", target: "strife.Griefer"):
            if f"looted{aspect.name}" in target.tags:
                return f"{target.nickname} already had {aspect.name.upper()} looted!"
            else:
                target.tags.append(f"looted{aspect.name}")
            value = max(target.power//6, 1)
            value *= 4
            stolen_target = aspect.permanent_adjust(target, -value, return_value=True)
            stolen = "0"
            for griefer in user.team_members:
                stolen = aspect.permanent_adjust(griefer, value//8, return_value=True)
            return f"{user.nickname} looted {stolen_target} {aspect.name.upper()} from {target.nickname} (+{stolen})!"
        return steal_effect

def scatter_effect_constructor(aspect: Aspect) -> Callable:
        def scatter_effect(user: "strife.Griefer", target: "strife.Griefer"):
            if user.player is None: return "What."
            bonus = user.power//12
            for player_name in user.player.session.starting_players:
                player = sessions.Player(player_name)
                if player.strife is not None:
                    player_griefer = player.strife.get_griefer(player.name)
                    log_message = aspect.permanent_adjust(player_griefer, bonus)
                    player_griefer.strife.log(log_message)
                else:
                    aspect.permanent_adjust_player(player, bonus)
            return f"{aspect.calculate_adjustment(bonus)} {aspect.name.upper()} was scattered!"
        return scatter_effect

def sway_effect_constructor(aspect: Aspect) -> Callable:
        def sway_effect(user: "strife.Griefer", target: "strife.Griefer"):
            bonus = int(user.power*1.5*get_balance_mult("witch", aspect))
            decrease_team = target.team
            if decrease_team == "blue": increase_team = "red"
            else: increase_team = "blue"
            for griefer in user.strife.griefer_list:
                if griefer.team == increase_team: adjustment = bonus
                else: adjustment = -bonus
                aspect.adjust(griefer, adjustment)
            return f"{aspect.calculate_adjustment(bonus)} {aspect.name.upper()} was swayed!"
        return sway_effect

for aspect_name, aspect in aspects.items():
    # knight
    aspectblade = ClassSkill(f"{aspect.name}blade", aspect, "knight", 25)
    aspectblade.description = f"Deals damage based on your {aspect.name.upper()}."
    aspectblade.damage_formula = f"user.base_damage * user.{aspect.name}.ratio * (4 + coin) * {get_balance_mult('knight', aspect)}"

    # 100 - passive

    # prince
    aspectloss = ClassSkill(f"{aspect.name}loss", aspect, "prince", 25)
    aspectloss.description = f"Sharply lowers the target's {aspect.name.upper()}."
    aspectloss.add_vial_cost("aspect", "user.power//2")
    aspectloss.add_aspect_change(aspect.name, f"-user.power*1.5 * {get_balance_mult('prince', aspect)}")
    aspectloss.parryable = False

    aspectblast = ClassSkill(f"{aspect.name}blast", aspect, "prince", 100)
    aspectblast.description = f"Deals damage based on your {aspect.name.upper()} and lowers the target's {aspect.name.upper()}"
    aspectblast.add_vial_cost("vim", "user.power//2")
    aspectblast.add_vial_cost("aspect", "user.power")
    aspectblast.damage_formula = f"user.base_damage * user.{aspect.name}.ratio * (5 + 2*coin)"
    aspectblast.cooldown = 2
    aspectblast.add_aspect_change(aspect.name, f"-user.power * {get_balance_mult('prince', aspect)}")

    # thief
    aspectsteal = ClassSkill(f"{aspect.name}-steal", aspect, "thief", 25)
    aspectsteal.description = f"Permanently steals {aspect.name.upper()} from the target based on their POWER and gives 1/4 of it to the user. Can be used once per target."
    aspectsteal.parryable = False
    aspectsteal.add_vial_cost("vim", "user.power//2")
    aspectsteal.add_vial_cost("aspect", "user.power")
    aspectsteal.cooldown = 1
    aspectsteal.special_effect = steal_effect_constructor(aspect)

    aspectrobbery = ClassSkill(f"{aspect.name} robbery", aspect, "thief", 100)
    aspectrobbery.description = f"Deals damage, steals maximum {aspect.name.upper()} based on the target's power (for this strife) and steals grist from the target. No limit for use."
    aspectrobbery.add_vial_cost("vim", "user.power//2")
    aspectrobbery.add_vial_cost("aspect", "user.power")
    aspectrobbery.damage_formula = f"user.base_damage * (1.25 + 1.5*coin) * {get_balance_mult('thief', aspect)}"
    aspectrobbery.cooldown = 2
    aspectrobbery.special_effect = robbery_effect_constructor(aspect)

    # mage
    findaspect = ClassSkill(f"find {aspect.name}", aspect, "mage", 25)
    findaspect.description = f"Applies a state for 5 turns which increases the target's {aspect.name.upper()} each turn."
    findaspect.parryable = False
    findaspect.need_damage_to_apply_states = False
    findaspect.add_vial_cost("aspect", "user.power//2")
    findaspect.cooldown = 1
    findaspect.action_cost = 0
    findaspect.add_apply_state(f"pursuit of {aspect.name}", 5, f"{get_balance_mult('mage', aspect)}")

    usershared = Skill(f"user_{aspect.name}shared")
    usershared.add_aspect_change(aspect.name, f"user.power//2 * {get_balance_mult('mage', aspect)}")
    usershared.parryable = False

    sharedaspect = ClassSkill(f"shared {aspect.name}", aspect, "mage", 100)
    sharedaspect.description = f"Increases the {aspect.name.upper()} of the user and sharply increases the {aspect.name.upper()} of the target."
    sharedaspect.parryable = False
    sharedaspect.add_vial_cost("aspect", "user.power//2")
    sharedaspect.action_cost = 0
    sharedaspect.cooldown = 1
    sharedaspect.add_aspect_change(aspect.name, f"user.power*2 * {get_balance_mult('mage', aspect)}")
    sharedaspect.user_skill = f"user_{aspect.name}shared"

    # witch
    userwork = Skill(f"user_{aspect.name}work")
    userwork.add_aspect_change(aspect.name, f"user.power//1.5 * {get_balance_mult('witch', aspect)}")
    userwork.parryable = False

    aspectwork = ClassSkill(f"{aspect.name}work", aspect, "witch", 25)
    aspectwork.description = f"Reduces the {aspect.name.upper()} of the target and increases the {aspect.name.upper()} of the user."
    aspectwork.add_vial_cost("aspect", "user.power//2")
    aspectwork.parryable = False
    aspectwork.cooldown = 1
    aspectwork.action_cost = 0
    aspectwork.user_skill = f"user_{aspect.name}work"
    aspectwork.add_aspect_change(aspect.name, f"-1 * user.power//1.5 * {get_balance_mult('witch', aspect)}")

    userplay = Skill(f"user_{aspect.name}play")
    userplay.add_aspect_change(aspect.name, f"-1 * user.power//1.5 * {get_balance_mult('witch', aspect)}")
    userplay.parryable = False

    aspectplay = ClassSkill(f"{aspect.name}play", aspect, "witch", 25)
    aspectplay.description = f"Increases the {aspect.name.upper()} of the target and decreases the {aspect.name.upper()} of the user."
    aspectplay.add_vial_cost("aspect", "user.power//2")
    aspectplay.parryable = False
    aspectplay.cooldown = 1
    aspectplay.action_cost = 0
    aspectplay.user_skill = f"user_{aspect.name}play"
    aspectplay.add_aspect_change(aspect.name, f"user.power//1.5 * {get_balance_mult('witch', aspect)}")

    swayaspect = ClassSkill(f"sway {aspect.name}", aspect, "witch", 100)
    swayaspect.description = f"Decreases the {aspect.name.upper()} of one team and gives it to the other."
    swayaspect.add_vial_cost("aspect", "user.power")
    swayaspect.cooldown = 2
    swayaspect.parryable = False
    swayaspect.special_effect = sway_effect_constructor(aspect)

    # maid
    aspectpiece = ClassSkill(f"{aspect.name}piece", aspect, "maid", 25)
    aspectpiece.description = f"Very sharply increases the {aspect.name.upper()} of the target."
    aspectpiece.add_vial_cost("aspect", "user.power")
    aspectpiece.add_aspect_change(aspect.name, f"user.power*2*{get_balance_mult('maid', aspect)}")
    aspectpiece.parryable = False

    aspectsweep = ClassSkill(f"{aspect.name}sweep", aspect, "maid", 100)
    aspectsweep.description = f"Increases the {aspect.name.upper()} of the target."
    aspectsweep.add_vial_cost("aspect", "user.power//2")
    aspectsweep.add_aspect_change(aspect.name, f"user.power*{get_balance_mult('maid', aspect)}")
    aspectsweep.parryable = False
    aspectsweep.action_cost = 0

    # page
    scatteraspect = ClassSkill(f"scatter {aspect.name}", aspect, "page", 25)
    scatteraspect.description = f"Increases the {aspect.name.upper()} of everyone in the session."
    scatteraspect.add_vial_cost("aspect", "user.power//2")
    scatteraspect.target_self = True
    scatteraspect.parryable = False
    scatteraspect.special_effect = scatter_effect_constructor(aspect)
    scatteraspect.action_cost = 0
    scatteraspect.cooldown = 2

    aspectturn = ClassSkill(f"{aspect.name}turn", aspect, "page", 100)
    aspectturn.description = f"Deals damage based on your {aspect.name.upper()}."
    aspectturn.add_vial_cost("aspect", "user.power//2")
    aspectturn.action_cost = 0
    aspectturn.cooldown = 1
    aspectturn.parryable = False
    aspectturn.damage_formula = f"user.base_damage * user.{aspect.name}.ratio * (2 + coin) * {get_balance_mult('page', aspect)}"

    # bard
    aspectclub = ClassSkill(f"{aspect.name}club", aspect, "bard", 25)
    aspectclub.description = f"Deals damage depending on how low your {aspect.name.upper()} is. Is free."
    aspectclub.damage_formula = f"user.base_damage * user.{aspect.name}.inverse_ratio * (4 + coin)*{get_balance_mult('bard', aspect)}"

    # rogue
    aspectloot = ClassSkill(f"{aspect.name}-loot", aspect, "rogue", 25)
    aspectloot.description = f"Permanently steals {aspect.name.upper()} from the target based on their POWER and gives 1/8 of it to the user's team. Can be used once per target."
    aspectloot.parryable = False
    aspectloot.add_vial_cost("vim", "user.power//2")
    aspectloot.add_vial_cost("aspect", "user.power")
    aspectloot.cooldown = 1
    aspectloot.special_effect = rogue_steal_effect_constructor(aspect)

    aspecttools = ClassSkill(f"{aspect.name} tools", aspect, "rogue", 100)
    aspecttools.description = f"Increases your ASPECT based on your {aspect.name.upper()}."
    aspecttools.parryable = False
    aspecttools.beneficial = True
    aspecttools.action_cost = 0
    aspecttools.cooldown = 1
    aspecttools.add_vial_cost("vim", "user.power//2")
    aspecttools.target_self = True
    aspecttools.add_vial_cost("aspect", f"-user.power*user.{aspect.name}.ratio")

    # seer
    denyaspect = ClassSkill(f"deny {aspect.name}", aspect, "seer", 25)
    denyaspect.description = f"Applies a state for 5 turns which decreases the target's {aspect.name.upper()} each turn."
    denyaspect.parryable = False
    denyaspect.need_damage_to_apply_states = False
    denyaspect.add_vial_cost("aspect", "user.power//2")
    denyaspect.cooldown = 1
    denyaspect.action_cost = 0
    denyaspect.add_apply_state(f"retreat from {aspect.name}", 5, f"*{get_balance_mult('seer', aspect)}")

    userward = Skill(f"user_{aspect.name}ward")
    userward.add_aspect_change(aspect.name, f"-user.power//2**{get_balance_mult('seer', aspect)}")
    userward.parryable = False

    wardaspect = ClassSkill(f"{aspect.name} hope", aspect, "seer", 100)
    wardaspect.description = f"Decreases the {aspect.name.upper()} of the user and sharply decreases the {aspect.name.upper()} of the target."
    wardaspect.parryable = False
    wardaspect.add_vial_cost("aspect", "-user.power//2")
    wardaspect.action_cost = 0
    wardaspect.cooldown = 1
    wardaspect.add_aspect_change(aspect.name, f"-user.power*2*{get_balance_mult('seer', aspect)}")
    wardaspect.user_skill = f"user_{aspect.name}ward"

    # heir

    # 25: passive

    # 100: passive

    # sylph

    stitchaspect = ClassSkill(f"stitch {aspect.name}", aspect, "sylph", 25)
    stitchaspect.description = f"Heals the target and increases their {aspect.name.upper()}."
    stitchaspect.parryable = False
    stitchaspect.add_vial_cost("aspect", "user.power//2")
    stitchaspect.action_cost = 0
    stitchaspect.cooldown = 1
    stitchaspect.add_vial_change("hp", f"user.power//2*{get_balance_mult('sylph', aspect)}")
    stitchaspect.add_aspect_change(aspect.name, f"user.power//2*{get_balance_mult('sylph', aspect)}")

    # 100: passive

def add_abstratus_skill(abstratus_name: str, skill: Skill, required_rung: int):
    if abstratus_name not in abstratus_skills: abstratus_skills[abstratus_name] = {}
    abstratus_skills[abstratus_name][skill.name] = required_rung

class AbstratusSkill(Skill):
    def __init__(self, name):
        super().__init__(name)
        self.category = "arsenal"

attack = AbstratusSkill("attack")
attack.description = f"Does as much damage as AGGRIEVE, but gives you VIM instead of costing it."
attack.damage_formula = AGGRIEVE_FORMULA
attack.cooldown = 0
attack.add_vial_cost("vim", "-user.power//2")

arraign = AbstratusSkill("arraign")
arraign.description = f"Does as much damage as ASSAIL, but is free."
arraign.cooldown = 0
arraign.damage_formula = ASSAIL_FORMULA

artillerate = AbstratusSkill("artillerate")
artillerate.description = f"Does as much damage as ASSAULT, but costs as much as ASSAIL."
artillerate.damage_formula = ASSAULT_FORMULA
artillerate.add_vial_cost("vim", "user.power//2")

AVENGE_FORMULA = "user.base_damage * (3 + coin)"

avenge = AbstratusSkill("avenge")
avenge.description = f"Does more damage than ASSAULT, but costs more."
avenge.damage_formula = AVENGE_FORMULA
avenge.add_vial_cost("vim", "user.power*1.5")

awaitskill = AbstratusSkill("await")
awaitskill.description = "The user AWAITS, regenerating some VIM and ASPECT."
awaitskill.parryable = False
awaitskill.beneficial = True
awaitskill.target_self = True
awaitskill.damage_formula = "0"
awaitskill.add_vial_cost("vim", "-user.power")
awaitskill.add_vial_cost("aspect", "-user.power//2")

anarchize = AbstratusSkill("anarchize")
anarchize.description = "Does all-or-nothing damage like AGGRESS, but is free."
anarchize.damage_formula = AGGRESS_FORMULA

accuse = AbstratusSkill("accuse")
accuse.description = "Drains the target's HOPE and increases their RAGE."
accuse.parryable = False
accuse.beneficial = False
accuse.add_vial_cost("vim", "user.power//3")
accuse.add_vial_change("hope", "-user.power//2")
accuse.add_vial_change("rage", "user.power//2")
accuse.action_cost = 0

# shared skills
antagonize = AbstratusSkill("antagonize")
antagonize.description = "Applies DEMORALIZE with potency 1.5 to the target for 4 turns and increases your VIM and ASPECT."
antagonize.parryable = False
antagonize.add_apply_state("demoralize", 4, "1.5")
antagonize.add_vial_cost("vim", "-user.power//2")
antagonize.add_vial_cost("aspect", "-user.power//2")

advance = AbstratusSkill("advance")
advance.description = "Deals damage and gives you another action this turn."
advance.add_vial_cost("vim", "user.power")
advance.damage_formula = AGGRIEVE_FORMULA
advance.action_cost = -1
advance.cooldown = 3

useranticipate = Skill("useranticipate")
useranticipate.add_apply_state("guard", 2, "1.0")
useranticipate.parryable = False

anticipate = AbstratusSkill("anticipate")
anticipate.description = "Deals damage to the target and gives you GUARD with potency 1.0 for 2 turns, decreasing damage taken."
anticipate.action_cost = 0
anticipate.cooldown = 3
anticipate.add_vial_cost("vim", "user.power//2")
anticipate.damage_formula = AGGRIEVE_FORMULA
anticipate.user_skill = "useranticipate"

asphyxiate = AbstratusSkill("asphyxiate")
asphyxiate.description = "Deals damage and decreases the target's BREATH (savvy)."
asphyxiate.damage_formula = ASSAIL_FORMULA
asphyxiate.add_aspect_change("breath", "-user.power//2")
asphyxiate.add_vial_cost("vim", "user.power//3")

aslurp = AbstratusSkill("aslurp")
aslurp.description = f"Heals you and increases your ASPECT."
aslurp.action_cost = 0
aslurp.cooldown = 3
aslurp.add_vial_cost("aspect", "-user.power//2")
aslurp.add_vial_change("hp", "user.power//2")
aslurp.parryable = False
aslurp.beneficial = True
aslurp.target_self = True

assemble = AbstratusSkill("assemble")
assemble.description = f"ASSEMBLES some food, restoring the health vial and VIM of the target."
assemble.cooldown = 2
assemble.parryable = False
assemble.beneficial = True
assemble.add_vial_change("hp", "user.power//2")
assemble.add_vial_change("vim", "user.power")

useraxe = Skill("useraxe")
useraxe.parryable = False
useraxe.need_damage_to_apply_states = False
useraxe.add_apply_state("vulnerable", 2, "1.0")

axe = AbstratusSkill("axe")
axe.description = f"Attacks recklessly, making you VULNERABLE for 2 turns with a 1.0 potency."
axe.action_cost = 0
axe.cooldown = 1
axe.damage_formula = AGGRIEVE_FORMULA
axe.user_skill = "useraxe"

aim = AbstratusSkill("aim")
aim.description = f"Applies FOCUS to yourself this turn with potency 1.5, increasing the chance to flip HEADS."
aim.action_cost = 0
aim.cooldown = 1
aim.add_vial_cost("vim", "user.power//3")
aim.add_apply_state("focus", 1, "1.0")
aim.target_self = True

aggerate = AbstratusSkill("aggerate")
aggerate.description = f"Deals damage to the target and all their friends."
aggerate.action_cost = 0
aggerate.cooldown = 1
aggerate.add_vial_cost("vim", "user.power//2")
aggerate.target_team = True

admonish = AbstratusSkill("admonish")
admonish.description = f"Applies DEMORALIZE to the target for two turns and increases the potency by 0.1."
admonish.parryable = False
admonish.action_cost = 0
admonish.cooldown = 1
admonish.add_vial_cost("vim", "user.power//3")
admonish.add_apply_state("demoralize", 2, "1.0")
admonish.add_state_potency_change("demoralize", "0.1")

applot = AbstratusSkill("applot")
applot.description = f"Deals damage similar to ASSAIL and applies BLEED with potency 1.0 for 3 turns. Also increases BLEED potency by 0.1."
applot.add_vial_cost("vim", "user.power//2")
applot.damage_formula = ASSAIL_FORMULA
applot.need_damage_to_apply_states = True
applot.add_apply_state("bleed", 3, "1.0")
applot.add_state_potency_change("bleed", "0.1")

auspicate = AbstratusSkill("auspicate")
auspicate.description = "Deals all-or-nothing damage similar to AGGRESS, but costs no actions."
auspicate.damage_formula = AGGRESS_FORMULA
auspicate.add_vial_cost("vim", "user.power//2")
auspicate.action_cost = 0
auspicate.cooldown = 1

ablate = AbstratusSkill("ablate")
ablate.description = "Deals damage similar to ASSAIL and applies IGNITE with potency 2.0 for 4 turns."
ablate.damage_formula = ASSAIL_FORMULA
ablate.add_vial_cost("vim", "user.power//2")
ablate.add_apply_state("ignite", 4, "2.0")

# unique skills
# aerosolkind
aflame = AbstratusSkill("aflame")
aflame.description = "Deals damage similar to ASSAIL and applies IGNITE for 3 turns with potency 1 to the target and all their friends."
aflame.damage_formula = ASSAIL_FORMULA
aflame.cooldown = 2
aflame.target_team = True
aflame.need_damage_to_apply_states = True
aflame.add_apply_state("ignite", 3, "1.0")
aflame.add_vial_cost("vim", "user.power")

# batkind
affrap = AbstratusSkill("affrap")
affrap.description = "Deals damage similar to ASSAULT and applies STUN with potency 2.0 which drains VIM."
affrap.damage_formula = ASSAULT_FORMULA
affrap.add_apply_state("stun", 1, "2.0")
affrap.need_damage_to_apply_states = True
affrap.add_vial_cost("vim", "user.power")

# ballkind
athleticize = AbstratusSkill("athleticize")
athleticize.description = "User increases their SPUNK and gains some VIM at the cost of their health vial."
athleticize.target_self = True
athleticize.beneficial = True
athleticize.parryable = False
athleticize.action_cost = 0
athleticize.cooldown = 1
athleticize.add_vial_cost("hp", "user.power//2")
athleticize.add_vial_cost("vim", "-user.power//2")
athleticize.add_stat_bonus("spunk", "user.power//18")

# bladekind
againstand = AbstratusSkill("againstand")
againstand.description = "Deals more damage the larger the difference is between the user and the target's power."
againstand.add_vial_cost("vim", "user.power//2")
againstand.damage_formula = AGGRIEVE_FORMULA + " * (target.power / user.power) * 1.5"

# bottlekind
userabdicate = AbstratusSkill("userabdicate")
userabdicate.need_damage_to_apply_states = False
userabdicate.add_apply_state("disarm", 3, "1.0")
userabdicate.parryable = False

abdicate = AbstratusSkill("abdicate")
abdicate.description = f"Deals a lot of damage but applies DISARM to you for 3 turns, which prevents you from ARSENALIZING."
abdicate.cooldown = 1
abdicate.damage_formula = AVENGE_FORMULA
abdicate.user_skill = "userabdicate"

# cupkind
def assober_effect(user: "strife.Griefer", target: "strife.Griefer"):
    bad_states = [state for state in user.states_list if not state.beneficial]
    if len(bad_states) == 0: return
    cured_state = random.choice(bad_states)
    user.remove_state(cured_state.name)
    user.strife.log(f"{user.nickname} was cured of {cured_state.name.upper()}!")

assober = AbstratusSkill("assober")
assober.description = f"Increases your ASPECT and cures a negative state."
assober.action_cost = 0
assober.cooldown = 2
assober.add_vial_cost("aspect", "-user.power//2")
assober.add_vial_cost("vim", "user.power//3")
assober.special_effect = assober_effect
assober.parryable = False

# dicekind
apothegmatize = AbstratusSkill("apothegmatize")
apothegmatize.description = "Increases your SAVVY and LUCK and restores your VIM."
apothegmatize.target_self = True
apothegmatize.beneficial = True
apothegmatize.parryable = False
apothegmatize.action_cost = 0
apothegmatize.cooldown = 1
apothegmatize.add_stat_bonus("savvy", "user.power//24")
apothegmatize.add_stat_bonus("luck", "user.power//18")
apothegmatize.add_vial_cost("vim", "-user.power//2")

# fistkind / glovekind
arrest = AbstratusSkill("arrest")
arrest.description = "Deals damage and applies DISARM and VULNERABLE with potency 1.5 for 2 turns."
arrest.add_vial_cost("vim", "user.power//2")
arrest.damage_formula = ASSAIL_FORMULA
arrest.add_apply_state("disarm", 2, "1.0")
arrest.add_apply_state("vulnerable", 2, "1.5")
arrest.need_damage_to_apply_states = True

# guitarkind
allure = AbstratusSkill("allure")
allure.description = "INSPIRES for 3 turns with potency 1.5 and REFRESHES the target and their friends with potency 2.0."
allure.add_vial_cost("vim", "user.power//2")
allure.add_apply_state("refresh", 1, "2.0")
allure.add_apply_state("inspire", 3, "1.5")
allure.beneficial = True
allure.parryable = False
allure.target_team = True

# knifekind
assassinate = AbstratusSkill("assassinate")
assassinate.description = "Deals more damage to the target the higher their LIFE. Also applies BLEED for 3 turns with a potency based on their missing health."
assassinate.add_vial_cost("vim", "user.power")
assassinate.damage_formula = "user.base_damage * (4 + 3*coin) * target.life.ratio"
assassinate.cooldown = 3
assassinate.add_apply_state("bleed", 3, "target.doom.ratio * 3")
assassinate.need_damage_to_apply_states = True

# penkind
def autograph_effect(user: "strife.Griefer", target: "strife.Griefer"):
    if "autographed" in target.tags:
        user.strife.log(f"{target.nickname} was already autographed!")
        return
    hp_change = user.power
    resource_change = user.power
    if target.team == user.team:
        target.change_vial("hp", hp_change)
        target.change_vial("aspect", resource_change)
    else:
        target.change_vial("hp", -hp_change*2)
        target.change_vial("vim", -resource_change)

autograph = AbstratusSkill("autograph")
autograph.description = "Can be used once per target. If used on an ally, restores HP and ASPECT. If used on an enemy, directly drains HP and VIM."
autograph.action_cost = 0
autograph.parryable = False
autograph.add_vial_cost("vim", "user.power//2")
autograph.special_effect = autograph_effect

# pepperspraykind
abate = AbstratusSkill("abate")
abate.description = f"Deals a small amount of damage and applies DEMORALIZE to all enemies with potency 1.0 for 2 turns."
abate.action_cost = 0
abate.cooldown = 1
abate.damage_formula = AGGRIEVE_FORMULA
abate.add_apply_state("demoralize", 2, "1.0")
abate.add_vial_cost("vim", "user.power//2")
abate.need_damage_to_apply_states = True

# pistolkind
aunter = AbstratusSkill("aunter")
aunter.description = f"Gain an additional action this turn."
aunter.add_vial_cost("vim", "user.power//3")
aunter.action_cost = -1
aunter.cooldown = 2
aunter.target_self = True
aunter.parryable = False

# pokerkind
accroach = AbstratusSkill("accroach")
accroach.description = "Deals a small amount of damage and applies VULNERABLE with a potency of 1.0 to the target this turn."
accroach.add_vial_cost("vim", "user.power//2")
accroach.action_cost = 0
accroach.damage_formula = AGGRIEVE_FORMULA
accroach.add_apply_state("vulnerable", 1, "1.0")

# rollingpinkind / ironkind
araze = AbstratusSkill("araze")
araze.description = f"Deals damage and reduces the target's SPACE."
araze.damage_formula = ASSAIL_FORMULA
araze.add_aspect_change("space", "-user.power//3")
araze.add_vial_cost("vim", "user.power//3")

# sawkind
assanguinate = AbstratusSkill("assanguinate")
assanguinate.description = f"Deals damage similar to assail and applies BLEED with potency 2 for 3 turns, which deals damage over time. Also increases BLEED potency by 0.2."
assanguinate.damage_formula = ASSAIL_FORMULA
assanguinate.add_vial_cost("vim", "user.power//2")
assanguinate.add_apply_state("bleed", 3, "2.0")
assanguinate.add_state_potency_change("bleed", "0.2")
assanguinate.need_damage_to_apply_states = True

# shotgunkind
adjudge = AbstratusSkill("adjudge")
adjudge.description = f"Uses two actions, but deals massive damage."
adjudge.damage_formula = "user.base_damage * (6 + 3*coin)"
adjudge.add_vial_cost("vim", "user.power")
adjudge.action_cost = 2

# umbrellakind
abear = AbstratusSkill("abear")
abear.description = "ABJURES for three turns and restores the user's health and VIM."
abear.add_vial_cost("vim", "-user.power//3")
abear.add_vial_change("hp", "user.power//3")
abear.parryable = False
abear.beneficial = True
abear.target_self = True
abear.cooldown = 4
abear.add_apply_state("abjure", 3, "1.0")

# hatkind
adonize = AbstratusSkill("adonize")
adonize.description = f"Raises your SAVVY and TACT."
adonize.parryable = False
adonize.action_cost = 0
adonize.cooldown = 1
adonize.add_vial_cost("vim", "user.power//3")
adonize.target_self = True
adonize.add_stat_bonus("savvy", "user.power//12")
adonize.add_stat_bonus("tact", "user.power//12")

# yoyokind
userayo = Skill("userayo")
userayo.add_apply_state("inspire", 2, "1.0")
userayo.target_team = True
userayo.parryable = False

ayo = AbstratusSkill("ayo")
ayo.description = "Deals damage to the target similar to AGGRESS, gives an additional action this turn, and INSPIRES the user and all their allies with potency 1.0 for 2 turns."
ayo.action_cost = -1
ayo.cooldown = 3
ayo.add_vial_cost("vim", "user.power")
ayo.damage_formula = AGGRESS_FORMULA
ayo.user_skill = "userayo"

# aerosolkind
add_abstratus_skill("aerosolkind", aflame, 1)
add_abstratus_skill("aerosolkind", attack, 50)
add_abstratus_skill("aerosolkind", asphyxiate, 75)

# axekind
add_abstratus_skill("axekind", axe, 1)
add_abstratus_skill("axekind", avenge, 50)

# bagkind
add_abstratus_skill("bagkind", asphyxiate, 1)
add_abstratus_skill("bagkind", awaitskill, 50)
    # abduct

# ballkind
add_abstratus_skill("ballkind", antagonize, 1)
add_abstratus_skill("ballkind", arraign, 50)
add_abstratus_skill("ballkind", athleticize, 75)

# batkind
add_abstratus_skill("batkind", affrap, 1)
add_abstratus_skill("batkind", attack, 50)
add_abstratus_skill("batkind", advance, 75)

# bladekind
add_abstratus_skill("bladekind", anticipate, 1)
add_abstratus_skill("bladekind", attack, 50)
add_abstratus_skill("bladekind", againstand, 75)

# bookkind
    # ask

# boomerangkind
# again

# bottlekind
add_abstratus_skill("bottlekind", aslurp, 1)
add_abstratus_skill("bottlekind", attack, 50)
add_abstratus_skill("bottlekind", abdicate, 75)

# bowkind
add_abstratus_skill("bowkind", artillerate, 50)
add_abstratus_skill("bowkind", aim, 75)

# cleaverkind
    # amputate
add_abstratus_skill("cleaverkind", avenge, 50)
add_abstratus_skill("cleaverkind", assemble, 75)

# cordkind
add_abstratus_skill("cordkind", asphyxiate, 1)

# cupkind
add_abstratus_skill("cupkind", aslurp, 1)
add_abstratus_skill("cupkind", awaitskill, 50)
add_abstratus_skill("cupkind", assober, 75)

# dicekind
add_abstratus_skill("dicekind", auspicate, 1)
add_abstratus_skill("dicekind", anarchize, 50)
add_abstratus_skill("dicekind", apothegmatize, 75)

# fancysantakind
add_abstratus_skill("fancysantakind", antagonize, 1)
add_abstratus_skill("fancysantakind", arraign, 50)

# fistkind
add_abstratus_skill("fistkind", arrest, 1)
add_abstratus_skill("fistkind", attack, 50)
add_abstratus_skill("fistkind", anticipate, 75)

# forkkind
    # avale
add_abstratus_skill("forkkind", arraign, 50)

# glovekind
add_abstratus_skill("glovekind", arrest, 1)
add_abstratus_skill("glovekind", arraign, 50)
add_abstratus_skill("glovekind", anticipate, 75)

# grimoirekind
# accurse

# guitarkind
add_abstratus_skill("guitarkind", allure, 1)
add_abstratus_skill("guitarkind", arraign, 50)
add_abstratus_skill("guitarkind", admonish, 75)

# hatchetkind
add_abstratus_skill("hatchetkind", axe, 1)
add_abstratus_skill("hatchetkind", artillerate, 50)

# hatkind
add_abstratus_skill("hatkind", adonize, 1)
add_abstratus_skill("hatkind", awaitskill, 50)
add_abstratus_skill("hatkind", admonish, 75)

# headphonekind
# amplify
add_abstratus_skill("headphonekind", awaitskill, 50)
# attune

# ironkind
add_abstratus_skill("ironkind", ablate, 1)
add_abstratus_skill("ironkind", awaitskill, 50)
add_abstratus_skill("ironkind", araze, 75)

# jumpropekind
    # abligate
add_abstratus_skill("jumpropekind", awaitskill, 50)
add_abstratus_skill("jumpropekind", asphyxiate, 75)

# knifekind
add_abstratus_skill("knifekind", applot, 1)
add_abstratus_skill("knifekind", artillerate, 50)
add_abstratus_skill("knifekind", assassinate, 75)

# ladlekind
add_abstratus_skill("ladlekind", assemble, 1)
add_abstratus_skill("ladlekind", attack, 50)

# pankind
add_abstratus_skill("pankind", assemble, 1)
add_abstratus_skill("pankind", arraign, 50)

# paperkind
add_abstratus_skill("paperkind", awaitskill, 50)
    # ask

# penkind
add_abstratus_skill("penkind", antagonize, 1)
add_abstratus_skill("penkind", accuse, 50)
add_abstratus_skill("penkind", autograph, 75)

# pepperspraykind
add_abstratus_skill("pepperspraykind", abate, 1)
add_abstratus_skill("pepperspraykind", awaitskill, 50)
add_abstratus_skill("pepperspraykind", aggerate, 75)

# pillowkind
add_abstratus_skill("pillowkind", asphyxiate, 1)
add_abstratus_skill("pillowkind", awaitskill, 50)

# pistolkind
add_abstratus_skill("pistolkind", aim, 1)
add_abstratus_skill("pistolkind", artillerate, 50)
add_abstratus_skill("pistolkind", aunter, 75)

# pizzacutterkind
add_abstratus_skill("pizzacutterkind", applot, 1)
add_abstratus_skill("pizzacutterkind", arraign, 50)

# plungerkind
add_abstratus_skill("plungerkind", arraign, 50)
add_abstratus_skill("plungerkind", antagonize, 75)

# pokerkind
add_abstratus_skill("pokerkind", accroach, 1)
add_abstratus_skill("pokerkind", artillerate, 50)
add_abstratus_skill("pokerkind", advance, 75)

# potkind
add_abstratus_skill("potkind", assemble, 1)
add_abstratus_skill("pankind", awaitskill, 50)

# riflekind
add_abstratus_skill("riflekind", aim, 1)
add_abstratus_skill("riflekind", artillerate, 50)

# rollingpinkind
add_abstratus_skill("rollingpinkind", araze, 1)
add_abstratus_skill("rollingpinkind", arraign, 50)
add_abstratus_skill("rollingpinkind", assemble, 75)

# sawkind
add_abstratus_skill("sawkind", assanguinate, 1)
add_abstratus_skill("sawkind", avenge, 50)
add_abstratus_skill("sawkind", axe, 75)

# scissorkind
add_abstratus_skill("scissorkind", applot, 1)
add_abstratus_skill("scissorkind", attack, 50)

# scythekind
# acquire

# shotgunkind
add_abstratus_skill("shotgunkind", aggerate, 1)
add_abstratus_skill("shotgunkind", avenge, 50)
add_abstratus_skill("shotgunkind", adjudge, 75)

# spoonkind
    # avale
add_abstratus_skill("spoonkind", awaitskill, 50)
add_abstratus_skill("spoonkind", antagonize, 75)

# umbrellakind
add_abstratus_skill("umbrellakind", admonish, 1)
add_abstratus_skill("umbrellakind", awaitskill, 50)
add_abstratus_skill("umbrellakind", abear, 75)

# woodwindkind
add_abstratus_skill("woodwindkind", awaitskill, 50)
add_abstratus_skill("woodwindkind", antagonize, 75)

# yoyokind
add_abstratus_skill("yoyokind", antagonize, 1)
add_abstratus_skill("yoyokind", arraign, 50)
add_abstratus_skill("yoyokind", ayo, 75)


unfinished = []
for kind in util.kinds:
    if kind not in abstratus_skills:
        unfinished.append(kind)
    elif len(abstratus_skills[kind]) < 3:
        unfinished.append(kind)
if len(unfinished) > 0:
    print("!!! Unfinished abstrati !!!")
    print(" ".join(sorted(unfinished)))