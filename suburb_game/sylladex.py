import os
import time
import random
from typing import Union, Optional, Callable
import pygame

import client
import util
from itemactions import item_actions, ItemAction
import render
import suburb
import themes

current_character_name = None

moduses: dict[str, "Modus"] = {}


class Item:
    def __init__(self, item_name: str, item_dict: dict):
        self.name = item_name
        self.item_dict = item_dict
        self.forbiddencode: bool = self.item_dict["forbiddencode"]
        self.power: int = self.item_dict["power"]
        self.size: int = self.item_dict["size"]
        self.code: str = self.item_dict["code"]
        self.kinds: list = self.item_dict["kinds"]
        self.onhit_states: dict[str, dict] = self.item_dict["onhit_states"]
        self.wear_states: dict[str, dict] = self.item_dict["wear_states"]
        self.consume_states: dict[str, dict] = self.item_dict["consume_states"]
        self.wearable: bool = self.item_dict["wearable"]
        self.use: list[str] = self.item_dict["use"] or []
        self.cost: dict[str, float] = self.item_dict["cost"]
        self.display_name: str = self.item_dict["display_name"]
        self.adjectives: list[str] = self.item_dict["adjectives"]
        self.secretadjectives: list[str] = self.item_dict["secretadjectives"]
        self.description: Optional[str] = self.item_dict["description"]

    @property
    def true_cost(self):
        out = {}
        for grist_name, value in self.cost.items():
            out[grist_name] = int(self.power * value)
        return out


