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
    test_overmap_tiles = """000000000000000000110000011111122411000000000000000001022320000001222222311111100000000000000000
000000000000000000110000021221222312000000000000000011122200000001222222222222200000000000000000
000000000000000001110000011122222200000000000000000111121120000000222222222222200000000000000000
000000000000000002120112111112222101000000000000021111121100000000011111111112000000000000000000
000000000000000002220211111111111111200000000000121111221112101000001111121112200000000000000000
000000000000000000202111112111111112220000000000222111111121100000002111111110000000000000000000
000000000000000000000122222221111211320000000000011111111111120000000111112100000000000000000000
000000000000000000000222222222111211100000000000131111112211120000000002112100000000000000000000
000010000000000000002222222111121212200000000010222332222211110000000000002200000000001112120010
000010000000000000000011021111121111000000000000022222222221120000000000000000000000221111120000
000000000000000000000002000120211110000000000000111112211112100000000000000000000002222121110000
000000000000000000000000011100211100000000000000011122211112210000000000000000011221111111211000
000000000000000000000000000000211121000000000000011122211322220000000000000000001211111111010000
000000000000000000000000000121121102000000000000022222211322000000000000000000000111111111200000
000000000000000000000000000022111122000000000000012222211111000000000000000000000011111011100000
000000000000000000000000000232111122210000000000010001211210000000000000000000002111200011200000
000000000000000100000000021132221112220000000000000000002000000000000000000221122002100001110000
000000000000000112022000022132221112122000000000000000000000000000000000000111111111200002000000
000000000000000222222222011122111111122000000000000000000000000000000000100111211111200001000000
000000000000021222222221011111112122122000000000000000000000000000000002121111111110000000000000
000000000000002222223222111111111122222120000000000000000000000000000000111111111120000000000000
000000000001111122222222111111212122222010000000000000000000000000000002111111111111100000000000
000000000002111222222222111111111122211000000000000000000000000000000211111111211222000000000000
000000000000111112222332111111121111012000000000000000000000000000001311111111111222200000000000
000000000000111112222333112111111211010000000000000000000000000000000111111111111222000000000000
000000000000211111221112232221112222010000000000000000000000000000000002222211111111000000000000
000000000000111111211122222222211221110000000000000000020000000000000022222221111111000000000000
000000000002111111113222222222211222200000000000000000001000000210000002222221111111000000000000
000000000000111111122222222222000220000000000000110111101000000200000022222211111120000000000000
000000000000222311112222232121000000000000000000112211101000000000000111122222222100000000000000
000000000001111311111221010000000000000000000001112211111000000000000011121122220000000000000000
000000000000001211111122000000000000000000000002112211111200000000002112222122211000000000000000
000000000000000202111111000000000000000000001211112211132000000000000020202100200000000000000000
000000000000000000021210000000000000000000000021211211123100000000000000001200000000000000000000
000000000000000000000000000000000000000000010011111122111100000000000000000000000000000000000000
000000000000000000000000000000000000000000010002111111112110200000000000000000000000000000000000
000000000000000000000000000000000000000000000001111111132222200000000000000000000000000000000000
000000000000000000000000000000000000000000000000111211112201110000000000000000000000000000000000
000000000000000000000000000000000000000000000200221231111111110000000000000000000000010000000000
000000000000000000000000000000000010000000000100221222111122200000000000000000000211210000000000
000000000000000000000000000000000011000000000111122222222222210000000000000000000011220000000000
000000000000000000000000000000000022000000222112122122222222200000000000000000000012220000001210
000000000000000000100000000000000120001000011110122022222111100000000000000000210222211120000000
000000000000000000000000000000000000002000000000001022222222202000000000000001222222111122000000
000000000000000000000000000000000000022222000000000001113222220000000000000000222222111112120000
000000000000000000000000000000000111222211120000000012311111110000000000000000113223121112111000
000000000000000000000000010000000211222211221020000002111111020000000000000000111111111112210000
000000000000000000000000000000000011112222220000001211111112000000000000000000011111111112220000
000000000000000000000000000200000211111323310000002311111212100000000002100001111121121122221022
000000000000000000000000000212002211111122220000000211111212000000000000000002211111211122222221
120121000000000000000000000011111111111122222020000111111110000000000000000000011011111112222222
112220000000000000000000000111111111111111111020010211220000000000000000000000002000211112221111
111111200000000000000000000111111111111111111220001111000000000000000000000000122000111123232222
111111000000000000000000001111221111111111111100000000000000000000000000000000001011111112211112
311113200010000000000000002111222111111111121000000000000000000000000000000000001111112111111123
111222201120000000000000012221111111111112200000000000000000000000000000000000001011111111111111
112222211100000000000000002211111111211111102000000000000000000000000000000000100111211221211112
222222312100000200000000001311111111111120000000000000000000000000000000000000112111111111111212
232222221100000000000000002221111111121110000000000000000000000000000000200112111111111111111212
222222331100000000000000001111111111111111000000000022200000000000000000000112111111111111111112
222222333200000000000000021111111111110210000000000010000000000000122000022112220111111111112112
113320121112200000000000211111211111100000000000000000000000020000122200012112200011111111111111
113122111222220000000000011111111122200000000000000000000011221212222200112112000022221111211111
111122111222210020000002211111111120000000000000000000000011111111132320222120000022211233111122
120132111222212220000011222111222120000000000021000000002111111111133111222110001233211132112222
001222111111111110000000222111222112200000000222220110000111111111332111012220022222211111112222
222111112211122110000000122111111111200000002111111100000111111111332210022312222222211111133121
022111112211322200000000222111111111200000012111111100000111122111111112000211111111111131112220
000111111222222221000000111121211100000002211111112200000022222333111111120011111221111122111110
001111111122222222200000222111221200002212222111121220002111111333112222000221111223121122211100
002121111122223220200001122211211321110222222311102221001111111111122220000022102001000222210200
000111111322211110122001020111001321122122222311200122111111111111122222000000000000000000000200
000012111322221111111122210011101111122222222210000222311111111112122111000000000012100000000000
000000111322221111111122000002121111122223322200012210221111111111111111000000000112200000000000
000000211222111121111111110022221111222212221222112210111111111111111111000000022112220000000000
000000002210111111111111112002321111222222211311112111111111111112111111221001222112221000000000
000000000200111111111111211212231111112222222111111111111211111111112221222001221111312200000000
000000000122112111111111120021011111112222222111111110211211111122111211223101011111112200000000
000000002322111111111111110122111111112222220111110120112211111122111211222311221111222000000000
000000012222111121113222200001211111232222212022000000022211111222111122222222222112222110100000
000000002222111111112222200002211111221222000000000000000211102222111113210022222111111212100000
000000021111111111211122220000000011211211000000000000000011201222111122212011222211111111100000
000000111111122111111322010000000021011210000000000000000002000023111122201000222111111111102120
000002111111112111111122000000000011102000000000000000000000000022120121000001111111111111121121
000001111111112111111100001221201220100000000000000000000000000022112100000001111111111112222211
000000111111132112222100002222111220220000000000000021000000000001000000000000011112112133222111
000000111111122232220000002022111122220000000000120012002000000000000000000000001011111133222221
000000021221223222200000022122111111110000000212111111222220000000000000000010000021111122221122
000000000021222322000000022111111122200000001232111111221222200000000000000000000011111111222221
000000000010222222000010111111111222220000011222121111221222100000000002200022000021111111122222
000000000000022200000012111211111311110000002222221111111111110000000011100020000000111311132322
000000000000000000000022111111121221100000000222221111121110220000002111120010000002222331111332
000000000000000000000101111221111112200000001222111111111111200000021111122100000022222311111232
000000000000000000000001221111111222221000011111111121144111100022101111122201200002222111111122
000000000000000000000001221111221232220000011113111111233211200011111111111111220001021111111122
000000000000000000000000221111221111100000011212112211133110000021111111111111120000000011212121
    """.replace(" ", "").split("\n")
    test_overmap_tiles = [list(line) for line in test_overmap_tiles if line]
    theme = themes.void
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
    # title() # normal game start
    test_overmap()
    # continue to render until render.render() returns False
    # imp = render.Enemy(0.5, 0.5, "shale", "imp") 
    # render.SolidColor(0, 0, render.SCREEN_WIDTH, render.SCREEN_HEIGHT, themes.default.black)
    # render.Overmap(0.5, 0.5, test_map)
    while render.render():
        ...

