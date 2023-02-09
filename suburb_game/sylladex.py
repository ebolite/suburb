from typing import Union

import client
import util

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
    def __init__(self):
        self.eject_velocity = 3
        self.size_limit = 30
        self.modus_name = "modus"
        self.data_type = "list"     # list or dict
    
    def verify(self, instance: Instance, sylladex: "Sylladex") -> bool:
        if sylladex.empty_cards == 0: return False
        if instance.size > self.size_limit: return False
        if "success" in client.requestplus("add_instance_to_sylladex", {"instance_name": instance.instance_name, "modus_name": self.modus_name}): return True
        else: return False

    def add_instance_to_sylladex(self, instance: Instance, sylladex: "Sylladex"):
            if not self.verify(instance, sylladex): return False
            sylladex.deck.append(instance)

class Sylladex():
    def __init__(self, modus: Modus, player_name: str, connection_host_port: str = f"{client.HOST}:{client.PORT}"):
        self.modus = modus
        self.player_name = player_name
        self.connection_host_port = connection_host_port
        if connection_host_port not in util.sylladexes:
            util.sylladexes[connection_host_port] = {}
        if player_name not in util.sylladexes[connection_host_port]:
            util.sylladexes[connection_host_port][player_name] = {}
        if modus.modus_name not in util.sylladexes[connection_host_port][player_name]:
            if modus.data_type == "list":
                util.sylladexes[connection_host_port][player_name][modus.modus_name] = []
            if modus.data_type == "dict":
                util.sylladexes[connection_host_port][player_name][modus.modus_name] = {}
        self.deck: list[Instance] = []

    @property
    def empty_cards(self) -> int:
        dic = client.requestdic("player_info")
        return int(dic["empty_cards"])    
