import strife

aspects = {}

class Aspect():
    def __init__(self, name):
        aspects[name] = self
        self.name = name
        self.stat_name: str = "placeholder"
        # balance mult, higher means aspect is generally shittier / less useful, lower means aspect is inherently good
        self.balance_mult: float = 1.0
        # ratio mult affects the power of ratios specifically (doom, for example, is harder to get a lot of, so its ratio mult is increased)
        self.ratio_mult: float = 1.0

    # skills that depend on how much ASPECT the target has use ratio
    # ratio should "generally" cap out at 6.0, meaning 100% ASPECT, though can get higher with perma bonuses
    def ratio(self, target: "strife.Griefer") -> float:
        stat_ratio = target.get_stat(self.stat_name) / target.get_stat("power")
        stat_ratio *= self.balance_mult
        stat_ratio *= self.ratio_mult
        return stat_ratio

    # skills that depend on how little ASPECT the target has use inverse_ratio
    # should "generally" cap out at 6.0
    def inverse_ratio(self, target: "strife.Griefer") -> float:
        return self.ratio(target) / (self.ratio_mult * self.balance_mult)
    
    def adjust(self, target: "strife.Griefer", value: int):
        target.add_bonus(self.stat_name, value)

    def permanent_adjust(self, target: "strife.Griefer", value: int):
        target.add_permanent_bonus(self.stat_name, value)

space = Aspect("space")
space.stat_name = "mettle"

time = Aspect("time")
time.stat_name = "spunk"
time.balance_mult = 0.8

mind = Aspect("mind")
mind.stat_name = "tact"
mind.balance_mult = 1.3

heart = Aspect("heart")
heart.stat_name = "vigor"

# hope

# rage

breath = Aspect("breath")
breath.stat_name = "savvy"
breath.balance_mult = 1.3

# blood

# life

# doom

light = Aspect("light")
light.stat_name = "luck"
light.balance_mult = 1.3

# void


    