from typing import Optional

import client
import render

class Npc():
    def __init__(self, name, npc_dict):
        self.name = name
        self.nickname = npc_dict["nickname"]
        self.power = npc_dict["power"]
        self.type = npc_dict["type"]

class Griefer():
    def __init__(self, name, griefer_dict):
        self.name = name
        self.type: str = griefer_dict["type"]
        self.grist_type: Optional[str] = griefer_dict["grist_type"]
        self.symbol_dict: dict = griefer_dict["symbol_dict"]
        self.player_name: Optional[str] = griefer_dict["player_name"]
        self.nickname: str = griefer_dict["nickname"]
        self.stats: dict = griefer_dict["stats_dict"]
        self.vials: dict = griefer_dict["vials_dict"]

    @property
    def power(self):
        return self.stats["power"]

class Strife():
    def __init__(self, strife_dict):
        self.griefers = {griefer_name:Griefer(griefer_name, strife_dict["griefers"][griefer_name]) for griefer_name in strife_dict["griefers"]}
        self.turn_num: int = strife_dict["turn_num"]
        self.submitted_actions: dict[str, list[dict]] = strife_dict["submitted_actions"]

def strife_scene(strife_dict: Optional[dict]=None):
    if strife_dict is None: strife_dict = client.requestdic(intent="strife_info")
    strife = Strife(strife_dict)
    for griefer_name in strife.griefers:
        griefer = strife.griefers[griefer_name]
        if griefer.type != "player":
            grist_type = griefer.grist_type or "build"
            sprite = render.Enemy(0.66, 0.5, grist_type, griefer.type)
        else:
            sprite = render.Symbol(0.33, 0.5, griefer.symbol_dict)