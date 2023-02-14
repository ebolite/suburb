from pygame import Color

class Theme():
    def __init__(self):
        self.white: Color = Color(255, 255, 255)
        self.light: Color = Color(157, 224, 255)
        self.dark: Color = Color(0, 175, 255)
        self.black: Color = Color(1, 1, 1)

default = Theme()

queue = Theme()
queue.dark = Color(207, 86, 12)
queue.light = Color(255, 96, 0)