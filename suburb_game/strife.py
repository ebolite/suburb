from typing import Optional, Union
import pygame
import math
import numpy as np
import random
import time

import client
import render
import config
import suburb
import themes

class Skill():
    def __init__(self, name: str, skill_dict: dict):
        self.name: str = name
        self.category: str = skill_dict["category"]
        self.action_cost: int = skill_dict["action_cost"]
        self.num_targets: int = skill_dict["num_targets"]
        self.cooldown: int = skill_dict["cooldown"]
        self.damage_formula: str = skill_dict["damage_formula"]
        self.user_skill: Optional[dict] = skill_dict["user_skill"]
        self.additional_skill: Optional[dict] = skill_dict["additional_skill"]
        self.valid_targets: list[str] = skill_dict["valid_targets"]
        self.costs: dict[str, int] = skill_dict["costs"]
        self.description = skill_dict["description"]
        self.usable = skill_dict["usable"]

class Npc():
    def __init__(self, name, npc_dict):
        self.name = name
        self.nickname = npc_dict["nickname"]
        self.power = npc_dict["power"]
        self.type = npc_dict["type"]

class Griefer():
    def __init__(self, name, strife: "Strife"):
        self.name = name
        self.strife = strife

    def get_vial(self, vial_name) -> int:
        return self.vials[vial_name]["current"]
    
    def get_usable_vial(self, vial_name: str) -> int:
        total = self.get_vial(vial_name)
        for skill in self.submitted_skills_list:
            if vial_name in skill.costs:
                total -= skill.costs[vial_name]
        return total
    
    def get_state_duration(self, state_name) -> int:
        return self.states[state_name]["duration"]
    
    def get_state_potency(self, state_name) -> float:
        return self.states[state_name]["potency"]
    
    def get_state_tooltip(self, state_name) -> str:
        try:
            return self.states[state_name]["tooltip"]
        except KeyError:
            return ""
        
    def is_state_passive(self, state_name) -> bool:
        return self.states[state_name]["passive"]
    
    def can_pay_costs(self, costs: dict[str, int]) -> bool:
        for vial_name in costs:
            if self.get_usable_vial(vial_name) < costs[vial_name]: return False
        return True
    
    def can_use_skill(self, skill: Skill) -> bool:
        if not skill.usable: return False
        if not self.can_pay_costs(skill.costs): return False
        if self.get_skill_cooldown(skill) > 0: return False
        if self.available_actions < skill.action_cost: return False
        return True
    
    def get_skill_cooldown(self, skill: Skill) -> int:
        cooldown = 0
        if skill.name not in self.skill_cooldowns:
            cooldown = 0
        else:
            cooldown = self.skill_cooldowns[skill.name]
        for submitted_skill in self.submitted_skills_list:
            if submitted_skill.name == skill.name:
                cooldown += skill.cooldown
        return cooldown
    
    def get_maximum_vial(self, vial_name) -> int:
        return self.vials[vial_name]["maximum"]
    
    def get_starting_vial(self, vial_name) -> int:
        return self.vials[vial_name]["starting"]

    def get_skill(self, skill_name) -> Skill:
        return Skill(skill_name, self.known_skills[skill_name])

    def is_state_affected(self, state_name) -> bool:
        if state_name in self.states: return True
        else: return False

    @property
    def available_actions(self) -> int:
        actions = self.actions
        for skill_dict in self.submitted_skills:
            skill_name = skill_dict["skill_name"]
            skill = self.get_skill(skill_name)
            actions -= skill.action_cost
        return actions

    @property
    def griefer_dict(self) -> dict:
        return self.strife.strife_dict["griefers"][self.name]

    @property
    def symbol_dict(self) -> dict:
        return self.griefer_dict["symbol_dict"]
    
    @property
    def submitted_skills(self) -> list[dict]:
        return self.griefer_dict["submitted_skills"]
    
    @property
    def submitted_skills_list(self) -> list[Skill]:
        out = []
        for skill_dict in self.submitted_skills:
            skill_name = skill_dict["skill_name"]
            out.append(Skill(skill_name, self.known_skills[skill_name]))
        return out
    
    @property
    def known_skills(self) -> dict[str, dict]:
        return self.griefer_dict["known_skills"]
    
    @property
    def known_skills_list(self) -> list[Skill]:
        return [Skill(skill_name, self.known_skills[skill_name]) for skill_name in self.known_skills]

    @property
    def ready(self) -> bool:
        return self.griefer_dict["ready"]

    @property
    def skill_categories(self) -> dict[str, list[Skill]]:
        categories: dict[str, list[Skill]] = {"none": []}
        for skill in self.known_skills_list:
            if skill.category not in categories: categories[skill.category] = []
            categories[skill.category].append(skill)
        return categories
    
    @property
    def skill_cooldowns(self) -> dict[str, int]:
        return self.griefer_dict["skill_cooldowns"]

    @property
    def player_name(self) -> Optional[str]:
        return self.griefer_dict["player_name"]
    
    @property
    def team(self) -> str:
        return self.griefer_dict["team"]
    
    @property
    def nickname(self) -> str:
        return self.griefer_dict["nickname"]
    
    @property
    def actions(self) -> int:
        return self.griefer_dict["actions"]

    @property
    def stats(self) -> dict:
        return self.griefer_dict["stats_dict"]
    
    @property
    def states(self) -> dict:
        return self.griefer_dict["states_dict"]

    @property
    def vials(self) -> dict:
        return self.griefer_dict["vials_dict"]

    @property
    def grist_type(self) -> Optional[str]:
        return self.griefer_dict["grist_type"]

    @property
    def type(self) -> str:
        return self.griefer_dict["type"]

    @property
    def power(self) -> int:
        return self.stats["power"]

