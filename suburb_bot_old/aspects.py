import explore

defaultratiomult = 3

aspects = {}

class Aspect:
    def __init__(self, name):
        self.name = name
        self.power = 1
        self.ratiomult = defaultratiomult
        if "maxadjust" not in dir(self):
            self.maxadjust = self.adjust
        aspects[self.name] = self

    def inverseratio(self, target):
        return self.ratio(target) / (self.ratiomult * self.power)

    def adjust(self):
        pass

    @property
    def aspect(self): # returns ASPECT
        return self.name.upper()

    @property
    def maxaspect(self): # either returns ASPECT or MAX ASPECT if applicable
        return self.aspect

class Space(Aspect):
    def adjust(self, target, value):
        target.stats["MET"] += int(value * self.power) // 3
        return f"{target.name} had {target.their} SPACE adjusted by {int(value * self.power) // 3}!"

    # def permanentadjust(self, target, value):
    #     if type(target) == explore.PlayerBattler:
    #         pass

    def ratio(self, target):
        r = target.getstat("MET") / target.getstat("POWER")
        r *= self.ratiomult * self.power
        return r

space = Space("space")

class Time(Aspect):
    def adjust(self, target, value):
        target.stats["SPK"] += int(value * self.power) // 3
        return f"{target.name} had {target.their} TIME adjusted by {int(value * self.power) // 3}!"

    def ratio(self, target):
        r = target.getstat("SPK") / target.getstat("POWER")
        r *= self.ratiomult * self.power
        return r

time = Time("time")
time.power = 0.8

class Heart(Aspect):
    def adjust(self, target, value):
        return self.maxadjust(target, value)
        # vial = "health"
        # numerator = value * self.power
        # denominator = target.power
        # ratio = numerator / denominator
        # ratio = ratio / 4 # 3x power = full heal
        # change = target.changevial(vial, int(target.vials[vial]["maximum"] * ratio))
        # return f"{target.name} had {target.their} HEART adjusted by {change} ({round((change/target.vials[vial]['maximum']) * 100)}%)!"

    def maxadjust(self, target, value):
        vial = "health"
        numerator = value * self.power
        if type(target) == explore.PlayerBattler:
            denominator = target.Player.power
        else:
            denominator = target.power
        ratio = numerator / denominator
        ratio = ratio / 4 # 5x power = doubled stat
        total = int(target.vials[vial]["maximum"] * ratio)
        add = int(target.vials[vial]["maximum"] * ratio)
        target.vials[vial]["maximum"] += int(target.vials[vial]["maximum"] * ratio)
        target.changevial(vial, add)
        return f"{target.name} had {target.their} HEART adjusted by {total} ({round(ratio*100)}%)!"

    def ratio(self, target):
        r = target.vials["health"]["maximum"] / target.getstat("POWER") / 2
        r *= self.ratiomult * self.power
        return r

heart = Heart("heart")
heart.power = .7

class Mind(Aspect):
    def adjust(self, target, value):
        if type(target) == explore.PlayerBattler:
            vial = target.Player.secondaryvial
        else:
            vial = "vim"
        numerator = value * self.power
        denominator = target.power
        ratio = numerator / denominator
        ratio = ratio / 4 # 5x power = full heal
        change = target.changevial(vial, int(target.vials[vial]["maximum"] * ratio))
        return f"{target.name} had {target.their} MIND adjusted by {change} ({round((change/target.vials[vial]['maximum']) * 100)}%)!"

    def maxadjust(self, target, value):
        if type(target) == explore.PlayerBattler:
            vial = target.Player.secondaryvial
        else:
            vial = "vim"
        numerator = value * self.power
        denominator = target.power
        ratio = numerator / denominator
        ratio = ratio / 4 # 5x power = doubled stat
        total = target.vials[vial]["maximum"] * ratio
        add = int(target.vials[vial]["maximum"] * ratio)
        target.vials[vial]["maximum"] += add
        target.changevial(vial, add)
        return f"{target.name} had {target.their} MAXIMUM MIND adjusted by {int(total)} ({round(ratio*100)}%)!"

    def ratio(self, target):
        if type(target) == explore.PlayerBattler:
            vial = target.Player.secondaryvial
        else:
            vial = "vim"
        r = target.vials[vial]["value"] / target.vials[vial]["maximum"]
        r *= self.ratiomult * self.power
        return r

    @property
    def maxaspect(self): # either returns ASPECT or MAX ASPECT if applicable
        return f"MAXIMUM {self.aspect}"

mind = Mind("mind")

class Light(Aspect):
    def adjust(self, target, value):
        print("light adjust")
        target.stats["LUK"] += int(value * self.power) // 3
        return f"{target.name} had {target.their} LIGHT adjusted by {int(value * self.power) // 3}!"

    def ratio(self, target):
        r = target.getstat("LUK") / target.getstat("POWER")
        r *= self.ratiomult * self.power
        return r

light = Light("light")
light.power = 1.5

class Breath(Aspect):
    def adjust(self, target, value):
        target.stats["SAV"] += int(value * self.power) // 3
        return f"{target.name} had {target.their} BREATH adjusted by {int(value * self.power) // 3}!"

    def ratio(self, target):
        r = target.getstat("SAV") / target.getstat("POWER")
        r *= self.ratiomult * self.power
        return r

breath = Breath("breath")
breath.power = 1.3

