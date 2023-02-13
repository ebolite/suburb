import os
import time
from typing import Union, Optional, Callable
import pygame

import client
import util
import render
import suburb

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
        self.front_path = ""
        self.back_path = ""
        self.bar_path = ""
        self.thumb_path = ""
        self.black_color: pygame.Color
        self.dark_color: pygame.Color
        self.light_color: pygame.Color
        self.white_color: pygame.Color
        moduses[name] = self

    def is_captchalogueable(self, instance: Instance, sylladex: "Sylladex") -> bool:
        return True
    
    def is_accessible(self, instance: Instance, sylladex: "Sylladex") -> bool:
        return True
    
    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.append(instance.instance_name)

    def get_cards_to_eject(self, sylladex: "Sylladex"):
        ejected = []
        while len(sylladex.data_list) > sylladex.empty_cards:
            ejected.append(sylladex.data_list.pop(0))
        return ejected

    def remove_from_modus_data(self, instance_name: str, sylladex: "Sylladex"):
        if instance_name in sylladex.data_list: sylladex.data_list.remove(instance_name)
    
    def convert_from_deck(self, deck: dict, sylladex: "Sylladex") -> list[str]:
        invalid_instance_names = []
        for instance_name in deck:
            sylladex.data_list.append(instance_name)
        return invalid_instance_names
    
    def get_eject_velocity(self) -> int:
        return self.eject_velocity
    
    def get_button_func(self, instance: Instance, last_scene: Callable) -> Callable:
        def wrapper():
            suburb.display_item(instance, last_scene, modus=self)
        return wrapper

    def draw_ui_bar(self, sylladex: "Sylladex", last_scene: Callable):
        start = time.time()
        sylladex_bar = render.Image(0, 0, self.bar_path)
        sylladex_bar.absolute = True
        instances_length = len(sylladex.data_list)
        num_cards_remaining = sylladex.empty_cards - len(sylladex.data_list)
        remaining_cards_display = render.Image(10, render.SCREEN_HEIGHT-85, "sprites/moduses/card_num_remaining.png")
        remaining_cards_display.absolute = True
        remaining_cards_label = render.Text(0.5, 0.6, str(num_cards_remaining))
        remaining_cards_label.bind_to(remaining_cards_display)
        if num_cards_remaining == 0: remaining_cards_label.color = pygame.Color(255, 0, 0)
        for i, instance_name in enumerate(sylladex.data_list):
            x = (render.SCREEN_WIDTH / 2) - 109 + 125*(i + 1 - instances_length/2)
            x = int(x)
            y = int(render.SCREEN_HEIGHT*0.80)
            instance = sylladex.get_instance(instance_name)
            button_function = self.get_button_func(instance, last_scene) if self.is_accessible(instance, sylladex) else lambda *args: None
            card_thumb = render.Button(x, y, "sprites/moduses/card_thumb.png", "sprites/moduses/card_thumb.png", button_function)
            card_thumb.absolute = True
            card_thumb.bind_to(sylladex_bar)
            image_path = f"sprites/items/{instance.item_name}.png"
            if os.path.isfile(image_path):
                card_image = render.ItemImage(0.49, 0.5, instance.item_name)
                card_image.bind_to(card_thumb)
                card_image.scale = 0.5
            else:
                card_image = None
            words = instance.item_name.replace("+", " ").split(" ")
            if len(words) > 2:
                base = words.pop()
                text = ""
                for word in words:
                    text += f"{word[0]}."
                label_text = f"{text} {base}"
            else:
                label_text = instance.item_name
            card_label = render.Text(0.49, 0.9, label_text)
            card_label.set_fontsize_by_width(90)
            card_label.bind_to(card_thumb)
            if not self.is_accessible(instance, sylladex): 
                card_thumb.alpha = 155
                card_label.alpha = 155
                if card_image is not None: card_image.alpha = 155
        print(f"draw ui bar - {time.time() - start}")

    
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

    def get_instance(self, instance_name) -> Instance:
        if instance_name not in self.deck:
            self.update_deck()
        return Instance(instance_name, self.deck[instance_name])

    def can_captchalogue(self, instance: Instance) -> bool:
        if not self.modus.is_captchalogueable(instance, self): return False
        if instance.size > self.modus.size_limit: return False
        return True

    def captchalogue(self, instance: Instance) -> bool:
        if not self.can_captchalogue(instance): return False
        self.modus.add_to_modus_data(instance, self)
        ejected = self.modus.get_cards_to_eject(self)
        for instance_name in ejected:
            self.eject(instance_name)
        util.captchalogue_instance(instance.instance_name, self.modus_name)
        self.update_deck()
        return True
    
    def eject(self, instance_name: str):
        velocity = self.modus.get_eject_velocity()
        client.requestplus("eject", {"instance_name": instance_name, "modus_name": self.modus_name, "velocity": velocity})
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

    def uncaptchalogue(self, instance_name: str):
        instance = self.get_instance(instance_name)
        if not self.modus.is_accessible(instance, self): return False
        client.requestplus("eject", {"instance_name": instance_name, "modus_name": self.modus_name, "velocity": 0})
        self.update_deck()
        self.modus.remove_from_modus_data(instance_name, self)
    
    def use(self, instance: Instance, effect_name: str):
        if not self.modus.is_accessible(instance, self): return False
        ...

    def equip(self, instance: Instance):
        if not self.modus.is_accessible(instance, self): return False
        ...

    def wear(self, instance: Instance, slot_number: int):
        if not self.modus.is_accessible(instance, self): return False
        ...

    def draw_ui_bar(self, last_scene: Callable):
        return self.modus.draw_ui_bar(self, last_scene)
    
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

    def get_cards_to_eject(self, sylladex: "Sylladex"):
        ejected = []
        while len(sylladex.data_list) > sylladex.empty_cards:
            ejected.append(sylladex.data_list.pop())
        return ejected

