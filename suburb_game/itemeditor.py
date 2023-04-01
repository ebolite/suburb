from typing import Optional, Callable

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
        self.power = 10
        self.inheritpower = 10
        self.weight = 5
        self.size = 5
        self.kinds = []
        self.wearable = False
        self.description = ""
        self.cost = {
            "build": 0.5,
            "jet": 0.5
        }

    def draw_scene(self):
        suburb.new_scene()
        self.draw_name_and_adjectives()
        self.draw_code()
        self.draw_power_size()
        self.draw_kinds_button()
        self.draw_wearable_toggle()
        self.draw_description()
        self.draw_costs()

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
        code_box = render.InputTextBox(0.15, 0.23, w=160, h=32)
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
        self.power_box = render.InputTextBox(0.35, 0.23, w=128, h=32)
        self.power_box.numbers_only = True
        self.power_box.text = str(self.power)
        def power_box_func():
            self.power = int(self.power_box.text)
            self.draw_scene()
            self.power_box.active = True
        self.power_box.key_press_func = power_box_func
        power_label = self.make_label(0.5, 1.4, "power", self.power_box)
        #
        inheritpower_box = render.InputTextBox(0.5, 0.23, w=128, h=32)
        inheritpower_box.numbers_only = True
        inheritpower_box.text = str(self.inheritpower)
        def inheritpower_box_func():
            self.inheritpower = int(inheritpower_box.text)
        inheritpower_box.key_press_func = inheritpower_box_func
        inheritpower_label = self.make_label(0.5, 1.4, "inherited power", inheritpower_box)
        #
        size_box = render.InputTextBox(0.65, 0.23, w=128, h=32)
        size_box.numbers_only = True
        size_box.text = str(self.size)
        def size_box_func():
            self.size = int(size_box.text)
        size_box.key_press_func = size_box_func
        size_label = self.make_label(0.5, 1.4, "size", size_box)
        #
        power_tooltip = render.ToolTip(0, 0, 128, 32)
        power_tooltip.bind_to(self.power_box)
        power_tooltip_label_line1 = self.make_label(0, 20, "Examples: Spoon: 2; Knife: 10; Baseball Bat: 20; Sword: 40; Pistol: 100", power_tooltip)
        power_tooltip_label_line1.absolute = True
        power_tooltip_label_line2 = self.make_label(0, 40, "Paper: 1; Lamp: 11; Toilet: 24; Bathtub: 32; Fireplace: 65", power_tooltip)
        power_tooltip_label_line2.absolute = True
        inheritpower_tooltip = render.ToolTip(0, 0, 128, 32)
        inheritpower_tooltip.bind_to(inheritpower_box)
        inheritpower_tooltip_label_line1 = self.make_label(-300, 20, "This is how metaphorically powerful or cool the item is. Usually 0.", inheritpower_tooltip)
        inheritpower_tooltip_label_line1.absolute = True
        inheritpower_tooltip_label_line2 = self.make_label(-300, 40, "Examples: Yoyo: 10; Chainsaw: 30; Statue of Liberty: 250; Clock: 300", inheritpower_tooltip)
        inheritpower_tooltip_label_line2.absolute = True
        size_tooltip = render.ToolTip(0, 0, 128, 32)
        size_tooltip.bind_to(size_box)
        size_tooltip_label = self.make_label(-450, 20, "Examples: Paper: 1; Knife: 2; Baseball Bat: 10; Zweihander: 20; Toilet: 30; Refrigerator: 45", size_tooltip)
        size_tooltip_label.absolute = True
        power_tooltip_label_line1.make_always_on_top()
        power_tooltip_label_line2.make_always_on_top()
        inheritpower_tooltip_label_line1.make_always_on_top()
        inheritpower_tooltip_label_line2.make_always_on_top()
        size_tooltip_label.make_always_on_top()

    def draw_kinds_button(self):
        kinds_label = render.Text(0.15, 0.35, "Kinds")
        kinds_label.color = self.theme.dark
        kinds_display = self.make_label(0.5, 1.4, f"{', '.join(self.kinds) if self.kinds else 'none!!'}", kinds_label)
        def last_scene():
            self.draw_scene()
        def select_button_constructor(kind_name: str):
            def button_func():
                if kind_name not in self.kinds:
                    self.kinds.append(kind_name)
                self.draw_scene()
            return button_func
        def kinds_button_func():
            kinds = client.requestdic(intent="kinds")
            kinds = list(kinds)
            kinds = [kind for kind in kinds if kind not in self.kinds]
            show_options_with_search(kinds, select_button_constructor, "Select a kind to add.", last_scene, self.theme, 0)
        kinds_button = render.TextButton(0.15, 0.45, 128, 32, "Add kind", kinds_button_func)
        if self.kinds:
            def remove_kinds_button_func():
                self.kinds.pop()
                self.draw_scene()
            remove_kinds_button = render.TextButton(0.15, 0.5, 128, 32, "Remove kind", remove_kinds_button_func)
    
    def draw_wearable_toggle(self):
        def wearable_button_func():
            self.wearable = not self.wearable
            self.draw_scene()
        label = render.Text(0.85, 0.21, "Donnable / wearable?")
        label.fontsize = 20
        label.color = self.theme.dark
        wearable_text = "yes" if self.wearable else "no"
        button = render.TextButton(0.85, 0.25, 96, 32, wearable_text, wearable_button_func)

    def draw_description(self):
        description = self.description if self.description else "!! no description !!"
        description = render.Text(0.5, 0.97, description)
        description.color = self.theme.dark
        description.fontsize = 14
        def set_description_button_func():
            self.set_description_scene()
        set_description_button = render.TextButton(0.5, 0.93, 160, 32, "Set description", set_description_button_func)

    def set_description_scene(self):
        suburb.new_scene()
        label = render.Text(0.5, 0.3, "Description:")
        label.color = self.theme.dark
        description_box = render.InputTextBox(0.5, 0.4)
        description_box.fontsize = 16
        def last_scene():
            self.description = description_box.text
            self.draw_scene()
        ok_button = render.TextButton(0.5, 0.5, 128, 32, "OK", last_scene)

    def draw_costs(self):
        label = render.Text(0.5, 0.31, "Cost")
        label.color = self.theme.dark
        grist_icons = render.make_grist_cost_display(0.5, 0.4, 24, self.true_cost, text_color = self.theme.dark, absolute=False, return_grist_icons=True)
        assert isinstance(grist_icons, dict)
        def get_increase_cost_func(grist_name: str):
            def button_func():
                self.cost[grist_name] += 0.1
                self.draw_scene()
            return button_func
        def get_decrease_cost_func(grist_name: str):
            def button_func():
                self.cost[grist_name] -= 0.1
                if self.cost[grist_name] <= 0:
                    self.cost.pop(grist_name)
                self.draw_scene()
            return button_func
        for grist_name, icon in grist_icons.items():
            if grist_name == "build": continue
            increase_cost_button = render.TextButton(0.5, -0.75, 24, 24, "+", get_increase_cost_func(grist_name))
            increase_cost_button.bind_to(icon)
            decrease_cost_button = render.TextButton(0.5, 1.75, 24, 24, "-", get_decrease_cost_func(grist_name))
            decrease_cost_button.bind_to(icon)
        last_grist = list(grist_icons)[-1]
        last_icon = grist_icons[last_grist]
        def last_scene():
            self.draw_scene()
        def get_grist_icon_path(grist_name: str):
            return f"sprites/grists/{grist_name}.png"
        def pick_grist_scene_constructor(grist_name: str):
            def button_func():
                self.cost[grist_name] = 0.1
                self.draw_scene()
            return button_func
        def add_grist_func():
            available_grists = client.requestdic(intent="grists")
            available_grists = list(available_grists)
            available_grists = [grist for grist in available_grists if grist not in self.cost]
            if "rainbow" in available_grists: available_grists.remove("rainbow")
            show_options_with_search(available_grists, pick_grist_scene_constructor, "Choose grist to add.", last_scene, self.theme, image_path_func=get_grist_icon_path, image_scale=0.5)
        add_grist_button = render.TextButton(0.5, 0.5, 128, 24, "Add grist", add_grist_func)

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
    
    @property
    def true_cost(self):
        out = {}
        for grist_name, value in self.cost.items():
            out[grist_name] = int(self.power*value)
        return out
    
