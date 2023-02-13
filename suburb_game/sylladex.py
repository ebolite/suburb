from typing import Union, Optional

import client
import util
import render

moduses = {}

class Instance():
    def __init__(self, instance_name: str, instance_dict: dict):
        self.instance_name = instance_name
        self.item_name = instance_dict["item_name"]
        self.item_dict = instance_dict["item_dict"]
        self.power = self.item_dict["power"]
        self.size = self.item_dict["size"]
        self.code = self.item_dict["code"]
        self.kinds = self.item_dict["kinds"]

# the default fetch modus is array
class Modus():
    def __init__(self, name):
        self.eject_velocity = 3
        self.size_limit = 30
        self.modus_name = name
        self.front_sprite_path = ""
        self.back_sprite_path = ""
        moduses[name] = self

    def is_captchalogueable(self, instance: Instance, sylladex: "Sylladex") -> bool:
        return True
    
    def is_accessible(self, instance: Instance, sylladex: "Sylladex") -> bool:
        return True
    
    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.append(instance.instance_name)

    def remove_from_modus_data(self, instance_name: str, sylladex: "Sylladex"):
        if instance_name in sylladex.data_list: sylladex.data_list.remove(instance_name)
    
    def convert_from_deck(self, deck: dict, sylladex: "Sylladex") -> list[str]:
        invalid_instance_names = []
        for instance_name in deck:
            sylladex.data_list.append(instance_name)
        return invalid_instance_names
    
    def get_eject_velocity(self) -> int:
        return self.eject_velocity
    
    def draw_ui_bar(self, sylladex):
        sylladex_bar = render.Image(0, 0, "sprites/moduses/bar.png")
        sylladex_bar.absolute = True
        instances_length = len(sylladex.data_list)
        print(sylladex.data_list)
        for i, instance_name in enumerate(sylladex.data_list):
            x = (render.SCREEN_WIDTH / 2) - 109
            x += 125 * (i + 1 - instances_length/2)
            x = int(x)
            y = int(render.SCREEN_HEIGHT*0.80)
            card_thumb = render.Image(x, y, "sprites/moduses/array_card_thumb.png")
            card_thumb.absolute = True
            card_thumb.bind_to(sylladex_bar)
    
class Sylladex():
    def __init__(self, player_name: str, connection_host_port: str = f"{client.HOST}:{client.PORT}"):
        self.__dict__["player"] = player_name
        self.__dict__["host_port"] = connection_host_port
        if connection_host_port not in util.sylladexes:
            util.sylladexes[connection_host_port] = {}
        if player_name not in util.sylladexes[connection_host_port]:
            util.sylladexes[connection_host_port][player_name] = {}
        try:
            self.data_dict
            self.data_list
            self.deck: dict
        except KeyError:
            self.data_dict = {}
            self.data_list = []
            self.deck: dict = {}
            self.update_deck()

    def __getattr__(self, attr):
        return util.sylladexes[self.__dict__["host_port"]][self.__dict__["player"]][attr]
    
    def __setattr__(self, attr, value):
        util.sylladexes[self.__dict__["host_port"]][self.__dict__["player"]][attr] = value
        util.writejson(util.sylladexes, "sylladexes")

    @property
    def modus(self) -> Modus:
        return moduses[self.modus_name]
    
    @property
    def empty_cards(self) -> int:
        dic = client.requestdic("player_info")
        return int(dic["empty_cards"])    
    
    @property
    def moduses(self) -> list[str]:
        dic = client.requestdic("player_info")
        return dic["moduses"]

    def update_deck(self):
        self.deck = client.requestdic("sylladex")

    def can_captchalogue(self, instance: Instance) -> bool:
        if not self.modus.is_captchalogueable(instance, self): return False
        if instance.size > self.modus.size_limit: return False
        return True

    def captchalogue(self, instance: Instance) -> bool:
        if not self.can_captchalogue(instance): return False
        if not util.captchalogue_instance(instance.instance_name, self.modus.modus_name): return False
        self.update_deck()
        self.modus.add_to_modus_data(instance, self)
        return True
    
    def eject(self, instance_name: str):
        velocity = self.modus.get_eject_velocity
        client.requestplus("eject", {"instance_name": instance_name, "modus_name": self.modus.modus_name, "velocity": velocity})
        self.update_deck()
        self.modus.remove_from_modus_data(instance_name, self)

    def switch_modus(self, new_modus_name: str):
        if new_modus_name not in self.moduses: return False
        self.modus_name = new_modus_name
        self.data_dict = {}
        self.data_list = []
        invalid_instance_names = self.modus.convert_from_deck(self.deck, self)
        for instance_name in invalid_instance_names:
            self.eject(instance_name)
        self.update_deck()
        return True

    def uncaptchalogue(self, instance: Instance):
        if not self.modus.is_accessible(instance, self): return False
        ...
    
    def use(self, instance: Instance, effect_name: str):
        if not self.modus.is_accessible(instance, self): return False
        ...

    def equip(self, instance: Instance):
        if not self.modus.is_accessible(instance, self): return False
        ...

    def wear(self, instance: Instance, slot_number: int):
        if not self.modus.is_accessible(instance, self): return False
        ...

    def draw_ui_bar(self):
        return self.modus.draw_ui_bar(self)
    
    @staticmethod
    def new_sylladex(player_name, modus_name) -> "Sylladex":
        connection_host_port = f"{client.HOST}:{client.PORT}"
        if connection_host_port not in util.sylladexes: util.sylladexes[connection_host_port] = {}
        if player_name in util.sylladexes[connection_host_port]:
            return util.sylladexes[connection_host_port][player_name]
        else:
            new_sylladex = Sylladex(player_name, connection_host_port)
            new_sylladex.switch_modus(modus_name)
            return new_sylladex

    @staticmethod
    def get_sylladex(player_name) -> "Sylladex":
        connection_host_port = f"{client.HOST}:{client.PORT}"
        return Sylladex(player_name, connection_host_port)

    @staticmethod
    def current_sylladex() -> "Sylladex":
        return Sylladex.get_sylladex(client.dic["character"])

class Stack(Modus):
    def is_accessible(self, instance: Instance, sylladex: Sylladex):
        if instance.instance_name in sylladex.data_list and sylladex.data_list[0] == instance.instance_name: return True
        else: return False

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.insert(0, instance.instance_name)

stack_modus = Stack("stack")
stack_modus.front_sprite_path = "/sprites/moduses/stack_card.png"
stack_modus.back_sprite_path = "/sprites/moduses/stack_card_flipped.png"

class Queue(Modus):
    def is_accessible(self, instance: Instance, sylladex: Sylladex):
        if instance.instance_name in sylladex.data_list and sylladex.data_list[-1] == instance.instance_name: return True
        else: return False

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.insert(0, instance.instance_name)

queue_modus = Queue("queue")
queue_modus.front_sprite_path = "/sprites/moduses/queue_card.png"
queue_modus.back_sprite_path = "/sprites/moduses/queue_card_flipped.png"

class Array(Modus):
    pass

array_modus = Array("array")
array_modus.front_sprite_path = "/sprites/moduses/array_card.png"
array_modus.back_sprite_path = "/sprites/moduses/array_card_flipped.png"