import pygame
import sys
import pathlib
import hashlib
import socket
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
"gristcategory": None
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
            aspectcharacter()
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
    item_display = render.RoomItemDisplay(70, 190, {})
    ui_bar = Sylladex.current_sylladex().draw_ui_bar(map_scene)
    tilemap = render.TileMap(0.5, 0.5, item_display)
    portfolio_button = render.TextButton(render.SCREEN_WIDTH-256, render.SCREEN_HEIGHT-166-64, 256, 64, "strife portfolio", strife_portfolio, theme=themes.strife)
    portfolio_button.absolute = True
    portfolio_button.fill_color = themes.strife.dark
    portfolio_button.text_color = themes.strife.light
    portfolio_button.outline_color = themes.strife.black
    overmap_button = render.TextButton(0.9, 0.1, 196, 64, ">OVERMAP", overmap)
    log = render.LogWindow(map_scene, tilemap=tilemap, draw_console=True)

@scene
def overmap():
    map_tiles = client.requestdic(intent="current_overmap")["map_tiles"]
    background = render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, themes.default.black)
    overmap = render.Overmap(0.5, 0.5, map_tiles)
    backbutton = render.Button(0.1, 0.1, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", map_scene)

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
        if reply: util.log("You assigned {kind_name}!")
        else: util.log("Failed to assign.")
        last_scene()
    confirm_button = render.Button(0.5, 0.2, "sprites/buttons/confirm.png", "sprites/buttons/confirmpressed.png", confirm)
    back_button = render.Button(0.5, 0.3, "sprites/buttons/back.png", "sprites/buttons/backpressed.png", last_scene)

@scene
def strife_portfolio(selected_kind:Optional[str]=None):
    theme = themes.strife
    background = render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, theme.dark)
    player_dict = client.requestdic(intent="player_info")
    # kind_name:dict[instance_name:instance_dict]
    strife_portfolio = player_dict["strife_portfolio"]
    if selected_kind is None: 
        if strife_portfolio:
            selected_kind = list(strife_portfolio.keys())[0]
        else:
            selected_kind = None
    if selected_kind is not None:
        print(selected_kind)
        strife_deck_bar = render.Image(0, 0, "sprites/itemdisplay/strife_deck_bar.png")
        strife_deck_bar.absolute = True
        label = render.Text(0.5, 0.065, selected_kind)
        label.color = theme.light
        label.fontsize = 48
        abstratus_display = render.Image(0.51, 0.43, "sprites/itemdisplay/strife_abstratus_display.png")
        if os.path.isfile(f"sprites\\kinds\\{selected_kind}.png"):
            kind_image = render.Image(0.5, 0.5, f"sprites\\kinds\\{selected_kind}.png")
            kind_image.bind_to(abstratus_display)
            kind_image.scale = 3
            instances_length = len(strife_portfolio[selected_kind])
            def get_button_func(instance: Instance) -> Callable:
                def wrapper():
                    display_item(instance, strife_portfolio, modus=None, strife=True)
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
    back_button = render.Button(0.1, 0.1, "sprites/buttons/back.png", "sprites/buttons/backpressed.png", map_scene, theme=theme)

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

