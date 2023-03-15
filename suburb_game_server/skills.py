from typing import Optional
from copy import deepcopy

import strife
import random
import config

aspects: dict["str", "Aspect"] = {}
skills: dict["str", "Skill"] = {}
base_skills: list[str] = [] # everyone has these
player_skills: list[str] = [] # only players get these

SECONDARY_VIALS = ["horseshitometer", "gambit", "imagination", "mangrit"]

SKILL_CATEGORIES = ["aggressive", "abstinent", "abusive", "aspected", "arsenal", "none"]

def modify_damage(damage: int, mettle: int):
    new_damage = damage * (damage / (damage + mettle*6)) # damage squared over damage plus mettle*6
    return int(new_damage)

def stat_edge(user_stat: int, target_stat: int) -> float:
    edge = (user_stat - target_stat) / (user_stat + target_stat)
    edge += 1
    return max(edge, 0.1)

# todo: make this matter
def flip_coin(user_luck: int, target_luck: int) -> bool:
    edge = stat_edge(user_luck, target_luck)
    roll = random.random() * edge
    if roll > 0.5: return True
    else: return False

class Skill():
    def __init__(self, name):
        self.name = name
        skills[name] = self
        self.category = "none"
        self.description = ""
        self.target_self = False
        self.beneficial = False
        self.parryable = True
        self.action_cost = 1
        self.num_targets = 1
        self.cooldown = 0
        self.damage_formula = ""
        self.apply_states = {}
        self.vial_change_formulas = {}
        self.need_damage_to_apply_states = True
        self.vial_cost_formulas = {}
        self.use_message = ""
        self.user_skill: Optional[str] = None
        self.additional_skill: Optional[str] = None

    def add_apply_state(self, state_name: str, duration: int, potency: float):
        self.apply_states[state_name] = {
            "duration": duration,
            "potency": potency,
        }

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

    # affect each target in list
    def use(self, user: "strife.Griefer", targets_list: list["strife.Griefer"]):
        costs = self.get_costs(user)
        if not user.can_pay_vial_costs(costs): return
        user.pay_costs(costs)
        user.add_cooldown(self.name, self.cooldown)
        if self.use_message: 
            message = self.use_message
            message = message.replace("{user}", user.nickname)
            user.strife.log(message)
        for target in targets_list:
            self.affect(user, target)
        if self.additional_skill is not None: 
            skill = skills[self.additional_skill]
            skill.use(user, targets_list)
        if self.user_skill is not None: 
            skill = skills[self.user_skill]
            skill.affect(user, user)

    # apply skill effects to individual target
    def affect(self, user: "strife.Griefer", target: "strife.Griefer"):
        if target.name not in self.get_valid_targets(user): return

        # damage step
        damage_formula = self.format_formula(self.damage_formula, user, target)
        # coin is 1 if user wins, 0 if target wins
        if "coin" in damage_formula:
            coin = flip_coin(user.get_stat("luck"), target.get_stat("luck"))
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
            edge += (stat_edge(target.get_stat("luck"), user.get_stat("luck"))/4) - 0.25
            if edge >= 0:
                roll = random.uniform(0-edge, 1)
            else:
                roll = random.uniform(0, 1+-edge)
            if roll < config.base_parry_chance:
                target.strife.log(f"{target.name} AUTO-PARRIES!")
                for vial in target.vials_list:
                    vial.on_parry(target, damage)
                return
        if damage != 0: target.take_damage(damage, coin=coin)
        if damage != 0 or not self.need_damage_to_apply_states:
            for state_name in self.apply_states:
                potency = self.apply_states[state_name]["potency"]
                duration = self.apply_states[state_name]["duration"]
                target.apply_state(state_name, user, potency, duration)

        # vial change step

        for vial_name in self.vial_change_formulas:
            vial_formula = self.vial_change_formulas[vial_name]
            vial_formula = self.format_formula(vial_formula, user, target)
            if vial_name in target.vials:
                change = target.change_vial(vial_name, int(eval(vial_formula)))
                if change > 0: user.strife.log(f"{user.nickname}'s {vial_name.upper()} increased by {change}!")
                elif change < 0: user.strife.log(f"{user.nickname}'s {vial_name.upper()} decreased by {-change}!")

    def is_usable_by(self, griefer: "strife.Griefer"):
        if not griefer.can_pay_vial_costs(self.get_costs(griefer)): return False
        if griefer.get_skill_cooldown(self.name) > 0: return False
        return True

    def get_dict(self, griefer: "strife.Griefer") -> dict:
        out = deepcopy(self.__dict__)
        if self.user_skill is not None: out["user_skill"] = skills[self.user_skill].get_dict(griefer)
        if self.additional_skill is not None: out["additional_skill"] = skills[self.additional_skill].get_dict(griefer)
        out["costs"] = self.get_costs(griefer)
        out["valid_targets"] = self.get_valid_targets(griefer)
        return out

aggrieve = Skill("aggrieve")
aggrieve.description = "Deals damage and is free. An acceptable technique."
aggrieve.use_message = "{user} aggrieves!"
aggrieve.damage_formula = "user.base_damage * (1 + 0.5*coin)"
aggrieve.category = "aggressive"
base_skills.append("aggrieve")

assail = Skill("assail")
assail.description = "Deals additional damage compared to aggrieve, but costs a bit of VIM."
assail.use_message = "{user} assails!"
assail.damage_formula = "user.base_damage * (1.5 + 0.75*coin)"
assail.category = "aggressive"
assail.vial_cost_formulas = {
    "vim": "user.power//2",
}
base_skills.append("assail")

