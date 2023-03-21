from typing import Optional, Union, Callable
from copy import deepcopy

import strife
import random
import config
import sessions

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
        self.target_team = False
        self.beneficial = False
        self.parryable = True
        self.action_cost = 1
        self.num_targets = 1
        self.cooldown = 0
        self.damage_formula = "0"
        self.apply_states = {}
        self.need_damage_to_apply_states = True
        self.vial_change_formulas = {}
        self.vial_cost_formulas = {}
        self.aspect_change_formulas = {}
        self.use_message = ""
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

    def add_aspect_change(self, aspect_name: str, formula: str):
        self.aspect_change_formulas[aspect_name] = formula

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
        print(f"{self.name} formula {formula}")
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
            # user_skill is not used if the target is the user
            for griefer in targets_list:
                if griefer.name == user.name:
                    break
            else:
                skill = skills[self.user_skill]
                skill.affect(user, user)
        for vial in user.vials_list:
            vial.use_skill(user, self)

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
            for state in target.states_list: edge += state.parry_roll_modifier(target) - 1
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
                potency_formula = self.apply_states[state_name]["potency_formula"]
                potency_formula = self.format_formula(potency_formula, user, target)
                potency = float(eval(potency_formula))
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

    def is_usable_by(self, griefer: "strife.Griefer"):
        if not griefer.can_pay_vial_costs(self.get_costs(griefer)): return False
        if griefer.get_skill_cooldown(self.name) > 0: return False
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
assail.add_vial_cost("vim", "user.power//2")
base_skills.append("assail")

aggress = Skill("aggress")
aggress.description = "An all-or-nothing attack which does either massive damage or a very pitiful amount of it."
aggress.use_message = "{user} aggresses!"
aggress.damage_formula = "user.base_damage * (0.25 + 3*coin)"
aggress.category = "aggressive"
aggress.add_vial_cost("vim", "user.power//2")
player_skills.append("aggress")

assault = Skill("assault")
assault.description = "Deals a lot of extra damage, but costs a lot of VIM."
assault.use_message = "{user} assaults!"
assault.damage_formula = "user.base_damage * (2 + 0.75*coin)"
assault.category = "aggressive"
assault.add_vial_cost("vim", "user.power")
base_skills.append("assault")

abjure = Skill("abjure")
abjure.description = "The user ABJURES, reducing oncoming damage for 2 turns."
abjure.use_message = "{user} abjures!"
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
abstain.use_message = "{user} abstains!"
abstain.parryable = False
abstain.beneficial = True
abstain.target_self = True
abstain.damage_formula = "0"
abstain.category = "abstinent"
abstain.add_vial_change("vim", "user.power")
player_skills.append("abstain")

abuse = Skill("abuse")
abuse.description = "The user ABUSES the enemy, causing them to become DEMORALIZED and lowering their damage output."
abuse.use_message = "{user} abuses!"
abuse.damage_formula = "user.base_damage * (0.5 + 1.5*coin)"
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
abscond.use_message = "{user} absconds!"
abscond.parryable = False
abscond.target_self = True
abscond.special_effect = abscond_func
abscond.beneficial = True
player_skills.append("abscond")

# enemy skills

abhor = Skill("abhor")
abhor.description = "Drains the VIM and ASPECT of the target."
abhor.use_message = "{user} uses abhorrent magick!"
abhor.parryable = False
abhor.action_cost = 0
abhor.cooldown = 2
abhor.add_vial_cost("vim", "user.power//2")
abhor.add_vial_change("vim", "-user.power//2")
abhor.add_vial_change("aspect", "-user.power//2")

awreak = Skill("awreak")
awreak.description = "Does a lot of damage."
awreak.use_message = "{user} awreaks!"
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
breath.balance_mult = 1.3

blood = Aspect("blood")
blood.is_vial = True
blood.vials = ["vim"]
blood.adjustment_divisor = 1
blood.ratio_mult = 1.3

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
void.vials = ["vim", "aspect"] + SECONDARY_VIALS
void.ratio_mult = 2
void.adjustment_divisor = 2


# aspect skills
for aspect_name in aspects:
    aspect_skills[aspect_name] = {}

class AspectSkill(Skill):
    def __init__(self, skill_name: str, aspect: Aspect, rung_required: int):
        super().__init__(skill_name)
        aspect_skills[aspect.name][skill_name] = rung_required
        self.category = "aspected"
        self.use_message = f">{{user}}: {skill_name.capitalize()}."

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
stack_deck.target_team
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