class Instance:
    def __init__(self, instance_name: str, instance_dict: dict):
        self.name: str = instance_name
        self.item_name: str = instance_dict["item_name"]
        self.item_dict: dict = instance_dict["item_dict"]
        self.contained: dict = instance_dict["contained"]
        self.punched_code: str = instance_dict["punched_code"]
        self.punched_item_name: str = instance_dict["punched_item_name"]
        self.inserted: dict = instance_dict["inserted"]
        self.carved: str = instance_dict["carved"]
        self.carved_item_name: str = instance_dict["carved_item_name"]
        self.computer_data = instance_dict["computer_data"]
        self.color: tuple[int, int, int] = instance_dict["color"]

    @property
    def item(self) -> Item:
        return Item(self.item_name, self.item_dict)

    def display_name(self, short=False) -> str:
        contained_instance = self.contained_instance()
        if self.punched_code != "" and self.punched_item_name == "":
            return f"[:]-{self.punched_code}"
        if self.carved != "00000000" and self.carved_item_name == "":
            return f")(-{self.carved}"
        if short:
            if self.punched_item_name != "":
                return f"[:]-{util.shorten_item_name(self.punched_item_name)}"
            elif self.carved_item_name != "perfectly+generic object":
                return f")(-{util.shorten_item_name(self.carved_item_name)}"
            elif contained_instance is not None:
                return f"[ ]-{contained_instance.display_name(short)}"
            else:
                return util.shorten_item_name(self.item.display_name)
        else:
            if self.punched_item_name != "":
                return f"[:]-{self.punched_item_name}"
            elif self.carved_item_name != "perfectly+generic object":
                return f")(-{self.carved_item_name}"
            elif contained_instance is not None:
                return f"[ ]-{contained_instance.display_name(short)}"
            return self.item.display_name

    # for captchalogue cards
    def contained_instance(self) -> Optional["Instance"]:
        if self.contained == "":
            return None
        instance_name = self.contained["instance_name"]
        instance_dict = self.contained
        return Instance(instance_name, instance_dict)

    def inserted_instance(self) -> Optional["Instance"]:
        if self.inserted == "":
            return None
        instance_name = self.inserted["instance_name"]
        instance_dict = self.inserted
        return Instance(instance_name, instance_dict)

    def use_item(
        self, action_name: str, target_instance: Optional["Instance"] = None
    ) -> bool:
        if action_name not in item_actions:
            return False
        action: ItemAction = item_actions[action_name]
        target_instance_name = None if target_instance is None else target_instance.name
        target_instance_display_name = (
            None if target_instance is None else target_instance.display_name()
        )
        if action.special:
            return action.use_func(self)
        reply = client.requestplus(
            intent="use_item",
            content={
                "instance_name": self.name,
                "action_name": action_name,
                "target_name": target_instance_name,
            },
        )
        if reply == "False":
            if action.error_prompt:
                util.log(
                    action.error_message(
                        self.display_name(), target_instance_display_name
                    )
                )
            return False
        else:
            if action.use_prompt:
                util.log(
                    action.use_message(
                        self.display_name(), target_instance_display_name
                    )
                )
            self.update_sylladex_for_action(action_name, target_instance_name)
            return True

    # returns True if go back to last scene, False don't
    def update_sylladex_for_action(
        self, action_name: str, target_name: Optional[str] = None
    ) -> bool:
        syl = Sylladex.current_sylladex()
        action = item_actions[action_name]
        if action.consume:
            if self.name in syl.deck:
                syl.remove_instance(self.name)
        if action.consume_target:
            if target_name is not None and target_name in syl.deck:
                syl.remove_instance(target_name)
        # special, todo: put this behavior into itemactions.py
        if action_name == "add_card":
            card_instance = self.contained_instance()
            if card_instance is not None:
                syl.captchalogue(card_instance)
        syl.update_deck()
        return action.goto_last_scene

    def get_action_button_func(
        self, action_name: str, last_scene: Callable
    ) -> Callable:
        if action_name not in item_actions:
            return lambda *args: None
        syl = Sylladex.current_sylladex()
        action: ItemAction = item_actions[action_name]
        if action.targeted:

            def output_func():
                self.choose_target(action_name, last_scene)

        else:

            def output_func():
                reply = self.use_item(action_name, None)
                if reply:
                    self.goto_use_next_scene(last_scene, action_name, syl.modus)

        return output_func

    def get_target_button_func(
        self, target_instance: "Instance", action_name: str, last_scene: Callable
    ) -> Callable:
        if action_name not in item_actions:
            return lambda *args: None
        syl = Sylladex.current_sylladex()

        def choose_button_func():
            reply = self.use_item(action_name, target_instance)
            if reply:
                self.goto_use_next_scene(last_scene, action_name, syl.modus)

        return choose_button_func

    def goto_use_next_scene(
        self, last_scene: Callable, action_name: str, modus: "Modus"
    ):
        if action_name == "computer":
            suburb.computer(self)
        elif last_scene is suburb.map_scene:
            last_scene()
        else:
            suburb.display_item(self, last_scene, modus=modus)

    def choose_target(self, action_name: str, last_scene: Callable):
        suburb.new_scene()
        render.LogWindow(self.choose_target)
        valid_instances = client.requestplusdic(
            intent="valid_use_targets",
            content={"instance_name": self.name, "action_name": action_name},
        )
        syl = Sylladex.current_sylladex()
        syl.update_deck()
        action: ItemAction = item_actions[action_name]
        if action.prompt:
            util.log(action.prompt_message(self.display_name()))
        for i, target_instance_name in enumerate(valid_instances.keys()):
            button_height = 33
            button_width = 400
            x = int(render.SCREEN_WIDTH * 0.5 - button_width * 0.5)
            y = 120 + (button_height + 10) * i
            target_instance = Instance(
                target_instance_name, valid_instances[target_instance_name]
            )
            if target_instance_name in syl.deck:
                display_name = f"(Sylladex) {target_instance.display_name()}"
            else:
                display_name = target_instance.display_name()
            button_func = self.get_target_button_func(
                target_instance, action_name, last_scene
            )
            choose_button = render.TextButton(
                x, y, button_width, button_height, display_name, button_func
            )
            choose_button.absolute = True
            choose_button.truncate_text = True
        if last_scene is suburb.map_scene:

            def backbutton_func():
                last_scene()

        else:

            def backbutton_func():
                suburb.display_item(self, last_scene, syl.modus)

        backbutton = render.Button(
            0.1,
            0.07,
            "sprites/buttons/back.png",
            "sprites/buttons/backpressed.png",
            backbutton_func,
        )


