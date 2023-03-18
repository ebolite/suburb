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
    
    def parry_roll_modifier(self, griefer: "strife.Griefer") -> float:
        return 1.0
    
    def on_apply(self, griefer: "strife.Griefer"):
        pass

    def new_turn(self, griefer: "strife.Griefer"):
        pass

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

class DemoralizeState(State):
    def modify_damage_dealt(self, damage: int, griefer: "strife.Griefer") -> int:
        new_damage = damage
        new_damage *= 1 - (0.33 * self.potency(griefer))
        new_damage = int(new_damage)
        return max(new_damage, 0)
    
demoralize = DemoralizeState("demoralize")
demoralize.tooltip = "Reduces damage dealt."

class AiryState(State):
    def parry_roll_modifier(self, griefer: "strife.Griefer") -> float:
        reduction = 0.4 * self.potency(griefer)
        return 1 - reduction
    
airy = AiryState("airy")
airy.tooltip = "Increases AUTO-PARRY chance."

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
    aspectretreatstate = RetreatState(f"retreat from {aspect.name}", aspect)
    aspectretreatstate.tooltip = f"{aspect.name.upper()} decreases each turn."

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

class AspectyState(ClassPassive):
    def __init__(self, name, aspect: "skills.Aspect", required_rung: int):
        super().__init__(name, aspect, "heir", required_rung)

    def new_turn(self, griefer: "strife.Griefer"):
        adjust_reply = self.aspect.adjust(griefer, griefer.power//3)
        griefer.strife.log(adjust_reply)

class TragedyState(ClassPassive):
    def __init__(self, name, aspect: "skills.Aspect", required_rung: int):
        super().__init__(name, aspect, "bard", required_rung)

    def new_turn(self, griefer: "strife.Griefer"):
        adjust_reply = self.aspect.adjust(griefer, -griefer.power//3)
        griefer.strife.log(adjust_reply)

class FaeState(ClassPassive):
    def __init__(self, name, aspect: "skills.Aspect", required_rung: int):
        super().__init__(name, aspect, "sylph", required_rung)

    def new_turn(self, griefer: "strife.Griefer"):
        healing = griefer.power
        adjustment = griefer.power//4
        for allied_griefer in griefer.team_members:
            allied_griefer.change_vial("hp", healing)
            griefer.strife.log(self.aspect.adjust(allied_griefer, adjustment))

class BreakState(ClassPassive):
    def __init__(self, name, aspect: "skills.Aspect", required_rung: int):
        super().__init__(name, aspect, "knight", required_rung)

    def on_apply(self, griefer: "strife.Griefer"):
        adjust = int(griefer.get_aspect_ratio(self.aspect.name) * griefer.power)
        log_message = self.aspect.maximum_adjust(griefer, adjust)
        griefer.strife.log(log_message)

for _, aspect in skills.aspects.items():
    aspectystate = AspectyState(f"{aspect.name}y", aspect, 25)
    aspectystate.tooltip = f"{aspect.name.upper()} increases each turn."
    tragedystate = TragedyState(f"{aspect.name} tragedy", aspect, 25)
    tragedystate.tooltip = f"{aspect.name.upper()} decreases sharply each turn."
    faestate = FaeState(f"{aspect.name} fae", aspect, 25)
    faestate.tooltip = f"Heals all allies and increases their {aspect.name.upper()} each turn."
    breakstate = BreakState(f"{aspect.name}break", aspect, 100)
    breakstate.tooltip = f"Your {aspect.maximum_name} is increased at the start of combat based on your {aspect}."