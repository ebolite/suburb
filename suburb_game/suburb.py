import pygame
import sys
import pathlib
import hashlib
import socket
import time
import os

import util
import render
import client
import config

def placeholder():
    pass

def play():
    render.clear_elements()
    text = render.Text(0.5, 0.3, f"Login to an existing character or register a new character?")
    loginbutton = render.Button(.5, .4, "sprites\\buttons\\login.png", "sprites\\buttons\\loginpressed.png", login)
    registerbutton = render.Button(.5, .52, "sprites\\buttons\\register.png", "sprites\\buttons\\registerpressed.png", register)
    back = render.Button(.5, .64, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

def register():
    render.clear_elements()
    log = render.Text(0.5, 0.10, "")
    name = render.Text(0.5, 0.20, f"Username (Case-sensitive)")
    name.color = render.light_color
    name.outline_color = render.black_color
    namebox = render.InputTextBox(.5, .25)
    pw = render.Text(0.5, .35, f"Password")
    pw.color = render.light_color
    pw.outline_color = render.black_color
    pwbox = render.InputTextBox(.5, .40)
    pwbox.secure = True
    confirm = render.Text(0.5, .50, f"Confirm Password")
    confirm.color = render.light_color
    confirm.outline_color = render.black_color
    confirmbox = render.InputTextBox(.5, .55)
    confirmbox.secure = True
    def verify():
        print("verify")
        if pwbox.text == confirmbox.text:
            if len(namebox.text) != 0:
                if len(pwbox.text) != 0:
                    if len(namebox.text) < 32:
                        if len(pwbox.text) < 32:
                            print("final step")
                            client.dic["character"] = namebox.text
                            client.dic["character_pass_hash"] = client.hash(pwbox.text)
                            log.text = client.request("create_character")
                            if "Success" not in log.text:
                                client.dic["character"] = None
                                client.dic["character_pass_hash"] = None
                            print(f"log text {log.text}")
                        else:
                            log.text = f"Your password must be less than 32 characters. Yours: {len(pwbox.text)}"
                    else:
                        log.text = f"Username must be less than 32 characters. Yours: {len(namebox.text)}"
                else:
                    log.text = "Password field must not be empty."
            else:
                log.text = "Username must not be empty."
        else:
            log.text = "Passwords do not match."
    confirm = render.Button(.5, .67, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .80, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", play)

def login():
    render.clear_elements()
    log = render.Text(0.5, 0.20, "")
    name = render.Text(0.5, 0.30, f"Character Name (Case-sensitive)")
    name.color = render.light_color
    name.outline_color = render.black_color
    namebox = render.InputTextBox(.5, .35)
    pw = render.Text(0.5, .45, f"Password")
    pw.color = render.light_color
    pw.outline_color = render.black_color
    pwbox = render.InputTextBox(.5, .50)
    pwbox.secure = True
    def verify():
        if len(namebox.text) != 0:
            if len(pwbox.text) != 0:
                log.text = "Connecting..."
                client.dic["character"] = namebox.text
                client.dic["character_pass_hash"] = client.hash(pwbox.text)
                log.text = client.request("login")
                if "Success" not in log.text:
                    client.dic["character"] = None
                    client.dic["character_pass_hash"] = None
                else:
                    namecharacter() # todo: change to play game function
                print(f"log text {log.text}")
            else:
                log.text = "Password must not be empty."
        else:
            log.text = "Session name must not be empty."
    confirm = render.Button(.5, .62, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .75, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", play)

character_info = {
"name": None,
"noun": None,
"pronouns": ["they", "them", "their", "theirs"],
"interests": [],
"aspect": None,
"class": None,
"secondaryvial": None,
"gristcategory": None
}

def namecharacter():
    render.clear_elements()
    log = render.Text(0.5, 0.20, "")
    l1text = render.Text(0.5, 0.3, "A young being of indeterminate nature exists in some kind of area.")
    l1text.color = render.light_color
    l1text.outline_color = render.black_color
    l2text = render.Text(0.5, 0.4, "What will this being's name be?")
    l2text.color = render.light_color
    l2text.outline_color = render.black_color
    namebox = render.InputTextBox(.5, .48)
    def verify():
        if len(namebox.text) > 0 and len(namebox.text) < 32:
            character_info["name"] = namebox.text
            nouncharacter()
        else:
            log.text = "Name is too long or too short."
    confirm = render.Button(.50, .57, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)

def nouncharacter():
    render.clear_elements()
    log = render.Text(0.5, 0.20, "")
    log2 = render.Text(0.5, 0.30, "")
    l1text = render.Text(0.5, 0.4, f"You don't think \"being\" is a very accurate descriptor.")
    l1text.color = render.light_color
    l1text.outline_color = render.black_color
    l2text = render.Text(0.5, 0.5, f"What word best describes {character_info['name']}?")
    l2text.color = render.light_color
    l2text.outline_color = render.black_color
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

def pronounscharacter():
    render.clear_elements()
    log = render.Text(0.5, 0.20, "")
    log2 = render.Text(0.5, 0.30, "")
    log3 = render.Text(0.5, 0.40, "")
    l1text = render.Text(0.5, 0.5, f"What pronouns should this {character_info['noun']} go by?")
    l1text.color = render.light_color
    l1text.outline_color = render.black_color
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
        text.color = render.light_color
        text.outline_color = render.black_color
        blurb = render.Image(0.5, 0.39, f"sprites\\aspects\\{aspect}blurb.png")
        confirm = render.Button(0.5, 0.54, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", on_confirm)
        backbutton = render.Button(0.5, 0.66, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", aspectcharacter)
    return button

def aspectcharacter():
    render.clear_elements()
    space = render.Button(0,0, "sprites\\aspects\\space120.png", "sprites\\aspects\\space120.png", make_asbutton("space"), hover="sprites\\aspects\\space120hover.png")
    space.absolute = True
    spaceblurb = render.Image(120, 0, "sprites\\aspects\\spaceblurb.png")
    spaceblurb.absolute = True
    time = render.Button(640, 0, "sprites\\aspects\\time120.png", "sprites\\aspects\\time120.png", make_asbutton("time"), hover="sprites\\aspects\\time120hover.png")
    time.absolute = True
    timeblurb = render.Image(760, 0, "sprites\\aspects\\timeblurb.png")
    timeblurb.absolute= True
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
    doomblurb = render.Image(760, 480, "sprites\\aspects\\doomblurb.png")
    doomblurb.absolute = True
    light = render.Button(0, 600, "sprites\\aspects\\light120.png", "sprites\\aspects\\light120.png", make_asbutton("light"), hover="sprites\\aspects\\light120hover.png")
    light.absolute = True
    lightblurb = render.Image(120, 600, "sprites\\aspects\\lightblurb.png")
    lightblurb.absolute = True
    void = render.Button(640, 600, "sprites\\aspects\\void120.png", "sprites\\aspects\\void120.png", make_asbutton("void"), hover="sprites\\aspects\\void120hover.png")
    void.absolute = True
    voidblurb = render.Image(760, 600, "sprites\\aspects\\voidblurb.png")
    voidblurb.absolute = True

def make_classbutton(c):
    def button():
        def on_confirm():
            character_info["class"] = f"{c}"
            chooseinterests()
        render.clear_elements()
        text = render.Text(0.5, 0.3, f"Are you sure you want to be the {c.upper()} of {character_info['aspect'].upper()}?")
        text.color = render.light_color
        text.outline_color = render.black_color
        confirm = render.Button(0.5, 0.40, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", on_confirm)
        backbutton = render.Button(0.5, 0.52, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", chooseclass)
    return button

def chooseclass():
    render.clear_elements()
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

def chooseinterests():
    render.clear_elements()
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

def choosegrists():
    render.clear_elements()
    # 19 grist categories
    # todo: add indicators for which grist types the session already has
    logtext = render.Text(.5, .05, "Select the type of land you would like.")
    infotext = render.Text(.75, .9, "A yellow background indicates exotic grist.")
    infotext.fontsize = 20
    infotext = render.Text(.75, .93, "Exotic grist types cannot normally be obtained")
    infotext.fontsize = 20
    infotext = render.Text(.75, .96, "unless a player has specifically picked them.")
    infotext.fontsize = 20
    def choosegristtype(grist):
        def out():
            logtext.fontsize = 20
            t = f"Are you sure you want {grist.upper()}? Press the button again to confirm."
            if logtext.text == t:
                character_info["gristcategory"] = grist
                logtext.text = client.requestplus("setup_character",  character_info)
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
            if "exotic" in config.grists[grist] and config.grists[grist]["exotic"]:
                img.highlight_color = (255,255,0)
    backbutton = render.Button(0.1, 0.07, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", choosevial)

def choosevial():
    def vialbutton(vial):
        def out():
            character_info["secondaryvial"] = vial
            choosegrists()
        return out
    render.clear_elements()
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

def newsessionprompt():
    render.clear_elements()
    text = render.Text(0.5, 0.3, f"Create a new session?")
    text.color = render.light_color
    text.outline_color = render.black_color
    text2 = render.Text(0.5, 0.35, f"The first character to join will become the admin of the session.")
    text2.color = render.light_color
    text2.outline_color = render.black_color
    new = render.Button(.5, .48, "sprites\\buttons\\newsession.png", "sprites\\buttons\\newsessionpressed.png", newsession)
    back = render.Button(.5, .60, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

def newsession():
    render.clear_elements()
    log = render.Text(0.5, 0.10, "")
    name = render.Text(0.5, 0.20, f"Session Name")
    name.color = render.light_color
    name.outline_color = render.black_color
    namebox = render.InputTextBox(.5, .25)
    pw = render.Text(0.5, .35, f"Session Password")
    pw.color = render.light_color
    pw.outline_color = render.black_color
    pwbox = render.InputTextBox(.5, .40)
    pwbox.secure = True
    confirm = render.Text(0.5, .50, f"Confirm Password")
    confirm.color = render.light_color
    confirm.outline_color = render.black_color
    confirmbox = render.InputTextBox(.5, .55)
    confirmbox.secure = True
    def verify():
        print("verify")
        if pwbox.text == confirmbox.text:
            if len(namebox.text) != 0:
                if len(pwbox.text) != 0:
                    if len(namebox.text) < 32:
                        if len(pwbox.text) < 32:
                            print("final step")
                            client.dic["session"] = namebox.text
                            client.dic["session_pass_hash"] = client.hash(pwbox.text)
                            log.text = client.request("create_session")
                            if "Success" not in log.text:
                                client.dic["session"] = None
                                client.dic["session_pass_hash"] = None
                            print(f"log text {log.text}")
                        else:
                            log.text = f"Your password must be less than 32 characters. Yours: {len(pwbox.text)}"
                    else:
                        log.text = f"Session name must be less than 32 characters. Yours: {len(namebox.text)}"
                else:
                    log.text = "Password field must not be empty."
            else:
                log.text = "Session name must not be empty."
        else:
            log.text = "Passwords do not match."
    confirm = render.Button(.5, .67, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .80, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

def connect():
    render.clear_elements()
    log = render.Text(0.5, 0.20, "")
    name = render.Text(0.5, 0.30, f"Session Name")
    name.color = render.light_color
    name.outline_color = render.black_color
    namebox = render.InputTextBox(.5, .35)
    pw = render.Text(0.5, .45, f"Session Password")
    pw.color = render.light_color
    pw.outline_color = render.black_color
    pwbox = render.InputTextBox(.5, .50)
    pwbox.secure = True
    def verify():
        if len(namebox.text) != 0:
            if len(pwbox.text) != 0:
                log.text = "Connecting..."
                client.dic["session"] = namebox.text
                client.dic["session_pass_hash"] = client.hash(pwbox.text)
                log.text = client.request("connect")
                if "Success" not in log.text:
                    client.dic["session"] = None
                    client.dic["session_pass_hash"] = None
                print(f"log text {log.text}")
            else:
                log.text = "Password must not be empty."
        else:
            log.text = "Session name must not be empty."
    confirm = render.Button(.5, .62, "sprites\\buttons\\confirm.png", "sprites\\buttons\\confirmpressed.png", verify)
    back = render.Button(.5, .75, "sprites\\buttons\\back.png", "sprites\\buttons\\backpressed.png", title)

def title():
    render.clear_elements()
    logo = render.Image(.5, .20, "sprites\\largeicon.png")
    logotext = render.Image(.5, .47, "sprites\\suburb.png")
    def isconnected():
        if client.dic["session"] != None:
            return False # return False because the alternative condition is unclickable
        else:
            return True
    play_button = render.Button(.5, .59, "sprites\\buttons\\play.png", "sprites\\buttons\\playpressed.png", play, alt=isconnected, altpath="sprites\\buttons\\playgrey.png", altclick = None)
    play_button.alt_alpha = 100
    connect_button = render.Button(.5, .70, "sprites\\buttons\\connect.png", "sprites\\buttons\\connectpressed.png", connect)
    new_session_button = render.Button(.5, .81, "sprites\\buttons\\newsession.png", "sprites\\buttons\\newsessionpressed.png", newsessionprompt)
    options_button = render.Button(.5, .92, "sprites\\buttons\\options.png", "sprites\\buttons\\optionspressed.png", newsessionprompt)
    versiontext = render.Text(0, 0, f"SUBURB Version {util.VERSION}")
    versiontext.absolute = True
    versiontext.color = render.light_color
    versiontext.outline_color = render.black_color
    if client.dic["session"] != None:
        conntextcontent = f"Session `{client.dic['session']}`"
    else:
        conntextcontent = f"No session."
    conntext = render.Text(0, 30, conntextcontent)
    conntext.absolute = True

if __name__ == "__main__":
    client.connect() # connect to server
    # aspectcharacter() # choose scene to test
    # chooseinterests()
    # choosegrists()
    # choosevial()
    #render.TileMap(0.5, 0.5, map)
    title() # normal game start



map = [
[".",".",".",".",".",".",".",".",".",],
[".",".",".","/","|","\\",".",".",".",],
[".",".",".","|","A","|",".",".",".",],
[".",".",".","|","^","|",".",".",".",],
[".",".","/","|","F","|","\\",".",".",],
[".","/","|","|","v","|","|","\\",".",],
[".","[","B",".","e","O","b","]",".",],
[".","|","^","|","v","|","|","|",".",],
[".","<","F","W","e","D","G",">",".",],
["#","|","^","|","|","|","|","|","#",],
["#","#","-","C","C","C","C","#","#",],
["#","#","#","#","#","#","#","#","#",],
["#","#","#","#","#","#","#","#","#",]
]

# continue to render until render.render() returns False
while render.render():
    pass