# the default fetch modus is array
class Modus:
    def __init__(self, name):
        self.eject_velocity = 3
        self.size_limit = 30
        self.modus_name = name
        self.front_path = ""
        self.back_path = ""
        self.bar_path = ""
        self.thumb_path = ""
        self.theme: themes.Theme = themes.array
        self.label_color: pygame.Color = pygame.Color(36, 214, 255)
        self.can_uncaptchalogue = True
        self.description = ""
        self.difficulty = ""
        moduses[name] = self

    def is_captchalogueable(self, instance: Instance, sylladex: "Sylladex") -> bool:
        return True

    def is_accessible(self, instance: Instance, sylladex: "Sylladex") -> bool:
        return True

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.append(instance.name)

    def get_cards_to_eject(self, sylladex: "Sylladex"):
        ejected = []
        while len(sylladex.data_list) > sylladex.empty_cards:
            ejected.append(sylladex.data_list.pop(0))
        return ejected

    def remove_from_modus_data(self, instance_name: str, sylladex: "Sylladex"):
        if instance_name in sylladex.data_list:
            sylladex.data_list.remove(instance_name)

    def convert_from_deck(self, deck: dict, sylladex: "Sylladex") -> list[str]:
        invalid_instance_names = []
        for instance_name in deck.copy():
            if instance_name not in sylladex.data_list:
                sylladex.data_list.append(instance_name)
        for instance_name in sylladex.data_list.copy():
            if instance_name not in deck:
                sylladex.data_list.remove(instance_name)
        return invalid_instance_names

    def get_instance_name(self, instance: Instance, short=False):
        return instance.display_name(short=short)

    def get_eject_velocity(self) -> int:
        return self.eject_velocity

    def get_button_func(self, instance: Instance, last_scene: Callable) -> Callable:
        def wrapper():
            suburb.display_item(instance, last_scene, modus=self)

        return wrapper

    def get_ui_bar_card_instances(self, sylladex: "Sylladex", remaining_cards: int):
        instances = sylladex.data_list.copy()
        empty_cards = ["" for i in range(remaining_cards)]
        return empty_cards + instances

    def make_bar_backgound(self) -> "render.Image":
        sylladex_bar = render.Image(0, 0, self.bar_path)
        sylladex_bar.absolute = True
        sylladex_label = render.Text(6, 560, "sylladex :: captchalogue deck")
        sylladex_label.absolute = True
        sylladex_label.color = self.label_color
        sylladex_label.fontsize = 16
        modus_label = render.Text(6, 560, f"fetch modus :: {self.modus_name}")
        modus_label.absolute = True
        modus_label.color = self.label_color
        modus_label.fontsize = 16
        modus_label.x = render.SCREEN_WIDTH - modus_label.get_width() - 6
        return sylladex_bar

    def make_remaining_cards_indicator(
        self, x, y, sylladex: "Sylladex", last_scene: Callable, remaining_cards: int
    ) -> "render.Button":
        def drop_empty_card_button():
            client.request("drop_empty_card")
            sylladex.update_deck()
            last_scene()

        remaining_cards_display = render.Button(
            x,
            y,
            "sprites/moduses/card_num_remaining.png",
            "sprites/moduses/card_num_remaining.png",
            drop_empty_card_button,
        )
        remaining_cards_display.absolute = True
        remaining_cards_label = render.Text(0.5, 0.6, str(remaining_cards))
        remaining_cards_label.bind_to(remaining_cards_display)
        if remaining_cards == 0:
            remaining_cards_label.color = pygame.Color(255, 0, 0)
        return remaining_cards_display

    def make_card_thumb(
        self,
        x,
        y,
        instance: Optional[Instance],
        sylladex: "Sylladex",
        last_scene: Callable,
    ) -> Union["render.Image", "render.Button"]:
        if instance is not None:
            button_function = (
                self.get_button_func(instance, last_scene)
                if self.is_accessible(instance, sylladex)
                else lambda *args: None
            )
            card_thumb = render.Button(
                x,
                y,
                "sprites/moduses/card_thumb.png",
                "sprites/moduses/card_thumb.png",
                button_function,
            )
            card_thumb.absolute = True
        else:
            card_thumb = render.Image(x, y, "sprites/moduses/card_thumb.png")
            card_thumb.absolute = True
            card_thumb.alpha = 155
            return card_thumb
        card_image = render.make_item_image(0.49, 0.5, instance)
        if card_image is not None:
            card_image.bind_to(card_thumb)
            card_image.scale = 0.5
            contained_instance = instance.contained_instance()
            if contained_instance is not None:
                contained_image = render.make_item_image(0.45, 0.5, contained_instance)
                if contained_image is not None:
                    contained_image.bind_to(card_image)
                    contained_image.scale = 0.25
            if instance.item.name == "punched card":
                render.spawn_punches(
                    card_image, instance.punched_code, 18, 31, w=40, h=60
                )
        label_text = self.get_instance_name(instance, True)
        card_label = render.Text(0.49, 0.9, label_text)
        card_label.set_fontsize_by_width(90)
        card_label.bind_to(card_thumb)
        if not self.is_accessible(instance, sylladex):
            card_thumb.alpha = 155
            card_label.alpha = 155
            if card_image is not None:
                card_image.alpha = 155
        return card_thumb

    def draw_ui_bar(self, sylladex: "Sylladex", last_scene: Callable) -> "render.Image":
        sylladex_bar = self.make_bar_backgound()
        num_cards_remaining = sylladex.empty_cards - len(sylladex.data_list)
        remaining_cards_display = self.make_remaining_cards_indicator(
            10, render.SCREEN_HEIGHT - 85, sylladex, last_scene, num_cards_remaining
        )
        ui_bar_card_instances = self.get_ui_bar_card_instances(
            sylladex, num_cards_remaining
        )
        instances_length = len(ui_bar_card_instances)
        for i, instance_name in enumerate(ui_bar_card_instances):
            x = (render.SCREEN_WIDTH / 2) - 109 + 125 * (i + 1 - instances_length / 2)
            x = int(x)
            y = int(render.SCREEN_HEIGHT * 0.80)
            if instance_name != "":
                instance = sylladex.get_instance(instance_name)
            else:
                instance = None
            card_thumb = self.make_card_thumb(x, y, instance, sylladex, last_scene)
            card_thumb.bind_to(sylladex_bar)
        return sylladex_bar


