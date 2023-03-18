import util
import os
import random
from pygame import Color
from typing import Union, Optional

sample_parts = {
    "base": "kid",
    "hair": "egbert",
    "mouth": "egbert",
    "eyes": "egbert",
    "shirt": "egbert",
    "pants": "egbert",
    "shoes": "egbert",
}

tiles = {
    "?": "sprites\\tiles\\oob.png",
    "|": "sprites\\tiles\\wall.png",
    "#": "sprites\\tiles\\#.png",
    ".": "sprites\\tiles\\..png",
    "=": "sprites\\tiles\\floor.png",
    "+": "sprites\\tiles\\girder.png",
    "}": "sprites\\tiles\\rightwall.png",
    "{": "sprites\\tiles\\leftwall.png",
    "]": "sprites\\tiles\\rightwindow.png",
    "[": "sprites\\tiles\\leftwindow.png",
    ">": "sprites\\tiles\\rightdoor.png",
    "<": "sprites\\tiles\\leftdoor.png",
    "/": "sprites\\tiles\\rampright.png",
    "\\": "sprites\\tiles\\rampleft.png",
    "^": "sprites\\tiles\\stairs.png",
    "v": "sprites\\tiles\\elevatorshaft.png",
    "e": "sprites\\tiles\\elevator.png",
    "b": "sprites\\tiles\\bathroom.png",
    "B": "sprites\\tiles\\bedroom.png",
    "S": "sprites\\tiles\\studioapt.png",
    "s": "sprites\\tiles\\security.png",
    "F": "sprites\\tiles\\foyer.png",
    "C": "sprites\\tiles\\cellar.png",
    "D": "sprites\\tiles\\diningroom.png",
    "K": "sprites\\tiles\\kitchen.png",
    "O": "sprites\\tiles\\office.png",
    "L": "sprites\\tiles\\livingroom.png",
    "l": "sprites\\tiles\\laundryroom.png",
    "A": "sprites\\tiles\\attic.png",
    "I": "sprites\\tiles\\pillar.png",
    "G": "sprites\\tiles\\garage.png",
    "g": "sprites\\tiles\\gameroom.png",
    "W": "sprites\\tiles\\workout.png",
    "-": "sprites\\tiles\\stairwell.png",
    "0": "sprites\\tiles\\returngate.png",
    "1": "sprites\\tiles\\gate1.png",
    "2": "sprites\\tiles\\gate2.png",
    "3": "sprites\\tiles\\gate3.png",
    "4": "sprites\\tiles\\gate4.png",
    "5": "sprites\\tiles\\gate5.png",
    "6": "sprites\\tiles\\gate6.png",
    "7": "sprites\\tiles\\gate7.png",
    "'": "sprites\\tiles\\stalactite.png",
    "$": "sprites\\tiles\\stash.png",
    "n": "sprites\\tiles\\nest.png",
    "_": "sprites\\tiles\\_.png",
    "i": "sprites\\tiles\\rope.png",
    }

icons = {
    "no_icon": "sprites/icons/no_icon.png",
    "player": "sprites/icons/player_alt.png",
    "alchemiter": "sprites/icons/alchemiter.png",
    "cruxtruder": "sprites/icons/cruxtruder.png",
    "sealed cruxtruder": "sprites/icons/sealed cruxtruder.png",
    "punch designix": "sprites/icons/punch designix.png",
    "totem lathe": "sprites/icons/totem lathe.png",
    "Sburb disc": "sprites/icons/Sburb disc.png",
    "center": "sprites/icons/center.png",
    "deploy": "sprites/icons/deploy.png",
    "select": "sprites/icons/select.png",
    "imp": "sprites/icons/imp.png",
    "ogre": "sprites/icons/ogre.png",
    "lich": "sprites/icons/lich.png",
}

header_icons = {
    "grist_cache": "sprites/computer/Sburb/grist_cache.png",
    "atheneum": "sprites/computer/Sburb/atheneum.png",
    "phernalia_registry": "sprites/computer/Sburb/phernalia_registry.png",
    "alchemize": "sprites/computer/Sburb/alchemize.png",
    "revise": "sprites/computer/Sburb/revise.png"
}

