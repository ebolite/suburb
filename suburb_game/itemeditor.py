from typing import Optional, Callable
import datetime

import render
import client
import suburb
import themes
import binaryoperations
import util

def placeholder():
    pass

class MapEditor():
    view_tiles = 9
    def __init__(self):
        self.setup_defaults()
        reply = client.requestdic(intent="all_tiles")
        self.available_tiles: list[str] = reply["tiles"]
        self.tile_labels: dict[str, str] = reply["labels"]
        self.current_mode = "select"
        self.current_selected_tile = "."
        self.theme = suburb.current_theme()
        self.viewx = len(self.map_tiles[0])//2
        self.viewy = len(self.map_tiles)//2

    def setup_defaults(self):
        self.map_tiles = [["." for i in range(24)] for i in range(12)]
        self.map_tiles += [["#" for i in range(24)] for i in range(2)]

    def draw_scene(self):
        suburb.new_scene()
        self.tilemap = render.TileMap(0.5, 0.5, map_editor=self)
        top_bar = render.SolidColor(0.5, 0, 200, 140, self.theme.light)
        top_bar.absolute = False
        top_bar.outline_color = self.theme.dark
        top_bar.border_radius = 12
        select_color = self.theme.white
        revise_color = self.theme.white
        deploy_color = self.theme.white
        match self.current_mode:
            case "select": select_color = self.theme.dark
            case "revise": revise_color = self.theme.dark
            case "deploy": deploy_color = self.theme.dark
        def select_func():
            self.current_mode = "select"
            self.draw_scene()
        selectbutton_background = render.SolidColor(-2, -2, 49, 49, select_color)
        selectbutton_background.border_radius = 2
        selectbutton = render.Button(0.25, 0.75, "sprites/computer/Sburb/select_button.png", None, select_func)
        selectbutton.overlay_on_click = True
        selectbutton_background.bind_to(selectbutton)
        selectbutton.bind_to(top_bar)
        def revise_func():
            self.current_mode = "revise"
            self.draw_scene()
        revisebutton_background = render.SolidColor(-2, -2, 49, 49, revise_color)
        revisebutton_background.border_radius = 2
        revisebutton = render.Button(0.5, 0.75, "sprites/computer/Sburb/revise_button.png", None, revise_func)
        revisebutton.overlay_on_click = True
        revisebutton_background.bind_to(revisebutton)
        revisebutton.bind_to(top_bar)
        def deploy_func():
            self.current_mode = "deploy"
            self.draw_scene()
        deploybutton_background = render.SolidColor(-2, -2, 49, 49, deploy_color)
        deploybutton_background.border_radius = 2
        deploybutton = render.Button(0.75, 0.75, "sprites/computer/Sburb/deploy_button.png", None, deploy_func)
        deploybutton.overlay_on_click = True
        deploybutton_background.bind_to(deploybutton)
        deploybutton.bind_to(top_bar)
        def make_tile_button(tile: str):
            def button_func():
                self.current_selected_tile = tile
                self.current_mode = "revise"
                self.draw_scene()
            return button_func
        row = 0
        column = 0
        COLUMNS = 6
        PADDING = 4
        STARTING_X = 1000
        STARTING_Y = 200
        palette_window = render.SolidColor(STARTING_X-25, STARTING_Y-25, COLUMNS*(render.tile_wh+PADDING) + 50 - PADDING, 400, self.theme.white)
        palette_window.outline_color = self.theme.dark
        palette_window.border_radius = 4
        for tile in self.available_tiles:
            x = STARTING_X + (render.tile_wh+PADDING)*column
            y = STARTING_Y + (render.tile_wh+PADDING) * row
            if self.current_selected_tile == tile:
                tile_background = render.SolidColor(x-PADDING//2, y-PADDING//2, render.tile_wh+(PADDING), render.tile_wh+(PADDING), self.theme.dark)
            tile_display = render.TileDisplay(x, y, tile)
            tile_display.absolute = True
            tile_display.tooltip = self.tile_labels[tile]
            tile_button = render.TextButton(0, 0, render.tile_wh, render.tile_wh, "", make_tile_button(tile))
            tile_button.absolute = True
            tile_button.bind_to(tile_display)
            tile_button.draw_sprite = False
            column += 1
            if column == COLUMNS:
                column = 0
                row += 1

    def change_tile(self, x, y, tile: str):
        self.map_tiles[y][x] = tile

    def change_relative_tile(self, dx, dy, tile: str):
        x = self.viewx + dx
        y = self.viewy + dy
        self.change_tile(x, y, tile)

    def move_view(self, dx, dy):
        if self.is_tile_in_bounds(self.viewx+dx, self.viewy+dy):
            self.viewx, self.viewy = self.viewx+dx, self.viewy+dy

    def move_view_by_direction(self, direction: str):
        match direction:
            case "right":
                dx = 1
                dy = 0
            case "left":
                dx = -1
                dy = 0
            case "up":
                dx = 0
                dy = -1
            case "down":
                dx = 0
                dy = 1
            case _:
                return
        self.move_view(dx, dy)
        

    def get_view(self):
        out_map_tiles = []
        map_tiles = self.map_tiles
        for map_tile_y, real_y in enumerate(range(self.viewy-self.view_tiles, self.viewy+self.view_tiles+1)):
            new_line = []
            for map_tile_x, real_x in enumerate(range(self.viewx-self.view_tiles, self.viewx+self.view_tiles+1)):
                if real_y < 0 or real_y >= len(map_tiles): new_line.append("?") # out of bounds
                elif real_x < 0 or real_x >= len(map_tiles[0]): new_line.append("?") # out of bounds
                else: 
                    new_line.append(map_tiles[real_y][real_x])
            out_map_tiles.append(new_line)
        map_dict = {
            "map": out_map_tiles,
            "instances": {}, # todo
            "specials": {},
            "npcs": {},
            "players": {},
            "room_name": "",
            "theme": "default"
        }
        return map_dict
    
    def is_tile_in_bounds(self, x, y) -> bool:
        if y < 0: return False
        if x < 0: return False
        if y >= len(self.map_tiles): return False
        if x >= len(self.map_tiles[0]): return False
        return True

class ItemEditor():
    def __init__(self):
        self.setup_defaults()

    def setup_defaults(self):
        self.theme = themes.default
        self.item_name = "adjective base"
        self.display_name = ""
        self.code = ""
        self.power = 10
        self.inheritpower = 10
        self.size = 0
        self.kinds = []
        self.wearable = False
        self.description = ""
        self.cost = {
            "build": 0.5
        }
        self.onhit_states = {}
        self.wear_states = {}
        self.consume_states = {}
        self.secret_states = {}
        self.prototype_name: Optional[str] = None
        self.secretadjectives = []
        self.interests = []
        self.interests_rarity = "uncommon"
        self.tiles = []
        self.tiles_rarity = "uncommon"

    def item_editor_scene(self):
        suburb.new_scene()
        def last_scene():
            self.item_editor_scene()
        def load_item_func_constructor(item_name):
            def button_func():
                self.load(item_name)
                self.draw_scene()
            return button_func
        def load_item_button_func():
            item_names = [item_name for item_name in util.saved_items]
            show_options_with_search(item_names, load_item_func_constructor, "What item do you want to load?", last_scene, self.theme)
        load_item_button = render.TextButton(0.5, 0.4, 196, 32, "Load Item", load_item_button_func)
        def new_item_button_func():
            self.setup_defaults()
            self.draw_scene()
        new_item_button = render.TextButton(0.5, 0.5, 196, 32, "New Item", new_item_button_func)
        title_button = render.TextButton(0.5, 0.8, 196, 32, "Back to Title", suburb.title)
        def continue_func():
            self.load("autosave")
            self.draw_scene()
        if "autosave" in util.saved_items:
            continue_button = render.TextButton(0.5, 0.6, 196, 32, "Resume Editing", continue_func)
        def search_func():
            self.search_scene()
        search_button = render.TextButton(0.5, 0.7, 196, 32, "Search Items", search_func)

    def search_scene(self):
        suburb.new_scene()
        label = render.Text(0.5, 0.3, "Search existing items:")
        label.color = self.theme.dark
        search_box = render.InputTextBox(0.5, 0.4)
        search_box.fontsize = 16
        def last_scene():
            self.item_editor_scene()
        def search_func():
            reply = client.requestplusdic(intent="search_items", content=search_box.text)
            options = list(reply)
            self.display_search_results(options)
        search_button = render.TextButton(0.5, 0.5, 128, 32, "SEARCH", search_func)
        back_button = render.TextButton(0.5, 0.6, 128, 32, "BACK", last_scene)

    def display_search_results(self, results):
        suburb.new_scene()
        label_text = render.Text(0.5, 0.05, "Search Results")
        label_text.color = self.theme.dark
        def last_scene():
            self.item_editor_scene()
        def button_func_constructor(option:str):
            def button_func():
                item_info = client.requestplusdic(intent="item_info", content=option)
                self.loadinfo(option, item_info)
                self.draw_scene()
            return button_func
        for i, option in enumerate(results):
            y = 0.20 + 0.05*i
            button_func = button_func_constructor(option)
            button = render.TextButton(0.5, y, 196, 32, option, button_func)
        backbutton = render.Button(0.1, 0.92, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", last_scene)

    def confirm_leave(self):
        suburb.new_scene()
        text = render.Text(0.5, 0.2, "Are you sure you want to leave? Any unsaved changes will be lost.")
        def confirm(): self.item_editor_scene()
        confirmbutton = render.Button(.5, .3, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", confirm)
        def back(): self.draw_scene()
        backbutton = render.Button(0.5, 0.4, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", back)

    def submission_scene(self):
        suburb.new_scene()
        logtext = render.Text(0.5, 0.2, "Are you sure you want to submit your item? This cannot be undone.")
        def confirm():
            reply = self.verify_and_submit()
            if reply is True:
                logtext.text = "Successfully submitted your item!"
            else:
                logtext.text = reply
            logtext.fontsize = 32
            logtext.set_fontsize_by_width(1200)
        confirmbutton = render.Button(.5, .3, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", confirm)
        def back(): self.draw_scene()
        backbutton = render.Button(0.5, 0.4, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", back)

    def draw_scene(self):
        suburb.new_scene()
        self.autosave()
        self.draw_name_and_adjectives()
        self.draw_code()
        self.draw_power_size()
        self.draw_kinds_button()
        self.draw_wearable_toggle()
        self.draw_description()
        self.draw_costs()
        self.draw_states()
        self.draw_sprite_name()
        self.draw_secret_adjectives()
        self.draw_interests()
        def back(): self.confirm_leave()
        savelog = render.Text(0.5, 0.82, "")
        savelog.fontsize = 16
        def save(): 
            self.save()
            savelog.text = f"saved at {datetime.datetime.now().strftime('%I:%M:%S')}"
        savebutton = render.TextButton(0.43, 0.85, 128, 32, "SAVE", save)
        def submit():
            self.submission_scene()
        submitbutton = render.TextButton(0.57, 0.85, 128, 32, "SUBMIT", submit)
        backbutton = render.Button(0.1, 0.92, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", back)

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
        display_name_text = f"{self.display_name if self.display_name else self.item_name.replace('+', ' ')}"
        display_name = render.Text(0.37, 0.47, display_name_text)
        display_name.color = self.theme.dark
        display_name.fontsize = 18
        display_name.set_fontsize_by_width(475)
        display_name_label = render.Text(0.37, 0.44, "display name")
        display_name_label.fontsize = 14
        display_name_label.color = self.theme.dark
        def set_display_name_button_func():
            self.set_display_name_scene()
        set_display_name_button = render.TextButton(0.37, 0.4, 128, 32, "Set", set_display_name_button_func)

    def set_display_name_scene(self):
        suburb.new_scene()
        label = render.Text(0.5, 0.3, "Display name (for named items):")
        label.color = self.theme.dark
        description_box = render.InputTextBox(0.5, 0.4)
        description_box.fontsize = 16
        def last_scene():
            self.display_name = description_box.text
            self.draw_scene()
        ok_button = render.TextButton(0.5, 0.5, 128, 32, "OK", last_scene)

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
        power_tooltip_label_line1.color = self.theme.black
        power_tooltip_label_line2 = self.make_label(0, 40, "Paper: 1; Lamp: 11; Toilet: 24; Bathtub: 32; Fireplace: 65", power_tooltip)
        power_tooltip_label_line2.absolute = True
        power_tooltip_label_line2.color = self.theme.black
        inheritpower_tooltip = render.ToolTip(0, 0, 128, 32)
        inheritpower_tooltip.bind_to(inheritpower_box)
        inheritpower_tooltip_label_line1 = self.make_label(-300, 20, "This is how metaphorically powerful or cool the item is. Usually 0.", inheritpower_tooltip)
        inheritpower_tooltip_label_line1.absolute = True
        inheritpower_tooltip_label_line1.color = self.theme.black
        inheritpower_tooltip_label_line2 = self.make_label(-300, 40, "Examples: Yoyo: 10; Chainsaw: 30; Statue of Liberty: 250; Clock: 300", inheritpower_tooltip)
        inheritpower_tooltip_label_line2.absolute = True
        inheritpower_tooltip_label_line2.color = self.theme.black
        size_tooltip = render.ToolTip(0, 0, 128, 32)
        size_tooltip.bind_to(size_box)
        size_tooltip_label = self.make_label(-450, 20, "Examples: Paper: 1; Knife: 2; Baseball Bat: 10; Zweihander: 20; Toilet: 30; Refrigerator: 45", size_tooltip)
        size_tooltip_label.absolute = True
        size_tooltip_label.color = self.theme.black
        power_tooltip_label_line1.make_always_on_top()
        power_tooltip_label_line2.make_always_on_top()
        inheritpower_tooltip_label_line1.make_always_on_top()
        inheritpower_tooltip_label_line2.make_always_on_top()
        size_tooltip_label.make_always_on_top()

    def draw_kinds_button(self):
        kinds_label = render.Text(0.15, 0.35, "Kinds")
        kinds_label.color = self.theme.dark
        kinds_display = self.make_label(0.5, 1.4, f"{', '.join(self.kinds) if self.kinds else '!!none!!'}", kinds_label)
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
        # label = render.Text(0.5, 0.31, "Cost")
        # label.color = self.theme.dark
        grist_icons = render.make_grist_cost_display(0.6, 0.35, 24, self.true_cost, text_color = self.theme.dark, absolute=False, return_grist_icons=True)
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
        add_grist_button = render.TextButton(0.6, 0.45, 128, 24, "Add grist", add_grist_func)

    def draw_state_icons(self, states_type: str, binding: "render.UIElement", item_states: dict[str, dict]):
        STATE_PADDING = 11
        if states_type == "onhit": states_dict = self.onhit_states
        elif states_type == "wear": states_dict = self.wear_states
        elif states_type == "consume": states_dict = self.consume_states
        else: states_dict = self.secret_states
        def get_increase_potency_func(state_name: str):
            def button_func():
                states_dict[state_name] += 0.1
                self.draw_scene()
            return button_func
        def get_decrease_potency_func(state_name: str):
            def button_func():
                states_dict[state_name] -= 0.1
                # account for floating point error
                if states_dict[state_name] - 0.05 <= 0:
                    states_dict.pop(state_name)
                self.draw_scene()
            return button_func
        state_icons = []
        for state_name, potency in states_dict.items():
            state_dict = item_states[state_name].copy()
            state_dict["potency"] = potency
            if len(state_icons) == 0:
                x, y = 0.5, 1.65
                offsetx = (16+STATE_PADDING) * (len(states_dict) - 1)
                offsetx = offsetx//2 * -1
            else:
                x, y = 1, 0.5
                offsetx = STATE_PADDING + 8
            icon = render.NoGrieferStateIcon(x, y, state_name, state_dict, theme=self.theme)
            icon.rect_x_offset = offsetx
            if len(state_icons) == 0: icon.bind_to(binding)
            else: icon.bind_to(state_icons[-1])
            state_icons.append(icon)
            increase_cost_button = render.TextButton(0.5, -0.5, 12, 12, "+", get_increase_potency_func(state_name))
            increase_cost_button.bind_to(icon)
            increase_cost_button.fontsize = 10
            decrease_cost_button = render.TextButton(0.5, 1.5, 12, 12, "-", get_decrease_potency_func(state_name))
            decrease_cost_button.bind_to(icon)
            decrease_cost_button.fontsize = 10
            potency_label = render.Text(0.5, 2.5, f"{potency:.1f}")
            potency_label.fontsize = 10
            potency_label.color = self.theme.dark
            potency_label.bind_to(icon)

    def draw_states(self):
        item_states = client.requestdic("item_states")
        def last_scene():
            self.draw_scene()
        def pick_state_constructor_constructor(state_type: str):
            if state_type == "onhit": states_dict = self.onhit_states
            elif state_type == "wear": states_dict = self.wear_states
            elif state_type == "consume": states_dict = self.consume_states
            else: states_dict = self.secret_states
            def pick_state_constructor(state_name: str):
                def button_func():
                    states_dict[state_name] = 0.1
                    self.draw_scene()
                return button_func
            return pick_state_constructor
        def add_state_button_constructor(state_type: str):
            if state_type == "onhit": states_dict = self.onhit_states
            elif state_type == "wear": states_dict = self.wear_states
            elif state_type == "consume": states_dict = self.consume_states
            else: states_dict = self.secret_states
            def button_func():
                possible_states = list(client.requestdic("item_states"))
                possible_states = [state_name for state_name in possible_states if state_name not in states_dict]
                show_options_with_search(possible_states, pick_state_constructor_constructor(state_type), "Choose state to add.", last_scene, self.theme)
            return button_func
        onhit_label = render.Text(0.15, 0.55, "On-Hit States")
        onhit_label.color = self.theme.dark
        self.draw_state_icons("onhit", onhit_label, item_states)
        add_onhit_state_button = render.TextButton(1.15, 0.5, 32, 32, "+", add_state_button_constructor("onhit"))
        add_onhit_state_button.bind_to(onhit_label)
        wear_label = render.Text(0.5, 0.55, "Donned States")
        wear_label.color = self.theme.dark
        self.draw_state_icons("wear", wear_label, item_states)
        add_wear_state_button = render.TextButton(1.15, 0.5, 32, 32, "+", add_state_button_constructor("wear"))
        add_wear_state_button.bind_to(wear_label)
        consume_label = render.Text(0.15, 0.7, "Consume States")
        consume_label.color = self.theme.dark
        self.draw_state_icons("consume", consume_label, item_states)
        add_consume_state_button = render.TextButton(1.15, 0.5, 32, 32, "+", add_state_button_constructor("consume"))
        add_consume_state_button.bind_to(consume_label)
        secret_label = render.Text(0.5, 0.7, "Secret States")
        secret_label.color = self.theme.dark
        self.draw_state_icons("secret", secret_label, item_states)
        add_secret_state_button = render.TextButton(1.15, 0.5, 32, 32, "+", add_state_button_constructor("secret"))
        add_secret_state_button.bind_to(secret_label)
        secret_tooltip_text = render.Text(-0.1, 0.5, "(?)")
        secret_tooltip_text.fontsize = 24
        secret_tooltip_text.color = self.theme.dark
        secret_tooltip_text.outline_color = self.theme.white
        secret_tooltip_text.bind_to(secret_label)
        secret_tooltip = render.ToolTip(0, 0, secret_tooltip_text.get_width(), 24)
        secret_tooltip.bind_to(secret_tooltip_text)
        secret_tooltip_label_1 = self.make_label(-200, 20, "Secret tooltips may manifest after alchemy.", secret_tooltip)
        secret_tooltip_label_1.absolute = True
        secret_tooltip_label_1.color = self.theme.black
        secret_tooltip_label_2 = self.make_label(-200, 40, "They represent the metaphorical abilities of the item.", secret_tooltip)
        secret_tooltip_label_2.absolute = True
        secret_tooltip_label_2.color = self.theme.black

    def draw_sprite_name(self):
        def button_func():
            self.choose_sprite_name()
        sprite_name_box = render.TextButton(0.85, 0.35, 256, 32, "", button_func)
        sprite_name_text = render.Text(0.5, 0.5, "")
        sprite_name_text.fontsize = 18
        def sprite_name_func():
            return f"{self.base.replace('+','')}sprite" if self.prototype_name is None else f"{self.prototype_name}sprite"
        sprite_name_text.text_func = sprite_name_func
        sprite_name_text.bind_to(sprite_name_box)
        sprite_name_label = self.make_label(0.5, 1.4, "Sprite Name", sprite_name_box)

    def choose_sprite_name(self):
        suburb.new_scene()
        name_box = render.InputTextBox(0.5, 0.4)
        name_box.fontsize = 16
        def label_func():
            return f"{self.base.replace('+','')}sprite" if not name_box.text else f"{name_box.text}sprite"
        label = render.Text(0.5, 0.3, "")
        label.color = self.theme.dark
        label.text_func = label_func
        def last_scene():
            if name_box.text:
                self.prototype_name = name_box.text.lower()
            else:
                self.prototype_name = None
            self.draw_scene()
        ok_button = render.TextButton(0.5, 0.5, 128, 32, "OK", last_scene)

    def draw_secret_adjectives(self):
        secret_adjectives_label = render.Text(0.8, 0.85, f"{'!!' if not self.secretadjectives else ''} ({len(self.secretadjectives)} inheritable adjective{'s' if len(self.secretadjectives) != 1 else ''}) {'!!' if not self.secretadjectives else ''}")
        secret_adjectives_label.fontsize = 16
        secret_adjectives_label.color = self.theme.dark
        def button_func():
            self.set_secret_adjectives()
        add_secret_adjectives_button = render.TextButton(0.8, 0.9, 96, 32, "Set", button_func)

    def draw_interests(self):
        interests_text = f"{len(self.interests)} Interest{'s' if len(self.interests) != 1 else ''}"
        interests_label = render.Text(0.85, 0.45, interests_text)
        interests_label.color = self.theme.dark
        def last_scene():
            self.draw_scene()
        def choose_interests_button_constructor(interest: str):
            def button_func():
                if interest in self.interests:
                    self.interests.remove(interest)
                else:
                    self.interests.append(interest)
            return button_func
        def is_interest_in_interests(interest: str):
            if interest in self.interests: return True
            else: return False
        def choose_interests():
            options = client.requestdic("interests")
            options = list(options)
            show_options_with_search(options, choose_interests_button_constructor, "Choose interests for this item.", last_scene, self.theme, option_active_func=is_interest_in_interests, reload_on_button_press=True)
        choose_interests_button = render.TextButton(0.5, 2.5, 128, 32, "Choose", choose_interests)
        choose_interests_button.bind_to(interests_label)
        def interest_rarity_button_func():
            match self.interests_rarity:
                case "common":
                    self.interests_rarity = "uncommon"
                case "uncommon":
                    self.interests_rarity = "rare"
                case "rare":
                    self.interests_rarity = "exotic"
                case "exotic":
                    self.interests_rarity = "common"
            self.draw_scene()
        interests_rarity_button = render.TextButton(0.5, 1.4, 128, 32, self.interests_rarity, interest_rarity_button_func)
        interests_rarity_button.bind_to(interests_label)

        tiles_text = f"{len(self.tiles)} Room{'s' if len(self.tiles) != 1 else ''}"
        tiles_label = render.Text(0.85, 0.6, tiles_text)
        tiles_label.color = self.theme.dark
        def choose_tiles_button_constructor(tile: str):
            def button_func():
                if tile in self.tiles:
                    self.tiles.remove(tile)
                else:
                    self.tiles.append(tile)
            return button_func
        def is_tile_in_tiles(tile: str):
            if tile in self.tiles: return True
            else: return False
        def choose_tiles():
            options = client.requestdic("tile_spawnlists")
            options = list(options)
            show_options_with_search(options, choose_tiles_button_constructor, "Choose room spawnlists for this item.", last_scene, self.theme, option_active_func=is_tile_in_tiles, reload_on_button_press=True)
        choose_tiles_button = render.TextButton(0.5, 2.5, 128, 32, "Choose", choose_tiles)
        choose_tiles_button.bind_to(tiles_label)
        def tile_rarity_button_func():
            match self.tiles_rarity:
                case "common":
                    self.tiles_rarity = "uncommon"
                case "uncommon":
                    self.tiles_rarity = "rare"
                case "rare":
                    self.tiles_rarity = "exotic"
                case "exotic":
                    self.tiles_rarity = "common"
            self.draw_scene()
        tiles_rarity_button = render.TextButton(0.5, 1.4, 128, 32, self.tiles_rarity, tile_rarity_button_func)
        tiles_rarity_button.bind_to(tiles_label)

    def set_secret_adjectives(self):
        suburb.new_scene()
        adjectives_box = render.InputTextBox(0.5, 0.4)
        adjectives_box.fontsize = 16
        adjectives_box.text = " ".join(self.secretadjectives)
        label = render.Text(0.5, 0.2, "Inherited adjectives may be gained upon alchemizing.")
        label.color = self.theme.dark
        label_2 = render.Text(0.5, 0.3, "Choose 4-10 words related to the item.")
        label_2.color = self.theme.dark
        adjectives_label = render.Text(0.5, 0.5, "")
        def adjectives_label_func():
            return ", ".join(adjectives_box.text.split(" ")).replace("+", " ")
        adjectives_label.color = self.theme.dark
        adjectives_label.fontsize = 16
        adjectives_label.text_func = adjectives_label_func
        def last_scene():
            secretadjectives = adjectives_box.text.split(" ")
            self.secretadjectives = [adj for adj in secretadjectives if adj]
            self.draw_scene()
        ok_button = render.TextButton(0.5, 0.6, 128, 32, "OK", last_scene)

    def make_label(self, x, y, text, binding) -> "render.Text":
        label = render.Text(x, y, text)
        label.bind_to(binding)
        label.fontsize = 16
        label.color = self.theme.dark
        label.outline_color = self.theme.light
        return label

    def get_dict(self):
        out_dict = {
            "item_name": self.item_name,
            "base": True,
            "power": self.power,
            "size": self.size,
            "kinds": self.kinds,
            "wearable": self.wearable,
            "description": self.description,
            "cost": self.cost,
            "onhit_states": self.onhit_states,
            "wear_states": self.wear_states,
            "consume_states": self.consume_states,
            "secret_states": self.secret_states,
            "secretadjectives": self.secretadjectives,
            "forbiddencode": False,
            "use": [],
            "inheritpower": self.inheritpower,
            "adjectives": self.adjectives,
            "code": self.code if self.code else None,
            "attached_skills": [],
            "prototype_name": self.prototype_name,
            "creator": client.dic["username"],
            "interests": self.interests,
            "interests_rarity": self.interests_rarity,
            "tiles": self.tiles,
            "tiles_rarity": self.tiles_rarity,
            "display_name": self.display_name,
        }
        return out_dict

    def verify_and_submit(self):
        if self.power == 0: return "Power cannot be 0."
        if self.size == 0: return "Size cannot be 0."
        if not self.kinds: return "You must choose at least one kind. If none make sense, save and ask the dev to add another."
        if not self.description: return "Please include a description for your item."
        if len(self.cost) == 1: return "Include at least one other grist type for your item to cost."
        if len(self.secretadjectives) < 4: return "Please include at least 4 secret adjectives for your item."
        if self.code:
            if not binaryoperations.is_valid_code(self.code): return "Invalid captchalogue code."
        if len(self.interests+self.tiles) == 0: return "Include at least once place for your item to spawn, and interest or a room."
        reply = client.requestplus(intent="submit_item", content={"item_name": self.item_name, "item_dict": self.get_dict()})
        if reply != "True": return reply
        else: return True

    def save(self):
        util.saved_items[self.item_name] = self.get_dict()
        util.writejson(util.saved_items, "saved_items")

    def autosave(self):
        util.saved_items["autosave"] = self.get_dict()
        util.writejson(util.saved_items, "saved_items")

    def loadinfo(self, item_name, load_dict):
        self.__dict__.update(load_dict)
        self.item_name = item_name
        if "item_name" in load_dict: self.item_name = load_dict["item_name"]
        if self.code is None: self.code = ""

    def load(self, item_name):
        assert item_name in util.saved_items
        load_dict = util.saved_items[item_name]
        self.loadinfo(item_name, load_dict)

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
                             search: Optional[str]=None, image_path_func: Optional[Callable]=None, image_scale=1.0, option_active_func: Optional[Callable]=None,
                             reload_on_button_press=False):
    args = (options, button_func_constructor, label, last_scene, theme, page, search, image_path_func, image_scale, option_active_func, reload_on_button_press)
    suburb.new_scene()
    def wrap_button_func_with_reload(button_func):
        def wrapped():
            button_func()
            show_options_with_search(*args)
        return wrapped
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
        button_func = button_func_constructor(option)
        if reload_on_button_press:
            button_func = wrap_button_func_with_reload(button_func)
        button = render.TextButton(0.5, y, 196, 32, option, button_func)
        if option_active_func is not None and option_active_func(option):
            button.fill_color = theme.light
        if image_path_func is not None:
            image = render.Image(0.4, y, image_path_func(option))
            image.scale = image_scale
    if page != 0:
        def previous_page(): 
            show_options_with_search(options, button_func_constructor, label, last_scene, theme, page-1, search_bar.text, image_path_func, image_scale, option_active_func, reload_on_button_press)
        previous_page_button = render.TextButton(0.5, 0.15, 32, 32, "▲", previous_page)
    if possible_options[(page+1)*OPTIONS_PER_PAGE:(page+2)*OPTIONS_PER_PAGE]:
        def next_page(): 
            show_options_with_search(options, button_func_constructor, label, last_scene, theme, page+1, search_bar.text, image_path_func, image_scale, option_active_func, reload_on_button_press)
        next_page_button = render.TextButton(0.5, 0.8, 32, 32, "▼", next_page)
    search_bar = render.InputTextBox(0.5, 0.9)
    def search_func():
        show_options_with_search(options, button_func_constructor, label, last_scene, theme, page, search_bar.text, image_path_func, image_scale, option_active_func, reload_on_button_press)
    search_bar.key_press_func = search_func
    if search is not None: 
        search_bar.active = True
        search_bar.text = search
    backbutton = render.Button(0.1, 0.92, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", last_scene)