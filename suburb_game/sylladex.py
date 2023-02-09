from typing import Union

import client
import util

class Instance():
    def __init__(self, instance_name: str, instance_dict: dict):
        self.instance_name = instance_name
        self.item_name = instance_dict["item_name"]
        self.item_dict = instance_dict["item_dict"]
        self.power = self.item_dict["power"]
        self.code = self.item_dict["code"]
        self.kinds = self.item_dict["kinds"]

# the default fetch modus is array
class Modus():
    def __init__(self):
        self.eject_velocity = 3
        self.size_limit = 30
        self.modus_name = "modus"
        self.data_type = "list"     # list or dict

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
        self.deck = []