grists = {
    "build": {"tier": 0, "image": "sprites\\grists\\build.png"},
    "acid": {"tier": 4, "exotic": True, "image": "sprites\\grists\\acid.png"},
    "amber": {"tier": 3, "image": "sprites\\grists\\amber.png"},
    "amethyst": {"tier": 3, "image": "sprites\\grists\\amethyst.png"},
    "aquamarine": {"tier": 1, "image": "sprites\\grists\\aquamarine.png"},
    "blood": {"tier": 3, "image": "sprites\\grists\\blood.png"},
    "caulk": {"tier": 5, "image": "sprites\\grists\\caulk.png"},
    "chalk": {"tier": 1, "image": "sprites\\grists\\chalk.png"},
    "cobalt": {"tier": 4, "image": "sprites\\grists\\cobalt.png"},
    "copper": {"tier": 2, "image": "sprites\\grists\\copper.png"},
    "diamond": {"tier": 9, "image": "sprites\\grists\\diamond.png"},
    "emerald": {"tier": 8, "image": "sprites\\grists\\emerald.png"},
    "fluorite": {"tier": 5, "exotic": True, "image": "sprites\\grists\\fluorite.png"},
    "frosting": {"tier": 1, "image": "sprites\\grists\\frosting.png"},
    "garnet": {"tier": 3, "image": "sprites\\grists\\garnet.png"},
    "gold": {"tier": 6, "image": "sprites\\grists\\gold.png"},
    "iodine": {"tier": 1, "image": "sprites\\grists\\iodine.png"},
    "iron": {"tier": 5, "image": "sprites\\grists\\iron.png"},
    "jet": {"tier": 2, "image": "sprites\\grists\\jet.png"},
    "lead": {"tier": 2, "image": "sprites\\grists\\lead.png"},
    "lux": {"tier": 9, "image": "sprites\\grists\\lux.png"},
    "malachite": {"tier": 2, "exotic": True, "image": "sprites\\grists\\malachite.png"},
    "marble": {"tier": 3, "image": "sprites\\grists\\marble.png", "exotic": True},
    "mercury": {"tier": 4, "image": "sprites\\grists\\mercury.png"},
    "mist": {"tier": 3, "exotic": True, "image": "sprites\\grists\\mist.png"},
    "moonstone": {"tier": 6, "exotic": True, "image": "sprites\\grists\\moonstone.png"},
    "neon": {"tier": 4, "exotic": True, "image": "sprites\\grists\\neon.png"},
    "nitrogen": {"tier": 3, "image": "sprites\\grists\\nitrogen.png"},
    "obsidian": {"tier": 7, "image": "sprites\\grists\\obsidian.png"},
    "onyx": {"tier": 9, "image": "sprites\\grists\\onyx.png"},
    "permafrost": {"tier": 8, "image": "sprites\\grists\\permafrost.png"},
    "quartz": {"tier": 7, "image": "sprites\\grists\\quartz.png"},
    "rainbow": {"tier": 10, "image": "sprites\\grists\\rainbow.png"},
    "redstone": {"tier": 7, "image": "sprites\\grists\\redstone.png"},
    "rock candy": {"tier": 2, "image": "sprites\\grists\\rock candy.png"},
    "rose quartz": {"tier": 5, "exotic": True, "image": "sprites\\grists\\rose quartz.png"},
    "ruby": {"tier": 6, "image": "sprites\\grists\\ruby.png"},
    "rust": {"tier": 1, "image": "sprites\\grists\\rust.png"},
    "sandstone": {"tier": 2, "image": "sprites\\grists\\sandstone.png"},
    "shale": {"tier": 1, "image": "sprites\\grists\\shale.png"},
    "silicon": {"tier": 4, "image": "sprites\\grists\\silicon.png"},
    "silk": {"tier": 6, "exotic": True, "image": "sprites\\grists\\silk.png"},
    "slime": {"tier": 2, "exotic": True, "image": "sprites\\grists\\slime.png"},
    "star sapphire": {"tier": 8, "exotic": True, "image": "sprites\\grists\\star sapphire.png"},
    "sulfur": {"tier": 5, "exotic": True, "image": "sprites\\grists\\sulfur.png"},
    "sunstone": {"tier": 7, "exotic": True, "image": "sprites\\grists\\sunstone.png"},
    "tar": {"tier": 4, "image": "sprites\\grists\\tar.png"},
    "titanium": {"tier": 9, "image": "sprites\\grists\\titanium.png"},
    "topaz": {"tier": 5, "exotic": True, "image": "sprites\\grists\\topaz.png"},
    "uranium": {"tier": 8, "image": "sprites\\grists\\uranium.png"},
    "wood": {"tier": 1, "image": "sprites\\grists\\wood.png"},
    "zilium": {"tier": 10, "exotic": True, "image": "sprites\\grists\\zilium.png"},
}

