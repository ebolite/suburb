import random

import strife
import skills

states: dict[str, "State"] = {}
class_passives: dict[str, dict[str, dict[str, int]]] = {}

class State():
    def __init__(self, name):
        states[name] = self
        self.name = name
        self.beneficial = False
        self.passive = False
        self.tooltip = ""

    def potency(self, griefer: "strife.Griefer") -> float:
        return griefer.get_state_potency(self.name)
    
    def applier_stats(self, griefer: "strife.Griefer") -> dict:
        return griefer.get_applier_stats(self.name)

    def modify_damage_received(self, damage: int, griefer: "strife.Griefer") -> int:
        return damage

    def modify_damage_dealt(self, damage: int, griefer: "strife.Griefer") -> int:
        return damage
    
    def lock_categories(self, griefer: "strife.Griefer") -> list[str]:
        return []
    
    def extra_actions(self, griefer: "strife.Griefer") -> int:
        return 0

    # lower is better
    def parry_roll_modifier(self, griefer: "strife.Griefer") -> float:
        return 1.0
    
    # lower is better
    def coinflip_modifier(self, griefer: "strife.Griefer") -> float:
        return 1.0
    
    def on_apply(self, griefer: "strife.Griefer"):
        pass

    def new_turn(self, griefer: "strife.Griefer"):
        pass

class OneTimeState(State):
    def on_apply(self, griefer: "strife.Griefer"):
        griefer.remove_state(self.name)

# one-time states
class RefreshState(OneTimeState):
    def on_apply(self, griefer: "strife.Griefer"):
        value = self.applier_stats(griefer)["power"]//6 * self.potency(griefer)
        value = int(value)
        griefer.change_vial("vim", value)
        griefer.change_vial("hp", value)
        griefer.strife.log(f"{griefer.nickname} was refreshed by {value}!")
        return super().on_apply(griefer)
    
refresh = RefreshState("refresh")
refresh.beneficial = True
refresh.tooltip = "Increases the target's VIM and HEALTH."

class CaffeinateState(OneTimeState):
    def on_apply(self, griefer: "strife.Griefer"):
        value = self.applier_stats(griefer)["power"]//6 * self.potency(griefer)
        value = int(value)
        griefer.change_vial("vim", value)
        griefer.change_vial("aspect", value)
        return super().on_apply(griefer)
    
caffeinate = CaffeinateState("caffeinate")
caffeinate.beneficial = True
caffeinate.tooltip = "Increases the target's VIM and ASPECT."

class DouseState(OneTimeState):
    def on_apply(self, griefer: "strife.Griefer"):
        bad_states = [state for state in griefer.states_list if not state.beneficial]
        if len(bad_states) == 0: return
        cured_state = random.choice(bad_states)
        griefer.remove_state(cured_state.name)
        griefer.strife.log(f"{griefer.nickname} was cured of {cured_state.name.upper()}!")
        super().on_apply(griefer)

douse = DouseState("douse")
douse.beneficial = True
douse.tooltip = "Removes a negative state of the target."

# basic states
class AbjureState(State):
    def modify_damage_received(self, damage: int, griefer: "strife.Griefer") -> int:
        new_damage = damage - griefer.get_stat("mettle")*3*self.potency(griefer)
        new_damage *= 0.75
        new_damage = int(new_damage)
        return max(new_damage, 0)
    
abjure = AbjureState("abjure")
abjure.beneficial = True
abjure.tooltip = "Reduces damage taken based on mettle."

class WeakState(State):
    def modify_damage_dealt(self, damage: int, griefer: "strife.Griefer") -> int:
        mod = 0.25 * self.potency(griefer)
        mod = 1 - mod
        return int(damage * mod)
    
weak = WeakState("weak")
weak.beneficial = False
weak.tooltip = "Reduces damage dealt."

class StrengthState(State):
    def modify_damage_dealt(self, damage: int, griefer: "strife.Griefer") -> int:
        mod = 0.25 * self.potency(griefer)
        mod = 1 + mod
        return int(damage * mod)
    
strength = StrengthState("strength")
strength.beneficial = True
strength.tooltip = "Increases damage dealt."

class DemoralizeState(State):
    def new_turn(self, griefer: "strife.Griefer"):
        change = self.applier_stats(griefer)["power"]//4 * -1 * self.potency(griefer)
        change = int(change)
        logmessage = skills.aspects["hope"].adjust(griefer, change)
        griefer.strife.log(logmessage)
    
demoralize = DemoralizeState("demoralize")
demoralize.beneficial = False
demoralize.tooltip = "Reduces hope each turn."

