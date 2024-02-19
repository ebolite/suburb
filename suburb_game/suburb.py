import pygame
import ssl
import traceback
import math
import time
from captcha.image import ImageCaptcha
import cv2
import os
import numpy as np
import random
import json
from typing import Callable, Optional

import util
import render
import client
import config
import themes
import strife
import itemeditor
import sylladex
from sylladex import Instance, Sylladex, Modus


def current_theme():
    return themes.default


def new_scene():
    render.clear_elements()
    fps_counter = render.FpsCounter(1150, 0)
    fps_counter.fontsize = 20
    fps_counter.absolute = True
    render.update_check.remove(fps_counter)
    render.always_on_top_check.append(fps_counter)


def scene(func):
    def out(*args, **kwargs):
        t = time.time()
        new_scene()
        func(*args, **kwargs)
        print(f"{func} - {time.time() - t}")

    return out


captcha_generator = ImageCaptcha(
    width=261,
    height=336,
    fonts=["fonts/cour.ttf", "fonts/courbd.ttf", "fonts/courbi.ttf", "fonts/couri.ttf"],
)


def get_captcha(code) -> str:
    path = f"{util.homedir}/sprites/captchas/{code}.png".replace("?", "-")
    if not os.path.isfile(path):
        captcha_generator.write(code, path)
        img = cv2.imread(path)
        mask = cv2.imread(f"{util.homedir}/sprites/mask.png")
        img_masked = cv2.bitwise_and(img, mask)
        black_mask = np.all(img_masked <= 2, axis=-1)
        alpha = np.uint8(np.logical_not(black_mask)) * int(255)
        bgra = np.dstack((img_masked, alpha))
        cv2.imwrite(path, bgra)
    return path


def placeholder():
    pass


@scene
def play(page=0):
    theme = current_theme()
    label = render.Text(0.5, 0.02, "CHOOSE YOUR CHARACTER!")
    label.color = pygame.Color(255, 0, 0)
    label.outline_color = pygame.Color(255, 255, 0)
    label.fontsize = 16
    current_sessions: dict[str, Optional[dict]] = client.requestdic(
        intent="all_session_characters"
    )
    session_names: list[Optional[str]] = list(current_sessions.keys())
    if len(current_sessions) > 0:
        sessions_to_display = session_names[page * 4 : page * 4 + 4]
    else:
        sessions_to_display = []
    while len(sessions_to_display) < 4:
        sessions_to_display.append(None)

    def get_button_func(session_name):
        if session_name is None:

            def button_func():
                connect()

        else:

            def button_func():
                client.dic["session_name"] = session_name
                if current_sessions[session_name] is None:
                    character_creator = CharacterCreator()
                    character_creator.start()
                else:
                    newgame()

        return button_func

    for i, session_name in enumerate(sessions_to_display):
        x = 0.2 * (i + 1)
        y = 0.4
        if session_name is not None and current_sessions[session_name] is not None:
            player_dict = current_sessions[session_name]
            assert player_dict is not None
            box_theme = themes.themes[player_dict["aspect"]]
        else:
            player_dict = None
            box_theme = theme
        session_box = render.SolidColor(x, y, 250, 400, box_theme.light)
        session_box.absolute = False
        session_box.outline_color = box_theme.dark
        session_box.border_radius = 4
        if player_dict is not None and session_name is not None:
            symbol = render.Symbol(0.5, 0.5, player_dict["symbol_dict"])
            symbol.bind_to(session_box)
            character_name_display_box = render.SolidColor(
                0.5, 0.07, 230, 30, box_theme.white
            )
            character_name_display_box.absolute = False
            character_name_display_box.outline_color = box_theme.black
            character_name_display_box.border_radius = 8
            character_name_display_box.bind_to(session_box)
            character_name_label = render.Text(0.5, 0.5, player_dict["nickname"])
            character_name_label.color = box_theme.black
            character_name_label.bind_to(character_name_display_box)
            character_name_label.fontsize = 24
            character_name_label.set_fontsize_by_width(220)
            session_name_display = render.Text(0.5, 0.85, session_name)
            session_name_display.fontsize = 20
            session_name_display.set_fontsize_by_width(250)
            session_name_display.color = box_theme.dark
            session_name_display.bind_to(session_box)
            character_title_label = render.Text(0.5, 0.9, player_dict["title"])
            character_title_label.fontsize = 20
            character_title_label.set_fontsize_by_width(250)
            character_title_label.color = box_theme.dark
            character_title_label.bind_to(session_box)
            character_rung_label = render.Text(
                0.5, 0.95, f"Rung: {player_dict['echeladder_rung']}"
            )
            character_rung_label.fontsize = 20
            character_rung_label.set_fontsize_by_width(250)
            character_rung_label.color = box_theme.dark
            character_rung_label.bind_to(session_box)
        else:
            character_name_display_box = render.SolidColor(
                0.5, 0.07, 230, 30, theme.white
            )
            character_name_display_box.absolute = False
            character_name_display_box.outline_color = theme.black
            character_name_display_box.border_radius = 8
            character_name_display_box.bind_to(session_box)
            character_name_label = render.Text(0.5, 0.5, "ENTER NAME")
            character_name_label.color = theme.black
            character_name_label.bind_to(character_name_display_box)
            character_name_label.fontsize = 24
            if session_name is None:
                text = "NO SESSION"
            else:
                text = "NO CHARACTER"
            no_session_text = render.Text(0.5, 0.5, text)
            no_session_text.bind_to(session_box)
            no_session_text.color = theme.dark
        box_button = render.TextButton(
            0, 0, 250, 400, "", get_button_func(session_name)
        )
        box_button.draw_sprite = False
        box_button.absolute = True
        box_button.bind_to(session_box)
    if session_names + [""][page + 1 * 4 : page + 1 * 4 + 4]:

        def right_button():
            play(page + 1)

        rightpage = render.TextButton(0.95, 0.4, 96, 32, "->", right_button)
    if page > 0:

        def left_button():
            play(page - 1)

        leftpage = render.TextButton(0.05, 0.4, 96, 32, "<-", left_button)
    backbutton = render.Button(
        0.1,
        0.92,
        "sprites\\buttons\\back.png",
        "sprites\\buttons\\backpressed.png",
        title,
    )