def show_options_with_search(options: list, button_func_constructor: Callable, label:str, last_scene: Callable, theme: "themes.Theme", page=0, 
                             search: Optional[str]=None, image_path_func: Optional[Callable]=None, image_scale=1.0):
    suburb.new_scene()
    OPTIONS_PER_PAGE = 12
    label_text = render.Text(0.5, 0.05, label)
    label_text.color = theme.dark
    if search is not None: possible_options = [option for option in options if search in option]
    else: possible_options = options.copy()
    display_options = possible_options[page*OPTIONS_PER_PAGE:(page+1)*OPTIONS_PER_PAGE]
    if not display_options: 
        page=0
        display_options = possible_options[page*OPTIONS_PER_PAGE:(page+1)*OPTIONS_PER_PAGE]
    for i, option in enumerate(display_options):
        y = 0.20 + 0.05*i
        button = render.TextButton(0.5, y, 196, 32, option, button_func_constructor(option))
        if image_path_func is not None:
            image = render.Image(0.4, y, image_path_func(option))
            image.scale = image_scale
    if page != 0:
        def previous_page(): 
            show_options_with_search(options, button_func_constructor, label, last_scene, theme, page=page-1, search=search, image_path_func=image_path_func, image_scale=image_scale)
        previous_page_button = render.TextButton(0.5, 0.15, 32, 32, "▲", previous_page)
    if possible_options[(page+1)*OPTIONS_PER_PAGE:(page+2)*OPTIONS_PER_PAGE]:
        def next_page(): 
            show_options_with_search(options, button_func_constructor, label, last_scene, theme, page=page+1, search=search, image_path_func=image_path_func, image_scale=image_scale)
        next_page_button = render.TextButton(0.5, 0.8, 32, 32, "▼", next_page)
    search_bar = render.InputTextBox(0.5, 0.9)
    def search_func():
        show_options_with_search(options, button_func_constructor, label, last_scene, theme, page, search=search_bar.text, image_path_func=image_path_func, image_scale=image_scale)
    search_bar.key_press_func = search_func
    if search is not None: 
        search_bar.active = True
        search_bar.text = search
    backbutton = render.Button(0.1, 0.92, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", last_scene)