class Strife():
    hotkeys = {
        0: pygame.K_q,
        1: pygame.K_w,
        2: pygame.K_e,
        3: pygame.K_r,
        4: pygame.K_t,
        5: pygame.K_a,
        6: pygame.K_s,
        7: pygame.K_d,
        8: pygame.K_f,
        9: pygame.K_g,
    }
    hotkey_labels = ["q", "w", "e", "r", "t", "a", "s", "d", "f", "g"]

    def __init__(self, strife_dict: Optional[dict]=None):
        print("init")
        if strife_dict is None: strife_dict = client.requestdic(intent="strife_info")
        self.strife_dict = strife_dict
        self.griefer_sprites: dict[str, Union[render.Enemy, render.PlayerGriefer]] = {}
        self.vials: dict[str, render.Vial] = {}
        self.selected_targets: list[str] = []
        self.selected_skill_name: Optional[str] = None
        self.hovered_skill_name: Optional[str] = None
        self.theme = suburb.current_theme()
        self.layer_2_buttons: list[render.UIElement] = []
        self.last_update = time.time()
        self.tooltips: list[render.Text] = []
        self.last_displayed_skill_name: str = ""
        render.ui_elements.append(self)

    def update_strife_dict(self, strife_dict):
        if not strife_dict:
            spoils_dict = client.requestdic(intent="collect_spoils")
            unclaimed_grist = spoils_dict["unclaimed_grist"]
            unclaimed_rungs = spoils_dict["unclaimed_rungs"]
            if unclaimed_grist or unclaimed_rungs:
                suburb.spoils(unclaimed_grist, unclaimed_rungs)
            else:
                suburb.map_scene()
            return
        self.strife_dict = strife_dict
        for griefer_name in self.griefer_sprites.copy():
            if griefer_name not in self.griefers:
                self.griefer_sprites[griefer_name].delete()
                self.griefer_sprites.pop(griefer_name)
        for griefer_name in self.griefers:
            if griefer_name not in self.griefer_sprites:
                self.make_griefer_sprites()

    def make_griefer_sprites(self):
        for sprite in self.griefer_sprites.values():
            sprite.delete()
        self.griefer_sprites = {}
        blue_sprites: list[Union["render.Enemy", "render.PlayerGriefer"]] = []
        red_sprites: list[Union["render.Enemy", "render.PlayerGriefer"]] = []
        scale = 1.0
        for griefer_name in self.griefers:
            griefer = self.get_griefer(griefer_name)
            sprite = self.make_griefer_sprite(griefer)
            if griefer.team == "blue": blue_sprites.append(sprite)
            else: red_sprites.append(sprite)
            sprite.send_to_bottom()
        for sprite in red_sprites + blue_sprites:
            if scale > 0.66 and sprite.get_height() > 800: scale = 0.66
            elif scale > 0.75 and sprite.get_height() > 500: scale = 0.75
        if len(red_sprites+blue_sprites) > 4 and scale > 0.75: scale = 0.75
        if len(red_sprites+blue_sprites) > 9 and scale > 0.66: scale = 0.66
        for sprite in red_sprites + blue_sprites:
            sprite.scale = scale
        self.reposition_sprites(red_sprites, "right", scale)
        self.reposition_sprites(blue_sprites, "left", scale)

    def reposition_sprites(self, sprites_list: list[Union["render.Enemy", "render.PlayerGriefer"]], direction: str, scale: float):
        sprites_xy = []
        for i, sprite in enumerate(sprites_list):
            if i == 0:
                center_offset = 0.16 if direction == "right" else -0.16
                starting_x = 0.5 + (center_offset * scale)
                sprite.x = starting_x
                sprite_x = starting_x * self.canvas.w - sprite.get_width()//2
                sprite_y = sprite.y * self.canvas.h - sprite.get_height()//2
                sprites_xy.append((sprite_x, sprite_y))
                if isinstance(sprite, render.Enemy):
                    sprite.rect_y_offset = sprite.get_height()//3 * -1
                continue
            previous_sprite = sprites_list[i-1]
            old_width = previous_sprite.get_width() if isinstance(previous_sprite, render.Enemy) else 400
            dx = int(old_width)
            old_x, old_y = sprites_xy[i-1]
            new_x = old_x + dx if direction == "right" else old_x - dx
            new_y = render.SCREEN_HEIGHT//2 + 100
            if isinstance(sprite, render.Enemy):
                new_y -= sprite.get_height()
            else:
                new_y -= 250
            sprite.x, sprite.y = new_x, new_y
            sprite.absolute = True
            sprites_xy.append((new_x, new_y))

    def make_griefer_sprite(self, griefer: Griefer) -> Union["render.Enemy", "render.PlayerGriefer"]:
        # todo: make positions differ with more griefers
        # todo: flip sprites on different team
        blue_pos = (0.33, 0.5)
        red_pos = (0.66, 0.5)
        if griefer.team == "blue":
            pos = blue_pos
        else:
            pos = red_pos
        if griefer.type != "player":
            sprite = render.Enemy(*pos, griefer)
            sprite.bind_to(self.canvas)
            self.griefer_sprites[griefer.name] = sprite
        else:
            sprite = render.PlayerGriefer(*pos, griefer)
            sprite.bind_to(self.canvas)
            self.griefer_sprites[griefer.name] = sprite
        return sprite

    def get_skill_button_func(self, skill_name):
        def button_func(): 
            skill = self.player_griefer.get_skill(skill_name)
            if not self.player_griefer.can_use_skill(skill): return
            if self.player_griefer.available_actions < skill.action_cost: return
            if skill_name != self.selected_skill_name: self.selected_targets = []
            self.selected_skill_name = skill_name
            if self.selected_skill is not None and len(self.selected_skill.valid_targets) == 1:
                self.selected_targets.append(self.selected_skill.valid_targets[0])
                self.submit_skill()
            self.clear_next_layer_buttons()
        return button_func
    
    def get_skill_hover_func(self, skill_name):
        def hover_func():
            self.hovered_skill_name = skill_name
        return hover_func
    
    def get_skill_inactive_condition(self, skill_name):
        def inactive_condition():
            skill = self.player_griefer.get_skill(skill_name)
            if self.player_griefer.can_use_skill(skill):
                return False
            else:
                return True
        return inactive_condition
    
    def get_category_button_func(self, category_name):
        def button_func():
            self.make_next_layer_buttons(category_name)
        return button_func

    def make_skill_button(self, skill: Skill, x: int, y: int) -> "render.TextButton":
        if self.player_griefer.get_skill_cooldown(skill) > 0:
            button_text = f"{'[I] ' if skill.action_cost <= 0 else ''}>{skill.name.upper()} (CD{self.player_griefer.get_skill_cooldown(skill)})"
        else:
            button_text = f"{'[I] ' if skill.action_cost <= 0 else ''}>{skill.name.upper()}"
        skill_button = render.TextButton(x, y, 196, 32, button_text, self.get_skill_button_func(skill.name))
        skill_button.absolute = True
        skill_button.fill_color = themes.default.white
        skill_button.outline_color = config.get_category_color(skill.category)
        skill_button.text_color = config.get_category_color(skill.category)
        skill_button.hover_color = pygame.Color(225, 225, 225)
        skill_button.inactive_condition = self.get_skill_inactive_condition(skill.name)
        skill_button.hover_func = self.get_skill_hover_func(skill.name)
        return skill_button

    def make_hotkey_label(self, button: "render.TextButton", i, category_name, first_layer=True):
        if i not in self.hotkeys: return
        hotkey = self.hotkeys[i]
        label = self.hotkey_labels[i]
        button.click_keys.append(hotkey)
        hotkey_label = render.Text(0.9, 0.5, f"({label})")
        hotkey_label.bind_to(button)
        hotkey_label.fontsize = 12
        hotkey_label.color = config.get_category_color(category_name)
        if first_layer:
            def inactive_condition():
                if self.layer_2_buttons: return True
                else: return False
            button.hotkey_inactive_condition = inactive_condition

    def draw_scene(self):
        bar_br = 30
        self.canvas = render.SolidColor(0.5, 0.5, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, self.theme.light)
        self.canvas.right_click_pan = True
        self.canvas.absolute = True
        render.update_check.remove(self.canvas)
        render.always_on_bottom_check.append(self.canvas)
        self.make_griefer_sprites()
        top_bar = render.SolidColor(0, -bar_br, render.SCREEN_WIDTH, 120+bar_br, self.theme.light)
        top_bar.outline_color = self.theme.dark
        top_bar.border_radius = bar_br
        # todo: make skill categories
        x = 4
        y = 200
        i = 0
        for category_name in self.player_griefer.skill_categories:
            if category_name == "none": continue
            category_button = render.TextButton(4, y, 196, 32, f"{category_name.upper()}", self.get_category_button_func(category_name))
            category_button.absolute = True
            category_button.fill_color = themes.default.white
            category_button.outline_color = config.get_category_color(category_name)
            category_button.text_color = config.get_category_color(category_name)
            self.make_hotkey_label(category_button, i, category_name)
            y += 48
            i += 1
        for skill in self.player_griefer.skill_categories["none"]:
            skill_button = self.make_skill_button(skill, x, y)
            self.make_hotkey_label(skill_button, i, "none")
            y += 48
        def submit_button_func():
            reply = client.requestdic(intent="strife_ready")
            self.update_strife_dict(reply)
        def revert_button_func():
            reply = client.requestdic(intent="unsubmit_skill")
            self.update_strife_dict(reply)
        def button_condition():
            return not self.player_griefer.ready
        revert_button = render.TextButton(0.85, 0.2, 196, 32, ">REVERT", revert_button_func)
        revert_button.draw_condition = button_condition
        revert_button_label = render.Text(0.5, 1.2, "(escape)")
        revert_button_label.bind_to(revert_button)
        revert_button_label.fontsize = 12
        revert_button_label.color = self.theme.dark
        submit_button = render.TextButton(0.5, 0.78, 256, 48, ">READY", submit_button_func)
        submit_button.draw_condition = button_condition
        submit_button.text_color = self.theme.dark
        submit_button.fontsize = 32
        submit_button.click_keys = [pygame.K_SPACE]
        submit_button_label = render.Text(0.5, 1.15, "(space)")
        submit_button_label.bind_to(submit_button)
        submit_button_label.fontsize = 12
        submit_button_label.color = self.theme.dark
        self.strife_log_window = render.LogWindow(None, None, lines_to_display=5, log_list=self.strife_log)
        self.submitted_skills_window = render.LogWindow(None, None, lines_to_display=4, x=1080, width=300, log_list=[])
        self.submitted_skills_window.background_color = self.theme.dark
        self.submitted_skills_window.text_color = self.theme.black
        self.remaining_skills_text = render.Text(0.8425, 0.14, "")
        self.remaining_skills_text.text_func = lambda *args: f"Actions left: {self.player_griefer.available_actions}"
        self.remaining_skills_text.color = self.theme.dark
        self.remaining_skills_text.fontsize = 28
        def currently_selected_text_func():
            if self.player_griefer.ready: return "Waiting for others..."
            elif self.selected_skill is None: return ""
            else: return f"{self.selected_skill.name.upper()}? (target {self.selected_skill.num_targets - len(self.selected_targets)})"
        self.selected_skill_text = render.Text(0.5, 0.19, "")
        self.selected_skill_text.text_func = currently_selected_text_func
        self.selected_skill_text.color = self.theme.dark
        self.make_skill_info_window()
        self.update_submitted_skills()
        self.update_vials()
        render.update_check.append(self)
        render.key_check.append(self)

    def make_skill_info_window(self):
        PADDING = 8
        BOX_HEIGHT = 120
        self.hovered_skill_info_box = render.SolidColor(0, render.SCREEN_HEIGHT-BOX_HEIGHT, render.SCREEN_WIDTH, BOX_HEIGHT, self.theme.light)
        self.hovered_skill_info_box.outline_color = self.theme.dark
        self.skill_name_label = render.Text(PADDING, PADDING, "")
        self.skill_name_label.color = self.theme.dark
        self.skill_name_label.absolute = True
        self.skill_name_label.bind_to(self.hovered_skill_info_box)

    def make_skill_tooltip_display(self):
        PADDING = 8
        LINE_PADDING = 4
        LINE_CHARACTERS = 55
        assert self.hovered_skill is not None
        for element in self.tooltips.copy():
            element.delete()
            self.tooltips.remove(element)
        tooltip: str = self.hovered_skill.description
        lines: list[list[str]] = [[]]
        index = 0
        for word in tooltip.split(" "):
            if len(" ".join(lines[index])) + len(word) > LINE_CHARACTERS: 
                index += 1
                lines.append([])
            lines[index].append(word)
        joined_lines: list[str] = [" ".join(line) for line in lines]
        fontsize = min(self.hovered_skill_info_box.h//len(joined_lines) - LINE_PADDING, 20)
        for i, line in enumerate(joined_lines):
            line_text = render.Text(PADDING, PADDING*5 + (fontsize+LINE_PADDING)*i, line)
            line_text.color = self.theme.dark
            line_text.absolute = True
            line_text.fontsize = fontsize
            line_text.bind_to(self.hovered_skill_info_box)
            self.tooltips.append(line_text)
        self.last_displayed_skill_name = self.hovered_skill.name

    def update_skill_info_window(self):
        if self.hovered_skill is None:
            self.skill_name_label.text = "SELECT A TECHNIQUE"
        else:
            self.skill_name_label.text = f"{self.hovered_skill.name.upper()}"
            if self.hovered_skill.name != self.last_displayed_skill_name:
                self.make_skill_tooltip_display()

    def make_next_layer_buttons(self, category_name: str):
        self.clear_next_layer_buttons()
        x = 204
        for i, skill in enumerate(self.player_griefer.skill_categories[category_name]):
            y = 200 + 48*i
            skill_button = self.make_skill_button(skill, x, y)
            self.make_hotkey_label(skill_button, i, category_name, first_layer=False)
            self.layer_2_buttons.append(skill_button)

    def clear_next_layer_buttons(self):
        for button in self.layer_2_buttons.copy():
            button.delete()
            self.layer_2_buttons.remove(button)

    def update(self):
        if time.time() - self.last_update > 1:
            reply = client.requestdic(intent="strife_info")
            self.update_strife_dict(reply)
            self.last_update = time.time()
        if self.strife_log_window.log_list != self.strife_log:
            self.strife_log_window.log_list = self.strife_log
            self.strife_log_window.update_logs()
        # if we clicked off the menu, close the menu
        if pygame.mouse.get_pressed()[0] and self.layer_2_buttons:
            for button in self.layer_2_buttons:
                if button.is_mouseover(): break
            else:
                self.clear_next_layer_buttons()
        if self.strife_log_window.is_mouseover() and self.strife_log_window.lines_to_display == 5:
            self.strife_log_window.lines_to_display = 30
            self.strife_log_window.update_logs()
        elif not self.strife_log_window.is_mouseover() and self.strife_log_window.lines_to_display > 5:
            self.strife_log_window.lines_to_display = 5
            self.strife_log_window.update_logs()
        self.update_submitted_skills()
        self.update_skill_info_window()
        self.update_vials()

    def keypress(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.layer_2_buttons: self.clear_next_layer_buttons()
            elif self.selected_skill_name is not None: self.selected_skill_name = None
            else: 
                reply = client.requestdic(intent="unsubmit_skill")
                self.update_strife_dict(reply)

    def delete(self):
        if self in render.ui_elements: render.ui_elements.remove(self)
        for check_list in render.checks:
            if self in check_list:
                check_list.remove(self)

    def click_griefer(self, griefer: Griefer):
        print(f"griefer clicked {griefer.name}")
        if self.selected_skill is None: return
        print("add to targets")
        self.selected_targets.append(griefer.name)
        if len(self.selected_targets) == self.selected_skill.num_targets:
            self.submit_skill()

    def submit_skill(self):
        reply = client.requestplusdic(intent="submit_strife_action", content={"skill_name": self.selected_skill_name, "targets": self.selected_targets})
        self.update_strife_dict(reply)
        self.selected_skill_name = None
        self.selected_targets = []

    def update_submitted_skills(self):
        submitted_skills_log = ["CURRENT ACTIONS:"]
        for i, skill_dict in enumerate(self.player_griefer.submitted_skills):
            skill_name = skill_dict["skill_name"]
            skill = self.player_griefer.get_skill(skill_name)
            submitted_skills_log.append(f"{i+1}. {skill_name} ({skill.action_cost})")
        if len(submitted_skills_log) == 1: submitted_skills_log.append("...")
        while len(submitted_skills_log) < self.submitted_skills_window.lines_to_display:
            submitted_skills_log.append("")
        if self.submitted_skills_window.log_list != submitted_skills_log:
            self.submitted_skills_window.log_list = submitted_skills_log
            self.submitted_skills_window.update_logs()

    def update_vials(self):
        for vial_name in self.player_griefer.vials:
            hidden = config.vials[vial_name]["hidden"]
            if vial_name in self.vials: 
                continue
            elif hidden and self.player_griefer.get_vial(vial_name) == self.player_griefer.get_starting_vial(vial_name): continue
            else: self.make_vials()

    def make_vials(self):
        for vial_name in self.vials:
            self.vials[vial_name].delete()
        self.vials = {}
        vial_x = 0.1
        vial_y = 0
        vial_y_increase = 0.035
        for vial_name in self.player_griefer.vials:
            hidden = config.vials[vial_name]["hidden"]
            if hidden and self.player_griefer.get_vial(vial_name) == self.player_griefer.get_starting_vial(vial_name): continue
            vial_y += vial_y_increase
            new_vial = render.Vial(vial_x, vial_y, 150, self.player_griefer, vial_name)
            new_vial.absolute = False
            self.vials[vial_name] = new_vial

    def get_griefer(self, griefer_name) -> Griefer:
        return Griefer(griefer_name, self)

    @property
    def selected_skill(self) -> Optional[Skill]:
        if self.selected_skill_name is None: return None
        skill = self.player_griefer.get_skill(self.selected_skill_name)
        return skill
    
    @property
    def hovered_skill(self) -> Optional[Skill]:
        if self.hovered_skill_name is None: return None
        skill = self.player_griefer.get_skill(self.hovered_skill_name)
        return skill

    @property
    def turn_num(self) -> int:
        return self.strife_dict["turn_num"]
    
    @property
    def strife_log(self) -> list[str]:
        return self.strife_dict["strife_log"]

    @property
    def player_griefer(self) -> Griefer:
        return self.get_griefer(client.dic["character"])
    
    @property
    def griefers(self) -> dict:
        return self.strife_dict["griefers"]

    @property
    def submitted_skills(self) -> dict[str, list[dict]]:
        return self.strife_dict["submitted_skills"]
    

    