aggress = Skill("aggress")
aggress.description = "An all-or-nothing attack which does either massive damage or a very pitiful amount of it."
aggress.use_message = "{user} aggresses!"
aggress.damage_formula = "user.base_damage * (0.25 + 3*coin)"
aggress.category = "aggressive"
aggress.vial_cost_formulas = {
    "vim": "user.power//2"
}
player_skills.append("aggress")

assault = Skill("assault")
assault.description = "Deals a lot of extra damage, but costs a lot of VIM."
assault.use_message = "{user} assaults!"
assault.damage_formula = "user.base_damage * (2 + 0.75*coin)"
assault.category = "aggressive"
assault.vial_cost_formulas = {
    "vim": "user.power",
}
base_skills.append("assault")

abjure = Skill("abjure")
abjure.description = "The user ABJURES, reducing oncoming damage for 2 turns."
abjure.use_message = "{user} abjures!"
abjure.parryable = False
abjure.beneficial = True
abjure.target_self = True
abjure.damage_formula = "0"
abjure.cooldown = 2
abjure.category = "abstinent"
abjure.add_apply_state("abjure", 2, 1.0)
abjure.need_damage_to_apply_states = False
abjure.vial_cost_formulas = {
    "vim": "user.power//2",
}
base_skills.append("abjure")

abstain = Skill("abstain")
abstain.description = "The user ABSTAINS, regenerating some VIM but accomplishing nothing else."
abstain.use_message = "{user} abstains!"
abstain.parryable = False
abstain.beneficial = True
abstain.target_self = True
abstain.damage_formula = "0"
abstain.category = "abstinent"
abstain.vial_change_formulas = {
    "vim": "user.power"
}
player_skills.append("abstain")

abuse = Skill("abuse")
abuse.description = "The user ABUSES the enemy, causing them to become DEMORALIZED and lowering their damage output."
abuse.use_message = "{user} abuses!"
abuse.damage_formula = "user.base_damage * (0.5 + 1.5*coin)"
abuse.add_apply_state("demoralize", 3, 1.0)
abuse.vial_cost_formulas = {
    "vim": "user.power",
}
abuse.category = "abusive"
base_skills.append("abuse")

class Aspect():
    def __init__(self, name):
        aspects[name] = self
        self.name = name
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
    # ratio should "generally" cap out at 6.0, meaning 100% ASPECT, though can get higher with perma bonuses
    def ratio(self, target: "strife.Griefer", raw=False) -> float:
        if not self.is_vial:
            stat_ratio = target.get_stat(self.stat_name) / target.get_stat("power")
        else:
            stat_ratio = target.get_vial(self.stat_name) / target.get_vial_maximum(self.stat_name)
            stat_ratio *= 6
        if not raw:
            stat_ratio *= self.balance_mult
            stat_ratio *= self.ratio_mult
        return stat_ratio

    # skills that depend on how little ASPECT the target has use inverse_ratio
    # should "generally" cap out at 3.0 because usually having less of an aspect is easier than having more of it
    def inverse_ratio(self, target: "strife.Griefer") -> float:
        stat_ratio = self.ratio(target, raw=True)
        stat_ratio = 6 - stat_ratio
        stat_ratio = stat_ratio / 2
        stat_ratio *= self.balance_mult
        stat_ratio *= self.ratio_mult
        return stat_ratio
    
    def adjust(self, target: "strife.Griefer", value: int):
        if self.check_vials: old_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
        else: old_vials = {}
        adjustment = int(value/self.adjustment_divisor)
        if self.is_vial:
            for vial_name in self.vials:
                target.change_vial(vial_name, adjustment)
        else:
            target.add_bonus(self.stat_name, adjustment)
        if self.check_vials:
            new_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
            for vial_name in old_vials:
                if old_vials[vial_name] != new_vials[vial_name]:
                    target.change_vial(vial_name, new_vials[vial_name]-old_vials[vial_name])

    def permanent_adjust(self, target: "strife.Griefer", value: int):
        if self.check_vials: old_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
        else: old_vials = {}
        adjustment = int(value/self.adjustment_divisor)
        if self.is_vial:
            for vial_name in self.vials:
                target.add_permanent_bonus(vial_name, adjustment)
        else:
            target.add_permanent_bonus(self.stat_name, adjustment)
        if self.check_vials:
            new_vials = {vial_name:target.get_vial_maximum(vial_name) for vial_name in target.vials}
            for vial_name in old_vials:
                if old_vials[vial_name] != new_vials[vial_name]:
                    target.change_vial(vial_name, new_vials[vial_name]-old_vials[vial_name])

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

space = Aspect("space")
space.stat_name = "mettle"

time = Aspect("time")
time.stat_name = "spunk"
time.balance_mult = 0.8

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
hope.adjustment_divisor = 0.5

rage = Aspect("rage")
rage.is_vial = True
rage.vials = ["rage"]
rage.adjustment_divisor

breath = Aspect("breath")
breath.stat_name = "savvy"
breath.balance_mult = 1.3

blood = Aspect("blood")
blood.is_vial = True
blood.vials = ["vim"]
blood.adjustment_divisor = 0.5

life = Aspect("life")
life.is_vial = True
life.vials = ["hp"]
life.adjustment_divisor = 0.5

doom = NegativeAspect("doom")
doom.is_vial = True
doom.vials = ["hp"]
doom.adjustment_divisor = 0.5
doom.ratio_mult = 2

light = Aspect("light")
light.stat_name = "luck"
light.balance_mult = 1.3

# void
void = NegativeAspect("void")
void.is_vial = True
void.vials = ["vim", "aspect", "hope", "rage"] + SECONDARY_VIALS
void.adjustment_divisor = 0.5