stack_modus = Stack("stack")
stack_modus.front_path = "sprites/moduses/stack_card.png"
stack_modus.back_path = "sprites/moduses/stack_card_flipped.png"
stack_modus.bar_path = "sprites/moduses/stack_bar.png"
stack_modus.thumb_path = "sprites/moduses/stack_card_thumb.png"
stack_modus.black_color = pygame.Color(0, 0, 0)
stack_modus.dark_color = pygame.Color(154, 36, 70)
stack_modus.light_color = pygame.Color(255, 5, 124)
stack_modus.white_color = pygame.Color(255, 255, 255)

class Queue(Modus):
    def is_accessible(self, instance: Instance, sylladex: Sylladex):
        if instance.instance_name in sylladex.data_list and sylladex.data_list[-1] == instance.instance_name: return True
        else: return False

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.insert(0, instance.instance_name)

    def get_cards_to_eject(self, sylladex: "Sylladex"):
        ejected = []
        while len(sylladex.data_list) > sylladex.empty_cards:
            ejected.append(sylladex.data_list.pop())
        return ejected

queue_modus = Queue("queue")
queue_modus.front_path = "sprites/moduses/queue_card.png"
queue_modus.back_path = "sprites/moduses/queue_card_flipped.png"
queue_modus.bar_path = "sprites/moduses/queue_bar.png"
queue_modus.thumb_path = "sprites/moduses/queue_card_thumb.png"
queue_modus.black_color = pygame.Color(0, 0, 0)
queue_modus.dark_color = pygame.Color(207, 86, 12)
queue_modus.light_color = pygame.Color(255, 96, 0)
queue_modus.white_color = pygame.Color(255, 255, 255)

class Array(Modus):
    def is_captchalogueable(self, instance: Instance, sylladex: "Sylladex") -> bool:
        if sylladex.empty_cards < len(sylladex.data_list) + 1: return False
        return True

array_modus = Array("array")
array_modus.front_path = "sprites/moduses/array_card.png"
array_modus.back_path = "sprites/moduses/array_card_flipped.png"
array_modus.bar_path = "sprites/moduses/array_bar.png"
array_modus.thumb_path = "sprites/moduses/array_card_thumb.png"
array_modus.black_color = pygame.Color(0, 0, 0)
array_modus.dark_color = pygame.Color(16, 147, 216)
array_modus.light_color = pygame.Color(6, 182, 255)
array_modus.white_color = pygame.Color(255, 255, 255)