@scene
def register():
    log = render.Text(0.5, 0.10, "")
    name = render.Text(0.5, 0.20, f"Username (Case-sensitive)")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(0.5, 0.25)
    pw = render.Text(0.5, 0.35, f"Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(0.5, 0.40)
    pwbox.secure = True
    confirm = render.Text(0.5, 0.50, f"Confirm Password")
    confirm.color = current_theme().dark
    confirm.outline_color = current_theme().black
    confirmbox = render.InputTextBox(0.5, 0.55)
    confirmbox.secure = True
    namebox.tab_box = pwbox
    pwbox.tab_box = confirmbox
    confirmbox.tab_box = namebox

    def verify():
        if pwbox.text != confirmbox.text:
            log.text = "Passwords do not match."
            return
        if len(namebox.text) == 0:
            log.text = "Username must not be empty."
            return
        if len(pwbox.text) == 0:
            log.text = "Password field must not be empty."
            return
        if len(namebox.text) >= 32:
            log.text = (
                f"Username must be less than 32 characters. Yours: {len(namebox.text)}"
            )
            return
        if len(pwbox.text) >= 32:
            log.text = f"Your password must be less than 32 characters. Yours: {len(pwbox.text)}"
            return
        client.dic["username"] = namebox.text
        client.dic["password"] = pwbox.text
        log.text = client.request("create_account")
        if "Success" not in log.text:
            client.dic["username"] = ""
            client.dic["password"] = ""
        print(f"log text {log.text}")

    namebox.enter_func = verify
    pwbox.enter_func = verify
    confirmbox.enter_func = verify
    registerbutton = render.Button(
        0.5,
        0.67,
        "sprites\\buttons\\register.png",
        "sprites\\buttons\\registerpressed.png",
        verify,
    )
    back = render.Button(
        0.5,
        0.80,
        "sprites\\buttons\\back.png",
        "sprites\\buttons\\backpressed.png",
        login_scene,
    )


def login():
    login_reply = client.request("login")
    if login_reply == "False":
        return login_reply
    reply = client.request("get_token")
    client.dic["password"] = ""
    if reply != "False":
        client.dic["token"] = reply
        print(reply)
        title()
        return None
    return reply


def logout():
    client.dic["username"] = ""
    client.dic["password"] = ""
    client.dic["token"] = ""
    login_scene()


@scene
def login_scene():
    if client.dic["token"] != "":
        reply = client.request("verify_token")
        if reply == "True":
            title()
            return
    log = render.Text(0.5, 0.20, "Please log in or create an account.")
    name = render.Text(0.5, 0.30, f"Username (Case-sensitive)")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(0.5, 0.35)
    pw = render.Text(0.5, 0.45, f"Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(0.5, 0.50)
    pwbox.secure = True
    namebox.tab_box = pwbox
    pwbox.tab_box = namebox

    def verify():
        if len(namebox.text) == 0:
            log.text = "Username must not be empty."
            return
        if len(pwbox.text) == 0:
            log.text = "Password must not be empty."
            return
        client.dic["username"] = namebox.text
        client.dic["password"] = pwbox.text
        reply = login()
        if reply is not None:
            log.text = reply

    namebox.enter_func = verify
    pwbox.enter_func = verify
    loginbutton = render.Button(
        0.5,
        0.62,
        "sprites\\buttons\\login.png",
        "sprites\\buttons\\loginpressed.png",
        verify,
    )
    registerbutton = render.Button(
        0.5,
        0.75,
        "sprites\\buttons\\register.png",
        "sprites\\buttons\\registerpressed.png",
        register,
    )


@scene
def character_selection():
    ...
    # player_info = client.requestdic("player_info")
    # if player_info["setup"]:
    #     Sylladex.current_sylladex().validate()
    #     map_scene()
    # else:
    #     namecharacter() # todo: change to play game function


@scene
def newsessionprompt():
    text = render.Text(0.5, 0.3, f"Create a new session?")
    text.color = current_theme().dark
    text.outline_color = current_theme().black
    text2 = render.Text(
        0.5, 0.35, f"The first character to join will become the admin of the session."
    )
    text2.color = current_theme().dark
    text2.outline_color = current_theme().black
    new = render.Button(
        0.5,
        0.48,
        "sprites\\buttons\\newsession.png",
        "sprites\\buttons\\newsessionpressed.png",
        newsession,
    )
    back = render.Button(
        0.5,
        0.60,
        "sprites\\buttons\\back.png",
        "sprites\\buttons\\backpressed.png",
        title,
    )


@scene
def newsession():
    log = render.Text(0.5, 0.10, "")
    name = render.Text(0.5, 0.20, f"Session Name")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(0.5, 0.25)
    pw = render.Text(0.5, 0.35, f"Session Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(0.5, 0.40)
    pwbox.secure = True
    confirm = render.Text(0.5, 0.50, f"Confirm Password")
    confirm.color = current_theme().dark
    confirm.outline_color = current_theme().black
    confirmbox = render.InputTextBox(0.5, 0.55)
    confirmbox.secure = True
    namebox.tab_box = pwbox
    pwbox.tab_box = confirmbox
    confirmbox.tab_box = namebox

    def verify():
        if pwbox.text != confirmbox.text:
            log.text = "Passwords do not match."
            return
        if len(namebox.text) == 0:
            log.text = "Session name must not be empty."
            return
        if len(pwbox.text) == 0:
            log.text = "Password field must not be empty."
            return
        if len(namebox.text) > 32:
            log.text = f"Session name must be less than 32 characters. Yours: {len(namebox.text)}"
            return
        if len(pwbox.text) > 32:
            log.text = f"Your password must be less than 32 characters. Yours: {len(pwbox.text)}"
            return
        client.dic["session_name"] = namebox.text
        client.dic["session_password"] = pwbox.text
        log.text = client.request("create_session")
        if "success" not in log.text:
            client.dic["session_name"] = ""
        client.dic["session_password"] = ""
        print(f"log text {log.text}")

    namebox.enter_func = verify
    pwbox.enter_func = verify
    confirmbox.enter_func = verify
    confirm = render.Button(
        0.5,
        0.67,
        "sprites\\buttons\\confirm.png",
        "sprites\\buttons\\confirmpressed.png",
        verify,
    )
    back = render.Button(
        0.5,
        0.80,
        "sprites\\buttons\\back.png",
        "sprites\\buttons\\backpressed.png",
        title,
    )


@scene
def connect():
    log = render.Text(0.5, 0.1, "")
    title_text = render.Text(0.5, 0.2, f"Connect to a session.")
    title_text.color = current_theme().dark
    title_text.outline_color = current_theme().black
    name = render.Text(0.5, 0.30, f"Session Name")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(0.5, 0.35)
    pw = render.Text(0.5, 0.45, f"Session Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(0.5, 0.50)
    pwbox.secure = True
    namebox.tab_box = pwbox
    pwbox.tab_box = namebox

    def verify():
        if len(namebox.text) == 0:
            log.text = "Session name must not be empty."
            return
        if len(pwbox.text) == 0:
            log.text = "Password must not be empty."
            return
        log.text = "Connecting..."
        client.dic["session_name"] = namebox.text
        client.dic["session_password"] = pwbox.text
        log.text = client.request("join_session")
        if "Success" not in log.text:
            client.dic["session_name"] = ""
            client.dic["session_password"] = ""
        else:
            client.dic["session_password"] = ""
            creator = CharacterCreator()
            creator.start()
        print(f"log text {log.text}")

    namebox.enter_func = verify
    pwbox.enter_func = verify
    confirm = render.Button(
        0.5,
        0.62,
        "sprites\\buttons\\confirm.png",
        "sprites\\buttons\\confirmpressed.png",
        verify,
    )
    back = render.Button(
        0.5,
        0.75,
        "sprites\\buttons\\back.png",
        "sprites\\buttons\\backpressed.png",
        play,
    )


class CharacterCreator:
    def __init__(self):
        self.name: str = "default"
        self.noun: str = "bug"
        self.pronouns: tuple[str, str, str, str] = ("they", "them", "their", "theirs")
        self.interests: list[str] = []
        self.aspect: str = random.choice(self.ASPECTS)
        self.gameclass: str = "knight"
        self.secondaryvial: str = "mangrit"
        self.modus: str = "array"
        self.gristcategory: str = "stone"
        self.kingdom: str = "prospit"
        self.map_name: str = ""
        self.symbol_dict: dict = config.get_random_symbol()

    def start(self):
        self.make_symbol()

    @scene
    def make_symbol(self):
        symbol = render.Symbol(0.66, 0.5, self.symbol_dict)

        def get_button_func(part, direction: str):
            def button_func():
                current = self.symbol_dict[part]
                current_index = config.possible_parts[part].index(current)
                if direction == "left":
                    new_index = current_index - 1
                else:
                    new_index = current_index + 1
                try:
                    new_item_name = config.possible_parts[part][new_index]
                except IndexError:
                    new_item_name = config.possible_parts[part][0]
                self.symbol_dict[part] = new_item_name
                if (
                    self.symbol_dict["style_dict"][part]
                    not in config.part_styles[part][new_item_name]
                ):
                    self.symbol_dict["style_dict"][part] = random.choice(
                        config.part_styles[part][new_item_name]
                    )
                symbol.__init__(0.66, 0.5, self.symbol_dict)
                symbol.surf = symbol.load_image("")

            return button_func

        def get_style_button_func(part, direction: str):
            def button_func():
                current_style = self.symbol_dict["style_dict"][part]
                current_item_name = self.symbol_dict[part]
                current_index = config.part_styles[part][current_item_name].index(
                    current_style
                )
                if direction == "left":
                    new_index = current_index - 1
                else:
                    new_index = current_index + 1
                try:
                    new_style_name = config.part_styles[part][current_item_name][
                        new_index
                    ]
                except IndexError:
                    new_style_name = config.part_styles[part][current_item_name][0]
                self.symbol_dict["style_dict"][part] = new_style_name
                symbol.__init__(0.66, 0.5, self.symbol_dict)
                symbol.surf = symbol.load_image("")

            return button_func

        def get_style_button_condition(part):
            def condition():
                current_item_name = self.symbol_dict[part]
                if len(config.part_styles[part][current_item_name]) > 1:
                    return True
                else:
                    return False

            return condition

        def get_text_func(part):
            def text_func():
                return self.symbol_dict[part]

            return text_func

        def get_style_text_func(part):
            def text_func():
                current_item_name = self.symbol_dict[part]
                style = self.symbol_dict["style_dict"][part]
                if len(config.part_styles[part][current_item_name]) > 1:
                    return style
                else:
                    return ""

            return text_func

        def get_color_button_func(color_list: list[int]):
            def color_button_func():
                self.symbol_dict["color"] = color_list
                symbol.__init__(0.66, 0.5, self.symbol_dict)
                symbol.surf = symbol.load_image("")

            return color_button_func

        def random_button():
            self.symbol_dict = config.get_random_symbol(self.symbol_dict["base"])
            symbol.__init__(0.66, 0.5, self.symbol_dict)
            symbol.surf = symbol.load_image("")

        randomize = render.TextButton(0.33, 0.05, 196, 32, ">RANDOM", random_button)
        for i, part in enumerate(config.possible_parts):
            y = 0.13 + 0.1 * i
            text = render.Text(0.33, y, "fuck")
            text.text_func = get_text_func(part)
            text.color = current_theme().dark
            label = render.Text(0.5, -0.1, part)
            label.fontsize = 18
            label.bind_to(text)
            left_button = render.TextButton(
                0.2, y, 32, 32, "<", get_button_func(part, "left")
            )
            right_button = render.TextButton(
                0.46, y, 32, 32, ">", get_button_func(part, "right")
            )
            style_label = render.Text(0.5, 1.2, "fuck")
            style_label.text_func = get_style_text_func(part)
            style_label.color = current_theme().dark
            style_label.fontsize = 18
            style_label.bind_to(text)
            left_style_button = render.TextButton(
                0.27, y + 0.04, 20, 20, "<", get_style_button_func(part, "left")
            )
            left_style_button.draw_condition = get_style_button_condition(part)
            right_style_button = render.TextButton(
                0.39, y + 0.04, 20, 20, ">", get_style_button_func(part, "right")
            )
            right_style_button.draw_condition = get_style_button_condition(part)
        color_swatch_x = 680
        color_swatch_y = 50
        color_swatch_wh = 32
        color_swatch_columns = 12
        color_swatch_rows = math.ceil(
            len(config.pickable_colors) / color_swatch_columns
        )
        current_column = 0
        current_row = 0
        outline_width = 4
        background = render.SolidColor(
            color_swatch_x - outline_width,
            color_swatch_y - outline_width,
            color_swatch_wh * color_swatch_columns + outline_width * 2,
            color_swatch_wh * color_swatch_rows + outline_width * 2,
            current_theme().dark,
        )
        background.border_radius = 2
        for color_list in config.pickable_colors:
            x = color_swatch_x + color_swatch_wh * current_column
            y = color_swatch_y + color_swatch_wh * current_row
            color = pygame.Color(color_list[0], color_list[1], color_list[2])
            color_button = render.TextButton(
                x,
                y,
                color_swatch_wh,
                color_swatch_wh,
                "",
                get_color_button_func(color_list),
            )
            color_button.absolute = True
            color_button.fill_color = color
            color_button.hover_color = color
            color_button.outline_color = color
            current_column += 1
            if current_column == color_swatch_columns:
                current_column = 0
                current_row += 1
        custom_color_button = render.TextButton(
            1080, 65, 128, 32, ">CUSTOM", self.pick_custom_color
        )
        custom_color_button.absolute = True
        confirm_button = render.Button(
            0.65,
            0.75,
            "sprites\\buttons\\confirm.png",
            "sprites\\buttons\\confirmpressed.png",
            self.namecharacter,
        )

    @scene
    def pick_custom_color(self):
        color_list = self.symbol_dict["color"]
        red_box = render.InputTextBox(0.5, 0.5, 128, 32)
        green_box = render.InputTextBox(0.5, 0.6, 128, 32)
        blue_box = render.InputTextBox(0.5, 0.7, 128, 32)
        red_box.numbers_only = True
        red_box.maximum_value = 255
        red_box.text = str(color_list[0])
        red_label = render.Text(0.5, -0.3, "RED")
        red_label.fontsize = 20
        red_label.color = current_theme().dark
        red_label.bind_to(red_box)
        green_box.numbers_only = True
        green_box.maximum_value = 255
        green_box.text = str(color_list[1])
        green_label = render.Text(0.5, -0.3, "GREEN")
        green_label.fontsize = 20
        green_label.color = current_theme().dark
        green_label.bind_to(green_box)
        blue_box.numbers_only = True
        blue_box.maximum_value = 255
        blue_box.text = str(color_list[2])
        blue_label = render.Text(0.5, -0.3, "BLUE")
        blue_label.fontsize = 20
        blue_label.color = current_theme().dark
        blue_label.bind_to(blue_box)

        def color_display_func():
            try:
                r, g, b = int(red_box.text), int(green_box.text), int(blue_box.text)
                r, g, b = max(r, 0), max(g, 0), max(b, 0)
                return pygame.Color(r, g, b)
            except ValueError:
                return pygame.Color(0, 0, 0)

        color_display_wh = 128
        color_display = render.SolidColor(
            render.SCREEN_WIDTH // 2 - color_display_wh // 2,
            3 * render.SCREEN_HEIGHT // 10 - color_display_wh // 2,
            color_display_wh,
            color_display_wh,
            pygame.Color(0, 0, 0),
        )
        color_display.color_func = color_display_func

        def confirm_button_func():
            r, g, b = int(red_box.text), int(green_box.text), int(blue_box.text)
            self.symbol_dict["color"] = [r, g, b]
            self.make_symbol()

        confirm_button = render.Button(
            0.5,
            0.85,
            "sprites\\buttons\\confirm.png",
            "sprites\\buttons\\confirmpressed.png",
            confirm_button_func,
        )

    @scene
    def namecharacter(self):
        symbol = render.Symbol(0.5, 0.65, self.symbol_dict)
        log = render.Text(0.5, 0.10, "")
        l2text = render.Text(0.5, 0.3, "What will this being's name be?")
        l2text.color = current_theme().dark
        l2text.outline_color = current_theme().black
        namebox = render.InputTextBox(0.5, 0.4)

        def verify():
            if len(namebox.text) > 0 and len(namebox.text) < 32:
                self.name = namebox.text
                self.nouncharacter()
            else:
                log.text = "Name is too long or too short."

        confirm = render.Button(
            0.5,
            0.9,
            "sprites\\buttons\\confirm.png",
            "sprites\\buttons\\confirmpressed.png",
            verify,
        )
        backbutton = render.Button(
            0.08,
            0.1,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.make_symbol,
        )

    @scene
    def nouncharacter(self):
        log = render.Text(0.5, 0.10, "")
        log2 = render.Text(0.5, 0.20, "")
        l1text = render.Text(
            0.5, 0.3, f'You don\'t think "being" is a very accurate descriptor.'
        )
        l1text.color = current_theme().dark
        l1text.outline_color = current_theme().black
        l2text = render.Text(0.5, 0.4, f"What word best describes {self.name}?")
        l2text.color = current_theme().dark
        l2text.outline_color = current_theme().black
        namebox = render.InputTextBox(0.5, 0.5)

        def verify():
            if len(namebox.text) > 0 and len(namebox.text) < 32:
                example = f"A newly-created {namebox.text} stands in a room."
                if log.text == example:
                    self.noun = namebox.text
                    self.pronounscharacter()
                else:
                    log.text = example
                    log2.text = "Press confirm again if this sounds okay."
            else:
                log.text = "That word is too long or too short."
                log2.text = ""

        confirm = render.Button(
            0.5,
            0.6,
            "sprites\\buttons\\confirm.png",
            "sprites\\buttons\\confirmpressed.png",
            verify,
        )
        backbutton = render.Button(
            0.5,
            0.7,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.namecharacter,
        )

    @scene
    def pronounscharacter(self):
        log = render.Text(0.5, 0.20, "")
        log2 = render.Text(0.5, 0.30, "")
        log3 = render.Text(0.5, 0.40, "")
        l1text = render.Text(0.5, 0.5, f"What pronouns should this {self.noun} go by?")
        l1text.color = current_theme().dark
        l1text.outline_color = current_theme().black

        def confirmnouns(pronouns):  # [0] they [1] them [2] their [3] theirs
            example1 = f"A newly-created {self.noun} stands in {pronouns[2]} room. It surrounds {pronouns[1]}."
            example2 = f"Today {pronouns[0]} will play a game with some friends of {pronouns[3]}."
            if log.text == example1 and log2.text == example2:
                self.pronouns = pronouns
                self.choose_aspect()
            else:
                log.text = example1
                log2.text = example2
                log3.text = "Press your selection again if this sounds okay."

        def himnouns():
            pronouns = ["he", "him", "his", "his"]
            confirmnouns(pronouns)

        def hernouns():
            pronouns = ["she", "her", "her", "hers"]
            confirmnouns(pronouns)

        def themnouns():
            pronouns = ["they", "them", "their", "theirs"]
            confirmnouns(pronouns)

        hehim = render.Button(
            0.20,
            0.62,
            "sprites\\buttons\\hehim.png",
            "sprites\\buttons\\hehimpressed.png",
            himnouns,
        )
        sheher = render.Button(
            0.4,
            0.62,
            "sprites\\buttons\\sheher.png",
            "sprites\\buttons\\sheherpressed.png",
            hernouns,
        )
        theyem = render.Button(
            0.6,
            0.62,
            "sprites\\buttons\\theyem.png",
            "sprites\\buttons\\theyempressed.png",
            themnouns,
        )
        other = render.Button(
            0.8,
            0.62,
            "sprites\\buttons\\other.png",
            "sprites\\buttons\\otherpressed.png",
            self.custom_pronouns,
        )
        backbutton = render.Button(
            0.5,
            0.8,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.namecharacter,
        )

    @scene
    def custom_pronouns(self):
        example1 = f"        stands in        room. It surrounds       ."
        example2 = f"Today        will play a game with some friends of        ."
        name = render.Text(0.15, 0.2, str(self.name))
        name.set_fontsize_by_width(200)
        name.color = current_theme().dark
        log = render.Text(0.5, 0.20, example1)
        log2 = render.Text(0.5, 0.30, example2)
        their_box = render.InputTextBox(0.435, 0.2, 120, 32)
        their_box.text = "their"
        them_box = render.InputTextBox(0.815, 0.2, 120, 32)
        them_box.text = "them"
        they_box = render.InputTextBox(0.195, 0.3, 120, 32)
        they_box.text = "they"
        theirs_box = render.InputTextBox(0.865, 0.3, 120, 32)
        theirs_box.text = "theirs"

        def confirm_func():
            self.pronouns = (
                they_box.text,
                them_box.text,
                their_box.text,
                theirs_box.text,
            )
            self.choose_aspect()

        confirm_button = render.Button(
            0.5,
            0.5,
            "sprites\\buttons\\confirm.png",
            "sprites\\buttons\\confirmpressed.png",
            confirm_func,
        )
        backbutton = render.Button(
            0.5,
            0.66,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.pronounscharacter,
        )

    ASPECTS_DESCRIPTIONS = {
        "space": [
            "Associated with METTLE, the damage reduction stat.",
            "SPACE is a part of the fabric of reality itself.",
            "These players are big thinkers and innovators, creatives capable of seeing the big picture.",
        ],
        "time": [
            "Associated with SPUNK, the damage stat.",
            "TIME is the counterpart to SPACE, as it composes the other part of the fabric of reality.",
            "These players are action-driven and goal-focused.",
        ],
        "mind": [
            "Associated with TACT, the resource stat.",
            "MIND players are the greatest minds in the universe.",
            "These players are cerebral and analytic, capable of creating and executing plans materfully.",
        ],
        "heart": [
            "Associated with VIGOR, the maximum HP stat.",
            "HEART represents the soul itself.",
            "These players are very in-tune with their sense of self and emotions.",
        ],
        "hope": [
            "The HOPE vial gives buffs to all stats each turn.",
            "HOPE represents justice and hope.",
            "These players have a very strong sense of morality.",
            "By its very nature, HOPE defies destiny.",
        ],
        "rage": [
            "The RAGE vial increases both damage dealt and received.",
            "RAGE represents negative emotions and rage.",
            "These players are bringers of chaos, unpredictable and unstable.",
        ],
        "breath": [
            "Associated with SAVVY, the auto-parry and speed stat.",
            "BREATH represents freedom, confidence and heroism.",
            "These players do their own thing and can't be held down by others.",
        ],
        "blood": [
            "Associated with the VIM vial, used as a resource in combat.",
            "BLOOD represents bonds, both metaphorical and literal.",
            "These players motivate their allies and form strong relationships between their teams.",
        ],
        "life": [
            "Associated with the HEALTH vial.",
            "LIFE represents life, healing and empathy.",
            "These players are caretakers and nurturers.",
            "A LIFE palyer is deeply empathetic and intuitive.",
        ],
        "doom": [
            "Associated with draining the HEALTH vial.",
            "DOOM represents futility, restriction, and doom.",
            "These players are cursed by fate to suffer, though their misery gives unique insight into others.",
        ],
        "light": [
            "Associated with LUCK, which stacks the deck for you.",
            "LIGHT represents fortune and knowledge.",
            "These players enjoy finding loopholes in the rules they can exploit.",
        ],
        "void": [
            "Associated with draining the VIM and ASPECT vials.",
            "VOID represents lacking, obfuscation, and nothingness.",
            "Players of this aspect are mysterious and skeptical.",
            "They don't put much value in faith.",
        ],
    }

    ASPECTS = list(ASPECTS_DESCRIPTIONS.keys())

    CLASS_DESCRIPTIONS = {
        "knight": [
            "Fights with ASPECT",
            "Exploits ASPECT",
        ],
        "page": [
            "Provides ASPECT",
            "Has great potential",
        ],
        "prince": [
            "Destroys ASPECT",
            "Destroys with ASPECT",
        ],
        "bard": [
            "ASPECTless",
            "Heralds ASPECTpocalypse",
        ],
        "thief": [
            "Steals ASPECT",
            "Hoards ASPECT",
        ],
        "rogue": [
            "Steals ASPECT",
            "Shares ASPECT",
        ],
        "mage": [
            "Sees ASPECT",
            "Pursues ASPECT",
        ],
        "witch": ["Manipulates ASPECT"],
        "heir": [
            "Becomes ASPECT",
            "Inherits ASPECT",
        ],
        "maid": [
            "Creates ASPECT",
        ],
        "sylph": ["Restores ASPECT", "Heals with ASPECT"],
    }

    CLASSES = list(CLASS_DESCRIPTIONS.keys())

    @scene
    def choose_aspect(self):
        current_index = self.ASPECTS.index(self.aspect)
        try:
            next_aspect = self.ASPECTS[current_index + 1]
        except IndexError:
            next_aspect = self.ASPECTS[0]
        next_aspect_theme = themes.themes[next_aspect]
        previous_aspect = self.ASPECTS[current_index - 1]
        previous_aspect_theme = themes.themes[previous_aspect]

        def next_aspect_func():
            self.aspect = next_aspect
            self.choose_aspect()

        def previous_aspect_func():
            self.aspect = previous_aspect
            self.choose_aspect()

        theme = themes.themes[self.aspect]
        bg = render.SolidColor(
            0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.light
        )
        icon_bg = render.SolidColor(0.5, 0.15, 130, 130, theme.dark)
        icon_bg.border_radius = 4
        icon_bg.absolute = False
        icon = render.Image(0.5, 0.15, f"sprites/aspects/{self.aspect}120.png")
        icon.convert = False
        previous_bg = render.SolidColor(0.4, 0.15, 64, 64, previous_aspect_theme.dark)
        previous_bg.border_radius = 2
        previous_bg.absolute = False
        previous_aspect_icon = render.Button(
            0.4,
            0.15,
            f"sprites/aspects/{previous_aspect}120.png",
            None,
            previous_aspect_func,
        )
        previous_aspect_icon.convert = False
        previous_aspect_icon.scale = 0.5
        next_bg = render.SolidColor(0.6, 0.15, 64, 64, next_aspect_theme.dark)
        next_bg.border_radius = 2
        next_bg.absolute = False
        next_aspect_icon = render.Button(
            0.6, 0.15, f"sprites/aspects/{next_aspect}120.png", None, next_aspect_func
        )
        next_aspect_icon.convert = False
        next_aspect_icon.scale = 0.5
        title = render.Text(0.5, 0.3, self.aspect.upper())
        title.color = theme.black
        title.outline_color = theme.white
        y = 0.35
        for line in self.ASPECTS_DESCRIPTIONS[self.aspect]:
            text = render.Text(0.5, y, line)
            text.color = theme.white
            text.outline_color = theme.black
            text.fontsize = 20
            y += 0.05
        confirm_button = render.Button(
            0.5,
            0.65,
            "sprites\\buttons\\confirm.png",
            "sprites\\buttons\\confirmpressed.png",
            self.chooseclass,
            theme=theme,
        )
        backbutton = render.Button(
            0.08,
            0.07,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.pronounscharacter,
            theme=theme,
        )

    def make_classbutton(self, game_class):
        def button():
            self.gameclass = game_class
            self.chooseinterests()

        return button

    @scene
    def chooseclass(self):
        theme = themes.themes[self.aspect]
        bg = render.SolidColor(
            0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.light
        )
        knighttitle = render.Text(0.14, 0.19, f"Knight")
        knighttitle.color = theme.black
        knighttitle.outline_color = theme.white
        knightsymbol = render.Button(
            0.14,
            0.3,
            "sprites\\classes\\knight.png",
            None,
            self.make_classbutton("knight"),
            theme=theme,
        )
        knighttext = render.Text(0.14, 0.4, f"Fights with {self.aspect.upper()}")
        knighttext.fontsize = 15
        knighttext.color = theme.black
        knighttext2 = render.Text(0.14, 0.42, f"Exploits {self.aspect.upper()}")
        knighttext2.fontsize = 15
        knighttext2.color = theme.black
        pagetitle = render.Text(0.14, 0.59, f"Page")
        pagetitle.color = theme.black
        pagetitle.outline_color = theme.white
        pagesymbol = render.Button(
            0.14,
            0.7,
            "sprites\\classes\\page.png",
            None,
            self.make_classbutton("page"),
            theme=theme,
        )
        pagetext = render.Text(0.14, 0.8, f"Provides {self.aspect.upper()}")
        pagetext.fontsize = 15
        pagetext.color = theme.black
        pagetext2 = render.Text(0.14, 0.82, f"Scales")
        pagetext2.fontsize = 15
        pagetext2.color = theme.black
        princetitle = render.Text(0.29, 0.19, f"Prince")
        princetitle.color = theme.black
        princetitle.outline_color = theme.white
        princesymbol = render.Button(
            0.29,
            0.3,
            "sprites\\classes\\prince.png",
            None,
            self.make_classbutton("prince"),
            theme=theme,
        )
        princetext = render.Text(0.29, 0.4, f"Destroys {self.aspect.upper()}")
        princetext.fontsize = 15
        princetext.color = theme.black
        princetext2 = render.Text(0.29, 0.42, f"Destroys with {self.aspect.upper()}")
        princetext2.fontsize = 15
        princetext2.color = theme.black
        bardtitle = render.Text(0.29, 0.59, f"Bard")
        bardtitle.color = theme.black
        bardtitle.outline_color = theme.white
        bardsymbol = render.Button(
            0.29,
            0.7,
            "sprites\\classes\\bard.png",
            None,
            self.make_classbutton("bard"),
            theme=theme,
        )
        bardtext = render.Text(0.29, 0.8, f"{self.aspect.upper()}less")
        bardtext.fontsize = 15
        bardtext.color = theme.black
        bardtext2 = render.Text(0.29, 0.82, f"Heralds {self.aspect.upper()}-stinction")
        bardtext2.fontsize = 15
        bardtext2.color = theme.black
        thieftitle = render.Text(0.43, 0.19, f"Thief")
        thieftitle.color = theme.black
        thieftitle.outline_color = theme.white
        thiefsymbol = render.Button(
            0.43,
            0.3,
            "sprites\\classes\\thief.png",
            None,
            self.make_classbutton("thief"),
            theme=theme,
        )
        thieftext = render.Text(0.43, 0.4, f"Steals {self.aspect.upper()}")
        thieftext.fontsize = 15
        thieftext.color = theme.black
        thieftext2 = render.Text(0.43, 0.42, f"Hoards {self.aspect.upper()}")
        thieftext2.fontsize = 15
        thieftext2.color = theme.black
        roguetitle = render.Text(0.43, 0.59, f"Rogue")
        roguetitle.color = theme.black
        roguetitle.outline_color = theme.white
        roguesymbol = render.Button(
            0.43,
            0.7,
            "sprites\\classes\\rogue.png",
            None,
            self.make_classbutton("rogue"),
            theme=theme,
        )
        roguetext = render.Text(0.43, 0.8, f"Steals {self.aspect.upper()}")
        roguetext.fontsize = 15
        roguetext.color = theme.black
        roguetext2 = render.Text(0.43, 0.82, f"Shares {self.aspect.upper()}")
        roguetext2.fontsize = 15
        roguetext2.color = theme.black
        magetitle = render.Text(0.57, 0.19, f"Mage")
        magetitle.color = theme.black
        magetitle.outline_color = theme.white
        magesymbol = render.Button(
            0.57,
            0.3,
            "sprites\\classes\\placeholder.png",
            None,
            self.make_classbutton("mage"),
            theme=theme,
        )
        magetext = render.Text(0.57, 0.4, f"Sees {self.aspect.upper()}")
        magetext.fontsize = 15
        magetext.color = theme.black
        magetext2 = render.Text(0.57, 0.42, f"Pursues {self.aspect.upper()}")
        magetext2.fontsize = 15
        magetext2.color = theme.black
        seertitle = render.Text(0.57, 0.59, f"Seer")
        seertitle.color = theme.black
        seertitle.outline_color = theme.white
        seersymbol = render.Button(
            0.57,
            0.7,
            "sprites\\classes\\seer.png",
            None,
            self.make_classbutton("seer"),
            theme=theme,
        )
        seertext = render.Text(0.57, 0.8, f"Sees {self.aspect.upper()}")
        seertext.fontsize = 15
        seertext.color = theme.black
        seertext2 = render.Text(0.57, 0.82, f"Avoids {self.aspect.upper()}")
        seertext2.fontsize = 15
        seertext2.color = theme.black
        witchtitle = render.Text(0.71, 0.19, f"Witch")
        witchtitle.color = theme.black
        witchtitle.outline_color = theme.white
        witchsymbol = render.Button(
            0.71,
            0.3,
            "sprites\\classes\\witch.png",
            None,
            self.make_classbutton("witch"),
            theme=theme,
        )
        witchtext = render.Text(0.71, 0.4, f"Manipulates {self.aspect.upper()}")
        witchtext.fontsize = 15
        witchtext.color = theme.black
        heirtitle = render.Text(0.71, 0.59, f"Heir")
        heirtitle.color = theme.black
        heirtitle.outline_color = theme.white
        heirsymbol = render.Button(
            0.71,
            0.7,
            "sprites\\classes\\heir.png",
            None,
            self.make_classbutton("heir"),
            theme=theme,
        )
        heirtext = render.Text(0.71, 0.8, f"Becomes {self.aspect.upper()}")
        heirtext.fontsize = 15
        heirtext.color = theme.black
        heirtext2 = render.Text(0.71, 0.82, f"Inherits {self.aspect.upper()}")
        heirtext2.fontsize = 15
        heirtext2.color = theme.black
        maidtitle = render.Text(0.86, 0.19, f"Maid")
        maidtitle.color = theme.black
        maidtitle.outline_color = theme.white
        maidsymbol = render.Button(
            0.86,
            0.3,
            "sprites\\classes\\maid.png",
            None,
            self.make_classbutton("maid"),
            theme=theme,
        )
        maidtext = render.Text(0.86, 0.4, f"Creates {self.aspect.upper()}")
        maidtext.fontsize = 15
        maidtext.color = theme.black
        sylphtitle = render.Text(0.86, 0.59, f"Sylph")
        sylphtitle.color = theme.black
        sylphtitle.outline_color = theme.white
        sylphsymbol = render.Button(
            0.86,
            0.7,
            "sprites\\classes\\sylph.png",
            None,
            self.make_classbutton("sylph"),
            theme=theme,
        )
        sylphtext = render.Text(0.86, 0.8, f"Restores {self.aspect.upper()}")
        sylphtext.fontsize = 15
        sylphtext.color = theme.black
        sylphtext2 = render.Text(0.86, 0.82, f"Heals with {self.aspect.upper()}")
        sylphtext2.fontsize = 15
        sylphtext2.color = theme.black
        backbutton = render.Button(
            0.1,
            0.08,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.choose_aspect,
            theme=theme,
        )

    @scene
    def chooseinterests(self):
        # text = render.Text(0.5, 0.2, f"Interests: {client.requestdic('interests')}")
        logtext = render.Text(0.5, 0.2, "Choose 3 interests.")
        if self.interests:
            interests_text = render.Text(
                0.5, 0.3, f'Chosen: {", ".join(self.interests)}'
            )

        def option_active_func(interest: str):
            if interest in self.interests:
                return True
            else:
                return False

        def choose_interest_func_constructor(interest: str):
            def button_func():
                if interest in self.interests:
                    self.interests.remove(interest)
                else:
                    self.interests.append(interest)

            return button_func

        def choose():
            interests = list(client.requestdic("interests"))
            render.show_options_with_search(
                interests,
                choose_interest_func_constructor,
                "Choose 3 interests.",
                self.chooseinterests,
                current_theme(),
                option_active_func=option_active_func,
                reload_on_button_press=True,
            )

        choose_button = render.TextButton(0.5, 0.5, 192, 32, "Choose", choose)
        if len(self.interests) == 3:
            confirm = render.Button(
                0.5,
                0.7,
                "sprites\\buttons\\confirm.png",
                "sprites\\buttons\\confirmpressed.png",
                self.choosevial,
            )
        backbutton = render.Button(
            0.1,
            0.07,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.chooseclass,
        )

    @scene
    def choosevial(self, page=0):
        theme = current_theme()
        VIAL_COORDS = {
            0: (0.33, 0.33),
            1: (0.66, 0.33),
            2: (0.33, 0.66),
            3: (0.66, 0.66),
        }
        secondary_vials: dict[str, str] = client.requestdic(intent="secondary_vials")

        def vialbutton(vial):
            def out():
                self.secondaryvial = vial
                self.choosemodus()

            return out

        logtext = render.Text(0.5, 0.05, "Choose a SECONDARY VIAL.")
        current_vials = list(secondary_vials)[page * 4 : (page + 1) * 4]
        for i, vial_name in enumerate(current_vials):
            x, y = VIAL_COORDS[i]
            vial_bg = render.SolidColor(x, y, 375, 200, theme.dark)
            vial_bg.absolute = False
            vial_bg.outline_color = theme.white
            vial_bg.border_radius = 5
            button = render.TextButton(x, y, 375, 200, "", vialbutton(vial_name))
            button.draw_sprite = False
            vial = render.Vial(0.5, 0.2, 150, vial_name, 1)
            vial.absolute = False
            vial.bind_to(vial_bg)
            title_text = render.Text(0.5, 0.4, vial_name.upper())
            title_text.color = theme.white
            title_text.set_fontsize_by_width(375)
            title_text.bind_to(vial_bg)
            descriptions = secondary_vials[vial_name].split("\n")
            for i, line in enumerate(descriptions):
                y = 0.6 + 0.1 * i
                description = render.Text(0.5, y, line)
                description.fontsize = 16
                description.set_fontsize_by_width(375)
                description.color = theme.white
                description.bind_to(vial_bg)

        def last_page():
            self.choosevial(page - 1)

        def next_page():
            self.choosevial(page + 1)

        if page != 0:
            last_page_button = render.TextButton(0.1, 0.5, 64, 32, "<-", last_page)
        if list(secondary_vials)[(page + 1) * 4 : (page + 2) * 4]:
            next_page_button = render.TextButton(0.9, 0.5, 64, 32, "->", next_page)
        backbutton = render.Button(
            0.1,
            0.07,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.chooseinterests,
        )

    @scene
    def choosemodus(self, page=0):
        def modusbutton(modus_name: str):
            def out():
                self.modus = modus_name
                self.choose_moon()

            return out

        modus_to_display = list(sylladex.moduses)[page]
        modus = sylladex.moduses[modus_to_display]
        logtext = render.Text(0.5, 0.05, "Select your starting FETCH MODUS.")
        modus_image = render.Button(
            0.5, 0.45, modus.front_path, None, modusbutton(modus.modus_name)
        )
        modus_label = render.Text(0.55, 1.05, modus.modus_name)
        modus_label.bind_to(modus_image)
        modus_description = render.Text(0.55, 1.13, modus.description)
        modus_description.fontsize = 20
        modus_description.bind_to(modus_image)
        modus_difficulty = render.Text(0.55, 1.23, f"Difficulty: {modus.difficulty}")
        modus_difficulty.fontsize = 20
        modus_difficulty.bind_to(modus_image)

        def rightpage():
            new_page = page + 1
            try:
                list(sylladex.moduses)[new_page]
            except IndexError:
                new_page = 0
            self.choosemodus(new_page)

        def leftpage():
            new_page = page - 1
            if new_page < 0:
                new_page = len(sylladex.moduses) - 1
            self.choosemodus(new_page)

        leftbutton = render.TextButton(0.3, 0.5, 96, 32, "<-", leftpage)
        rightbutton = render.TextButton(0.7, 0.5, 96, 32, "->", rightpage)
        backbutton = render.Button(
            0.1,
            0.07,
            "sprites/buttons/back.png",
            "sprites/buttons/backpressed.png",
            self.choosevial,
        )

    @scene
    def choose_moon(self):
        prospit_theme = themes.prospit
        prospitbg = render.SolidColor(
            0, 0, render.SCREEN_WIDTH // 2, render.SCREEN_HEIGHT, prospit_theme.light
        )
        prospit_image = render.Image(0.5, 0.37, "sprites/prospit.png", convert=False)
        prospit_image.bind_to(prospitbg)
        prospit_title = render.Text(0.45, 0.6, "Prospit")
        prospit_title.fontsize = 50
        prospit_title.antialias = False
        prospit_title.font_location = "./fonts/Carima Regular.ttf"
        prospit_title.color = prospit_theme.white
        prospit_title.outline_color = prospit_theme.dark
        prospit_title.bind_to(prospitbg)

        def choose_prospit():
            self.kingdom = "prospit"
            self.choose_map()

        choose_prospit_button = render.TextButton(
            0.5, 0.95, 128, 48, "CHOOSE", choose_prospit, theme=prospit_theme
        )
        choose_prospit_button.text_color = prospit_theme.dark
        choose_prospit_button.bind_to(prospitbg)
        prospit_line_1 = render.Text(
            0.5, 0.75, "Prospit dreamers are optimistic, reactive and intuitive."
        )
        prospit_line_1.fontsize = 18
        prospit_line_1.color = prospit_theme.white
        prospit_line_1.outline_color = prospit_theme.dark
        prospit_line_1.bind_to(prospitbg)
        prospit_line_2 = render.Text(
            0.5, 0.8, "These dreamers enjoy the visions of Skaia."
        )
        prospit_line_2.fontsize = 18
        prospit_line_2.color = prospit_theme.white
        prospit_line_2.outline_color = prospit_theme.dark
        prospit_line_2.bind_to(prospitbg)
        derse_theme = themes.derse
        dersebg = render.SolidColor(
            render.SCREEN_WIDTH // 2,
            0,
            render.SCREEN_WIDTH // 2,
            render.SCREEN_HEIGHT,
            derse_theme.light,
        )
        derse_image = render.Image(0.5, 0.37, "sprites/derse.png", convert=False)
        derse_image.bind_to(dersebg)
        derse_title = render.Text(0.54, 0.6, "Derse")
        derse_title.fontsize = 50
        derse_title.antialias = False
        derse_title.font_location = "./fonts/Carima Regular.ttf"
        derse_title.color = derse_theme.white
        derse_title.outline_color = derse_theme.dark
        derse_title.bind_to(dersebg)

        def choose_derse():
            self.kingdom = "derse"
            self.choose_map()

        choose_derse_button = render.TextButton(
            0.5, 0.95, 128, 48, "CHOOSE", choose_derse, theme=derse_theme
        )
        choose_derse_button.text_color = derse_theme.dark
        choose_derse_button.bind_to(dersebg)
        derse_line_1 = render.Text(
            0.5, 0.75, "Derse dreamers are skeptical and rebellious."
        )
        derse_line_1.fontsize = 18
        derse_line_1.color = derse_theme.black
        derse_line_1.outline_color = derse_theme.dark
        derse_line_1.bind_to(dersebg)
        derse_line_2 = render.Text(
            0.5, 0.8, "They hear the whispers of the Furthest Ring."
        )
        derse_line_2.fontsize = 18
        derse_line_2.color = derse_theme.black
        derse_line_2.outline_color = derse_theme.dark
        derse_line_2.bind_to(dersebg)
        backbutton = render.Button(
            0.08,
            0.05,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.choosemodus,
            theme=prospit_theme,
        )

    @scene
    def choose_map(self):
        maps = client.requestdic(intent="house_maps")
        choices = list(maps)

        def button_func_constructor(map_name):
            def button_func():
                self.display_map(map_name, maps[map_name])

            return button_func

        render.show_options_with_search(
            choices,
            button_func_constructor,
            "Choose a starting map.",
            self.choose_moon,
            theme=current_theme(),
        )

    @scene
    def display_map(self, map_name, map_dict):
        map_editor = itemeditor.MapEditor()
        map_editor.loadinfo(map_name, map_dict)
        map_editor.tilemap = render.TileMap(0.5, 0.45, map_editor=map_editor)

        def confirm():
            self.map_name = map_name
            self.choosegrists()

        confirm_button = render.Button(
            0.5,
            0.9,
            "sprites\\buttons\\confirm.png",
            "sprites\\buttons\\confirmpressed.png",
            confirm,
        )
        backbutton = render.Button(
            0.08,
            0.05,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.choose_map,
        )

    @scene
    def choosegrists(self):
        # 19 grist categories
        # todo: add indicators for which grist types the session already has
        session_info = client.requestdic("session_info")
        available_types = session_info["current_grist_types"]
        logtext = render.Text(0.5, 0.05, "Select the type of land you would like.")
        infotext = render.Text(
            0.5,
            0.09,
            "A darkened background indicates grist already available in the session.",
        )
        infotext.fontsize = 20
        infotext = render.Text(
            0.75, 0.91, "A yellow background indicates exotic grist."
        )
        infotext.fontsize = 20
        infotext = render.Text(
            0.75, 0.94, "Exotic grist types cannot normally be obtained"
        )
        infotext.fontsize = 20
        infotext = render.Text(
            0.75, 0.97, "unless a player has specifically picked them."
        )
        infotext.fontsize = 20

        def choosegristtype(grist):
            def out():
                logtext.fontsize = 20
                t = f"Are you sure you want {grist.upper()}? Press the button again to confirm."
                if logtext.text == t:
                    self.gristcategory = grist
                    newgame(self)
                else:
                    logtext.text = t

            return out

        for i, category in enumerate(config.gristcategories):
            if i <= 9:
                x = 0.07
            else:
                x = 0.54
            num = i
            if num > 9:
                num -= 10
            y = (num + 1) / 12
            y += 0.08
            button = render.TextButton(
                x, y, 110, 33, category.upper(), choosegristtype(category)
            )
            for ind, grist in enumerate(config.gristcategories[category]):
                img = render.Image(
                    x + 0.07 + (0.04 * ind), y, config.grists[grist]["image"]
                )
                if grist in available_types:
                    img.highlight_color = current_theme().dark
                elif (
                    "exotic" in config.grists[grist] and config.grists[grist]["exotic"]
                ):
                    img.highlight_color = pygame.Color(255, 255, 0)
        backbutton = render.Button(
            0.08,
            0.05,
            "sprites\\buttons\\back.png",
            "sprites\\buttons\\backpressed.png",
            self.choose_map,
        )

    def get_dict(self):
        return self.__dict__


def newgame(character_creator: Optional["CharacterCreator"] = None):
    if character_creator is not None:
        reply = client.requestplus("create_character", character_creator.get_dict())
        print(reply)
    player_info = client.requestdic("player_info")
    player_name = player_info["name"]
    Sylladex.update_character(player_name)
    if character_creator is not None:
        new_sylladex = Sylladex.new_sylladex(player_name, character_creator.modus)
    else:
        new_sylladex = Sylladex.get_sylladex(player_name)
    new_sylladex.validate()
    map_scene()


def debug_speedrun():
    client.dic["session_name"] = "fuck"
    client.dic["session_password"] = "ass"
    client.request("create_session")
    client.request("join_session")
    character_creator = CharacterCreator()
    character_creator.name = "Inness"
    character_creator.noun = "rabbit girl"
    character_creator.pronouns = "she", "her", "her", "hers"
    character_creator.interests = ["music", "technology", "squiddles"]
    character_creator.aspect = "life"
    character_creator.gameclass = "sylph"
    character_creator.secondaryvial = "imagination"
    character_creator.modus = "array"
    character_creator.gristcategory = "amber"
    character_creator.kingdom = "prospit"
    character_creator.map_name = "suburban_1"
    style_dict = config.default_style_dict.copy()
    style_dict.update(
        {
            "pants": "rgb",
            "shoes": "trollian",
            "coat": "rgb",
        }
    )
    character_creator.symbol_dict = {
        "base": "troll",
        "eyes": "leo",
        "hair": "crocker",
        "horns": "gemini",
        "mouth": "gemini",
        "pants": "harley",
        "shirt": "aries",
        "shoes": "striber",
        "coat": "english",
        "color": [161, 161, 0],
        "style_dict": style_dict,
    }
    newgame(character_creator)


def debug_speedrun_2():
    client.dic["session_name"] = "fuck"
    client.dic["session_password"] = "ass"
    client.request("create_session")
    client.request("join_session")
    character_creator = CharacterCreator()
    character_creator.name = "Azaral"
    character_creator.noun = "basement demon"
    character_creator.pronouns = "he", "him", "his", "his"
    character_creator.interests = ["garbage", "anime", "horror"]
    character_creator.aspect = "doom"
    character_creator.gameclass = "bard"
    character_creator.secondaryvial = "gambit"
    character_creator.modus = "array"
    character_creator.gristcategory = "dark"
    character_creator.kingdom = "derse"
    character_creator.map_name = "urban"
    style_dict = config.default_style_dict.copy()
    style_dict.update(
        {
            "pants": "trollian",
            "eyes": "rgb",
            "shoes": "trollian",
            "coat": "trollian",
        }
    )
    character_creator.symbol_dict = {
        "base": "troll",
        "eyes": "libra",
        "hair": "scorpio",
        "horns": "aquarius",
        "mouth": "taurus",
        "pants": "leo",
        "shirt": "lalobbe",
        "shoes": "aquarius",
        "coat": "leo",
        "color": [68, 10, 127],
        "style_dict": style_dict,
    }
    newgame(character_creator)


@scene
def computer(instance: Instance):
    task_bar = render.TaskBar()
    apps = []
    for app_name in instance.computer_data["installed_programs"]:
        random.seed(instance.name + app_name)
        x = 0.1 + random.random() * 0.7
        random.seed(instance.name + app_name)
        y = 0.1 + random.random() * 0.7
        app_icon = render.AppIcon(random.random(), random.random(), app_name, task_bar)
        apps.append(app_icon)


def gristtorrent(window: "render.Window"):
    theme = themes.gristtorrent
    viewport = window.viewport
    viewport.kill_temporary_elements()
    padding = 7
    player_dict = client.requestdic("player_info")
    grist_cache = player_dict["grist_cache"]
    grist_cache_limit = player_dict["grist_cache_limit"]
    grist_gutter = player_dict["grist_gutter"]
    total_gutter_grist = player_dict["total_gutter_grist"]
    leeching: dict[str, int] = player_dict["leeching"]
    seeds: dict[str, int] = player_dict["seeds"]
    session_seeds = client.requestdic("session_seeds")
    banner_head = render.Image(0, 0, "sprites/computer/gristTorrent/banner.png")
    banner_head.absolute = True
    banner_head.bind_to(viewport, True)
    icon = render.Image(
        0.29, 0.5, "sprites/computer/apps/gristTorrent.png", convert=False
    )
    icon.bind_to(banner_head)
    banner_text = render.Text(0.56, 0.5, "gristTorrent")
    banner_text.color = theme.light
    banner_text.outline_color = theme.dark
    banner_text.outline_depth = 2
    banner_text.fontsize = 72
    banner_text.bind_to(banner_head)
    grist_display_w = viewport.w
    grist_display_h = 450
    num_rows = 12
    columns = []
    for grist_name in config.grists:
        for column in columns:
            if len(column) != num_rows:
                column.append(grist_name)
                break
        else:
            columns.append([grist_name])
    num_columns = len(columns)
    grist_box_outline_width = 1
    grist_box_w = grist_display_w // num_columns - padding - grist_box_outline_width
    grist_box_h = grist_display_h // num_rows - padding - grist_box_outline_width

    def get_box_button_func(grist_name):
        def box_button_func():
            client.requestplus(
                intent="computer",
                content={"command": "leech", "grist_type": grist_name},
            )
            window.reload()

        return box_button_func

    for column_index, column in enumerate(columns):
        grist_box_x = padding + (grist_box_w + padding) * column_index
        for row_index, grist_name in enumerate(column):
            grist_box_y = 150 + padding + (grist_box_h + padding) * row_index
            if grist_name in leeching:
                leeching_rate = leeching[grist_name]
            else:
                leeching_rate = 0
            best_seeds = session_seeds[grist_name]
            label = (
                f"{grist_cache[grist_name]} | {leeching_rate} Down | {best_seeds} Seeds"
            )
            if best_seeds == 0 or (
                grist_name in leeching and leeching[grist_name] == 0
            ):
                box_color = theme.black
                label_color = theme.white
                outline_color = theme.dark
            else:
                box_color = theme.dark
                label_color = theme.light
                outline_color = theme.black
            box = render.make_grist_display(
                grist_box_x,
                grist_box_y,
                grist_box_w,
                grist_box_h,
                padding,
                grist_name,
                grist_cache[grist_name],
                grist_cache_limit,
                theme,
                label=label,
                box_color=box_color,
                label_color=label_color,
                outline_color=outline_color,
            )
            box.border_radius = 2
            if grist_name in leeching:
                box.outline_color = pygame.Color(255, 0, 0)
            box.bind_to(viewport, True)
            box_button = render.TextButton(
                grist_box_x,
                grist_box_y,
                grist_box_w,
                grist_box_h,
                "",
                get_box_button_func(grist_name),
            )
            box_button.absolute = True
            box_button.draw_sprite = False
            box_button.bind_to(viewport, True)
    gutter_box_width = viewport.w // 2
    gutter_box_height = 40
    gutter_box = render.SolidColor(
        viewport.w - gutter_box_width - padding,
        viewport.h - gutter_box_height - padding,
        gutter_box_width,
        gutter_box_height,
        theme.white,
    )
    gutter_box.outline_color = theme.black
    gutter_box.bind_to(viewport, True)
    box_label = render.Text(0.5, 0.25, "grist gutter")
    box_label.color = theme.light
    box_label.fontsize = 18
    box_label.bind_to(gutter_box)
    small_icon = render.Image(
        -0.03, 0.5, "sprites/computer/apps/gristTorrent.png", convert=False
    )
    small_icon.scale = 0.33
    small_icon.bind_to(gutter_box)
    gutter_label = render.Text(0.5, 0.9, str(total_gutter_grist))
    gutter_label.color = theme.light
    gutter_label.fontsize = 12
    gutter_label.bind_to(gutter_box)
    gutter_bar_background_width = gutter_box_width - padding * 2
    gutter_bar_background_height = 8
    gutter_bar_background = render.SolidColor(
        padding,
        gutter_box_height * 1.5 // 3,
        gutter_bar_background_width,
        gutter_bar_background_height,
        theme.white,
    )
    gutter_bar_background.outline_color = theme.black
    gutter_bar_background.border_radius = 3
    gutter_bar_background.bind_to(gutter_box)
    # starting x
    gutter_bar_padding = 2
    total_bar_width = gutter_box_width - padding * 2 - gutter_bar_padding * 2
    gutter_bar_x = gutter_bar_padding
    gutter_bar_y = gutter_bar_padding
    for grist_name, amount in grist_gutter:
        bar_width = int(total_bar_width * (amount / total_gutter_grist))
        if bar_width == 0:
            continue
        gutter_bar_color = config.gristcolors[grist_name]
        gutter_bar = render.SolidColor(
            gutter_bar_x,
            gutter_bar_y,
            bar_width,
            gutter_bar_background_height - gutter_bar_padding * 2,
            gutter_bar_color,
        )
        gutter_bar.bind_to(gutter_bar_background)
        gutter_bar_x += bar_width


@scene
def map_scene():
    strife_data = client.requestdic(intent="strife_data")
    if strife_data:
        strife_scene(strife_data)
        return
    player_data = client.requestdic(intent="player_info")
    player_name = player_data["name"]
    Sylladex.update_character(player_name)
    Sylladex.current_sylladex().validate()
    ui_bar = Sylladex.current_sylladex().draw_ui_bar(map_scene)
    tilemap = render.TileMap(0.5, 0.5)
    portfolio_button = render.TextButton(
        render.SCREEN_WIDTH - 256,
        render.SCREEN_HEIGHT - 166 - 64,
        256,
        64,
        "strife portfolio",
        strife_portfolio_scene,
        theme=themes.strife,
    )
    portfolio_button.absolute = True
    portfolio_button.fill_color = themes.strife.dark
    portfolio_button.text_color = themes.strife.light
    portfolio_button.outline_color = themes.strife.black
    if player_data["entered"] or player_data["overmap_name"] in [
        "prospit",
        "derse",
        "prospitmoon",
        "dersemoon",
    ]:
        overmap_button = render.TextButton(0.9, 0.1, 196, 64, ">OVERMAP", overmap)
    log = render.LogWindow(map_scene, tilemap=tilemap, draw_console=True)


@scene
def strife_scene(strife_dict: Optional[dict] = None):
    strife.Strife(strife_dict).draw_scene()


@scene
def overmap():
    reply = client.requestdic(intent="current_overmap")
    map_tiles = reply["map_tiles"]
    map_specials = reply["map_specials"]
    map_types = reply["map_types"]
    theme_name = reply["theme"]
    illegal_moves = reply["illegal_moves"]
    title = reply["title"]
    overmap_type = reply["overmap_type"]
    if overmap_type == "kingdom" or overmap_type == "moon":
        top_block_image_path = "sprites/overmap/moon_block.png"
        if theme_name == "prospit":
            water_image_path = "sprites/overmap/prospit_water.png"
        else:
            water_image_path = "sprites/overmap/derse_water.png"
    else:
        top_block_image_path = "sprites/overmap/block.png"
        water_image_path = "sprites/overmap/water.png"
    theme = themes.themes[theme_name]
    background = render.SolidColor(
        0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.black
    )
    overmap = render.Overmap(
        0.5,
        0.75,
        map_tiles,
        map_specials,
        map_types,
        illegal_moves=illegal_moves,
        theme=theme,
        top_block_path=top_block_image_path,
        water_path=water_image_path,
    )
    backbutton = render.Button(
        0.1,
        0.1,
        "sprites\\buttons\\back.png",
        "sprites\\buttons\\backpressed.png",
        map_scene,
        theme=theme,
    )
    render.always_on_top_check.append(backbutton)
    render.update_check.remove(backbutton)
    title_text = render.Text(0.5, 0.05, title)
    title_text.font_location = "./fonts/Carima Regular.ttf"
    title_text.fontsize = 32
    title_text.color = theme.white
    title_text.outline_color = theme.dark
    title_text.antialias = False
    render.always_on_top_check.append(title_text)
    render.update_check.remove(title_text)


@scene
def display_item(
    instance: Instance,
    last_scene: Callable,
    modus: Optional[Modus] = None,
    flipped=False,
    strife=False,
):
    player_data = client.requestdic(intent="player_info")

    if strife:
        card_path = "sprites/itemdisplay/strife_captchalogue_card.png"
        card_flipped_path = "sprites/itemdisplay/strife_captchalogue_card_flipped.png"
        text_color = themes.strife.light
        text_outline_color = None
        theme = themes.strife

        def flip():
            if not instance.item.forbiddencode:
                display_item(
                    instance,
                    last_scene,
                    modus=modus,
                    flipped=not flipped,
                    strife=strife,
                )

    elif modus is None:
        card_path = "sprites\\itemdisplay\\captchalogue_card.png"
        card_flipped_path = "sprites\\itemdisplay\\captchalogue_card_flipped.png"
        text_color = current_theme().dark
        text_outline_color = None
        theme = current_theme()

        def flip():
            pass

    else:
        card_path = modus.front_path
        card_flipped_path = modus.back_path
        text_color = modus.theme.light
        text_outline_color = modus.theme.black
        theme = modus.theme

        def flip():
            if not instance.item.forbiddencode:
                display_item(
                    instance,
                    last_scene,
                    modus=modus,
                    flipped=not flipped,
                    strife=strife,
                )

    background = render.SolidColor(
        0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.light
    )
    log_window = render.LogWindow(display_item)
    log_window.text_color = theme.light
    log_window.update_logs()
    if not flipped:
        captcha_image = render.Button(0.5, 0.4, card_path, card_path, flip)
        image = render.make_item_image(0.5, 0.5, instance)
        if image is not None:
            image.bind_to(captcha_image)
            contained_instance = instance.contained_instance()
            if contained_instance is not None:
                contained_image = render.make_item_image(0.45, 0.5, contained_instance)
                if contained_image is not None:
                    contained_image.bind_to(image)
                    contained_image.scale = 0.5
        if modus is None:
            label_text = util.filter_item_name(instance.display_name())
        else:
            label_text = modus.get_instance_name(instance, short=False)
        label = render.Text(0.55, 0.91, label_text)
        label.bind_to(captcha_image)
        label.color = text_color
        label.outline_color = text_outline_color
        label.set_fontsize_by_width(240)
        num_actions = len(instance.item.use)
        for i, action_name in enumerate(instance.item.use):
            x = 0.05 + (1 / (num_actions + 1)) * (i + 1)
            y = 1.07
            path = f"sprites/item_actions/{action_name}.png"
            pressed_path = f"sprites/item_actions/{action_name}_pressed.png"
            if not os.path.isfile(path):
                path = "sprites/item_actions/generic_action.png"
            if not os.path.isfile(pressed_path):
                pressed_path = "sprites/item_actions/generic_action_pressed.png"
            action_button = render.Button(
                x,
                y,
                path,
                pressed_path,
                instance.get_action_button_func(action_name, last_scene),
                theme=theme,
            )
            action_button.scale = 2.0
            action_button.bind_to(captcha_image)
    else:
        code = instance.item.code
        captcha_image = render.Button(
            0.5, 0.4, card_flipped_path, card_flipped_path, flip
        )
        captcha_code = render.Image(32, 28, get_captcha(code), convert=False)
        captcha_code.bind_to(captcha_image)
        captcha_code.absolute = True
    power = instance.item.power
    power_bar = render.Image(
        0.5, 1.28, "sprites\\itemdisplay\\power_bar.png", theme=theme
    )
    power_bar.bind_to(captcha_image)
    power_label = render.Text(0.512, 0.51, str(power))
    power_label.bind_to(power_bar)
    power_label.color = theme.dark
    power_label.fontsize = 54
    power_label.set_fontsize_by_width(330)
    # description
    if instance.item.description is not None:
        description_text = instance.item.description
        description_lines = util.split_into_max_length_lines(description_text, 35)
        for i, line in enumerate(description_lines):
            y = 0.6 - (0.02 * len(description_lines)) + 0.04 * i
            description = render.Text(0.2, y, line)
            description.color = text_color
            description.outline_color = text_outline_color
            description.fontsize = 20

    # states

    STATE_PADDING = 3
    onhit_label = render.Text(0.2, 0.15, "On-hit States")
    onhit_label.color = theme.dark
    onhit_icons = []
    for state_name, state_dict in instance.item.onhit_states.items():
        if len(onhit_icons) == 0:
            x, y = 0.5, 1.2
            offsetx = (16 + STATE_PADDING) * (len(instance.item.onhit_states) - 1)
            offsetx = offsetx // 2 * -1
        else:
            x, y = 1, 0.5
            offsetx = STATE_PADDING + 8
        icon = render.NoGrieferStateIcon(x, y, state_name, state_dict, theme=theme)
        icon.rect_x_offset = offsetx
        if len(onhit_icons) == 0:
            icon.bind_to(onhit_label)
        else:
            icon.bind_to(onhit_icons[-1])
        onhit_icons.append(icon)

    wear_label = render.Text(0.2, 0.25, "Wear States")
    wear_label.color = theme.dark
    wear_icons = []
    for state_name, state_dict in instance.item.wear_states.items():
        if len(wear_icons) == 0:
            x, y = 0.5, 1.2
            offsetx = (16 + STATE_PADDING) * (len(instance.item.wear_states) - 1)
            offsetx = offsetx // 2 * -1
        else:
            x, y = 1, 0.5
            offsetx = STATE_PADDING + 8
        icon = render.NoGrieferStateIcon(x, y, state_name, state_dict, theme=theme)
        icon.rect_x_offset = offsetx
        if len(wear_icons) == 0:
            icon.bind_to(wear_label)
        else:
            icon.bind_to(wear_icons[-1])
        wear_icons.append(icon)

    consume_label = render.Text(0.2, 0.35, "Consume States")
    consume_label.color = theme.dark
    consume_icons = []
    for state_name, state_dict in instance.item.consume_states.items():
        if len(consume_icons) == 0:
            x, y = 0.5, 1.2
            offsetx = (16 + STATE_PADDING) * (len(instance.item.consume_states) - 1)
            offsetx = offsetx // 2 * -1
        else:
            x, y = 1, 0.5
            offsetx = STATE_PADDING + 8
        icon = render.NoGrieferStateIcon(x, y, state_name, state_dict, theme=theme)
        icon.rect_x_offset = offsetx
        if len(consume_icons) == 0:
            icon.bind_to(consume_label)
        else:
            icon.bind_to(consume_icons[-1])
        consume_icons.append(icon)

    # wearable
    if instance.item.wearable and instance.name != player_data["worn_instance_name"]:

        def wear_button_func():
            reply = client.requestplus(
                intent="wear", content={"instance_name": instance.name}
            )
            if reply:
                if modus is not None:
                    Sylladex.current_sylladex().remove_instance(instance.name)
                strife_portfolio_scene()

        wear_button = render.TextButton(
            0.26, 0.9, 196, 48, ">DON", wear_button_func, theme=theme
        )
        wear_button.text_color = theme.dark
    elif instance.item.wearable and instance.name == player_data["worn_instance_name"]:

        def wear_button_func():
            reply = client.request(intent="unwear")
            if reply:
                last_scene()

        wear_button = render.TextButton(
            0.26, 0.9, 196, 48, "(DONNED) >DOFF", wear_button_func, theme=theme
        )
        wear_button.text_color = theme.dark

    # kinds

    num_kinds = len(instance.item.kinds)

    def get_kind_button_func(kind_name):
        def kind_button_func():
            if modus is None:
                util.log(f"You must captchalogue this first.")
            player_dict = client.requestdic(intent="player_info")
            if kind_name in player_dict["strife_portfolio"]:
                reply = client.requestplus(
                    intent="move_to_strife_deck",
                    content={"instance_name": instance.name, "kind_name": kind_name},
                )
                if reply:
                    Sylladex.current_sylladex().remove_instance(instance.name)
                    strife_portfolio_scene()
            elif player_dict["unassigned_specibi"] <= 0:
                util.log("You don't have any unassigned specibi.")
                return
            elif kind_name in player_dict["strife_portfolio"]:
                util.log(f"You must captchalogue this first.")
                return
            else:
                assign_strife_specibus(kind_name, instance.name, last_scene)

        return kind_button_func

    for i, kind in enumerate(instance.item.kinds):
        x = 1.2
        y = 1 / (num_kinds + 1) * (i + 1)
        kind_card_image = render.Button(
            x,
            y,
            "sprites\\itemdisplay\\strife_card.png",
            None,
            get_kind_button_func(kind),
        )
        kind_card_image.bind_to(captcha_image)
        kind_card_image.hover_to_top = True
        kind_label = render.Text(0.55, 0.91, kind)
        kind_label.bind_to(kind_card_image)
        kind_label.fontsize = 16
        kind_label.color = themes.strife.light
        kind_label.set_fontsize_by_width(120)
        if os.path.isfile(f"sprites\\kinds\\{kind}.png"):
            kind_image = render.Image(0.5, 0.5, f"sprites\\kinds\\{kind}.png")
            kind_image.bind_to(kind_card_image)
    if instance.punched_code != "":
        if not flipped:
            render.spawn_punches(
                captcha_image, instance.punched_code, 122, 138, w=80, h=120
            )
    if strife:
        if (
            not instance.item.wearable
            or instance.name != player_data["worn_instance_name"]
        ):

            def eject_button_func():
                client.requestplus(
                    intent="eject_from_strife_deck",
                    content={"instance_name": instance.name},
                )
                last_scene()

            eject_button = render.TextButton(
                0.5,
                1.2,
                300,
                33,
                "eject from strife deck",
                eject_button_func,
                theme=theme,
            )
            eject_button.bind_to(power_bar)
    elif modus is not None:
        syl = Sylladex.current_sylladex()

        def uncaptcha_button_func():
            syl.uncaptchalogue(instance.name)
            last_scene()

        if modus.can_uncaptchalogue:
            uncaptchalogue_button = render.TextButton(
                0.5, 1.2, 200, 33, "uncaptchalogue", uncaptcha_button_func, theme=theme
            )
            uncaptchalogue_button.bind_to(power_bar)
    backbutton = render.Button(
        0.1,
        0.9,
        "sprites\\buttons\\back.png",
        "sprites\\buttons\\backpressed.png",
        last_scene,
        theme=theme,
    )


@scene
def assign_strife_specibus(
    kind_name: str, assigning_instance_name: str, last_scene: Callable = map_scene
):
    confirm_text = render.Text(
        0.5, 0.1, f"Do you want to assign {kind_name} as a new strife specibus?"
    )
    confirm_text.color = current_theme().dark

    def confirm():
        reply = client.requestplus("assign_specibus", {"kind_name": kind_name})
        if reply:
            util.log(f"You assigned {kind_name}!")
            reply = client.requestplus(
                intent="move_to_strife_deck",
                content={
                    "instance_name": assigning_instance_name,
                    "kind_name": kind_name,
                },
            )
            if reply:
                Sylladex.current_sylladex().remove_instance(assigning_instance_name)
        else:
            util.log("Failed to assign.")
        strife_portfolio_scene()

    confirm_button = render.Button(
        0.5,
        0.2,
        "sprites/buttons/confirm.png",
        "sprites/buttons/confirmpressed.png",
        confirm,
    )
    back_button = render.Button(
        0.5,
        0.3,
        "sprites/buttons/back.png",
        "sprites/buttons/backpressed.png",
        last_scene,
    )


@scene
def strife_portfolio_scene(selected_kind: Optional[str] = None):
    theme = themes.strife
    padding = 8
    background = render.SolidColor(
        0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.dark
    )
    player_dict = client.requestdic(intent="player_info")
    power = player_dict["power"]
    echeladder_rung = player_dict["echeladder_rung"]
    stat_ratios = player_dict["stat_ratios"]
    permanent_stat_bonuses = player_dict["permanent_stat_bonuses"]
    # kind_name:dict[instance_name:instance_dict]
    strife_portfolio = player_dict["strife_portfolio"]
    wielding = player_dict["wielding"]
    wielded_instance: Optional[Instance] = None
    donned = player_dict["worn_instance_name"]
    if donned is not None:
        donned_instance = Instance(donned, player_dict["worn_instance_dict"])
    else:
        donned_instance = None
    for kind in strife_portfolio:
        for instance_name in strife_portfolio[kind]:
            if instance_name == wielding:
                wielded_instance = Instance(
                    instance_name, strife_portfolio[kind][instance_name]
                )
    if selected_kind is None:
        if strife_portfolio:
            selected_kind = list(strife_portfolio.keys())[0]
        else:
            selected_kind = None

    def back():
        map_scene()

    if selected_kind is not None:
        # main box
        symbol = render.Symbol(0.825, 0.6, player_dict["symbol_dict"])
        strife_deck_bar = render.Image(0, 0, "sprites/itemdisplay/strife_deck_bar.png")
        strife_deck_bar.absolute = True
        label = render.Text(0.5, 0.065, selected_kind)
        label.color = theme.light
        label.fontsize = 48
        label.set_fontsize_by_width(350)
        abstratus_display = render.Image(
            0.51, 0.43, "sprites/itemdisplay/strife_abstratus_display.png"
        )
        if os.path.isfile(f"sprites\\kinds\\{selected_kind}.png"):
            kind_image = render.Image(0.5, 0.5, f"sprites\\kinds\\{selected_kind}.png")
            kind_image.bind_to(abstratus_display)
            kind_image.scale = 3
        # power label
        power_label = render.Text(padding, padding * 1, f"power: {power}")
        power_label.absolute = True
        power_label.color = theme.light
        power_label.set_fontsize_by_width(300)
        echeladder_label = render.Text(
            padding, padding * 6, f"echeladder rung: {echeladder_rung}"
        )
        echeladder_label.absolute = True
        echeladder_label.color = theme.light
        echeladder_label.fontsize = 20
        echeladder_label.set_fontsize_by_width(300)
        # stat ratios
        stat_boxes: dict[str, render.InputTextBox] = {}
        labels = {
            "spunk": "spunk (SPK) -> {}",
            "vigor": "vigor (VIG) -> {}",
            "tact": "tact (TAC) -> {}",
            "luck": "luck (LUK) -> {}",
            "savvy": "savvy (SAV) -> {}",
            "mettle": "mettle (MET) -> {}",
        }
        descriptions = {
            "spunk": "increases damage dealt",
            "vigor": "increases gel viscosity (HP)",
            "tact": "+vim and secondary vials",
            "luck": "biases rng",
            "savvy": "speed and auto-parry",
            "mettle": "decreases damage taken",
        }
        stats = ["spunk", "vigor", "tact", "luck", "savvy", "mettle"]

        def confirm():
            ratios = {}
            for stat in stats:
                ratios[stat] = int(stat_boxes[stat].text)
            client.requestplus(intent="set_stat_ratios", content={"ratios": ratios})

        def back():
            confirm()
            map_scene()

        for i, stat in enumerate(stats):
            box_width = 64
            fontsize = 20
            x = -box_width - padding
            y = i * (box_width + padding)
            box = render.InputTextBox(x, y, box_width, box_width, theme)
            box.absolute = True
            box.absolute_text = False
            box.text = str(stat_ratios[stat])
            box.inactive_color = theme.light
            box.active_color = theme.white
            box.text_color = theme.dark
            box.outline_color = theme.black
            box.numbers_only = True
            box.max_characters = 2
            box.bind_to(abstratus_display)
            stat_boxes[stat] = box

            def get_label_func(stat):
                def label_func():
                    total_ratios = 0
                    for box in stat_boxes.values():
                        total_ratios += int(box.text)
                    stats = {}
                    for stat_name in stat_boxes:
                        value = int(stat_boxes[stat_name].text)
                        if total_ratios != 0:
                            stat_mult = value / total_ratios
                        else:
                            stat_mult = 1 / len(stat_boxes)
                        stats[stat_name] = int(power * stat_mult)
                    remainder = power - sum(stats.values())
                    for stat_name in stats:
                        if remainder == 0:
                            break
                        if int(stat_boxes[stat_name].text) == 0:
                            continue
                        stats[stat_name] += 1
                        remainder -= 1
                    amount = stats[stat]
                    if stat in permanent_stat_bonuses:
                        bonus = permanent_stat_bonuses[stat]
                    else:
                        bonus = 0
                    amount += bonus
                    text = labels[stat].format(amount)
                    if bonus != 0:
                        text += f" (+{bonus})"
                    return text

                return label_func

            stat_label = render.Text(
                padding,
                padding * 4 + abstratus_display.rect.y + y + box_width - fontsize // 2,
                labels[stat],
            )
            stat_label.text_func = get_label_func(stat)
            stat_label.absolute = True
            stat_label.color = theme.light
            stat_label.fontsize = fontsize
            stat_description = render.Text(0, fontsize + padding, descriptions[stat])
            stat_description.absolute = True
            stat_description.color = theme.light
            stat_description.fontsize = fontsize
            stat_description.bind_to(stat_label)
            if i == 0:
                cool_bar = render.Image(0.5, -0.2, "sprites/itemdisplay/cool_bar.png")
                cool_bar.bind_to(box)
                label = render.Text(0, -0.5, "stat ratios")
                label.fontsize = 20
                label.color = theme.light
                label.bind_to(box)

        # wielded display
        wielded_display = render.Image(
            1.3, 0.2, "sprites/itemdisplay/strife_equip_display.png"
        )
        wielded_display.bind_to(abstratus_display)
        equipped_label = render.Text(0.5, 0, "wielding")
        equipped_label.fontsize = 20
        equipped_label.color = theme.black
        equipped_label.bind_to(wielded_display)
        if wielded_instance is not None:
            image_path = f"sprites/items/{wielded_instance.item.name}.png"
            if os.path.isfile(image_path):
                card_image = render.make_item_image(0.49, 0.5, wielded_instance)
                if card_image is not None:
                    card_image.bind_to(wielded_display)
                    card_image.scale = 0.5
            item_label = render.Text(0.6, 1.1, f"{wielded_instance.display_name(True)}")

            def view_wielded_item():
                confirm()
                display_item(
                    wielded_instance, last_scene=strife_portfolio_scene, strife=True
                )

            view_item_button = render.TextButton(
                0.5, 0.5, 102, 102, "", view_wielded_item
            )
            view_item_button.draw_sprite = False
            view_item_button.bind_to(wielded_display)
        else:
            item_label = render.Text(0.6, 1.1, f"nothing")
        item_label.fontsize = 20
        item_label.color = theme.light
        item_label.bind_to(wielded_display)

        # donned display
        donned_display = render.Image(
            1.7, 0.2, "sprites/itemdisplay/strife_equip_display.png"
        )
        donned_display.bind_to(abstratus_display)
        equipped_label = render.Text(0.5, 0, "donned")
        equipped_label.fontsize = 20
        equipped_label.color = theme.black
        equipped_label.bind_to(donned_display)
        if donned_instance is not None:
            image_path = f"sprites/items/{donned_instance.item.name}.png"
            if os.path.isfile(image_path):
                card_image = render.make_item_image(0.49, 0.5, donned_instance)
                if card_image is not None:
                    card_image.bind_to(donned_display)
                    card_image.scale = 0.5
            item_label = render.Text(0.6, 1.1, f"{donned_instance.display_name(True)}")

            def view_donned_item():
                confirm()
                display_item(
                    donned_instance, last_scene=strife_portfolio_scene, strife=True
                )

            view_item_button = render.TextButton(
                0.5, 0.5, 102, 102, "", view_donned_item
            )
            view_item_button.draw_sprite = False
            view_item_button.bind_to(donned_display)
        else:
            item_label = render.Text(0.6, 1.1, f"nothing")
        item_label.fontsize = 20
        item_label.color = theme.light
        item_label.bind_to(donned_display)

        # bottom bar
        instances_length = len(strife_portfolio[selected_kind])

        def get_button_func(instance: Instance) -> Callable:
            def wrapper():
                confirm()
                display_item(instance, strife_portfolio_scene, modus=None, strife=True)

            return wrapper

        def get_wield_button_func(instance_name: Instance) -> Callable:
            def wrapper():
                reply = client.requestplus(
                    intent="wield", content={"instance_name": instance_name}
                )
                confirm()
                strife_portfolio_scene(selected_kind)

            return wrapper

        for i, instance_name in enumerate(strife_portfolio[selected_kind]):
            x = (render.SCREEN_WIDTH / 2) - 109 + 125 * (i + 1 - instances_length / 2)
            x = int(x)
            y = int(render.SCREEN_HEIGHT * 0.80)
            instance = Instance(
                instance_name, strife_portfolio[selected_kind][instance_name]
            )
            button_function = get_button_func(instance)
            card_thumb = render.Button(
                x,
                y,
                "sprites/moduses/card_thumb.png",
                "sprites/moduses/card_thumb.png",
                button_function,
            )
            card_thumb.absolute = True
            card_thumb.bind_to(strife_deck_bar)
            image_path = f"sprites/items/{instance.item_name}.png"
            if os.path.isfile(image_path):
                card_image = render.make_item_image(0.49, 0.5, instance)
                if card_image is not None:
                    card_image.bind_to(card_thumb)
                    card_image.scale = 0.5
            else:
                card_image = None
            label_text = instance.display_name(short=True)
            card_label = render.Text(0.49, 0.9, label_text)
            card_label.set_fontsize_by_width(90)
            card_label.bind_to(card_thumb)
            if instance_name != wielding:
                wield_button = render.TextButton(
                    0.5,
                    -0.15,
                    100,
                    30,
                    ">wield",
                    get_wield_button_func(instance_name),
                    theme=theme,
                )
                wield_button.outline_color = theme.black
                wield_button.bind_to(card_thumb)
    else:
        # selected kind is None
        info_text = render.Text(
            0.5,
            0.3,
            "Add an item to your strife portfolio by clicking the specibus icon while viewing it.",
        )
        info_text_2 = render.Text(
            0.5, 0.7, "You can assign a strife specibus the same way."
        )
        info_text.color, info_text_2.color = theme.light, theme.light
        info_text.fontsize, info_text_2.fontsize = 20, 20
        abstratus_icon = render.Image(0.5, 0.5, "sprites/itemdisplay/strife_card.png")
    back_button = render.Button(
        0.08,
        0.95,
        "sprites/buttons/back.png",
        "sprites/buttons/backpressed.png",
        back,
        theme=theme,
    )


@scene
def spoils(grist_dict: dict, echeladder_rungs: int):
    text = render.Text(0.5, 0.3, "You make off with the following spoils:")
    text.color = current_theme().dark
    grist_display = render.make_grist_cost_display(
        0.5, 0.4, 24, grist_dict, None, absolute=False
    )
    if echeladder_rungs > 0:
        player_info = client.requestdic(intent="player_info")
        cache_limit = player_info["grist_cache_limit"]
        echeladder_notification = render.Text(
            0.5,
            0.5,
            f"You ascend {echeladder_rungs} rung{'s' if echeladder_rungs > 1 else ''} on your ECHELADDER!",
        )
        echeladder_notification.color = current_theme().dark
        echeladder_line_2 = render.Text(
            0.5, 0.6, f"Your grist cache limit is now {cache_limit}!"
        )
        echeladder_line_2.color = current_theme().dark
    back_button = render.Button(
        0.08,
        0.95,
        "sprites/buttons/back.png",
        "sprites/buttons/backpressed.png",
        map_scene,
    )
    back_button.click_keys = [pygame.K_SPACE]
    back_button_label = render.Text(0.5, -0.15, "(space)")
    back_button_label.bind_to(back_button)
    back_button_label.fontsize = 12
    back_button_label.color = current_theme().dark


def continue_button_func():
    # todo: token auth
    # client.load_client_data()
    login()


def continue_button_draw_condition():
    if util.last_client_data:
        return True
    else:
        return False


@scene
def title():
    logo = render.Image(0.5, 0.20, "sprites\\largeicon.png")
    logotext = render.Image(0.5, 0.47, "sprites\\suburb.png")
    play_button = render.Button(
        0.5,
        0.59,
        "sprites\\buttons\\play.png",
        "sprites\\buttons\\playpressed.png",
        play,
    )
    play_button.alt_alpha = 100
    new_session_button = render.Button(
        0.5,
        0.70,
        "sprites\\buttons\\newsession.png",
        "sprites\\buttons\\newsessionpressed.png",
        newsessionprompt,
    )
    # todo: options
    # options_button = render.Button(.5, .81, "sprites\\buttons\\options.png", "sprites\\buttons\\optionspressed.png", newsessionprompt)
    versiontext = render.Text(0, 0, f"SUBURB Version {util.VERSION}")
    versiontext.absolute = True
    versiontext.color = current_theme().dark
    versiontext.outline_color = current_theme().black
    conntextcontent = f"Logged in as: {client.dic['username']}"
    conntext = render.Text(0, 30, conntextcontent)
    conntext.absolute = True
    conntext.color = current_theme().dark
    logout_button = render.TextButton(0.5, 1.5, 96, 32, "log out", logout)
    logout_button.bind_to(conntext)
    debug_button = render.Button(
        0.1,
        0.92,
        "sprites\\buttons\\debug.png",
        "sprites\\buttons\\debug.png",
        debug_speedrun,
    )
    debug_button_2 = render.Button(
        0.1,
        0.82,
        "sprites\\buttons\\debug_2.png",
        "sprites\\buttons\\debug_2.png",
        debug_speedrun_2,
    )
    item_editor_button = render.TextButton(
        0.1, 0.2, 160, 32, "Item Editor", item_editor_scene
    )
    map_editor_button = render.TextButton(
        0.1, 0.3, 160, 32, "Map Editor", map_editor_scene
    )

    def character_creator_func():
        character_creator = CharacterCreator()
        character_creator.start()

    character_editor_button = render.TextButton(
        0.1, 0.4, 160, 32, "Character Editor", character_creator_func
    )
    # vial = render.Vial(0.5, 0.2, 150, "realness", 0.5)
    # vial.absolute = False
    # crash_button = render.TextButton(0.8, 0.5, 128, 32, "crash me", crash_button_func)


def map_from_file(file):
    with open(f"maps/{file}", "r") as f:
        content = f.read()
    content = content.split("\n")  # split y axis
    map = []
    for line in content:
        map.append(list(line))  # split each string in content into a list of letters
    return map


def test_overmap():
    test_overmap_tiles = map_from_file("test_map.txt")
    test_overmap_tiles = [list(line) for line in test_overmap_tiles if line]
    theme = themes.derse
    render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.black)
    render.Overmap(
        0.5,
        0.5,
        test_overmap_tiles,
        theme=theme,
        top_block_path="sprites/overmap/moon_block.png",
        water_path="sprites/overmap/moon_water.png",
        select_water_path="sprites/overmap/selectable.png",
    )


@scene
def connection_screen():
    @scene
    def try_again():
        if client.connect():
            login_scene()
        else:
            print("couldn't connect")
            connection_screen()

    text = render.Text(0.5, 0.1, "Could not connect to server.")
    text.color = themes.default.dark
    try_again_button = render.TextButton(0.5, 0.7, 196, 32, ">TRY AGAIN", try_again)
    spiro = render.get_spirograph(0.5, 0.3, False)

    def character_creator_func():
        character_creator = CharacterCreator()
        character_creator.start()

    character_editor_button = render.TextButton(
        0.1, 0.1, 160, 32, "Character Editor", character_creator_func
    )


def item_editor_scene():
    item_editor = itemeditor.ItemEditor()
    item_editor.item_editor_scene()


def map_editor_scene():
    map_editor = itemeditor.MapEditor()
    map_editor.map_editor_scene()


def render_loop():
    while render.render():
        pass


def main():
    # aspectcharacter() # choose scene to test
    # chooseinterests()
    # choosegrists()
    # choosevial()
    # choosemodus()
    # render.TileMap(0.5, 0.5, map)
    # computer()
    # make_symbol()
    # test_overmap()
    # continue to render until render.render() returns False
    # imp = render.Enemy(0.5, 0.5, "shale", "imp")
    # render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, themes.default.black)
    # render.Overmap(0.5, 0.5, test_map)
    # render.Symbol(0.5, 0.5, config.get_random_symbol())
    try:
        render_loop()
    except (
        TimeoutError,
        ConnectionResetError,
        ssl.SSLEOFError,
        json.decoder.JSONDecodeError,
    ) as e:
        traceback.print_exception(e)
        connection_screen()
        main()
    except Exception as e:
        traceback.print_exception(e)
        with open(f"{util.homedir}/crashlog-{time.time()}.txt", "w") as file:
            traceback.print_exception(e, file=file)


if __name__ == "__main__":
    connecting_text = render.Text(0.5, 0.5, "CONNECTING...")
    connecting_text.color = themes.default.dark
    connecting_text.outline_color = themes.default.black
    render.render()
    if client.connect():  # connect to server
        login_scene()  # normal game start
        # character_creator = CharacterCreator()
        # character_creator.choose_moon()
        # item_editor_scene()
        # map_editor_scene()
        # test_overmap()
    else:
        connection_screen()
    main()
