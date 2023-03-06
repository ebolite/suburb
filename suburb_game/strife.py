from typing import Optional

import client
import render

class Npc():
    def __init__(self, name, npc_dict):
        self.name = name
        self.nickname = npc_dict["nickname"]
        self.power = npc_dict["power"]
        self.type = npc_dict["type"]

def strife_scene(strife_dict: Optional[dict]=None):
    if strife_dict is None: strife_dict = client.requestdic(intent="strife_info")
    ...