class ClassSkill(Skill):
    def __init__(self, name: str, aspect: Aspect, class_name: str, required_rung: int):
        if class_name not in class_skills: class_skills[class_name] = {}
        if aspect.name not in class_skills[class_name]: class_skills[class_name][aspect.name] = {}
        class_skills[class_name][aspect.name][name] = required_rung
        super().__init__(name)
        self.category = "accolades"
        self.use_message = f">{{user}}: {name.capitalize()}."

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
            bonus = int(user.power*1.5)
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
    aspectblade.damage_formula = f"user.base_damage * user.{aspect.name}.ratio * (4 + coin)"

    # 100 - passive

    # prince
    aspectloss = ClassSkill(f"{aspect.name}loss", aspect, "prince", 25)
    aspectloss.description = f"Sharpy lowers the target's {aspect.name.upper()}."
    aspectloss.add_vial_cost("aspect", "user.power//2")
    aspectloss.add_aspect_change(aspect.name, f"-user.power*1.5")
    aspectloss.parryable = False

    aspectblast = ClassSkill(f"{aspect.name}blast", aspect, "prince", 100)
    aspectblast.description = f"Deals damage based on your {aspect.name.upper()} and lowers the target's {aspect.name.upper()}"
    aspectblast.add_vial_cost("vim", "user.power//2")
    aspectblast.add_vial_cost("aspect", "user.power")
    aspectblast.damage_formula = f"user.base_damage * user.{aspect.name}.ratio * (5 + 2*coin)"
    aspectblast.cooldown = 2
    aspectblast.add_aspect_change(aspect.name, f"-user.power")

    # thief
    aspectsteal = ClassSkill(f"{aspect.name}-steal", aspect, "thief", 25)
    aspectsteal.description = f"Permanently steals {aspect.name.upper()} from the target based on their POWER and gives 1/4 of it to the user. Can be used once per target."
    aspectsteal.parryable = False
    aspectsteal.add_vial_cost("vim", "user.power//2")
    aspectsteal.add_vial_cost("aspect", "user.power")
    aspectsteal.cooldown = 1
    aspectsteal.special_effect = steal_effect_constructor(aspect)

    # mage
    findaspect = ClassSkill(f"find {aspect.name}", aspect, "mage", 25)
    findaspect.description = f"Applies a state for 5 turns which increases the target's {aspect.name.upper()} each turn."
    findaspect.parryable = False
    findaspect.need_damage_to_apply_states = False
    findaspect.add_vial_cost("aspect", "user.power//2")
    findaspect.cooldown = 1
    findaspect.action_cost = 0
    findaspect.add_apply_state(f"pursuit of {aspect.name}", 5, "1.0")

    usershared = Skill(f"user_{aspect.name}shared")
    usershared.add_aspect_change(aspect.name, "user.power//2")
    usershared.parryable = False

    sharedaspect = ClassSkill(f"shared {aspect.name}", aspect, "mage", 100)
    sharedaspect.description = f"Increases the {aspect.name.upper()} of the user and sharply increases the {aspect.name.upper()} of the target."
    sharedaspect.parryable = False
    sharedaspect.add_vial_cost("aspect", "user.power//2")
    sharedaspect.action_cost = 0
    sharedaspect.cooldown = 1
    sharedaspect.add_aspect_change(aspect.name, f"user.power*2")
    sharedaspect.user_skill = f"user_{aspect.name}shared"

    # witch
    userwork = Skill(f"user_{aspect.name}work")
    userwork.add_aspect_change(aspect.name, f"user.power//1.5")
    userwork.parryable = False

    aspectwork = ClassSkill(f"{aspect.name}work", aspect, "witch", 25)
    aspectwork.description = f"Reduces the {aspect.name.upper()} of the target and increases the {aspect.name.upper()} of the user."
    aspectwork.add_vial_cost("aspect", "user.power//2")
    aspectwork.parryable = False
    aspectwork.cooldown = 1
    aspectwork.action_cost = 0
    aspectwork.user_skill = f"user_{aspect.name}work"
    aspectwork.add_aspect_change(aspect.name, f"-1 * user.power//1.5")

    userplay = Skill(f"user_{aspect.name}play")
    userplay.add_aspect_change(aspect.name, f"-1 * user.power//1.5")
    userplay.parryable = False

    aspectplay = ClassSkill(f"{aspect.name}play", aspect, "witch", 25)
    aspectplay.description = f"Increases the {aspect.name.upper()} of the target and decreases the {aspect.name.upper()} of the user."
    aspectplay.add_vial_cost("aspect", "user.power//2")
    aspectplay.parryable = False
    aspectplay.cooldown = 1
    aspectplay.action_cost = 0
    aspectplay.user_skill = f"user_{aspect.name}play"
    aspectplay.add_aspect_change(aspect.name, f"user.power//1.5")

    swayaspect = ClassSkill(f"sway {aspect.name}", aspect, "witch", 100)
    swayaspect.description = f"Decreases the {aspect.name.upper()} of one team and gives it to the other."
    swayaspect.add_vial_cost("aspect", "user.power")
    swayaspect.cooldown = 2
    swayaspect.parryable = False
    swayaspect.special_effect = sway_effect_constructor(aspect)

    # maid
    aspectpiece = ClassSkill(f"{aspect.name}piece", aspect, "maid", 25)
    aspectpiece.description = f"Very sharply increases the {aspect.name.upper()} of the target."
    aspectpiece.add_vial_cost("aspect", "user.power//2")
    aspectpiece.add_aspect_change(aspect.name, f"user.power*3")
    aspectpiece.parryable = False

    aspectsweep = ClassSkill(f"{aspect.name}sweep", aspect, "maid", 100)
    aspectsweep.description = f"Increases the {aspect.name.upper()} of the target."
    aspectsweep.add_vial_cost("aspect", "user.power//2")
    aspectsweep.add_aspect_change(aspect.name, f"user.power")
    aspectsweep.parryable = False

    # page
    scatteraspect = ClassSkill(f"scatter {aspect.name}", aspect, "page", 25)
    scatteraspect.description = f"Increases the {aspect.name.upper()} of everyone in the session."
    scatteraspect.add_vial_cost("aspect", "user.power//2")
    scatteraspect.target_self = True
    scatteraspect.parryable = False
    scatteraspect.special_effect = scatter_effect_constructor(aspect)
    scatteraspect.action_cost = 0
    scatteraspect.cooldown = 2

    # bard
    aspectclub = ClassSkill(f"{aspect.name}club", aspect, "bard", 25)
    aspectclub.description = f"Deals damage depending on how low your {aspect.name.upper()} is. Is free."
    aspectclub.damage_formula = f"user.base_damage * user.{aspect.name}.inverse_ratio * (4 + coin)"

    # rogue
    aspectloot = ClassSkill(f"{aspect.name}-loot", aspect, "rogue", 25)
    aspectloot.description = f"Permanently steals {aspect.name.upper()} from the target based on their POWER and gives 1/8 of it to the user's team. Can be used once per target."
    aspectloot.parryable = False
    aspectloot.add_vial_cost("vim", "user.power//2")
    aspectloot.add_vial_cost("aspect", "user.power")
    aspectloot.cooldown = 1
    aspectloot.special_effect = rogue_steal_effect_constructor(aspect)

    # seer
    denyaspect = ClassSkill(f"deny {aspect.name}", aspect, "seer", 25)
    denyaspect.description = f"Applies a state for 5 turns which decreases the target's {aspect.name.upper()} each turn."
    denyaspect.parryable = False
    denyaspect.need_damage_to_apply_states = False
    denyaspect.add_vial_cost("aspect", "user.power//2")
    denyaspect.cooldown = 1
    denyaspect.action_cost = 0
    denyaspect.add_apply_state(f"retreat from {aspect.name}", 5, "1.0")

    userward = Skill(f"user_{aspect.name}ward")
    userward.add_aspect_change(aspect.name, "-user.power//2")
    userward.parryable = False

    wardaspect = ClassSkill(f"{aspect.name} hope", aspect, "seer", 100)
    wardaspect.description = f"Decreases the {aspect.name.upper()} of the user and sharply decreases the {aspect.name.upper()} of the target."
    wardaspect.parryable = False
    wardaspect.add_vial_cost("aspect", "-user.power//2")
    wardaspect.action_cost = 0
    wardaspect.cooldown = 1
    wardaspect.add_aspect_change(aspect.name, f"-user.power*2")
    wardaspect.user_skill = f"user_{aspect.name}ward"

    # heir

    # 25: passive

    # sylph

    # 25: passive