from typing import Callable

import client
import util
import suburb
import render
import sylladex

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

    def request_npc_interaction(self, npc: Npc, additional_data={}):
        return client.requestplus(intent="interact_npc", content={"interaction_name": self.name, "npc_name": npc.name, "additional_data": additional_data})

    def use(self, npc: Npc, last_scene: Callable):
        reply = self.request_npc_interaction(npc)
        util.log(reply)

NpcInteraction("talk")
NpcInteraction("follow")

class NpcPrototype(NpcInteraction):
    def use(self, npc: Npc, last_scene: Callable):
        suburb.new_scene()
        render.LogWindow(None)
        valid_instances = client.requestdic(intent="prototype_targets")
        print(valid_instances)
        syl = sylladex.Sylladex.current_sylladex()
        syl.update_deck()
        util.log(f"What will you prototype {npc.nickname if npc.nickname != 'kernelsprite' else f'the kernelsprite'} with?")
        def get_button_func(target_instance: sylladex.Instance):
            def button_func():
                if target_instance.name in syl.deck:
                    syl.remove_instance(target_instance.name)
                reply = self.request_npc_interaction(npc, {"instance_name": target_instance.name})
                util.log(reply)
                last_scene()
            return button_func
        for i, target_instance_name in enumerate(valid_instances.keys()):
            button_height = 33
            button_width = 400
            x = int(render.SCREEN_WIDTH*0.5 - button_width*0.5)
            y = 120 + (button_height + 10)*i
            target_instance = sylladex.Instance(target_instance_name, valid_instances[target_instance_name])
            if target_instance_name in syl.deck: display_name = f"(Sylladex) {target_instance.display_name()}"
            else: display_name = target_instance.display_name()
            button_func = get_button_func(target_instance)
            choose_button = render.TextButton(x, y, button_width, button_height, display_name, button_func)
            choose_button.absolute = True
            choose_button.truncate_text = True
        backbutton = render.Button(0.1, 0.07, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", last_scene)
NpcPrototype("prototype")