from pygame import Color

themes: dict[str, "Theme"] = {}

class Theme():
    def __init__(self, name: str):
        self.white: Color = Color(255, 255, 255)
        self.light: Color = Color(157, 224, 255)
        self.dark: Color = Color(0, 175, 255)
        self.black: Color = Color(1, 1, 1)
        themes[name] = self

default = Theme("default")

gristtorrent = Theme("gristtorrent")
gristtorrent.light = Color(0, 175, 255)
gristtorrent.dark = Color(226, 226, 226)
gristtorrent.black = Color(120, 120, 120)

strife = Theme("strife")
strife.light = Color(0, 227, 113)
strife.dark = Color(0, 140, 69)
strife.black = Color(14, 96, 55)

array = Theme("array")
array.light = Color(6, 182, 255)
array.dark = Color(16, 147, 216)

queue = Theme("queue")
queue.dark = Color(207, 86, 12)
queue.light = Color(255, 96, 0)

stack = Theme("stack")
stack.light = Color(255, 6, 124)
stack.dark = Color(154, 36, 70)

blood = Theme("blood")
blood.white = Color(184, 15, 20)
blood.light = Color(62, 22, 1)
blood.dark = Color(47, 0, 0)

breath = Theme("breath")
breath.light = Color(15, 225, 254)
breath.dark = Color(1, 135, 235)
breath.black = Color(0, 83, 241)

doom = Theme("doom")
doom.white = Color(24, 89, 16)
doom.light = Color(32, 65, 33)
doom.dark = Color(36, 46, 38)

heart = Theme("heart")
heart.white = Color(188, 23, 100)
heart.light = Color(120, 23, 58)
heart.dark = Color(76, 15, 38)

hope = Theme("hope")
hope.light = Color(255, 224, 148)
hope.dark = Color(254, 196, 50)
hope.black = Color(223, 160, 3)

life = Theme("life")
life.white = Color(204, 195, 179)
life.light = Color(117, 195, 78)
life.dark = Color(96, 85, 66)

light = Theme("light")
light.light = Color(248, 251, 79)
light.dark = Color(249, 129, 1)
light.black = Color(251, 71, 0)

mind = Theme("mind")
mind.white = Color(70, 252, 197)
mind.light = Color(80, 178, 81)
mind.dark = Color(63, 107, 31)

rage = Theme("rage")
rage.white = Color(156, 77, 172)
rage.light = Color(111, 55, 160)
rage.dark = Color(57, 30, 114)

space = Theme("space")
space.light = Color(132, 132, 132)
space.dark = Color(47, 47, 47)

time = Theme("time")
time.white = Color(255, 33, 6)
time.light = Color(184, 13, 14)
time.dark = Color(81, 5, 6)

void = Theme("void")
void.white = Color(0, 77, 178)
void.light = Color(4, 52, 118)
void.dark = Color(0, 23, 79)