class Sylladex:
    def __init__(
        self, player_name: str, connection_host_port: str = f"{client.HOSTNAME}"
    ):
        self.__dict__["player"] = player_name
        self.__dict__["host_port"] = connection_host_port
        if connection_host_port not in util.sylladexes:
            util.sylladexes[connection_host_port] = {}
        if player_name not in util.sylladexes[connection_host_port]:
            util.sylladexes[connection_host_port][player_name] = {}
        try:
            self.data_dict
            self.data_list
            self.deck: dict[str, dict]
            self.empty_cards: int
        except KeyError:
            self.data_dict = {}
            self.data_list = []
            self.deck: dict[str, dict] = {}
            self.empty_cards: int = 0
            self.update_deck()

    def __getattr__(self, attr):
        return util.sylladexes[self.__dict__["host_port"]][self.__dict__["player"]][
            attr
        ]

    def __setattr__(self, attr, value):
        util.sylladexes[self.__dict__["host_port"]][self.__dict__["player"]][
            attr
        ] = value
        util.writejson(util.sylladexes, "sylladexes")

    @property
    def modus(self) -> Modus:
        try:
            return moduses[self.modus_name]
        except KeyError:
            self.modus_name = self.moduses[0]
            return moduses[self.modus_name]

    @property
    def moduses(self) -> list[str]:
        dic = client.requestdic("player_info")
        return dic["moduses"]

    def update_deck(self):
        self.empty_cards = client.requestdic("player_info")["empty_cards"]
        self.deck = client.requestdic("sylladex")

    # this needs to be included for dict modi
    def validate(self):
        self.update_deck()
        for instance_name in self.data_list:
            if instance_name not in self.deck:
                print(f"Found invalid instance {instance_name}!")
                self.modus.remove_from_modus_data(instance_name, self)
        for instance_name in self.deck:
            if instance_name not in self.data_list:
                print(f"Missing item {instance_name}! Converting from deck.")
                self.modus.convert_from_deck(self.deck, self)
                return self.validate()
            try:
                Instance(instance_name, self.deck[instance_name])
            except KeyError:
                self.modus.convert_from_deck(self.deck, self)
                return self.validate()

    def get_instance(self, instance_name) -> Instance:
        if instance_name not in self.deck:
            self.update_deck()
        if instance_name in self.deck:
            return Instance(instance_name, self.deck[instance_name])
        else:
            self.remove_instance(instance_name)
            raise KeyError

    def can_captchalogue(self, instance: Instance) -> bool:
        if not self.modus.is_captchalogueable(instance, self):
            return False
        if instance.item.size > self.modus.size_limit:
            return False
        return True

    def captchalogue(self, instance: Instance) -> bool:
        if self.empty_cards == 0:
            return False
        if not self.can_captchalogue(instance):
            return False
        self.modus.add_to_modus_data(instance, self)
        ejected = self.modus.get_cards_to_eject(self)
        for instance_name in ejected:
            self.eject(instance_name)
        util.captchalogue_instance(instance.name, self.modus_name)
        self.update_deck()
        return True

    def eject(self, instance_name: str):
        instance = self.get_instance(instance_name)
        if "add_card" in instance.item.use:
            if instance.use_item("add_card"):
                return
        velocity = self.modus.get_eject_velocity()
        client.requestplus(
            "eject",
            {
                "instance_name": instance_name,
                "modus_name": self.modus_name,
                "velocity": velocity,
            },
        )
        self.update_deck()
        self.modus.remove_from_modus_data(instance_name, self)

    def switch_modus(self, new_modus_name: str):
        if new_modus_name not in self.moduses:
            return False
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
        if not self.modus.is_accessible(instance, self):
            return False
        client.requestplus(
            "eject",
            {
                "instance_name": instance_name,
                "modus_name": self.modus_name,
                "velocity": 0,
            },
        )
        self.update_deck()
        self.modus.remove_from_modus_data(instance_name, self)

    def remove_instance(self, instance_name: str):
        self.update_deck()
        self.modus.remove_from_modus_data(instance_name, self)

    def use(self, instance: Instance, effect_name: str):
        if not self.modus.is_accessible(instance, self):
            return False
        ...

    def equip(self, instance: Instance):
        if not self.modus.is_accessible(instance, self):
            return False
        ...

    def wear(self, instance: Instance, slot_number: int):
        if not self.modus.is_accessible(instance, self):
            return False
        ...

    def draw_ui_bar(self, last_scene: Callable):
        return self.modus.draw_ui_bar(self, last_scene)

    @staticmethod
    def new_sylladex(player_name, modus_name) -> "Sylladex":
        connection_host_port = f"{client.HOSTNAME}"
        if connection_host_port not in util.sylladexes:
            util.sylladexes[connection_host_port] = {}
        if player_name in util.sylladexes[connection_host_port]:
            return Sylladex(player_name, connection_host_port)
        else:
            new_sylladex = Sylladex(player_name, connection_host_port)
            new_sylladex.switch_modus(modus_name)
            return new_sylladex

    @staticmethod
    def update_character(new_character_name: str):
        global current_character_name
        current_character_name = new_character_name

    @staticmethod
    def get_sylladex(player_name) -> "Sylladex":
        connection_host_port = f"{client.HOSTNAME}"
        return Sylladex(player_name, connection_host_port)

    @staticmethod
    def current_sylladex() -> "Sylladex":
        global current_character_name
        current_sylladex = Sylladex.get_sylladex(current_character_name)
        if current_character_name not in util.sylladexes[client.HOSTNAME]:
            return Sylladex.new_sylladex(current_character_name, current_sylladex.modus)
        else:
            return current_sylladex