gristcolors = {
    "build": Color(0, 175, 255),
    "acid": Color(139, 255, 106),
    "amber": Color(238, 214, 0),
    "amethyst": Color(139, 0, 172),
    "aquamarine": Color(115, 246, 230),
    "blood": Color(255, 0, 0),
    "caulk": Color(128, 128, 128),
    "chalk": Color(255, 255, 255),
    "cobalt": Color(8, 85, 222),
    "copper": Color(222, 76, 0),
    "diamond": Color(222, 230, 255),
    "emerald": Color(106, 242, 148),
    "fluorite": Color(33, 177, 254),
    "frosting": Color(255, 141, 255),
    "garnet": Color(180, 0, 0),
    "gold": Color(255, 226, 0),
    "iodine": Color(180, 85, 0),
    "iron": Color(167, 167, 167),
    "jet": Color(74, 72, 74),
    "lead": Color(70, 99, 127),
    "lux": Color(255, 238, 156),
    "malachite": Color(1, 84, 33),
    "marble": [Color(246, 242, 246), Color(238, 97, 230)],
    "mercury": Color(165, 165, 165),
    "mist": [Color(213, 238, 238), Color(255, 255, 255)],
    "moonstone": Color(148, 214, 230),
    "neon": Color(255, 165, 0),
    "nitrogen": Color(139, 246, 255),
    "obsidian": Color(1, 1, 1),
    "onyx": Color(52, 52, 52),
    "permafrost": Color(74, 246, 238),
    "quartz": Color(180, 255, 238),
    "rainbow": [Color(255, 60, 156), Color(115, 250, 156), Color(32, 165, 222), Color(8, 60, 255)],
    "redstone": Color(255, 64, 0),
    "rock candy": Color(230, 85, 255),
    "rose quartz": Color(246, 12, 74),
    "ruby": Color(255, 44, 24),
    "rust": Color(126, 47, 30),
    "sandstone": Color(156, 133, 41),
    "shale": Color(106, 32, 156),
    "silicon": Color(148, 174, 205),
    "silk": Color(238, 218, 255),
    "slime": Color(0, 226, 32),
    "star sapphire": Color(41, 52, 255),
    "sulfur": Color(227, 184, 0),
    "sunstone": Color(230, 125, 57),
    "tar": Color(5, 5, 5),
    "titanium": Color(215, 215, 215),
    "topaz": Color(255, 182, 32),
    "uranium": Color(32, 206, 57),
    "wood": Color(115, 80, 57),
    "zilium": [Color(41, 255, 74), Color(230, 76, 213), Color(0, 113, 189)]
}

