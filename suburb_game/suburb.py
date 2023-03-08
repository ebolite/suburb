import pygame
import sys
import pathlib
import hashlib
import socket
import math
import time
from captcha.image import ImageCaptcha
import cv2
import os
import numpy as np
import random
from typing import Callable, Optional

import util
import render
import client
import config
import themes
import strife
from sylladex import Instance, Sylladex, Modus

def current_theme():
    return themes.default

def scene(func):
    def out(*args, **kwargs):
        t = time.time()
        render.clear_elements()
        fps_counter = render.FpsCounter(1150, 0)
        fps_counter.fontsize = 20
        fps_counter.absolute = True
        render.update_check.remove(fps_counter)
        render.always_on_top_check.append(fps_counter)
        func(*args, **kwargs)
        print(f"{func} - {time.time() - t}")
    return out

captcha_generator = ImageCaptcha(width = 261, height = 336, fonts=["fonts/cour.ttf", "fonts/courbd.ttf", "fonts/courbi.ttf", "fonts/couri.ttf"])

def get_captcha(code) -> str:
    path = f"{util.homedir}/sprites/captchas/{code}.png".replace("?", "-")
    if not os.path.isfile(path):
        captcha_generator.write(code, path)
        img = cv2.imread(path)
        mask = cv2.imread(f"{util.homedir}/sprites/mask.png")
        img_masked = cv2.bitwise_and(img, mask)
        black_mask = np.all(img_masked<=2, axis=-1)
        alpha = np.uint8(np.logical_not(black_mask)) * int(255)
        bgra = np.dstack((img_masked, alpha))
        cv2.imwrite(path, bgra)
    return path

def placeholder():
    pass