class InspireState(State):
    def new_turn(self, griefer: "strife.Griefer"):
        change = self.applier_stats(griefer)["power"]//4 * self.potency(griefer)
        change = int(change)
        logmessage = skills.aspects["hope"].adjust(griefer, change)
        griefer.strife.log(logmessage)
    
inspire = InspireState("inspire")
inspire.beneficial = True
inspire.tooltip = "Increases hope each turn."

class TriggeredState(State):
    def new_turn(self, griefer: "strife.Griefer"):
        change = self.applier_stats(griefer)["power"]//4 * self.potency(griefer)
        change = int(change)
        logmessage = skills.aspects["rage"].adjust(griefer, change)
        griefer.strife.log(logmessage)

trigger = TriggeredState("triggered")
trigger.beneficial = True
trigger.tooltip = "Increases rage each turn."

class NumbState(State):
    def new_turn(self, griefer: "strife.Griefer"):
        change = self.applier_stats(griefer)["power"]//4 * -1 * self.potency(griefer)
        change = int(change)
        logmessage = skills.aspects["rage"].adjust(griefer, change)
        griefer.strife.log(logmessage)

numb = NumbState("numb")
numb.beneficial = True
numb.tooltip = "Decreases rage each turn."

class DisarmState(State):
    def lock_categories(self, griefer: "strife.Griefer") -> list[str]:
        return ["arsenal"]
    
disarm = DisarmState("disarm")
disarm.beneficial = False
disarm.tooltip = "Cannot use ARSENAL skills."

class VulnerableState(State):
    def modify_damage_received(self, damage: int, griefer: "strife.Griefer") -> int:
        mod = self.potency(griefer) * 0.25
        mod = 1 + mod
        return int(damage*mod)
    
vulnerable = VulnerableState("vulnerable")
vulnerable.beneficial = False
vulnerable.tooltip = "Increases damage taken."

class GuardState(State):
    def modify_damage_received(self, damage: int, griefer: "strife.Griefer") -> int:
        mod = self.potency(griefer) * 0.25
        mod = 1 - mod
        return int(damage*mod)
    
guard = GuardState("guard")
guard.beneficial = True
guard.tooltip = "Decreases damage taken."

class AiryState(State):
    def parry_roll_modifier(self, griefer: "strife.Griefer") -> float:
        reduction = 0.4 * self.potency(griefer)
        return 1 - reduction
    
airy = AiryState("airy")
airy.beneficial = True
airy.tooltip = "Increases AUTO-PARRY chance."

class BleedState(State):
    def new_turn(self, griefer: "strife.Griefer"):
        damage = self.applier_stats(griefer)["power"]//3 * self.potency(griefer)
        griefer.take_damage(damage)

bleed = BleedState("bleed")
bleed.beneficial = False
bleed.tooltip = "Taking damage at the start of each turn."

class IgniteState(State):
    def new_turn(self, griefer: "strife.Griefer"):
        damage = self.applier_stats(griefer)["power"] * self.potency(griefer)
        griefer.take_damage(damage)
        griefer.add_state_potency("ignite", -griefer.get_state_potency("ignite")/5)

ignite = BleedState("ignite")
ignite.beneficial = False
ignite.tooltip = "Taking damage at the start of each turn. Potency reduces each turn."

class FocusState(State):
    def coinflip_modifier(self, griefer: "strife.Griefer") -> float:
        reduction = 0.25 * self.potency(griefer)
        return 1 - reduction

focus = FocusState("focus")
focus.beneficial = True
focus.tooltip = "Chance to flip HEADS is increased."

# aspect states

class PursuitState(State):
    def __init__(self, name, aspect: "skills.Aspect"):
        super().__init__(name)
        self.aspect = aspect

    def new_turn(self, griefer: "strife.Griefer"):
        bonus = self.potency(griefer) * self.applier_stats(griefer)["power"] / 2
        bonus = int(bonus)
        logmessage = self.aspect.adjust(griefer, bonus)
        griefer.strife.log(logmessage)

class RetreatState(State):
    def __init__(self, name, aspect: "skills.Aspect"):
        super().__init__(name)
        self.aspect = aspect

    def new_turn(self, griefer: "strife.Griefer"):
        bonus = self.potency(griefer) * self.applier_stats(griefer)["power"] / 2
        bonus = int(bonus)
        logmessage = self.aspect.adjust(griefer, -bonus)
        griefer.strife.log(logmessage)