class Stack(Modus):
    def is_accessible(self, instance: Instance, sylladex: Sylladex):
        if (
            instance.name in sylladex.data_list
            and sylladex.data_list[0] == instance.name
        ):
            return True
        else:
            return False

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.insert(0, instance.name)

    def get_cards_to_eject(self, sylladex: "Sylladex"):
        ejected = []
        while len(sylladex.data_list) > sylladex.empty_cards:
            ejected.append(sylladex.data_list.pop())
        return ejected

    def get_ui_bar_card_instances(self, sylladex: "Sylladex", remaining_cards: int):
        instances = sylladex.data_list.copy()
        empty_cards = ["" for i in range(remaining_cards)]
        return instances + empty_cards


class Array(Modus):
    def is_captchalogueable(self, instance: Instance, sylladex: "Sylladex") -> bool:
        if sylladex.empty_cards < len(sylladex.data_list) + 1:
            return False
        return True


array_modus = Array("array")
array_modus.front_path = "sprites/moduses/array_card.png"
array_modus.back_path = "sprites/moduses/array_card_flipped.png"
array_modus.bar_path = "sprites/moduses/array_bar.png"
array_modus.thumb_path = "sprites/moduses/array_card_thumb.png"
array_modus.theme = themes.array
array_modus.label_color = themes.array.white
array_modus.description = (
    "You think it's cool that things don't always have to be a federal fucking issue."
)
array_modus.difficulty = "normal video game"