@scene
def play():
    text = render.Text(0.5, 0.3, f"Login to an existing character or register a new character?")
    loginbutton = render.Button(.5, .4, "sprites\\buttons\\login.png", "sprites\\buttons\\loginpressed.png", login)
    registerbutton = render.Button(.5, .52, "sprites\\buttons\\register.png", "sprites\\buttons\\registerpressed.png", register)
    back = render.Button(.5, .64, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

@scene
def register():
    log = render.Text(0.5, 0.10, "")
    name = render.Text(0.5, 0.20, f"Username (Case-sensitive)")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(.5, .25)
    pw = render.Text(0.5, .35, f"Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(.5, .40)
    pwbox.secure = True
    confirm = render.Text(0.5, .50, f"Confirm Password")
    confirm.color = current_theme().dark
    confirm.outline_color = current_theme().black
    confirmbox = render.InputTextBox(.5, .55)
    confirmbox.secure = True
    def verify():
        print("verify")
        if pwbox.text != confirmbox.text: log.text = "Passwords do not match."; return
        if len(namebox.text) == 0: log.text = "Username must not be empty."; return
        if len(pwbox.text) == 0: log.text = "Password field must not be empty."; return
        if len(namebox.text) >= 32: log.text = f"Username must be less than 32 characters. Yours: {len(namebox.text)}"; return
        if len(pwbox.text) >= 32: log.text = f"Your password must be less than 32 characters. Yours: {len(pwbox.text)}"; return
        print("final step")
        client.dic["character"] = namebox.text
        client.dic["character_pass_hash"] = client.hash(pwbox.text)
        log.text = client.request("create_character")
        if "Success" not in log.text:
            client.dic["character"] = ""
            client.dic["character_pass_hash"] = ""
        else:
            namecharacter()
        print(f"log text {log.text}")
    confirm = render.Button(.5, .67, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .80, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", play)

@scene
def login():
    log = render.Text(0.5, 0.20, "")
    name = render.Text(0.5, 0.30, f"Character Name (Case-sensitive)")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(.5, .35)
    pw = render.Text(0.5, .45, f"Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(.5, .50)
    pwbox.secure = True
    def verify():
        if len(namebox.text) == 0: log.text = "Session name must not be empty."; return
        if len(pwbox.text) == 0: log.text = "Password must not be empty."; return
        log.text = "Connecting..."
        client.dic["character"] = namebox.text
        client.dic["character_pass_hash"] = client.hash(pwbox.text)
        log.text = client.request("login")
        if "Success" not in log.text:
            client.dic["character"] = ""
            client.dic["character_pass_hash"] = ""
        else:
            player_info = client.requestdic("player_info")
            if player_info["setup"]:
                Sylladex.current_sylladex().validate()
                map_scene()
            else:
                namecharacter() # todo: change to play game function
        print(f"log text {log.text}")
    confirm = render.Button(.5, .62, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .75, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", play)

@scene
def newsessionprompt():
    text = render.Text(0.5, 0.3, f"Create a new session?")
    text.color = current_theme().dark
    text.outline_color = current_theme().black
    text2 = render.Text(0.5, 0.35, f"The first character to join will become the admin of the session.")
    text2.color = current_theme().dark
    text2.outline_color = current_theme().black
    new = render.Button(.5, .48, "sprites\\buttons\\newsession.png", "sprites\\buttons\\newsessionpressed.png", newsession)
    back = render.Button(.5, .60, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

@scene
def newsession():
    log = render.Text(0.5, 0.10, "")
    name = render.Text(0.5, 0.20, f"Session Name")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(.5, .25)
    pw = render.Text(0.5, .35, f"Session Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(.5, .40)
    pwbox.secure = True
    confirm = render.Text(0.5, .50, f"Confirm Password")
    confirm.color = current_theme().dark
    confirm.outline_color = current_theme().black
    confirmbox = render.InputTextBox(.5, .55)
    confirmbox.secure = True
    def verify():
        if pwbox.text != confirmbox.text: log.text = "Passwords do not match."; return
        if len(namebox.text) == 0: log.text = "Session name must not be empty."; return
        if len(pwbox.text) == 0: log.text = "Password field must not be empty."; return
        if len(namebox.text) > 32: log.text = f"Session name must be less than 32 characters. Yours: {len(namebox.text)}"; return
        if len(pwbox.text) > 32: log.text = f"Your password must be less than 32 characters. Yours: {len(pwbox.text)}"; return
        client.dic["session_name"] = namebox.text
        client.dic["session_pass_hash"] = client.hash(pwbox.text)
        log.text = client.request("create_session")
        if "success" not in log.text:
            client.dic["session_name"] = ""
            client.dic["session_pass_hash"] = ""
        print(f"log text {log.text}")
    confirm = render.Button(.5, .67, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .80, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

@scene
def connect():
    log = render.Text(0.5, 0.20, "")
    name = render.Text(0.5, 0.30, f"Session Name")
    name.color = current_theme().dark
    name.outline_color = current_theme().black
    namebox = render.InputTextBox(.5, .35)
    pw = render.Text(0.5, .45, f"Session Password")
    pw.color = current_theme().dark
    pw.outline_color = current_theme().black
    pwbox = render.InputTextBox(.5, .50)
    pwbox.secure = True
    def verify():
        if len(namebox.text) == 0: log.text = "Session name must not be empty."; return
        if len(pwbox.text) == 0: log.text = "Password must not be empty."; return
        log.text = "Connecting..."
        client.dic["session_name"] = namebox.text
        client.dic["session_pass_hash"] = client.hash(pwbox.text)
        log.text = client.request("connect")
        if "Success" not in log.text:
            client.dic["session_name"] = ""
            client.dic["session_pass_hash"] = ""
        print(f"log text {log.text}")
    confirm = render.Button(.5, .62, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .75, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

character_info = {
"name": None,
"noun": None,
"pronouns": ["they", "them", "their", "theirs"],
"interests": [],
"aspect": None,
"class": None,
"secondaryvial": None,
"modus": None,
"gristcategory": None,
"symbol_dict": config.get_random_symbol(),
}

@scene
def namecharacter():
    log = render.Text(0.5, 0.20, "")
    l1text = render.Text(0.5, 0.3, "A young being of indeterminate nature exists in some kind of area.")
    l1text.color = current_theme().dark
    l1text.outline_color = current_theme().black
    l2text = render.Text(0.5, 0.4, "What will this being's name be?")
    l2text.color = current_theme().dark
    l2text.outline_color = current_theme().black
    namebox = render.InputTextBox(.5, .48)
    def verify():
        if len(namebox.text) > 0 and len(namebox.text) < 32:
            character_info["name"] = namebox.text
            nouncharacter()
        else:
            log.text = "Name is too long or too short."
    confirm = render.Button(.50, .57, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)

@scene
def nouncharacter():
    log = render.Text(0.5, 0.20, "")
    log2 = render.Text(0.5, 0.30, "")
    l1text = render.Text(0.5, 0.4, f"You don't think \"being\" is a very accurate descriptor.")
    l1text.color = current_theme().dark
    l1text.outline_color = current_theme().black
    l2text = render.Text(0.5, 0.5, f"What word best describes {character_info['name']}?")
    l2text.color = current_theme().dark
    l2text.outline_color = current_theme().black
    namebox = render.InputTextBox(.5, .6)
    def verify():
        if len(namebox.text) > 0 and len(namebox.text) < 32:
            example = f"A newly-created {namebox.text} stands in a room."
            if log.text == example:
                character_info["noun"] = namebox.text
                pronounscharacter()
            else:
                log.text = example
                log2.text = "Press confirm again if this sounds okay."
        else:
            log.text = "That word is too long or too short."
            log2.text = ""
    confirm = render.Button(.5, .72, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)

@scene
def pronounscharacter():
    log = render.Text(0.5, 0.20, "")
    log2 = render.Text(0.5, 0.30, "")
    log3 = render.Text(0.5, 0.40, "")
    l1text = render.Text(0.5, 0.5, f"What pronouns should this {character_info['noun']} go by?")
    l1text.color = current_theme().dark
    l1text.outline_color = current_theme().black
    def confirmnouns(pronouns): # [0] they [1] them [2] their [3] theirs
        example1 = f"A newly-created {character_info['noun']} stands in {pronouns[2]} room. It surrounds {pronouns[1]}."
        example2 = f"Today {pronouns[0]} will play a game with some friends of {pronouns[3]}."
        if log.text == example1 and log2.text == example2:
            character_info["pronouns"] = pronouns
            make_symbol()
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
    hehim = render.Button(.20, 0.62, "sprites\\buttons\\hehim.png", "sprites\\buttons\\hehimpressed.png", himnouns)
    sheher = render.Button(.4, .62, "sprites\\buttons\\sheher.png", "sprites\\buttons\\sheherpressed.png", hernouns)
    theyem = render.Button(.6, .62, "sprites\\buttons\\theyem.png", "sprites\\buttons\\theyempressed.png", themnouns)
    other = render.Button(.8, .62, "sprites\\buttons\\other.png", "sprites\\buttons\\otherpressed.png", placeholder) # todo

@scene
def make_symbol():
    symbol = render.Symbol(0.66, 0.5, character_info["symbol_dict"])
    def get_button_func(part, direction: str):
        def button_func():
            current = character_info["symbol_dict"][part]
            current_index = config.possible_parts[part].index(current)
            if direction == "left":
                new_index = current_index - 1
            else:
                new_index = current_index + 1
            try:
                new_item_name = config.possible_parts[part][new_index]
            except IndexError:
                new_item_name = config.possible_parts[part][0]
            character_info["symbol_dict"][part] = new_item_name
            if character_info["symbol_dict"]["style_dict"][part] not in config.part_styles[part][new_item_name]:
                character_info["symbol_dict"]["style_dict"][part] = random.choice(config.part_styles[part][new_item_name])
            symbol.__init__(0.66, 0.5, character_info["symbol_dict"])
            symbol.surf = symbol.load_image("")
        return button_func
    def get_style_button_func(part, direction: str):
        def button_func():
            current_style = character_info["symbol_dict"]["style_dict"][part]
            current_item_name = character_info["symbol_dict"][part]
            current_index = config.part_styles[part][current_item_name].index(current_style)
            if direction == "left": new_index = current_index - 1
            else: new_index = current_index - 1
            try:
                new_style_name = config.part_styles[part][current_item_name][new_index]
            except IndexError:
                new_style_name = config.part_styles[part][current_item_name][0]
            character_info["symbol_dict"]["style_dict"][part] = new_style_name
            symbol.__init__(0.66, 0.5, character_info["symbol_dict"])
            symbol.surf = symbol.load_image("")
        return button_func
    def get_style_button_condition(part):
        def condition():
            current_item_name = character_info["symbol_dict"][part]
            if len(config.part_styles[part][current_item_name]) > 1: return True
            else: return False
        return condition
    def get_text_func(part):
        def text_func():
            return character_info["symbol_dict"][part]
        return text_func
    def get_style_text_func(part):
        def text_func():
            current_item_name = character_info["symbol_dict"][part]
            style = character_info["symbol_dict"]["style_dict"][part]
            if len(config.part_styles[part][current_item_name]) > 1: return style
            else: return ""
        return text_func
    def get_color_button_func(color_list: list[int]):
        def color_button_func():
            character_info["symbol_dict"]["color"] = color_list
            symbol.__init__(0.66, 0.5, character_info["symbol_dict"])
            symbol.surf = symbol.load_image("")
        return color_button_func
    def random_button():
        character_info["symbol_dict"] = config.get_random_symbol(character_info["symbol_dict"]["base"])
        symbol.__init__(0.66, 0.5, character_info["symbol_dict"])
        symbol.surf = symbol.load_image("")
    randomize = render.TextButton(0.33, 0.05, 196, 32, ">RANDOM", random_button)
    for i, part in enumerate(config.possible_parts):
        y = 0.13 + 0.1*i
        text = render.Text(0.33, y, "fuck")
        text.text_func = get_text_func(part)
        text.color = current_theme().dark
        label = render.Text(0.5, -0.1, part)
        label.fontsize = 18
        label.bind_to(text)
        left_button = render.TextButton(0.2, y, 32, 32, "<", get_button_func(part, "left"))
        right_button = render.TextButton(0.46, y, 32, 32, ">", get_button_func(part, "right"))
        style_label = render.Text(0.5, 1.2, "fuck")
        style_label.text_func = get_style_text_func(part)
        style_label.color = current_theme().dark
        style_label.fontsize = 18
        style_label.bind_to(text)
        left_style_button = render.TextButton(0.27, y+0.04, 20, 20, "<", get_style_button_func(part, "left"))
        left_style_button.draw_condition = get_style_button_condition(part)
        right_style_button = render.TextButton(0.39, y+0.04, 20, 20, ">", get_style_button_func(part, "right"))
        right_style_button.draw_condition = get_style_button_condition(part)
    color_swatch_x = 680
    color_swatch_y = 50
    color_swatch_wh = 32
    color_swatch_columns = 12
    color_swatch_rows = math.ceil(len(config.pickable_colors) / color_swatch_columns)
    current_column = 0
    current_row = 0
    outline_width = 4
    background = render.SolidColor(color_swatch_x-outline_width, color_swatch_y-outline_width, 
                                   color_swatch_wh*color_swatch_columns + outline_width*2,
                                   color_swatch_wh*color_swatch_rows + outline_width*2,
                                   current_theme().dark)
    background.border_radius = 2
    for color_list in config.pickable_colors:
        x = color_swatch_x + color_swatch_wh*current_column
        y = color_swatch_y + color_swatch_wh*current_row
        color = pygame.Color(color_list[0], color_list[1], color_list[2])
        color_button = render.TextButton(x, y, color_swatch_wh, color_swatch_wh, "", get_color_button_func(color_list))
        color_button.absolute = True
        color_button.fill_color = color
        color_button.hover_color = color
        color_button.outline_color = color
        current_column += 1
        if current_column == color_swatch_columns:
            current_column = 0
            current_row += 1
    custom_color_button = render.TextButton(1080, 65, 128, 32, ">CUSTOM", pick_custom_color)
    custom_color_button.absolute = True
    confirm_button = render.Button(0.65, 0.75, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", aspectcharacter)

@scene
def pick_custom_color():
    color_list = character_info["symbol_dict"]["color"]
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
        except ValueError: return pygame.Color(0, 0, 0)
    color_display_wh = 128
    color_display = render.SolidColor(render.SCREEN_WIDTH//2 - color_display_wh//2, 3*render.SCREEN_HEIGHT//10 - color_display_wh//2, 
                                      color_display_wh, color_display_wh, pygame.Color(0, 0, 0))
    color_display.color_func = color_display_func
    def confirm_button_func():
        r, g, b = int(red_box.text), int(green_box.text), int(blue_box.text)
        character_info["symbol_dict"]["color"] = [r, g, b]
        make_symbol()
    confirm_button = render.Button(0.5, 0.85, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", confirm_button_func)

def make_asbutton(aspect):
    def button():
        def on_confirm():
            character_info["aspect"] = f"{aspect}"
            chooseclass()
        render.clear_elements()
        text = render.Text(0.5, 0.25, "Is this the aspect you wish to choose?")
        text.color = current_theme().dark
        text.outline_color = current_theme().black
        blurb = render.Image(0.5, 0.39, f"sprites\\aspects\\{aspect}blurb.png")
        blurb.convert = False
        confirm = render.Button(0.5, 0.54, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", on_confirm)
        backbutton = render.Button(0.5, 0.66, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", aspectcharacter)
    return button

# NIGHTMARE NIGHTMARE NIGHTMARE!!!
@scene
def aspectcharacter():
    space = render.Button(0,0, "sprites\\aspects\\space120.png", "sprites\\aspects\\space120.png", make_asbutton("space"), hover="sprites\\aspects\\space120hover.png")
    space.absolute = True
    space.convert = False
    spaceblurb = render.Image(120, 0, "sprites\\aspects\\spaceblurb.png")
    spaceblurb.absolute = True
    time = render.Button(640, 0, "sprites\\aspects\\time120.png", "sprites\\aspects\\time120.png", make_asbutton("time"), hover="sprites\\aspects\\time120hover.png")
    time.absolute = True
    timeblurb = render.Image(760, 0, "sprites\\aspects\\timeblurb.png")
    timeblurb.absolute = True
    mind = render.Button(0, 120, "sprites\\aspects\\mind120.png", "sprites\\aspects\\mind120.png", make_asbutton("mind"), hover="sprites\\aspects\\mind120hover.png")
    mind.absolute = True
    mindblurb = render.Image(120, 120, "sprites\\aspects\\mindblurb.png")
    mindblurb.absolute = True
    heart = render.Button(640, 120, "sprites\\aspects\\heart120.png", "sprites\\aspects\\heart120.png", make_asbutton("heart"), hover="sprites\\aspects\\heart120hover.png")
    heart.absolute = True
    heartblurb = render.Image(760, 120, "sprites\\aspects\\heartblurb.png")
    heartblurb.absolute = True
    hope = render.Button(0, 240, "sprites\\aspects\\hope120.png", "sprites\\aspects\\hope120.png", make_asbutton("hope"), hover="sprites\\aspects\\hope120hover.png")
    hope.absolute = True
    hopeblurb = render.Image(120, 240, "sprites\\aspects\\hopeblurb.png")
    hopeblurb.absolute = True
    rage = render.Button(640, 240, "sprites\\aspects\\rage120.png", "sprites\\aspects\\rage120.png", make_asbutton("rage"), hover="sprites\\aspects\\rage120hover.png")
    rage.absolute = True
    rageblurb = render.Image(760, 240, "sprites\\aspects\\rageblurb.png")
    rageblurb.absolute = True
    breath = render.Button(0, 360, "sprites\\aspects\\breath120.png", "sprites\\aspects\\breath120.png", make_asbutton("breath"), hover="sprites\\aspects\\breath120hover.png")
    breath.absolute = True
    breathblurb = render.Image(120, 360, "sprites\\aspects\\breathblurb.png")
    breathblurb.absolute = True
    blood = render.Button(640, 360, "sprites\\aspects\\blood120.png", "sprites\\aspects\\blood120.png", make_asbutton("blood"), hover="sprites\\aspects\\blood120hover.png")
    blood.absolute = True
    bloodblurb = render.Image(760, 360, "sprites\\aspects\\bloodblurb.png")
    bloodblurb.absolute = True
    life = render.Button(0, 480, "sprites\\aspects\\life120.png", "sprites\\aspects\\life120.png", make_asbutton("life"), hover="sprites\\aspects\\life120hover.png")
    life.absolute = True
    lifeblurb = render.Image(120, 480, "sprites\\aspects\\lifeblurb.png")
    lifeblurb.absolute = True
    doom = render.Button(640, 480, "sprites\\aspects\\doom120.png", "sprites\\aspects\\doom120.png", make_asbutton("doom"), hover="sprites\\aspects\\doom120hover.png")
    doom.absolute = True
    doom.convert = False
    doomblurb = render.Image(760, 480, "sprites\\aspects\\doomblurb.png")
    doomblurb.absolute = True
    doomblurb.convert = False
    light = render.Button(0, 600, "sprites\\aspects\\light120.png", "sprites\\aspects\\light120.png", make_asbutton("light"), hover="sprites\\aspects\\light120hover.png")
    light.absolute = True
    lightblurb = render.Image(120, 600, "sprites\\aspects\\lightblurb.png")
    lightblurb.absolute = True
    void = render.Button(640, 600, "sprites\\aspects\\void120.png", "sprites\\aspects\\void120.png", make_asbutton("void"), hover="sprites\\aspects\\void120hover.png")
    void.absolute = True
    voidblurb = render.Image(760, 600, "sprites\\aspects\\voidblurb.png")
    voidblurb.absolute = True

def make_classbutton(game_class):
    def button():
        def on_confirm():
            character_info["class"] = f"{game_class}"
            chooseinterests()
        render.clear_elements()
        text = render.Text(0.5, 0.3, f"Are you sure you want to be the {game_class.upper()} of {character_info['aspect'].upper()}?")
        text.color = current_theme().dark
        text.outline_color = current_theme().black
        confirm = render.Button(0.5, 0.40, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", on_confirm)
        backbutton = render.Button(0.5, 0.52, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", chooseclass)
    return button

@scene
def chooseclass():
    knighttitle = render.Text(.14, .19, f"Knight")
    knightsymbol = render.Button(.14, .3, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("knight"), hover="sprites\\classes\\placeholderhover.png")
    knighttext = render.Text(.14, .4, f"Fights with {character_info['aspect'].upper()}")
    knighttext.fontsize = 15
    pagetitle = render.Text(.14, .59, f"Page")
    pagesymbol = render.Button(.14, .7, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("page"), hover="sprites\\classes\\placeholderhover.png")
    pagetext = render.Text(.14, .8, f"Provides {character_info['aspect'].upper()}")
    pagetext.fontsize = 15
    pagetext2 = render.Text(.14, .82, f"Becomes strong later")
    pagetext2.fontsize = 15
    princetitle = render.Text(.29, .19, f"Prince")
    princesymbol = render.Button(.29, .3, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("prince"), hover="sprites\\classes\\placeholderhover.png")
    princetext = render.Text(.29, .4, f"Destroys {character_info['aspect'].upper()}")
    princetext.fontsize = 15
    princetext2 = render.Text(.29, .42, f"Destroys with {character_info['aspect'].upper()}")
    princetext2.fontsize = 15
    bardtitle = render.Text(.29, .59, f"Bard")
    bardsymbol = render.Button(.29, .7, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("bard"), hover="sprites\\classes\\placeholderhover.png")
    bardtext = render.Text(.29, .8, f"{character_info['aspect'].upper()}less")
    bardtext.fontsize = 15
    thieftitle = render.Text(.43, .19, f"Thief")
    thiefsymbol = render.Button(.43, .3, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("thief"), hover="sprites\\classes\\placeholderhover.png")
    thieftext = render.Text(.43, .4, f"Steals {character_info['aspect'].upper()}")
    thieftext.fontsize = 15
    thieftext2 = render.Text(.43, .42, f"Hoards {character_info['aspect'].upper()}")
    thieftext2.fontsize = 15
    roguetitle = render.Text(.43, .59, f"Rogue")
    roguesymbol = render.Button(.43, .7, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("rogue"), hover="sprites\\classes\\placeholderhover.png")
    roguetext = render.Text(.43, .8, f"Steals {character_info['aspect'].upper()}")
    roguetext.fontsize = 15
    roguetext2 = render.Text(.43, .82, f"Shares {character_info['aspect'].upper()}")
    roguetext2.fontsize = 15
    magetitle = render.Text(.57, .19, f"Mage")
    magesymbol = render.Button(.57, .3, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("mage"), hover="sprites\\classes\\placeholderhover.png")
    magetext = render.Text(.57, .4, f"Sees {character_info['aspect'].upper()}")
    magetext.fontsize = 15
    magetext2 = render.Text(.57, .42, f"Pursues {character_info['aspect'].upper()}")
    magetext2.fontsize = 15
    seertitle = render.Text(.57, .59, f"Seer")
    seersymbol = render.Button(.57, .7, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("seer"), hover="sprites\\classes\\placeholderhover.png")
    seertext = render.Text(.57, .8, f"Sees {character_info['aspect'].upper()}")
    seertext.fontsize = 15
    seertext2 = render.Text(.57, .82, f"Avoids {character_info['aspect'].upper()}")
    seertext2.fontsize = 15
    witchtitle = render.Text(.71, .19, f"Witch")
    witchsymbol = render.Button(.71, .3, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("witch"), hover="sprites\\classes\\placeholderhover.png")
    witchtext = render.Text(.71, .4, f"Manipulates {character_info['aspect'].upper()}")
    witchtext.fontsize = 15
    heirtitle = render.Text(.71, .59, f"Heir")
    heirsymbol = render.Button(.71, .7, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("heir"), hover="sprites\\classes\\placeholderhover.png")
    heirtext = render.Text(.71, .8, f"Becomes {character_info['aspect'].upper()}")
    heirtext.fontsize = 15
    heirtext2 = render.Text(.71, .82, f"Inherits {character_info['aspect'].upper()}")
    heirtext2.fontsize = 15
    maidtitle = render.Text(.86, .19, f"Maid")
    maidsymbol = render.Button(.86, .3, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("maid"), hover="sprites\\classes\\placeholderhover.png")
    maidtext = render.Text(.86, .4, f"Creates {character_info['aspect'].upper()}")
    maidtext.fontsize = 15
    sylphtitle = render.Text(.86, .59, f"Sylph")
    sylphsymbol = render.Button(.86, .7, "sprites\\classes\\placeholder.png", "sprites\\classes\\placeholder.png", make_classbutton("sylph"), hover="sprites\\classes\\placeholderhover.png")
    sylphtext = render.Text(.86, .8, f"Restores {character_info['aspect'].upper()}")
    sylphtext.fontsize = 15
    sylphtext2 = render.Text(.86, .82, f"Heals with {character_info['aspect'].upper()}")
    sylphtext2.fontsize = 15
    backbutton = render.Button(0.1, 0.08, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", aspectcharacter)

@scene
def chooseinterests():
    #text = render.Text(0.5, 0.2, f"Interests: {client.requestdic('interests')}")
    logtext = render.Text(0.5, 0.1, "Select two interests.")
    interests = client.requestdic("interests")
    interestbuttons = {}
    for i, interest in enumerate(interests):
        y = 0.6 * ((i+1) / (len(interests)+1))
        y += .2
        b = render.TextButton(0.5, y, 110, 33, interest, placeholder)
        b.toggle = True
        interestbuttons[interest] = b
    def on_confirm():
        chosen = []
        for interest in interestbuttons:
            if interestbuttons[interest].active: chosen.append(interest)
        if len(chosen) < 2:
            logtext = "You need to choose at least two interests."
        elif len(chosen) > 2:
            logtext = "You may only choose two interests."
        else:
            character_info["interests"] = chosen
            choosevial()
    confirm = render.Button(0.5, 0.9, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", on_confirm)
    backbutton = render.Button(0.1, 0.07, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", chooseclass)

@scene
def choosevial():
    def vialbutton(vial):
        def out():
            character_info["secondaryvial"] = vial
            choosemodus()
        return out
    logtext = render.Text(.5, .05, "Choose a SECONDARY VIAL.")
    mangrittitle = render.Text(0.33, 0.24, "MANGRIT")
    mangritimage = render.Button(0.33, 0.33, "sprites\\vials\\mangrit\\mangritexample.png", "sprites\\vials\\mangrit\\mangritexamplepressed.png", vialbutton("mangrit"))
    mangritdescription = render.Text(0.33, 0.4, "Starts empty, but increases steadily.")
    mangritdescription.fontsize = 16
    mangritdescription2 = render.Text(0.33, 0.43, "Increases damage.")
    mangritdescription2.fontsize = 16
    imaginationtitle = render.Text(0.33, 0.57, "IMAGINATION")
    imaginationimage = render.Button(0.33, 0.66, "sprites\\vials\\imagination\\imaginationexample.png", "sprites\\vials\\imagination\\imaginationexamplepressed.png", vialbutton("imagination"))
    imaginationdescription = render.Text(0.33, 0.73, "Starts empty, increases as ASPECT vial is drained.")
    imaginationdescription.fontsize = 16
    imaginationdescription2 = render.Text(0.33, 0.76, "Increases ASPECT vial regeneration.")
    imaginationdescription2.fontsize = 16
    horseshitometertitle = render.Text(0.66, 0.17, "FLIGHTY BROADS AND")
    horseshitometertitle2 = render.Text(0.66, 0.24, "THEIR SNARKY HORSESHITOMETER")
    horseshitometerimage = render.Button(0.66, 0.33, "sprites\\vials\\horseshitometer\\horseshitometerexample.png", "sprites\\vials\\horseshitometer\\horseshitometerexamplepressed.png", vialbutton("horseshitometer"))
    horseshitometerdescription = render.Text(0.66, 0.4, "Starts 50%.")
    horseshitometerdescription.fontsize = 16
    horseshitometerdescription2 = render.Text(0.66, 0.43, "AUTO-PARRYING increases, getting hit decreases.")
    horseshitometerdescription2.fontsize = 16
    horseshitometerdescription3 = render.Text(0.66, 0.46, "Increases or decreases chance to AUTO-PARRY.")
    horseshitometerdescription3.fontsize = 16
    gambittitle = render.Text(0.66, 0.57, "PRANKSTER'S GAMBIT")
    gambitimage = render.Button(0.66, 0.66, "sprites\\vials\\gambit\\gambitexample.png", "sprites\\vials\\gambit\\gambitexamplepressed.png", vialbutton("gambit"))
    gambitdescription = render.Text(0.66, 0.73, "Starts 50%.")
    gambitdescription.fontsize = 16
    gambitdescription2 = render.Text(0.66, 0.76, "Increases when using FUNNY weapons.")
    gambitdescription2.fontsize = 16
    gambitdescription3 = render.Text(0.66, 0.79, "Increases damage dealt with FUNNY weapons.")
    gambitdescription3.fontsize = 16
    backbutton = render.Button(0.1, 0.07, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", chooseinterests)

@scene
def choosemodus():
    def modusbutton(modus):
        def out():
            character_info["modus"] = modus
            choosegrists()
        return out
    logtext = render.Text(.5, 0.05, "Select your starting FETCH MODUS.")
    stack_image = render.Button(0.11, 0.45, "sprites/moduses/stack_card.png", "sprites/moduses/stack_card_hover.png", modusbutton("stack"))
    stack_label = render.Text(0.55, 1.05, "stack")
    stack_label.bind_to(stack_image)
    stack_description = render.Text(0.55, 1.13, "first in, last out")
    stack_description.fontsize = 20
    stack_description.bind_to(stack_image)
    queue_image = render.Button(0.36, 0.45, "sprites/moduses/queue_card.png", "sprites/moduses/queue_card_hover.png", modusbutton("queue"))
    queue_label = render.Text(0.55, 1.05, "queue")
    queue_label.bind_to(queue_image)
    queue_description = render.Text(0.55, 1.13, "first in, first out")
    queue_description.fontsize = 20
    queue_description.bind_to(queue_image)
    array_image = render.Button(0.61, 0.45, "sprites/moduses/array_card.png", "sprites/moduses/array_card_hover.png", modusbutton("array"))
    array_label = render.Text(0.55, 1.05, "array")
    array_label.bind_to(array_image)
    array_description = render.Text(0.55, 1.13, "no bullshit, no fun")
    array_description.fontsize = 20
    array_description.bind_to(array_image)
    scratch_image = render.Button(0.86, 0.45, "sprites/moduses/array_card.png", "sprites/moduses/array_card.png", placeholder)
    backbutton = render.Button(0.1, 0.07, "sprites/buttons/back.png", "sprites/buttons/backpressed.png", choosevial)

    ...

@scene
def choosegrists():
    # 19 grist categories
    # todo: add indicators for which grist types the session already has
    session_info = client.requestdic("session_info")
    available_types = session_info["current_grist_types"]
    print(session_info)
    print(available_types)
    logtext = render.Text(.5, .05, "Select the type of land you would like.")
    infotext = render.Text(.5, .09, "A darkened background indicates grist already available in the session.")
    infotext.fontsize = 20
    infotext = render.Text(.75, .91, "A yellow background indicates exotic grist.")
    infotext.fontsize = 20
    infotext = render.Text(.75, .94, "Exotic grist types cannot normally be obtained")
    infotext.fontsize = 20
    infotext = render.Text(.75, .97, "unless a player has specifically picked them.")
    infotext.fontsize = 20
    def choosegristtype(grist):
        def out():
            logtext.fontsize = 20
            t = f"Are you sure you want {grist.upper()}? Press the button again to confirm."
            if logtext.text == t:
                character_info["gristcategory"] = grist
                newgame()
            else:
                logtext.text = t
        return out
    for i, category in enumerate(config.gristcategories):
        if i <= 9:
            x = .07
        else:
            x = .54
        num = i
        if num > 9:
            num -= 10
        y = ((num+1) / 12)
        y += .08
        button = render.TextButton(x, y, 110, 33, category.upper(), choosegristtype(category))
        for ind, grist in enumerate(config.gristcategories[category]):
            img = render.Image(x+0.07+(0.04 * ind), y, config.grists[grist]["image"])
            if grist in available_types:
                img.highlight_color = current_theme().dark
            elif "exotic" in config.grists[grist] and config.grists[grist]["exotic"]:
                img.highlight_color = pygame.Color(255,255,0)
    backbutton = render.Button(0.08, 0.05, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", choosemodus)

def newgame():
    client.requestplus("setup_character",  character_info)
    new_sylladex = Sylladex.new_sylladex(client.dic["character"], character_info["modus"])
    print(new_sylladex)
    new_sylladex.validate()
    map_scene()

def debug_speedrun():
    client.dic["session_name"] = "fuck"
    client.dic["session_pass_hash"] = client.hash("ass")
    client.request("create_session")
    client.dic["character"] = "alienatingParticles"
    client.dic["character_pass_hash"] = client.hash("ass")
    client.request("create_character")
    character_info["name"] = "Iness"
    character_info["noun"] = "rabbit girl"
    character_info["pronouns"] = ["she", "her", "her", "hers"]
    character_info["interests"] = ["music", "technology"]
    character_info["aspect"] = "life"
    character_info["class"] = "sylph"
    character_info["secondaryvial"] = "imagination"
    character_info["modus"] = "array"
    character_info["gristcategory"] = "amber"
    style_dict = config.default_style_dict.copy()
    style_dict.update({
            "pants": "rgb",
            "shoes": "trollian",
            "coat": "rgb",
        })
    character_info["symbol_dict"] = {
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
    newgame()

def debug_speedrun_2():
    client.dic["session_name"] = "fuck"
    client.dic["session_pass_hash"] = client.hash("ass")
    client.request("create_session")
    client.dic["character"] = "basementDemon"
    client.dic["character_pass_hash"] = client.hash("ass")
    client.request("create_character")
    character_info["name"] = "Azaral"
    character_info["noun"] = "basement demon"
    character_info["pronouns"] = ["he", "him", "his", "his"]
    character_info["interests"] = ["garbage", "anime"]
    character_info["aspect"] = "doom"
    character_info["class"] = "bard"
    character_info["secondaryvial"] = "gambit"
    character_info["modus"] = "array"
    character_info["gristcategory"] = "dark"
    style_dict = config.default_style_dict.copy()
    style_dict.update({
            "pants": "trollian",
            "eyes": "rgb",
            "shoes": "trollian",
            "coat": "trollian",
        })
    character_info["symbol_dict"] = {
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
    newgame()

@scene
def computer(instance: Instance):
    print(instance.computer_data)
    task_bar = render.TaskBar()
    apps = []
    for app_name in instance.computer_data["installed_programs"]:
        random.seed(instance.name+app_name)
        x = 0.1 + random.random() * 0.7
        random.seed(instance.name+app_name)
        y = 0.1 + random.random() * 0.7
        app_icon = render.AppIcon(random.random(), random.random(), app_name, task_bar)
        apps.append(app_icon)

def gristtorrent(window: "render.Window"):
    theme = themes.gristtorrent
    viewport = window.viewport
    padding = 7
    player_dict = client.requestdic("player_info")
    grist_cache = player_dict["grist_cache"]
    grist_cache_limit = player_dict["grist_cache_limit"]
    grist_gutter = player_dict["grist_gutter"]
    total_gutter_grist = player_dict["total_gutter_grist"]
    leeching = player_dict["leeching"]
    banner_head = render.Image(0, 0, "sprites/computer/gristTorrent/banner.png")
    banner_head.absolute = True
    banner_head.bind_to(viewport)
    icon = render.Image(0.29, 0.5, "sprites/computer/apps/gristTorrent.png", convert=False)
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
    grist_box_w = grist_display_w//num_columns - padding - grist_box_outline_width
    grist_box_h = grist_display_h//num_rows - padding - grist_box_outline_width
    def get_box_button_func(grist_name):
        def box_button_func():
            client.requestplus(intent="computer", content={"command": "leech", "grist_type": grist_name})
            window.reload()
        return box_button_func
    for column_index, column in enumerate(columns):
        grist_box_x = padding + (grist_box_w+padding)*column_index 
        for row_index, grist_name in enumerate(column):
            grist_box_y = 150 + padding + (grist_box_h+padding)*row_index
            box = render.make_grist_display(grist_box_x, grist_box_y, grist_box_w, grist_box_h, padding, grist_name, grist_cache[grist_name], grist_cache_limit, theme)
            box.border_radius = 2
            if grist_name in leeching: box.outline_color = pygame.Color(255, 0, 0)
            box.bind_to(viewport)
            box_button = render.TextButton(grist_box_x, grist_box_y, grist_box_w, grist_box_h, "", get_box_button_func(grist_name))
            box_button.absolute = True
            box_button.draw_sprite = False
            box_button.bind_to(viewport)
    gutter_box_width = viewport.w//2
    gutter_box_height = 40
    gutter_box = render.SolidColor(viewport.w-gutter_box_width-padding, viewport.h-gutter_box_height-padding, gutter_box_width, gutter_box_height, theme.white)
    gutter_box.outline_color = theme.black
    gutter_box.bind_to(viewport)
    box_label = render.Text(0.5, 0.25, "grist gutter")
    box_label.color = theme.light
    box_label.fontsize = 18
    box_label.bind_to(gutter_box)
    small_icon = render.Image(-0.03, 0.5, "sprites/computer/apps/gristTorrent.png", convert=False)
    small_icon.scale = 0.33
    small_icon.bind_to(gutter_box)
    gutter_label = render.Text(0.5, 0.9, str(total_gutter_grist))
    gutter_label.color = theme.light
    gutter_label.fontsize = 12
    gutter_label.bind_to(gutter_box)
    gutter_bar_background_width = gutter_box_width - padding*2
    gutter_bar_background_height = 8
    gutter_bar_background = render.SolidColor(padding, gutter_box_height*1.5//3, gutter_bar_background_width, gutter_bar_background_height, theme.white)
    gutter_bar_background.outline_color = theme.black
    gutter_bar_background.border_radius = 3
    gutter_bar_background.bind_to(gutter_box)
    #starting x
    gutter_bar_padding = 2
    total_bar_width = (gutter_box_width-padding*2 - gutter_bar_padding*2)
    gutter_bar_x = gutter_bar_padding
    gutter_bar_y = gutter_bar_padding
    for grist_name, amount in grist_gutter:
        bar_width = int(total_bar_width * (amount/total_gutter_grist))
        if bar_width == 0: continue
        gutter_bar_color = config.gristcolors[grist_name]
        gutter_bar = render.SolidColor(gutter_bar_x, gutter_bar_y, bar_width, gutter_bar_background_height - gutter_bar_padding*2, gutter_bar_color)
        gutter_bar.bind_to(gutter_bar_background)
        gutter_bar_x += bar_width

@scene
def map_scene():
    strife_data = client.requestdic(intent="strife_data")
    if strife_data: 
        strife_scene(strife_data)
        return
    ui_bar = Sylladex.current_sylladex().draw_ui_bar(map_scene)
    tilemap = render.TileMap(0.5, 0.5)
    portfolio_button = render.TextButton(render.SCREEN_WIDTH-256, render.SCREEN_HEIGHT-166-64, 256, 64, "strife portfolio", strife_portfolio_scene, theme=themes.strife)
    portfolio_button.absolute = True
    portfolio_button.fill_color = themes.strife.dark
    portfolio_button.text_color = themes.strife.light
    portfolio_button.outline_color = themes.strife.black
    overmap_button = render.TextButton(0.9, 0.1, 196, 64, ">OVERMAP", overmap)
    log = render.LogWindow(map_scene, tilemap=tilemap, draw_console=True)

@scene
def strife_scene(strife_dict: Optional[dict]=None):
    strife.strife_scene(strife_dict)

@scene
def overmap():
    reply = client.requestdic(intent="current_overmap")
    map_tiles = reply["map_tiles"]
    theme_name = reply["theme"]
    theme = themes.themes[theme_name]
    background = render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.black)
    overmap = render.Overmap(0.5, 0.5, map_tiles, theme=theme)
    backbutton = render.Button(0.1, 0.1, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", map_scene, theme=theme)

@scene
def display_item(instance: Instance, last_scene:Callable, modus:Optional[Modus] = None, flipped=False, strife=False):
    render.LogWindow(display_item)
    if strife:
        card_path = "sprites/itemdisplay/strife_captchalogue_card.png"
        card_flipped_path = "sprites/itemdisplay/strife_captchalogue_card_flipped.png"
        text_color = themes.strife.light
        text_outline_color = None
        def flip():
            if not instance.item.forbiddencode:
                display_item(instance, last_scene, modus=modus, flipped=not flipped, strife=strife)
    elif modus is None:
        card_path = "sprites\\itemdisplay\\captchalogue_card.png"
        card_flipped_path = "sprites\\itemdisplay\\captchalogue_card_flipped.png"
        text_color = current_theme().dark
        text_outline_color = None
        def flip():
            pass
    else:
        card_path = modus.front_path
        card_flipped_path = modus.back_path
        text_color = modus.theme.light
        text_outline_color = modus.theme.black
        def flip():
            if not instance.item.forbiddencode:
                display_item(instance, last_scene, modus=modus, flipped=not flipped, strife=strife)
    if not flipped:
        captcha_image = render.Button(0.5, 0.4, card_path, card_path, flip)
        image_path = None
        if os.path.isfile(f"sprites\\items\\{instance.item_name}.png"):
            image = render.Image(0.5, 0.5, f"sprites\\items\\{instance.item_name}.png")
            image.convert = False
            image.bind_to(captcha_image)
        label = render.Text(0.55, 0.91, util.filter_item_name(instance.item_name))
        label.bind_to(captcha_image)
        label.color = text_color
        label.outline_color = text_outline_color
        label.set_fontsize_by_width(240)
        num_actions = len(instance.item.use)
        for i, action_name in enumerate(instance.item.use):
            x = 0.05 + (1/(num_actions+1))*(i+1)
            y = 1.07
            path = f"sprites/item_actions/{action_name}.png"
            pressed_path = f"sprites/item_actions/{action_name}_pressed.png"
            if not os.path.isfile(path): path = "sprites/item_actions/generic_action.png"
            if not os.path.isfile(pressed_path): pressed_path = "sprites/item_actions/generic_action_pressed.png"
            action_button = render.Button(x, y, path, pressed_path, instance.get_action_button_func(action_name, last_scene))
            action_button.scale = 2.0
            action_button.bind_to(captcha_image)
    else:
        code = instance.item.code
        captcha_image = render.Button(0.5, 0.4, card_flipped_path, card_flipped_path, flip)
        captcha_code = render.Image(32, 28, get_captcha(code), convert=False)
        captcha_code.bind_to(captcha_image)
        captcha_code.absolute = True
    power = instance.item.power
    power_bar = render.Image(0.5, 1.28, "sprites\\itemdisplay\\power_bar.png")
    power_bar.bind_to(captcha_image)
    power_label = render.Text(0.512, 0.51, str(power))
    power_label.bind_to(power_bar)
    power_label.color = current_theme().dark
    power_label.fontsize = 54
    power_label.set_fontsize_by_width(330)
    num_kinds = len(instance.item.kinds)
    def get_kind_button_func(kind_name):
        def kind_button_func():
            player_dict = client.requestdic(intent="player_info")
            if kind_name in player_dict["strife_portfolio"] and modus is not None:
                reply = client.requestplus(intent="move_to_strife_deck", content={"instance_name": instance.name, "kind_name": kind_name})
                if reply:
                    Sylladex.current_sylladex().remove_instance(instance.name)
                    # todo: switch to strife portfolio scene
                    last_scene()
            elif player_dict["unassigned_specibi"] <= 0:
                util.log("You don't have any unassigned specibi.")
                return
            elif kind_name in player_dict["strife_portfolio"]:
                util.log(f"You must captchalogue this first.")
                return
            else:
                assign_strife_specibus(kind_name, last_scene)
        return kind_button_func
    for i, kind in enumerate(instance.item.kinds):
        x = 1.2
        y = (1/(num_kinds+1))*num_kinds/(i+1)
        kind_card_image = render.Button(x, y, "sprites\\itemdisplay\\strife_card.png", None, get_kind_button_func(kind))
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
            render.spawn_punches(captcha_image, instance.punched_code, 122, 138, w=80, h=120)
    if strife:
        def eject_button_func():
            client.requestplus(intent="eject_from_strife_deck", content={"instance_name": instance.name})
            last_scene()
        eject_button = render.TextButton(0.5, 1.2, 300, 33, "eject from strife deck", eject_button_func)
        eject_button.bind_to(power_bar)
    elif modus is not None:
        syl = Sylladex.current_sylladex()
        def uncaptcha_button_func():
            syl.uncaptchalogue(instance.name)
            last_scene()
        if modus.can_uncaptchalogue:
            uncaptchalogue_button = render.TextButton(0.5, 1.2, 200, 33, "uncaptchalogue", uncaptcha_button_func)
            uncaptchalogue_button.bind_to(power_bar)
    backbutton = render.Button(0.1, 0.9, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", last_scene)

@scene
def assign_strife_specibus(kind_name: str, last_scene: Callable = map_scene):
    confirm_text = render.Text(0.5, 0.1, f"Do you want to assign {kind_name} as a new strife specibus?")
    confirm_text.color = current_theme().dark
    def confirm():
        reply = client.requestplus("assign_specibus", {"kind_name": kind_name})
        if reply: util.log(f"You assigned {kind_name}!")
        else: util.log("Failed to assign.")
        strife_portfolio_scene()
    confirm_button = render.Button(0.5, 0.2, "sprites/buttons/confirm.png", "sprites/buttons/confirmpressed.png", confirm)
    back_button = render.Button(0.5, 0.3, "sprites/buttons/back.png", "sprites/buttons/backpressed.png", last_scene)

@scene
def strife_portfolio_scene(selected_kind:Optional[str]=None):
    theme = themes.strife
    padding = 8
    background = render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.dark)
    player_dict = client.requestdic(intent="player_info")
    # todo: get player power
    power = player_dict["power"]
    stat_ratios = player_dict["stat_ratios"]
    permanent_stat_bonuses = player_dict["permanent_stat_bonuses"]
    # kind_name:dict[instance_name:instance_dict]
    strife_portfolio = player_dict["strife_portfolio"]
    wielding = player_dict["wielding"]
    wielded_instance: Optional[Instance] = None
    for kind in strife_portfolio:
        for instance_name in strife_portfolio[kind]:
            print(instance_name)
            if instance_name == wielding: wielded_instance = Instance(instance_name, strife_portfolio[kind][instance_name])
    if selected_kind is None: 
        if strife_portfolio:
            selected_kind = list(strife_portfolio.keys())[0]
        else:
            selected_kind = None
    if selected_kind is not None:
        # main box
        symbol = render.Symbol(0.825, 0.6, player_dict["symbol_dict"])
        print(selected_kind)
        strife_deck_bar = render.Image(0, 0, "sprites/itemdisplay/strife_deck_bar.png")
        strife_deck_bar.absolute = True
        label = render.Text(0.5, 0.065, selected_kind)
        label.color = theme.light
        label.fontsize = 48
        label.set_fontsize_by_width(350)
        abstratus_display = render.Image(0.51, 0.43, "sprites/itemdisplay/strife_abstratus_display.png")
        if os.path.isfile(f"sprites\\kinds\\{selected_kind}.png"):
            kind_image = render.Image(0.5, 0.5, f"sprites\\kinds\\{selected_kind}.png")
            kind_image.bind_to(abstratus_display)
            kind_image.scale = 3
        # power label
        power_label = render.Text(padding, padding*3, f"power: {power}")
        power_label.absolute = True
        power_label.color = theme.light
        power_label.set_fontsize_by_width(300)
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
                    for box in stat_boxes.values(): total_ratios += int(box.text)
                    stats = {}
                    for stat_name in stat_boxes:
                        value = int(stat_boxes[stat_name].text)
                        if total_ratios != 0: stat_mult = (value/total_ratios)
                        else: stat_mult = 1/len(stat_boxes)
                        stats[stat_name] = int(power * stat_mult)
                    remainder = power - sum(stats.values())
                    for stat_name in stats:
                        if remainder == 0: break
                        if int(stat_boxes[stat_name].text) == 0: continue
                        stats[stat_name] += 1
                        remainder -= 1
                    amount = stats[stat]
                    if stat in permanent_stat_bonuses: bonus = permanent_stat_bonuses[stat]
                    else: bonus = 0
                    amount += bonus
                    text = labels[stat].format(amount)
                    if bonus != 0: text += f" (+{bonus})"
                    return text
                return label_func
            stat_label = render.Text(padding, padding*4 + abstratus_display.rect.y+y+box_width-fontsize//2, labels[stat])
            stat_label.text_func = get_label_func(stat)
            stat_label.absolute = True
            stat_label.color = theme.light
            stat_label.fontsize = fontsize
            stat_description = render.Text(0, fontsize+padding, descriptions[stat])
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
            if i == 5:
                def confirm():
                    ratios = {}
                    for stat in stats:
                        ratios[stat] = int(stat_boxes[stat].text)
                    client.requestplus(intent="set_stat_ratios", content={"ratios": ratios})
                confirm_button = render.TextButton(0, box_width + padding, box_width, box_width//2, ">save", confirm, theme=theme)
                confirm_button.absolute = True
                confirm_button.outline_color = theme.black
                confirm_button.fill_color = theme.light
                confirm_button.bind_to(box)
        # wielded display
        wielded_display = render.Image(1.3, 0.2, "sprites/itemdisplay/strife_equip_display.png")
        wielded_display.bind_to(abstratus_display)
        equipped_label = render.Text(0.5, 0, "wielding")
        equipped_label.fontsize = 20
        equipped_label.color = theme.black
        equipped_label.bind_to(wielded_display)
        if wielded_instance is not None:
            image_path = f"sprites/items/{wielded_instance.item.name}.png"
            if os.path.isfile(image_path):
                card_image = render.ItemImage(0.49, 0.5, wielded_instance.item_name)
                if card_image is not None:
                    card_image.convert = False
                    card_image.bind_to(wielded_display)
                    card_image.scale = 0.5
            item_label = render.Text(0.6, 1.1, f"{wielded_instance.display_name(True)}")
        else:
            item_label = render.Text(0.6, 1.1, f"nothing")
        item_label.fontsize = 20
        item_label.color = theme.light
        item_label.bind_to(wielded_display)
        # bottom bar
        instances_length = len(strife_portfolio[selected_kind])
        def get_button_func(instance: Instance) -> Callable:
            def wrapper():
                display_item(instance, strife_portfolio_scene, modus=None, strife=True)
            return wrapper
        def get_wield_button_func(instance_name: Instance) -> Callable:
            def wrapper():
                reply = client.requestplus(intent="wield", content={"instance_name": instance_name})
                print(reply)
                strife_portfolio_scene(selected_kind)
            return wrapper
        for i, instance_name in enumerate(strife_portfolio[selected_kind]):
            x = (render.SCREEN_WIDTH / 2) - 109 + 125*(i + 1 - instances_length/2)
            x = int(x)
            y = int(render.SCREEN_HEIGHT*0.80)
            instance = Instance(instance_name, strife_portfolio[selected_kind][instance_name])
            button_function = get_button_func(instance)
            card_thumb = render.Button(x, y, "sprites/moduses/card_thumb.png", "sprites/moduses/card_thumb.png", button_function)
            card_thumb.absolute = True
            card_thumb.bind_to(strife_deck_bar)
            image_path = f"sprites/items/{instance.item_name}.png"
            if os.path.isfile(image_path):
                card_image = render.ItemImage(0.49, 0.5, instance.item_name)
                if card_image is not None:
                    card_image.convert = False
                    card_image.bind_to(card_thumb)
                    card_image.scale = 0.5
            else:
                card_image = None
            label_text = instance.display_name(short=True)
            card_label = render.Text(0.49, 0.9, label_text)
            card_label.set_fontsize_by_width(90)
            card_label.bind_to(card_thumb)
            if instance_name != wielding:
                wield_button = render.TextButton(0.5, -0.15, 100, 30, ">wield", get_wield_button_func(instance_name), theme=theme)
                wield_button.outline_color = theme.black
                wield_button.bind_to(card_thumb)
    else:
        # selected kind is None
        info_text = render.Text(0.5, 0.3, "Add an item to your strife portfolio by clicking the specibus icon while viewing it.")
        info_text_2 = render.Text(0.5, 0.7, "You can assign a strife specibus the same way.")
        info_text.color, info_text_2.color = theme.light, theme.light
        info_text.fontsize, info_text_2.fontsize = 20, 20
        abstratus_icon = render.Image(0.5, 0.5, "sprites/itemdisplay/strife_card.png")
    back_button = render.Button(0.08, 0.95, "sprites/buttons/back.png", "sprites/buttons/backpressed.png", map_scene, theme=theme)

@scene
def title():
    logo = render.Image(.5, .20, "sprites\\largeicon.png")
    logotext = render.Image(.5, .47, "sprites\\suburb.png")
    def isconnected():
        if client.dic["session_name"] != "":
            return False # return False because the alternative condition is unclickable
        else:
            return True
    play_button = render.Button(.5, .59, "sprites\\buttons\\play.png", "sprites\\buttons\\playpressed.png", play, alt=isconnected, alt_img_path="sprites\\buttons\\playgrey.png", altclick = None)
    play_button.alt_alpha = 100
    connect_button = render.Button(.5, .70, "sprites\\buttons\\connect.png", "sprites\\buttons\\connectpressed.png", connect)
    new_session_button = render.Button(.5, .81, "sprites\\buttons\\newsession.png", "sprites\\buttons\\newsessionpressed.png", newsessionprompt)
    options_button = render.Button(.5, .92, "sprites\\buttons\\options.png", "sprites\\buttons\\optionspressed.png", newsessionprompt)
    versiontext = render.Text(0, 0, f"SUBURB Version {util.VERSION}")
    versiontext.absolute = True
    versiontext.color = current_theme().dark
    versiontext.outline_color = current_theme().black
    if client.dic["session_name"] != "":
        conntextcontent = f"Session `{client.dic['session_name']}`"
    else:
        conntextcontent = f"No session."
    conntext = render.Text(0, 30, conntextcontent)
    conntext.absolute = True
    debug_button = render.Button(.1, .92, "sprites\\buttons\\debug.png", "sprites\\buttons\\debug.png", debug_speedrun)
    debug_button_2 = render.Button(.1, .82, "sprites\\buttons\\debug_2.png", "sprites\\buttons\\debug_2.png", debug_speedrun_2)

def map_from_file(file):
    with open(f"maps/{file}", "r") as f:
        content = f.read()
    content = content.split("\n") #split y axis
    map = []
    for line in content:
        map.append(list(line)) # split each string in content into a list of letters
    return map

def test_overmap():
    test_overmap_tiles = map_from_file("test_map.txt")
    test_overmap_tiles = [list(line) for line in test_overmap_tiles if line]
    theme = random.choice(list(themes.themes.values()))
    render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.black)
    render.Overmap(0.5, 0.5, test_overmap_tiles, theme=theme)

if __name__ == "__main__":
    client.connect() # connect to server
    # aspectcharacter() # choose scene to test
    # chooseinterests()
    # choosegrists()
    # choosevial()
    # choosemodus()
    # render.TileMap(0.5, 0.5, map)
    # computer()
    # make_symbol()
    title() # normal game start
    # test_overmap()
    # continue to render until render.render() returns False
    # imp = render.Enemy(0.5, 0.5, "shale", "imp") 
    # render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, themes.default.black)
    # render.Overmap(0.5, 0.5, test_map)
    # render.Symbol(0.5, 0.5, config.get_random_symbol())
    while render.render():
        ...