for _, aspect in skills.aspects.items():
    aspectpursuitstate = PursuitState(f"pursuit of {aspect.name}", aspect)
    aspectpursuitstate.tooltip = f"{aspect.name.upper()} increases each turn."
    aspectpursuitstate.beneficial = True
    aspectretreatstate = RetreatState(f"retreat from {aspect.name}", aspect)
    aspectretreatstate.tooltip = f"{aspect.name.upper()} decreases each turn."
    aspectretreatstate.beneficial = True

# class passives and globals

class ClassPassive(State):
    def __init__(self, name, aspect: "skills.Aspect", class_name: str, required_rung: int):
        if class_name not in class_passives: class_passives[class_name] = {}
        if aspect.name not in class_passives[class_name]: class_passives[class_name][aspect.name] = {}
        class_passives[class_name][aspect.name][name] = required_rung
        super().__init__(name)
        self.passive = True
        self.beneficial = True
        self.aspect = aspect

# rogue
class GritState(ClassPassive):
    def modify_damage_received(self, damage: int, griefer: "strife.Griefer") -> int:
        mult = 1 - (self.aspect.ratio(griefer)/2)
        mult = max(0.4, mult)
        return int(damage*mult)

# heir

class AspectyState(ClassPassive):
    def new_turn(self, griefer: "strife.Griefer"):
        adjust_reply = self.aspect.adjust(griefer, griefer.power//3)
        griefer.strife.log(adjust_reply)

class BodyState(ClassPassive):
    def extra_actions(self, griefer: "strife.Griefer") -> int:
        ratio = self.aspect.ratio(griefer)
        extra_actions = 0
        if ratio > 0.5: extra_actions += 1
        if ratio > 0.9: extra_actions += 1
        if not self.aspect.is_vial: return extra_actions
        if ratio > 1.4: extra_actions += 1
        if ratio > 1.9: extra_actions += 1
        return extra_actions

# bard

class TragedyState(ClassPassive):
    def new_turn(self, griefer: "strife.Griefer"):
        adjust_reply = self.aspect.adjust(griefer, -griefer.power//3)
        griefer.strife.log(adjust_reply)

class DemiseState(ClassPassive):
    def new_turn(self, griefer: "strife.Griefer"):
        adjustment = -griefer.power//3
        adjust_reply = self.aspect.calculate_adjustment(adjustment)
        for other_griefer in griefer.strife.griefer_list:
            aspect.adjust(other_griefer, adjustment)
        griefer.strife.log(f"Everyone's {aspect.name.upper()} decreased by {-adjust_reply}!")

# sylph

class FaeState(ClassPassive):
    def new_turn(self, griefer: "strife.Griefer"):
        base_healing = griefer.power * 3
        adjustment = griefer.power//4
        for allied_griefer in griefer.team_members:
            griefer.strife.log(self.aspect.adjust(allied_griefer, adjustment))
            healing = base_healing * self.aspect.ratio(allied_griefer)
            allied_griefer.change_vial("hp", int(healing))

class BreakState(ClassPassive):
    def on_apply(self, griefer: "strife.Griefer"):
        adjust = int(griefer.get_aspect_ratio(self.aspect.name) * griefer.power)
        log_message = self.aspect.maximum_adjust(griefer, adjust)
        griefer.strife.log(log_message)

for _, aspect in skills.aspects.items():
    aspectystate = AspectyState(f"{aspect.name}y", aspect, "heir", 25)
    aspectystate.tooltip = f"{aspect.name.upper()} increases each turn."
    bodystate = BodyState(f"{aspect.name} body", aspect, "heir", 100)
    bodystate.tooltip = f"Gain additional actions each turn based on your {aspect.name}."
    tragedystate = TragedyState(f"{aspect.name} tragedy", aspect, "bard", 25)
    tragedystate.tooltip = f"{aspect.name.upper()} decreases each turn."
    demisestate = DemiseState(f"demise of {aspect.name}", aspect, "bard", 100)
    demisestate.tooltip = f"The {aspect.name.upper()} of everyone in the strife decreases each turn."
    faestate = FaeState(f"{aspect.name} fae", aspect, "sylph", 100)
    faestate.tooltip = f"Heals all allies based on their {aspect.name.upper()} and increases their {aspect.name.upper()} each turn."
    breakstate = BreakState(f"{aspect.name}break", aspect, "knight", 100)
    breakstate.tooltip = f"Your {aspect.maximum_name} is increased at the start of combat based on your {aspect}."
    gritstate = GritState(f"{aspect.name} grit", aspect, "rogue", 100)
    gritstate.tooltip = f"Damage received is reduced by {aspect.name}."