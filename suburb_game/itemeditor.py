import render
import client
import suburb
import themes
import binaryoperations

class ItemEditor():
    def __init__(self):
        self.theme = themes.default
        self.item_name = "adjective+1 adjective+2 base"
        self.code = ""
        self.power = 0
        self.inheritpower = 10
        self.weight = 5
        self.size = 5

    def draw_scene(self):
        suburb.new_scene()
        self.draw_name_and_adjectives()
        self.draw_code()
        self.draw_power_size()

    def draw_name_and_adjectives(self):
        item_name_box = render.InputTextBox(0.5, 0.05)
        item_name_box.text = self.item_name
        def item_name_func():
            self.item_name = item_name_box.text
        item_name_box.key_press_func = item_name_func
        def base_label_func(): return f"base: {self.base.replace('+', ' ')}"
        base_label = render.Text(0.5, 0.10, "")
        base_label.text_func = base_label_func
        base_label.fontsize = 20
        base_label.color = self.theme.dark
        def adj_label_func(): return f"adjectives: {', '.join([adjective.replace('+', ' ') for adjective in self.adjectives])}"
        adjectives_label = render.Text(0.5, 0.13, "")
        adjectives_label.text_func = adj_label_func
        adjectives_label.fontsize = 20
        adjectives_label.color = self.theme.dark
        def item_name_label_func(): return f"full item name: {' '.join([descriptor.replace('+', ' ') for descriptor in self.descriptors])}"
        item_name_label = render.Text(0.5, 0.16, "")
        item_name_label.text_func = item_name_label_func
        item_name_label.fontsize = 20
        item_name_label.color = self.theme.dark

    def draw_code(self):
        code_box = render.InputTextBox(0.1, 0.15, w=160, h=32)
        def code_box_func():
            self.code = code_box.text
        code_box.key_press_func = code_box_func
        code_box.text = self.code
        code_box_label = self.make_label(0.5, 1.4, "captchalogue code", code_box)
        valid_label = render.Text(0.5, 1.8, "")
        def valid_label_func():
            if self.code == "": return "(random)"
            elif binaryoperations.is_valid_code(self.code):
                return "valid code!"
            else:
                return "invalid code!"
        valid_label.text_func = valid_label_func
        valid_label.fontsize = 16
        valid_label.bind_to(code_box)

    def draw_power_size(self):
        power_box = render.InputTextBox(0.35, 0.23, w=128, h=32)
        power_box.numbers_only = True
        power_box.text = str(self.power)
        def power_box_func():
            self.power = int(power_box.text)
        power_box.key_press_func = power_box_func
        power_label = self.make_label(0.5, 1.4, "power", power_box)
        power_tooltip = render.ToolTip(0, 0, 128, 32)
        power_tooltip.bind_to(power_box)
        power_tooltip.make_always_on_top()
        power_tooltip_label_line1 = self.make_label(0, 20, "Examples: Spoon: 2; Knife: 10; Baseball Bat: 20; Sword: 40; Pistol: 100", power_tooltip)
        power_tooltip_label_line1.absolute = True
        power_tooltip_label_line2 = self.make_label(0, 40, "Paper: 1; Lamp: 11; Toilet: 24; Bathtub: 32; Fireplace: 65", power_tooltip)
        power_tooltip_label_line2.absolute = True
        #
        inheritpower_box = render.InputTextBox(0.5, 0.23, w=128, h=32)
        inheritpower_box.numbers_only = True
        inheritpower_box.text = str(self.inheritpower)
        def inheritpower_box_func():
            self.inheritpower = int(inheritpower_box.text)
        inheritpower_box.key_press_func = inheritpower_box_func
        inheritpower_label = self.make_label(0.5, 1.4, "inherited power", inheritpower_box)
        inheritpower_tooltip = render.ToolTip(0, 0, 128, 32)
        inheritpower_tooltip.bind_to(inheritpower_box)
        inheritpower_tooltip.make_always_on_top()
        inheritpower_tooltip_label_line1 = self.make_label(0, 20, "This is how metaphorically powerful or cool the item is. Usually 0.", inheritpower_tooltip)
        inheritpower_tooltip_label_line1.absolute = True
        inheritpower_tooltip_label_line2 = self.make_label(0, 40, "Examples: Yoyo: 10; Chainsaw: 30; Statue of Liberty: 250; Clock: 300", inheritpower_tooltip)
        inheritpower_tooltip_label_line2.absolute = True
        #
        size_box = render.InputTextBox(0.6, 0.23, w=128, h=32)
        size_box.numbers_only = True
        size_box.text = str(self.size)
        def size_box_func():
            self.size = int(size_box.text)
        size_box.key_press_func = size_box_func
        size_label = self.make_label(0.65, 1.4, "size", size_box)
        size_tooltip = render.ToolTip(0, 0, 128, 32)
        size_tooltip_label = self.make_label(0, 20, "Examples: Paper: 1; Knife: 2; Baseball Bat: 10; Zweihander: 20; Toilet: 30; Refrigerator: 45", size_tooltip)
        size_tooltip_label.absolute = True

    def make_label(self, x, y, text, binding) -> "render.Text":
        label = render.Text(x, y, text)
        label.bind_to(binding)
        label.fontsize = 16
        label.color = self.theme.dark
        label.outline_color = self.theme.light
        return label

    @property
    def base(self):
        try:
            base = self.descriptors[-1]
            return base
        except IndexError:
            return "!! no base !!"

    @property
    def adjectives(self):
        descriptors = self.descriptors
        descriptors.pop()
        return descriptors
        
    @property
    def descriptors(self):
        return self.item_name.split(" ")