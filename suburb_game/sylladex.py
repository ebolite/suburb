from typing import Union

import client
import util

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

    def is_captchalogueable(self, instance: Instance, sylladex: "Sylladex"):
        return True
    
    def is_accessible(self, instance: Instance, sylladex: "Sylladex"):
        return True
    
    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.append(instance)

    def remove_from_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        if instance in sylladex.data_list: sylladex.data_list.remove(instance)
    
    def convert_from_list(self, instance_list: list[Instance], sylladex: "Sylladex") -> list[Instance]:
        invalid_instances = []
        for instance in instance_list:
            sylladex.data_list.append(instance)
        return invalid_instances
    
    def get_eject_velocity(self):
        return self.eject_velocity

class Sylladex():
    def __init__(self, modus: Modus, player_name: str, connection_host_port: str = f"{client.HOST}:{client.PORT}"):
        self.modus = modus
        self.player_name = player_name
        self.connection_host_port = connection_host_port
        if connection_host_port not in util.sylladexes:
            util.sylladexes[connection_host_port] = {}
        if player_name not in util.sylladexes[connection_host_port]:
            util.sylladexes[connection_host_port][player_name] = self
        self.data_dict = {}
        self.data_list = []
        self.deck: list[Instance] = []

    def captchalogue(self, instance: Instance) -> bool:
        if not self.modus.is_captchalogueable(instance, self): return False
        if "success" not in client.requestplus("captchalogue", {"instance_name": instance.instance_name, "modus_name": self.modus.modus_name}): return False
        self.deck.append(instance)
        self.modus.add_to_modus_data(instance, self)
        return True
    
    def eject(self, instance):
        velocity = self.modus.get_eject_velocity
        client.requestplus("eject", {"instance_name": instance.instance_name, "modus_name": self.modus.modus_name, "velocity": velocity})
        self.modus.remove_from_modus_data(instance, self)

    def switch_modus(self, new_modus_name):
        if new_modus_name not in self.moduses: return False
        self.modus = moduses[new_modus_name]
        self.data_dict = {}
        self.data_list = []
        invalid_instances = self.modus.convert_from_list(self.deck, self)
        for instance in invalid_instances:
            self.eject(instance)
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

    @property
    def empty_cards(self) -> int:
        dic = client.requestdic("player_info")
        return int(dic["empty_cards"])    
    
    @property
    def moduses(self) -> list[str]:
        dic = client.requestdic("player_info")
        return dic["moduses"]

class Stack(Modus):
    def is_accessible(self, instance: Instance, sylladex: Sylladex):
        if instance in sylladex.data_list and sylladex.data_list[0] is instance: return True
        else: return False

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.insert(0, instance)

stack_modus = Stack("stack")
stack_modus.front_sprite_path = "/sprites/moduses/stack_card.png"
stack_modus.back_sprite_path = "/sprites/moduses/stack_card_flipped.png"

class Queue(Modus):
    def is_accessible(self, instance: Instance, sylladex: Sylladex):
        if instance in sylladex.data_list and sylladex.data_list[-1] is instance: return True
        else: return False

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.insert(0, instance)

queue_modus = Queue("queue")
queue_modus.front_sprite_path = "/sprites/moduses/queue_card.png"
queue_modus.back_sprite_path = "/sprites/moduses/queue_card_flipped.png"

class Array(Modus):
    pass

array_modus = Array("array")
array_modus.front_sprite_path = "/sprites/moduses/array_card.png"
array_modus.back_sprite_path = "/sprites/moduses/array_card_flipped.png"