gristcategories = {
    "amber": ["amber", "rust", "sulfur", "iron", "topaz", "garnet", "gold", "sunstone", "ruby"],
    "barren": ["rust", "sandstone", "mist", "chalk", "caulk", "sulfur", "sunstone", "permafrost", "onyx"],
    "beach": ["aquamarine", "sandstone", "shale", "cobalt", "gold", "sunstone", "quartz", "emerald", "star sapphire"],
    "block": ["rust", "chalk", "malachite", "fluorite", "obsidian", "iron", "permafrost", "redstone", "gold"],
    "calcite": ["chalk", "iodine", "marble", "amethyst", "garnet", "caulk", "obsidian", "gold", "lux"],
    "cold": ["aquamarine", "frosting", "chalk", "mist", "nitrogen", "cobalt", "quartz", "permafrost", "diamond"],
    "dark": ["jet", "tar", "blood", "garnet", "lead", "cobalt", "obsidian", "star sapphire", "onyx"],
    "elemental": ["iodine", "copper", "cobalt", "nitrogen", "lead", "mercury", "sulfur", "iron", "titanium"],
    "hot": ["amber", "rust", "garnet", "tar", "sulfur", "ruby", "sunstone", "gold", "redstone"],
    "liquid": ["iodine", "frosting", "blood", "nitrogen", "acid", "amber", "tar", "mercury", "caulk"],
    "metal": ["rust", "copper", "lead", "silicon", "mercury", "sulfur", "iron", "gold", "titanium"],
    "nature": ["shale", "wood", "sandstone", "amber", "topaz", "quartz", "obsidian", "gold", "emerald"],
    "oil": ["shale", "tar", "jet", "mercury", "cobalt", "fluorite", "moonstone", "quartz", "redstone"],
    "radiant": ["chalk", "frosting", "marble", "neon", "rose quartz", "gold", "moonstone", "quartz", "sunstone"],
    "science": ["copper", "slime", "acid", "nitrogen", "silicon", "neon", "lead", "uranium", "titanium"],
    "stone": ["malachite", "shale", "sandstone", "obsidian", "sunstone", "moonstone", "redstone", "uranium", "titanium"],
    "sweet": ["frosting", "rock candy", "amethyst", "marble", "rose quartz", "silk", "permafrost", "moonstone", "lux"],
    "uranium": ["malachite", "copper", "lead", "neon", "silicon", "sunstone", "uranium", "emerald", "star sapphire"],
    "wealth": ["aquamarine", "amethyst", "topaz", "ruby", "gold", "silk", "emerald", "star sapphire", "diamond"]
    }

default_vial = {
    "gel_vial": False,
    "segmented_vial": False,
    "middle_color": None,
    "hidden": True,
}

vials: dict[str, dict] = {
    "hp": { 
        "name": "HEALTH VIAL",
        "hidden": False,
        "gel_vial": True,
        "fill_color": Color(191, 75, 153), 
        "shade_color": Color(159, 54, 145),
        },
    "vim": {
        "name": "VIM GAUGE",
        "hidden": False,
        "fill_color": Color(54, 159, 54),
        "shade_color": Color(17, 119, 17),
    },
    "aspect": {
        "name": "ASPECT METER",
        "hidden": False,
        "fill_color": Color(54, 54, 159),
        "shade_color": Color(41, 41, 130),
    },
    "blood": {
        "name": "BLOOD WELL",
        "fill_color": Color(184, 15, 20),
        "shade_color": Color(112, 3, 6),
    },
    "hope": {
        "name": "HOPE",
        "fill_color": Color(255, 224, 148),
        "shade_color": Color(198, 163, 81),
    },
    "rage": {
        "name": "RAGE VAULT",
        "fill_color": Color(57, 30, 114),
        "shade_color": Color(29, 11, 68),
    },
    "mangrit": {
        "name": "MANGRIT",
        "hidden": False,
        "fill_color": Color(150, 224, 53),
        "shade_color": Color(106, 173, 19),
    },
    "imagination": {
        "name": "IMAGINATION",
        "hidden": False,
        "fill_color": Color(255, 182, 24),
        "shade_color": Color(188, 128, 0),
    },
    "horseshitometer": {
        "name": "FBATSH-OMETER",
        "hidden": False,
        "segmented_vial": True,
        "fill_color": Color(20, 135, 56),
        "shade_color": Color(4, 96, 32),
        "middle_color": Color(44, 146, 88),
    },
    "gambit": {
        "name": "PRANKSTER'S GAMBIT",
        "hidden": False,
        "segmented_vial": True,
        "fill_color": Color(213, 73, 232),
        "shade_color": Color(147, 28, 165),
        "middle_color": Color(255, 148, 198),
    },
}

for vial_name in vials:
    new_dict = default_vial.copy()
    new_dict.update(vials[vial_name])
    vials[vial_name] = new_dict

