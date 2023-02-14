import util

item_actions = {}

class ItemAction():
    def __init__(self, name):
        self.targeted = False
        item_actions[name] = self

add_card = ItemAction("add_card")

insert_card = ItemAction("insert_card")
insert_card.targeted = True

remove_card = ItemAction("remove_card")

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
    }

icons = {
    "player": "sprites\\icons\\player_alt.png"
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
    "rock candy": {"tier": 2, "image": "sprites\\grists\\rock_candy.png"},
    "rose quartz": {"tier": 5, "exotic": True, "image": "sprites\\grists\\rose_quartz.png"},
    "ruby": {"tier": 6, "image": "sprites\\grists\\ruby.png"},
    "rust": {"tier": 1, "image": "sprites\\grists\\rust.png"},
    "sandstone": {"tier": 2, "image": "sprites\\grists\\sandstone.png"},
    "shale": {"tier": 1, "image": "sprites\\grists\\shale.png"},
    "silicon": {"tier": 4, "image": "sprites\\grists\\silicon.png"},
    "silk": {"tier": 6, "exotic": True, "image": "sprites\\grists\\silk.png"},
    "slime": {"tier": 2, "exotic": True, "image": "sprites\\grists\\slime.png"},
    "star sapphire": {"tier": 8, "exotic": True, "image": "sprites\\grists\\star_sapphire.png"},
    "sulfur": {"tier": 5, "exotic": True, "image": "sprites\\grists\\sulfur.png"},
    "sunstone": {"tier": 7, "exotic": True, "image": "sprites\\grists\\sunstone.png"},
    "tar": {"tier": 4, "image": "sprites\\grists\\tar.png"},
    "titanium": {"tier": 9, "image": "sprites\\grists\\titanium.png"},
    "topaz": {"tier": 5, "exotic": True, "image": "sprites\\grists\\topaz.png"},
    "uranium": {"tier": 8, "image": "sprites\\grists\\uranium.png"},
    "wood": {"tier": 1, "image": "sprites\\grists\\wood.png"},
    "zilium": {"tier": 10, "exotic": True, "image": "sprites\\grists\\zilium.png"},
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
