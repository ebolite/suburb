from typing import Optional, Union

import client
import render
import config

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
    
    def get_maximum_vial(self, vial_name) -> int:
        return self.vials[vial_name]["maximum"]
    
    def get_starting_vial(self, vial_name) -> int:
        return self.vials[vial_name]["starting"]

    def get_skill(self, skill_name) -> Skill:
        return Skill(skill_name, self.known_skills[skill_name])

    @property
    def available_actions(self) -> int:
        actions = self.actions
        for skill_name in self.submitted_actions:
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
    def submitted_actions(self) -> dict:
        return self.griefer_dict["submitted_actions"]
    
    @property
    def known_skills(self) -> dict[str, dict]:
        return self.griefer_dict["known_skills"]

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
        return self.griefer_dict["stats"]

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
        self.griefers: dict[str, Griefer] = {}
        self.vials: dict[str, render.Vial] = {}
        self.selected_target: Optional[str] = None
        self.selected_skill: Optional[str] = None
        self.verify_griefers()

    def add_griefer(self, griefer_name):
        if griefer_name in self.griefers: return
        self.griefers[griefer_name] = Griefer(griefer_name, self)

    def verify_griefers(self):
        for griefer_name in self.strife_dict["griefers"]:
            if griefer_name not in self.griefers:
                self.add_griefer(griefer_name)

    def draw_scene(self):
        for griefer_name in self.griefers:
            griefer = self.griefers[griefer_name]
            # todo: make positions differ with more griefers
            # todo: flip sprites on different team
            if griefer.team == "blue":
                pos = (0.33, 0.5)
            else:
                pos = (0.66, 0.5)
            if griefer.type != "player":
                sprite = render.Enemy(*pos, griefer)
                self.griefer_sprites[griefer_name] = sprite
            else:
                sprite = render.PlayerGriefer(*pos, griefer)
                self.griefer_sprites[griefer_name] = sprite
        # todo: make skill categories
        for i, skill_name in enumerate(self.player_griefer.known_skills):
            y = 200 + 48*i
            def button_func(): self.selected_skill = skill_name
            skill_button = render.TextButton(4, y, 196, 32, f">{skill_name.upper()}", button_func)
            skill_button.absolute = True
        self.update_vials()
        render.update_check.append(self)

    def update(self):
        ...

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
        vial_x = 0.25
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

    @property
    def turn_num(self) -> int:
        return self.strife_dict["turn_num"]

    @property
    def player_griefer(self) -> Griefer:
        return self.griefers[client.dic["character"]]

    @property
    def submitted_actions(self) -> dict[str, list[dict]]:
        return self.strife_dict["submitted_actions"]
    

    