class Life(Aspect):
    def adjust(self, target, value):
        change = target.damage(value * self.power)
        return f"{target.name} had {target.their} LIFE adjusted by {change} ({round((change/target.vials['health']['maximum'])*100)}%)!"

    def maxadjust(self, target, value):
        numerator = value * self.power
        denominator = target.power
        ratio = numerator / denominator
        ratio = ratio / 4 # 4x power = double healing received
        target.healmult += ratio
        return f"{target.name} had {target.their} LIFE INCREASE adjusted by {round(ratio, 2)}!"

    def ratio(self, target):
        r = target.vials["health"]["value"] / target.vials["health"]["maximum"]
        r *= self.ratiomult * self.power
        return r

    @property
    def maxaspect(self): # either returns ASPECT or MAX ASPECT if applicable
        return f"HEALING RECEIVED"

life = Life("life")
life.power = 1.1

class Doom(Aspect):
    def adjust(self, target, value):
        change = -1 * target.changevial("health", int(value * self.power) * -1)
        return f"{target.name} had {target.their} DOOM adjusted by {-1 * change} ({round((change/target.vials['health']['maximum'])*100)}%)!"

    def ratio(self, target):
        if target.vials["health"]["value"] != 0:
            r = target.vials["health"]["maximum"] / target.vials["health"]["value"]
        else:
            r = self.ratiomult
        r *= self.power
        if r > self.ratiomult * self.power:
            r = self.ratiomult * self.power
        if r < 1:
            r = 1
        return r

doom = Doom("doom")
doom.ratiomult = defaultratiomult * 2.5

class Void(Aspect):
    def adjust(self, target, value):
        if "aspect" in target.vials:
            vial = "aspect"
        else:
            vial = "vim"
        change = -1 * target.changevial(vial, int(value * self.power) // 4 * -1)
        return f"{target.name} had {target.their} VOID adjusted by {int(change)} ({round((change/target.vials[vial]['maximum'])*100)}%)!"

    def ratio(self, target):
        if "aspect" in target.vials:
            vial = "aspect"
        else:
            vial = "vim"
        if target.vials[vial]["value"] != 0:
            r = target.vials[vial]["maximum"] / target.vials[vial]["value"]
        else:
            r = self.ratiomult
        r *= self.power
        if r > self.ratiomult * self.power:
            r = self.ratiomult * self.power
        if r < 1:
            r = 1
        return r

void = Void("void")
void.ratiomult = defaultratiomult * 2

class Hope(Aspect):
    def adjust(self, target, value):
        vial = "hope"
        change = target.changevial(vial, int(value * self.power) // 4)
        return f"{target.name} had {target.their} HOPE adjusted by {change} ({round((change/target.vials[vial]['maximum'])*100)}%)!"

    def maxadjust(self, target, value):
        vial = "hope"
        ratio = target.vials[vial]["value"] / target.vials[vial]["maximum"]
        add = int(value * self.power) // 4
        target.vials[vial]["maximum"] += add
        target.changevial(vial, int(add * ratio))
        return f"{target.name} had {target.their} MAXIMUM HOPE adjusted by {add}!"

    def ratio(self, target):
        difference = target.vials["hope"]["value"] - (target.vials["hope"]["maximum"] / 2)
        if difference < 0:
            difference *= -1
        r = (difference / (target.vials["hope"]["maximum"] / 2)) + (1/self.ratiomult)
        r *= (self.ratiomult - 1) * self.power
        if r < 0:
            r = -1 * (1 / r)
        return r

    @property
    def maxaspect(self): # either returns ASPECT or MAX ASPECT if applicable
        return f"MAXIMUM {self.aspect}"

hope = Hope("hope")

class Rage(Aspect):
    def adjust(self, target, value):
        vial = "rage"
        change = target.changevial(vial, int(value * self.power) // 4)
        return f"{target.name} had {target.their} RAGE adjusted by {change} ({round((change/target.vials[vial]['maximum'])*100)}%)!"

    def maxadjust(self, target, value):
        vial = "rage"
        ratio = target.vials[vial]["value"] / target.vials[vial]["maximum"]
        add = int(value * self.power) // 4
        target.vials[vial]["maximum"] += add
        target.changevial(vial, int(add * ratio))
        return f"{target.name} had {target.their} MAXIMUM RAGE adjusted by {add}!"

    def ratio(self, target):
        difference = target.vials["rage"]["value"] - (target.vials["rage"]["maximum"] / 2)
        if difference < 0:
            difference *= -1
        r = (difference / (target.vials["rage"]["maximum"] / 2)) + (1/self.ratiomult)
        r *= (self.ratiomult - 1) * self.power
        if r < 0:
            r = -1 * (1 / r)
        return r

    @property
    def maxaspect(self): # either returns ASPECT or MAX ASPECT if applicable
        return f"MAXIMUM {self.aspect}"

rage = Rage("rage")

class Blood(Aspect):
    def adjust(self, target, value):
        if "blood" in target.vials:
            vial = "blood"
        else:
            vial = "vim"
        change = target.changevial(vial, int(value * self.power) // 4)
        return f"{target.name} had {target.their} BLOOD adjusted by {change} ({round((change/target.vials[vial]['maximum'])*100)}%)!"

    def maxadjust(self, target, value):
        if "blood" in target.vials:
            vial = "blood"
        else:
            vial = "vim"
        ratio = target.vials[vial]["value"] / target.vials[vial]["maximum"]
        add = int(value * self.power) // 4
        target.vials[vial]["maximum"] += add
        target.changevial(vial, int(add * ratio))
        return f"{target.name} had {target.their} MAXIMUM BLOOD adjusted by {add}!"

    def ratio(self, target):
        if "blood" in target.vials:
            vial = "blood"
        else:
            vial = "vim"
        r = target.vials[vial]["value"] / target.vials[vial]["maximum"]
        r *= self.ratiomult * self.power
        return r

    @property
    def maxaspect(self): # either returns ASPECT or MAX ASPECT if applicable
        return f"MAXIMUM {self.aspect}"

blood = Blood("blood")
