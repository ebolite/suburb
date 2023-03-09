from typing import Optional, Union

import client
import render
import config

class Npc():
    def __init__(self, name, npc_dict):
        self.name = name
        self.nickname = npc_dict["nickname"]
        self.power = npc_dict["power"]
        self.type = npc_dict["type"]

class Griefer():
    def __init__(self, name, griefer_dict):
        self.name = name
        self.griefer_dict = griefer_dict

    def get_vial(self, vial_name) -> int:
        return self.vials[vial_name]["current"]
    
    def get_maximum_vial(self, vial_name) -> int:
        print(self.griefer_dict)
        print(self.vials)
        return self.vials[vial_name]["maximum"]
    
    def get_starting_vial(self, vial_name) -> int:
        return self.vials[vial_name]["starting"]

    @property
    def symbol_dict(self) -> dict:
        return self.griefer_dict["symbol_dict"]
    
    @property
    def player_name(self) -> Optional[str]:
        return self.griefer_dict["player_name"]
    
    @property
    def nickname(self) -> str:
        return self.griefer_dict["nickname"]
    
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
        self.vials: dict[str, render.Vial] = {}

    def draw_scene(self):
        for griefer_name in self.griefers:
            griefer = self.griefers[griefer_name]
            if griefer.type != "player":
                grist_type = griefer.grist_type or "build"
                sprite = render.Enemy(0.66, 0.5, griefer)
                self.griefer_sprites[griefer_name] = sprite
            else:
                sprite = render.PlayerGriefer(0.33, 0.5, griefer)
                self.griefer_sprites[griefer_name] = sprite
        self.update_vials()

    def update_vials(self):
        for vial_name in self.player_griefer.vials:
            hidden = config.vials[vial_name]["hidden"]
            if vial_name in self.vials: 
                self.vials[vial_name].current = self.player_griefer.get_vial(vial_name)
                self.vials[vial_name].maximum = self.player_griefer.get_maximum_vial(vial_name)
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
            new_vial = render.Vial(vial_x, vial_y, 150, self.player_griefer.get_vial(vial_name), self.player_griefer.get_vial(vial_name), vial_name)
            new_vial.absolute = False
            self.vials[vial_name] = new_vial

    @property
    def turn_num(self) -> int:
        return self.strife_dict["turn_num"]

    @property
    def griefers(self) -> dict[str, Griefer]:
        return {griefer_name:Griefer(griefer_name, self.strife_dict["griefers"][griefer_name]) for griefer_name in self.strife_dict["griefers"]}

    @property
    def player_griefer(self) -> Griefer:
        return self.griefers[client.dic["character"]]

    @property
    def submitted_actions(self) -> dict[str, list[dict]]:
        return self.strife_dict["submitted_actions"]
    

    