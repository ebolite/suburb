from typing import Callable

import client
import util

npc_interactions: dict[str, "NpcInteraction"] = {}

class Npc():
    def __init__(self, name, npc_dict):
        self.name = name
        self.nickname = npc_dict["nickname"]
        self.power = npc_dict["power"]
        self.type = npc_dict["type"]
        self.interactions = npc_dict["interactions"]

    def get_npc_interaction_button(self, interaction_name: str, last_scene: Callable):
        if interaction_name not in npc_interactions: return lambda *args: util.log("Unimplemented")
        else:
            def button_func():
                npc_interactions[interaction_name].use(self, last_scene)
        return button_func

class NpcInteraction():
    def __init__(self, name):
        self.name = name
        npc_interactions[name] = self

    def request_npc_interaction(self, npc: Npc):
        return client.requestplus(intent="interact_npc", content={"interaction_name": self.name, "npc_name": npc.name})

    def use(self, npc: Npc, last_scene: Callable):
        pass

class NpcTalk(NpcInteraction):
    name = "talk"
    def use(self, npc: Npc, last_scene: Callable):
        reply = self.request_npc_interaction(npc)
        util.log(reply)
NpcTalk("talk")