strife_category_colors = {
    "aggressive": Color(255, 75, 45),
    "abstinent": Color(56, 213, 244),
    "abusive": Color(255, 184, 45),
    "aspected": Color(54, 54, 159),
    "accolades": Color(54, 54, 159),
    "arsenal": Color(155, 56, 244),
    "none": Color(0, 175, 255),
}

def get_category_color(category) -> Color:
    if category in strife_category_colors:
        return strife_category_colors[category]
    else:
        return strife_category_colors["none"]

# first is light color, second is dark color
pickable_colors = [
    # kids colors
    [4, 254, 58],
    [213, 157, 248],
    [248, 12, 1],
    [84, 163, 255],
    [74, 213, 242],
    [32, 147, 0],
    [255, 111, 212],
    [253, 115, 6],
    [108, 108, 108],
    # 255
    [0, 0, 255],
    [0, 255, 0],
    [255, 0, 0],
    # hemospectrum
    [161, 0, 0],
    [162, 82, 3],
    [161, 161, 0],
    [101, 130, 0],
    [64, 102, 0],
    [7, 136, 70],
    [0, 130, 130],
    [0, 65, 130],
    [0, 33, 203],
    [68, 10, 127],
    [106, 0, 106],
    [153, 0, 77],
]

troll_colors = [
    [161, 0, 0], # rust
    [162, 82, 3], # bronze
    [161, 161, 0], # gold
    [101, 130, 0], # lime
    [64, 102, 0], # olive
    [7, 136, 70], # jade
    [0, 130, 130], # teal
    [0, 65, 130], # cobalt
    [0, 33, 203], # indigo
    [68, 10, 127], # purple
    [106, 0, 106], # violet
    [153, 0, 77], # fuchsia
]

parts_files = {
    "base": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/base")],
    "eyes": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/eyes")],
    "hair": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/hair")],
    "horns": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/horns")],
    "mouth": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/mouth")],
    "pants": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/pants")],
    "shirt": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/shirt")],
    "shoes": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/shoes")],
    "coat": [filename.replace(".png", "") for filename in os.listdir("sprites/symbol/coat")],
}

possible_parts = {}
part_styles = {}

for part in parts_files:
    possible_parts[part] = []
    part_styles[part] = {}
    for item_name in parts_files[part]:
        style = "standard"
        if "-" in item_name:
            split_item = item_name.split("-")
            final_item_name: str = split_item[0]
            style: str = split_item[1]
        else:
            final_item_name = item_name
        if final_item_name not in possible_parts[part]:
            possible_parts[part].append(final_item_name)
        if final_item_name not in part_styles[part]:
            part_styles[part][final_item_name] = []
        if style not in part_styles[part][final_item_name]:
            part_styles[part][final_item_name].append(style)

default_style_dict = {part:"standard" for part in possible_parts}

def get_random_symbol(base: Optional[str] = None) -> dict:
    symbol_dict: dict[str, Union[str, list, dict]] = {
        "base": random.choice(possible_parts["base"]),
        "eyes": random.choice(possible_parts["eyes"]),
        "hair": random.choice(possible_parts["hair"]),
        "horns": random.choice(possible_parts["horns"]),
        "mouth": random.choice(possible_parts["mouth"]),
        "pants": random.choice(possible_parts["pants"]),
        "shirt": random.choice(possible_parts["shirt"]),
        "shoes": random.choice(possible_parts["shoes"]),
    }
    if base is None: symbol_dict["base"] = random.choice(possible_parts["base"])
    else: symbol_dict["base"] = base
    if random.random() < 0.5:
        symbol_dict["coat"] = random.choice(possible_parts["coat"])
    else:
        symbol_dict["coat"] = "none"
    if symbol_dict["base"] != "troll":
        symbol_dict["horns"] = "none"
    style_dict = {}
    for part in symbol_dict:
        item_name = symbol_dict[part]
        style_dict[part] = random.choice(part_styles[part][item_name])
    symbol_dict["style_dict"] = style_dict
    if symbol_dict["base"] != "troll": 
        symbol_dict["color"] = random.choice(pickable_colors)
    else:
        symbol_dict["color"] = random.choice(troll_colors)
    return symbol_dict