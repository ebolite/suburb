from pygame import Color

class Theme():
    def __init__(self):
        self.white: Color = Color(255, 255, 255)
        self.light: Color = Color(157, 224, 255)
        self.dark: Color = Color(0, 175, 255)
        self.black: Color = Color(1, 1, 1)

default = Theme()

strife = Theme()
strife.light = Color(0, 227, 113)
strife.dark = Color(0, 140, 69)
strife.black = Color(14, 96, 55)

array = Theme()
array.light = Color(6, 182, 255)
array.dark = Color(16, 147, 216)

queue = Theme()
queue.dark = Color(207, 86, 12)
queue.light = Color(255, 96, 0)

stack = Theme()
stack.light = Color(255, 6, 124)
stack.dark = Color(154, 36, 70)