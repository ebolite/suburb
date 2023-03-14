from typing import Optional, Union
import pygame

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
        return self.states[state_name]["tooltip"]
    
    def can_pay_costs(self, costs: dict[str, int]) -> bool:
        for vial_name in costs:
            if self.get_usable_vial(vial_name) < costs[vial_name]: return False
        return True
    
    def can_use_skill(self, skill: Skill) -> bool:
        if not self.can_pay_costs(skill.costs): return False
        if self.available_actions < skill.action_cost: return False
        return True
    
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
    def skill_categories(self) -> dict[str, list[Skill]]:
        categories: dict[str, list[Skill]] = {"none": []}
        for skill in self.known_skills_list:
            if skill.category not in categories: categories[skill.category] = []
            categories[skill.category].append(skill)
        return categories

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
    def __init__(self, strife_dict: Optional[dict]=None):
        print("init")
        if strife_dict is None: strife_dict = client.requestdic(intent="strife_info")
        self.strife_dict = strife_dict
        self.griefer_sprites: dict[str, Union[render.Enemy, render.PlayerGriefer]] = {}
        self.vials: dict[str, render.Vial] = {}
        self.selected_targets: list[str] = []
        self.selected_skill_name: Optional[str] = None
        self.theme = suburb.current_theme()
        self.layer_2_buttons: list[render.UIElement] = []
        render.ui_elements.append(self)

    def update_strife_dict(self, strife_dict):
        if not strife_dict:
            # todo: loot screen
            suburb.map_scene()
            return
        self.strife_dict = strife_dict
        for griefer_name in self.griefer_sprites:
            if griefer_name not in self.griefers:
                self.griefer_sprites[griefer_name].delete()
                self.griefer_sprites.pop(griefer_name)
        for griefer_name in self.griefers:
            if griefer_name not in self.griefer_sprites:
                self.make_griefer_sprite(self.get_griefer(griefer_name))

    def make_griefer_sprite(self, griefer: Griefer) -> Union["render.Enemy", "render.PlayerGriefer"]:
        # todo: make positions differ with more griefers
        # todo: flip sprites on different team
        if griefer.team == "blue":
            pos = (0.33, 0.5)
        else:
            pos = (0.66, 0.5)
        if griefer.type != "player":
            sprite = render.Enemy(*pos, griefer)
            self.griefer_sprites[griefer.name] = sprite
        else:
            sprite = render.PlayerGriefer(*pos, griefer)
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
        skill_button = render.TextButton(x, y, 196, 32, f">{skill.name.upper()}", self.get_skill_button_func(skill.name))
        skill_button.absolute = True
        skill_button.fill_color = themes.default.white
        skill_button.outline_color = config.get_category_color(skill.category)
        skill_button.text_color = config.get_category_color(skill.category)
        skill_button.hover_color = pygame.Color(225, 225, 225)
        skill_button.inactive_condition = self.get_skill_inactive_condition(skill.name)
        return skill_button

    def draw_scene(self):
        bar_br = 30
        top_bar = render.SolidColor(0, -bar_br, render.SCREEN_WIDTH, 120+bar_br, self.theme.light)
        top_bar.outline_color = self.theme.dark
        top_bar.border_radius = bar_br
        for griefer_name in self.griefers:
            griefer = self.get_griefer(griefer_name)
            self.make_griefer_sprite(griefer)
        # todo: make skill categories
        x = 4
        y = 200
        for category_name in self.player_griefer.skill_categories:
            if category_name == "none": continue
            category_button = render.TextButton(4, y, 196, 32, f"{category_name.upper()}", self.get_category_button_func(category_name))
            category_button.absolute = True
            category_button.fill_color = themes.default.white
            category_button.outline_color = config.get_category_color(category_name)
            category_button.text_color = config.get_category_color(category_name)
            y += 48
        for skill in self.player_griefer.skill_categories["none"]:
            self.make_skill_button(skill, x, y)
            y += 48
        def submit_button_func():
            reply = client.requestdic(intent="strife_ready")
            self.update_strife_dict(reply)
        def revert_button_func():
            reply = client.requestdic(intent="unsubmit_skill")
            self.update_strife_dict(reply)
        revert_button = render.TextButton(0.85, 0.2, 196, 32, ">REVERT", revert_button_func)
        submit_button = render.TextButton(0.85, 0.25, 196, 32, ">SUBMIT", submit_button_func)
        self.strife_log_window = render.LogWindow(None, None, lines_to_display=5, log_list=self.strife_log)
        self.submitted_skills_window = render.LogWindow(None, None, lines_to_display=4, x=1080, width=300, log_list=[])
        self.submitted_skills_window.background_color = self.theme.dark
        self.submitted_skills_window.text_color = self.theme.black
        self.remaining_skills_text = render.Text(0.8425, 0.14, "")
        self.remaining_skills_text.text_func = lambda *args: f"Actions left: {self.player_griefer.available_actions}"
        self.remaining_skills_text.color = self.theme.dark
        self.remaining_skills_text.fontsize = 28
        def currently_selected_text_func():
            if self.selected_skill is None: return ""
            else: return f"{self.selected_skill.name.upper()}? (target {self.selected_skill.num_targets - len(self.selected_targets)})"
        self.selected_skill_text = render.Text(0.5, 0.19, "")
        self.selected_skill_text.text_func = currently_selected_text_func
        self.selected_skill_text.color = self.theme.dark
        self.update_submitted_skills()
        self.update_vials()
        render.update_check.append(self)

    def make_next_layer_buttons(self, category_name: str):
        self.clear_next_layer_buttons()
        x = 204
        for i, skill in enumerate(self.player_griefer.skill_categories[category_name]):
            y = 200 + 48*i
            skill_button = self.make_skill_button(skill, x, y)
            self.layer_2_buttons.append(skill_button)

    def clear_next_layer_buttons(self):
        for button in self.layer_2_buttons.copy():
            button.delete()
            self.layer_2_buttons.remove(button)

    def update(self):
        if self.strife_log_window.log_list != self.strife_log:
            self.strife_log_window.log_list = self.strife_log
            self.strife_log_window.update_logs()
        # if we clicked off the menu, close the menu
        if pygame.mouse.get_pressed()[0] and self.layer_2_buttons:
            for button in self.layer_2_buttons:
                if button.is_mouseover(): break
            else:
                self.clear_next_layer_buttons()
        self.update_submitted_skills()
        self.update_vials()

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
            if vial_name == "hp": continue
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
    

    