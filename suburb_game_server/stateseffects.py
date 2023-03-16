import strife
import skills

states: dict[str, "State"] = {}

class State():
    def __init__(self, name):
        states[name] = self
        self.name = name
        self.beneficial = False
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
    
    def new_turn(self, griefer: "strife.Griefer"):
        pass

class PursuitState(State):
    def __init__(self, name, aspect: "skills.Aspect"):
        super().__init__(name)
        self.aspect = aspect

    def new_turn(self, griefer: "strife.Griefer"):
        bonus = self.potency(griefer) * self.applier_stats(griefer)["power"] / 2
        bonus = int(bonus)
        logmessage = self.aspect.adjust(griefer, bonus)
        griefer.strife.log(logmessage)

for _, aspect in skills.aspects.items():
    aspectpursuitstate = PursuitState(f"pursuit of {aspect.name}", aspect)
    aspectpursuitstate.tooltip = f"{aspect.name.upper()} increases each turn."

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