stack_modus = Stack("stack")
stack_modus.front_path = "sprites/moduses/stack_card.png"
stack_modus.back_path = "sprites/moduses/stack_card_flipped.png"
stack_modus.bar_path = "sprites/moduses/stack_bar.png"
stack_modus.thumb_path = "sprites/moduses/stack_card_thumb.png"
stack_modus.theme = themes.stack
stack_modus.can_uncaptchalogue = False
stack_modus.description = "First in, last out. Annoying but simple."
stack_modus.difficulty = "annoying"


class Queue(Modus):
    def is_accessible(self, instance: Instance, sylladex: Sylladex):
        if (
            instance.name in sylladex.data_list
            and sylladex.data_list[-1] == instance.name
        ):
            return True
        else:
            return False

    def add_to_modus_data(self, instance: Instance, sylladex: "Sylladex"):
        sylladex.data_list.insert(0, instance.name)

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
queue_modus.theme = themes.queue
queue_modus.can_uncaptchalogue = False
queue_modus.description = "First in, first out. Stack's ugly twin."
queue_modus.difficulty = "annoying"


class ScratchAndSniff(Modus):
    def is_captchalogueable(self, instance: Instance, sylladex: "Sylladex") -> bool:
        if sylladex.empty_cards < len(sylladex.data_list) + 1:
            return False
        return True

    def get_instance_name(self, instance: Instance, short):
        possible_words = instance.item.adjectives + instance.item.secretadjectives
        if short:
            return random.choice(possible_words)
        chosen = random.choices(possible_words, k=2)
        name = f" ".join(chosen)
        return name


scratch_and_sniff_modus = ScratchAndSniff("scratch and sniff")
scratch_and_sniff_modus.front_path = "sprites/moduses/scratch_and_sniff_card.png"
scratch_and_sniff_modus.back_path = "sprites/moduses/scratch_and_sniff_card_flipped.png"
scratch_and_sniff_modus.bar_path = "sprites/moduses/scratch_and_sniff_bar.png"
scratch_and_sniff_modus.theme = themes.scratch_and_sniff
scratch_and_sniff_modus.label_color = pygame.Color(11, 193, 125)
scratch_and_sniff_modus.description = (
    "For when you really hate knowing what things are."
)
scratch_and_sniff_modus.difficulty = "confusing"
