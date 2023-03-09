import strife

aspects = {}
SECONDARY_VIALS = ["horseshitometer", "gambit", "imagination", "mangrit"]

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

light = Aspect("light")
light.stat_name = "luck"
light.balance_mult = 1.3

# void
void = NegativeAspect("void")
void.is_vial = True
void.vials = ["vim", "aspect", "hope", "rage"] + SECONDARY_VIALS