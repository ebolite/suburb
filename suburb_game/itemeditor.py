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

    def draw_scene(self):
        suburb.new_scene()
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
        code_box = render.InputTextBox(0.1, 0.15, w=160, h=32)
        def code_box_func():
            self.code = code_box.text
        code_box.key_press_func = code_box_func
        code_box.text = self.code
        code_box_label = render.Text(0.5, 1.4, "captchalogue code")
        code_box_label.fontsize = 16
        code_box_label.color = self.theme.dark
        code_box_label.bind_to(code_box)
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