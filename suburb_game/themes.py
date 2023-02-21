from pygame import Color

themes = {}

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