def test_overmap():
    test_overmap_tiles = """000000000222121111000000000112222332110000000000000000000000000000000000000000000000000000000000
000000000222223111100000000011122121120000000000000000000000000000000000000000000000000000000000
000000211221111112120000000021111111120000000000000000000000000000000000000000000000000000000000
000000020111111100100220000232113222100000000000000000000000000000021011000000000000000000000000
000000021111111000000222100022212223200000000000000000000000000000002021000000000000000000000000
000000001111121200012221110022233322210000000000000000000000000000211122020000000000000000000000
000000002223111000022331200000111122000000000000000000000000000000021112212010000000000000000000
000000002212211000111111110000001120000000000000000000002000000000131111112010000000000000000000
000000023222122001112111222200000000000000101000000000211000000000122331111220000000000002222222
000000022332222001111122222210000000000000122000000000110000000022331133111100000000000012231220
000001222122222101211132221111200000000021222200000001202000010022332222222200000000000011222221
000002222322211012211112221110000000000011112000000002111010011222332112222100000000021222221222
000011233320012011121112211220000000001221110000000001223210021112211111200000000001222222222222
000011023100000001122211221222221000002100012100000011111211111212211111000000000000221231111111
000000021000000000223111331122211100002122111000000001111111111213222220000000000000213211111322
000000000000000000011112211232222000000002112000000001112111111223222200000000000001111111122222
000000000000000000001111111143222000000002000000000011111122011221111110000000022101111211001111
000000000000000000001111112132202000000000000000001211111122201111111120000000000201111112000211
000000000000000000000110223120000000000000000000002212122111200121120000000000000121233110000021
000000000000000000000000112120000000000000000000002111122111100021022200000000000221333112210000
000000000200000000020000212012000000000000000000001121121111000000021100000000022221331111000000
000000000000000000110000220001000000000000000000001111222211221000000000000000022212311121200000
000000000000000001112200010000000000000000000000000111221111111000000000000000011331111001100000
000000001000000000110000000000000000000000000001222221111111122000000000000000011211112001100000
000000020000000022211000000000000000000000000121113223111111122221000000000001011122212202000000
000000022111221022222000000000000000000000000011111221112111211220000000000001111113211112200000
000000002112211222220000000000000000000000001111111112111211211220000000000001111123211112200000
000000000210111231100000000000000000000000010211111111111113212322200000000000212111211232200000
000000001212212221000000000000000000020001212221111312111222211221100000000001111111211120000000
000000222210213101000000000000000000012111122211111211111222232222200000000002110111211100000000
000000022211132000000000000000000000011111111312212220111222222222200000000200000021111112120000
000002121110211100000000000000000000012111132222000011121202222220000000011222100010211312100000
000211111121101000000000000000000000022222232232200000001000222110000000111222100000011202100000
000021232120000000000000000000001020223222221222200000000000200000000202222232220000211200000000
000012221110000000000000100000002210021222212322100000000000000010000211222133210000002000000000
000002111120000000000001100000022110000222223222000000000000000010000001111234311000000000000000
000001122120011000000001210012222322220222222222000000000000201122000012121444421000000000000000
000001122000002000002111110002222132210200111100000000000002201122212111122442311000000000000000
000000000000002000001111112112222111111100221210000000000000211122002111122231210000000000000000
000000000000222000011111112112222111112100000010000000000000111220001211223221000000000000000000
000000000010002011112111211112232211112220000000000000000002221000000000022222000000000000000000
000000000000222111011111111111221111111110000000000000000102222120000000011100000000000000000000
000000000000121111231112111221111111111100000000000000000223222122020000111000000000000000000000
000000000000111111111211111021322221112110000000000000000022112222200002112000000000000000000000
000000000000112321111011122211222321110000000000000000020002111111100002110000000000000000000000
000000000001113211111121112020012222000000000000000000000000022222112120120210000000000000022000
000000000000211111111001110000002122000000000000000000000000012223222212210200000000000002112000
000000000002211211111110100000000000000000000000000000000000000213222010220000000000000022222200
000000000000211111111122000000000000000000000000020020000000000113310000200200000000000001011100
000000000000211111111100000000000000000000000000000000000000211123322000000220000000000000011220
000000000000001111111200000000000000000000000000000000000012211111220000001220000000000000001200
000000000000000201111200000000000000000000000000000000100022211111000000002322021000000000000210
000000000000002100100000000000000000000000100001100222121222212110000000012231111000000000012110
000000000000000200000000000000000000000121111021122221121122000000000001023221111100000000020000
000000000000000000001000000000000000000000111123333221111122000000000221013122111000000000022000
000000000000000000002122221000000000000002111133122222221332100010101221111111111200000020020000
000000000000000000001211122220000000000000232212001123111111000012211221113233112200001221120000
000000000000000000000011222210000220000000232200002221113211000022221201233111121110001021112000
000000000000000000000011332312000011200000011100001221122220001022211121222111111110012211110000
000000000000000000000001343212122111200000001120000022221100011222211121211111111000021232210000
000000000000000000000001232211122121100000000000000022220000011232211111111111110000022322022112
000000000000000000000021122211222221120000000000000002011000121111321111111111112100223210001120
000000000000000000000021122211222222111000000000000001000000002311112221111111111002222111002120
000000000000000000000221122233311222111000000000000000000000000211112222111111121121122110000010
000000001020000000000021122233111122211100000000000000000000002011112222211112111201121110000110
000010021210000000000221222233111112211000000000000000000000002001102012211113110121021110000120
000112122331000000000012211131122112212000000000000000000000021211111120111122200000012221012000
000022111122000000000002211121111112110000000000000000000000222211120100111220000000012202002000
000022321121000000000001111122112223220000000000000000000000222211210000200000000000000100000000
000022111100000000000002111120023221200000000000000000000021111121111002100000000000000000000000
000011111000000000000000212110122222000000000000000000000021212221110002000000000000000000000000
000002000000000000021000010000222210000000000002000000000022111231110000000000000000000000000000
000000000000000001111000020000022200000000000022100000000012111111110000000000000000000000000000
000000000000000012111212000000000100000000011132200000000021111111120000000000000000001000000000
000000000000000211111111000000000200000000112211110000000021111131220000000000000002002000011000
000000000000022113321111200000000000000000211111120000000000211132221200000000000122212222220000
000000000000000012222112000000000000010001111111100000000000111112320000000000100011112222211000
000000000000000000023112000000000000012022111122200000000020111112220000000002221011111111110000
000000000000000000012100000000000000012002111122200000000012222111110000000000002211211111111110
000000000000000000000000000000002002000001111122320000000012222311112000000000001111111111110020
000000000000000000000000000000022101100002220102100000000011222221112200000000001121121111111000
000000000000000000000000000000012221200000220000100000000011122222222000000000000011111111111100
002000000000000000000000000000022221100000000000100000000023113222232200000000000012122121111100
012220010000000000000000000000011221121112000000000000000022113212222200000000000002111111211000
012211222100000000000000000000211111121112000000000000000022331111332120000000000002211111110000
011111132200000000221001000000021121222111120000000000000012211113322000000000000002211113320000
111111112000000001231111112000000011223221120000000000000002211113212200000000000000111223222100
111111200000000001131112110000000022213222200000000000000000211202222200000000000000223232223220
112220000000000000111122222000000020211011100000000000000000000022220000000000000000022211132221
111121000000000001111132010000000020000001120000000000000000000021220000200000000000023111111211
111111000000000002122111000000000000001222100000000000000000000000000000100000000000021111122211
121120000000000121111120000000000000021122000000000000000000000000000000000000000000000222322211
211112000000000223212222000100012200011220000000000000000000000000000000000000000000001321132211
111120000000000232232200001321233322233311100000000000000000000000000000000000000000012211112111
112310000000012022232210000222223333221111200000000000000000000000000000000000000000000213111112
112112100022101111122010000112222334222121210000000000000000000000000000000000000000000222121012
    """.replace(" ", "").split("\n")
    test_overmap_tiles = [list(line) for line in test_overmap_tiles]
    render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, themes.default.black)
    render.Overmap(0.5, 0.5, test_overmap_tiles)

if __name__ == "__main__":
    client.connect() # connect to server
    # aspectcharacter() # choose scene to test
    # chooseinterests()
    # choosegrists()
    # choosevial()
    # choosemodus()
    # render.TileMap(0.5, 0.5, map)
    # computer()
    # title() # normal game start
    test_overmap()
    # continue to render until render.render() returns False
    # imp = render.Enemy(0.5, 0.5, "shale", "imp") 
    # render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, themes.default.black)
    # render.Overmap(0.5, 0.5, test_map)
    while render.render():
        ...

