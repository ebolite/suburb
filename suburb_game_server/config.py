import util

max_wielded_size = 20
max_worn_size = 40

overmap_width = 96
terrain_decay = 0.01

base_parry_chance: float = 0.1
player_hp_threshold_damage_mult: float = 0.25

sburb = "<a:suburbspirograph:820899074986606613>"

# items which appear as icons to clients
special_items = ["punch designix", "cruxtruder", "sealed cruxtruder", "totem lathe", "alchemiter", "Sburb disc"]

verbs = [
    "Transforming",
    "Reorganizing",
    "Formalizing",
    "Justifying",
    "Advising",
    "Managing",
    "Recasting",
    "Achieving",
    "Officiating",
    "Exhibiting",
    "Processing",
    "Jerry-building",
    "Informing",
    "Inverting",
    "Performing",
    "Judging",
    "Upgrading",
    "Regrowing",
    "Recommending",
    "Approving",
    "Sweeping",
    "Sewing",
    "Detailing",
    "Enforcing",
    "Distributing",
    "Interwinding",
    "Piloting",
    "Gathering",
    "Supplying",
    "Undertaking",
    "Accelerating",
    "Logging",
    "Correlating",
    "Uniting",
    "Qualifying",
    "Sharing",
    "Obtaining",
    "Ranking",
    "Sensing",
    "Originating",
    "Translating",
    "Regulating"
]
nouns = [
    "Soffits",
    "Keys",
    "Immersion Joints",
    "Kick Extractors",
    "Aggregates",
    "Elbows",
    "Connectors",
    "Aluminum Trowels",
    "Disks",
    "Absolute Spigots",
    "Coil Hydrants",
    "Reflectors",
    "Casters",
    "Rubber Hoists",
    "Wrenches",
    "Chalk Adapters",
    "Ignition Paths",
    "Flashing",
    "Ratchets",
    "Barriers",
    "Impact Fillers",
    "Mirrors",
    "Collectors",
    "Measures",
    "Systems",
    "Registers",
    "Ash Diffusers",
    "Cranks",
    "Eave Pockets",
    "Scroll Stops",
    "Straps",
    "Downspouts",
    "Shingles",
    "Mallets",
    "Electrostatic Lifts",
    "Clamps",
    "Circular Fluids",
    "Foundation Gauges",
    "Miter Brackets",
    "Space Networks",
    "Drills"
    "Guards"
]

grists = {
    "build": {"tier": 0},
    "acid": {"tier": 4, "exotic": True},
    "amber": {"tier": 3},
    "amethyst": {"tier": 3},
    "aquamarine": {"tier": 1},
    "blood": {"tier": 3},
    "caulk": {"tier": 5},
    "chalk": {"tier": 1},
    "cobalt": {"tier": 4},
    "copper": {"tier": 2},
    "diamond": {"tier": 9},
    "emerald": {"tier": 8},
    "fluorite": {"tier": 5, "exotic": True},
    "frosting": {"tier": 1},
    "garnet": {"tier": 3},
    "gold": {"tier": 6},
    "iodine": {"tier": 1},
    "iron": {"tier": 5},
    "jet": {"tier": 2},
    "lead": {"tier": 2},
    "lux": {"tier": 9},
    "malachite": {"tier": 2, "exotic": True},
    "marble": {"tier": 3, "exotic": True},
    "mercury": {"tier": 4},
    "mist": {"tier": 3, "exotic": True},
    "moonstone": {"tier": 6, "exotic": True},
    "neon": {"tier": 4, "exotic": True},
    "nitrogen": {"tier": 3},
    "obsidian": {"tier": 7},
    "onyx": {"tier": 9},
    "permafrost": {"tier": 8},
    "quartz": {"tier": 7},
    "rainbow": {"tier": 10, "exotic": True},
    "redstone": {"tier": 7},
    "rock candy": {"tier": 2},
    "rose quartz": {"tier": 5, "exotic": True},
    "ruby": {"tier": 6},
    "rust": {"tier": 1},
    "sandstone": {"tier": 2},
    "shale": {"tier": 1},
    "silicon": {"tier": 4},
    "silk": {"tier": 6, "exotic": True},
    "slime": {"tier": 2, "exotic": True},
    "star sapphire": {"tier": 8, "exotic": True},
    "sulfur": {"tier": 5, "exotic": True},
    "sunstone": {"tier": 7, "exotic": True},
    "tar": {"tier": 4},
    "titanium": {"tier": 9},
    "topaz": {"tier": 5, "exotic": True},
    "uranium": {"tier": 8},
    "wood": {"tier": 1},
    "zilium": {"tier": 10, "exotic": True},
}

aspect_grists = {
    "space": {
        "jet": 1, 
        "chalk": 1, 
        "onyx": 0.2
    },
    "time": {
        "garnet": 1,
        "redstone": 0.2,
        "ruby": 0.2
    },
    "mind": {
        "emerald": 0.3,
        "acid": 0.3,
        "uranium": 0.3
    },
    "heart": {
        "frosting": 1,
        "rock candy": 1,
        "rose quartz": 0.4,
    },
    "hope": {
        "gold": 0.5,
        "sunstone": 0.5,
        "amber": 1,
    },
    "rage": {
        "amethyst": 1.5,
        "shale": 1.5,
    },
    "breath": {
        "aquamarine": 1,
        "fluorite": 0.5,
        "diamond": 0.2,
    },
    "blood": {
        "blood": 1.5,
        "rust": 0.5,
        "iron": 0.5,
    },
    "life": {
        "wood": 0.5,
        "aquamarine": 1,
        "slime": 0.5,
    },
    "doom": {
        "malachite": 1,
        "sulfur": 0.3,
        "tar": 0.5,
    },
    "light": {
        "lux": 1,
        "neon": 1
    },
    "void": {
        "mist": 1
    }
}

aspect_secretadjectives = {
    "space": ["massive", "immense", "cosmic", "reality-bending", "astronomical", "gigantic", "black", "white"],
    "time": ["time-travelling", "clockwork", "gear-filled", "antique", "futuristic", "paradox", "ticking", "red"],
    "mind": ["smart", "intelligent", "clever", "brainy", "cerebral", "analytical", "precise", "mind-reading", "precognitive", "teal"],
    "heart": ["soulful", "heartfelt", "emotional", "self-absorbed", "narcissistic", "passionate", "sincere", "pink"],
    "hope": ["hopeful", "defiant", "justice", "justified", "moral", "destined", "chosen", "faithful", "yellow", "white"],
    "rage": ["pissed+off", "mad", "angry", "passionate", "insane", "depressed", "chaotic", "unpredictable", "unstable", "irate", "wrathful",
             "furious", "enraged", "demented", "crazy", "deranged", "purple"],
    "breath": ["free", "airy", "heroic", "confident", "unchained", "unrestricted", "independent", "brave", "gallant", "breathing", "blue"],
    "blood": ["bloody", "chained", "restrained", "motivational", "inspiring", "bloodstained", "crimson", "sanguine", "gory", "red"],
    "life": ["lively", "living", "vigorous", "breathing", "vital", "live", "wooden", "green", "pale"],
    "doom": ["dead", "doomed", "dying", "cursed", "suffering", "miserable", "lifeless", "deceased", "the+late", "cadaverous", "necrotic", "rotting", "rotten", "green", "black"],
    "light": ["glowing", "illuminant", "shining", "lustrous", "beaming", "vivid", "vibrant", "gleaming", "phosphorescent", "lambent", "golden", "lucky", "fortunate"],
    "void": ["anti", "illusory", "unreal", "false", "void", "empty", "barren", "bare", "meaningless", "null", "fruitless", "vain", "hollow", "vacuous", "blue"]
}

modus_max_sizes = {"wallet": 413612}

enemies = ["imp", "ogre", "basilisk", "octopisc", "lich", "titachnid", "serpentipede", "giclops", "bicephalon", "acheron"]

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

categoryproperties = { # mapgen properties
    "amber": {
        "islands": 72,
        "landrate": .5,
        "lakes": 24,
        "lakerate": .4,
        "smoothness": 0.6,
        "steepness": 0.6,
        },
    "barren": {
        "islands": 12,
        "landrate": 1,
        "lakes": 60,
        "lakerate": .2,
        "extralands": 24,
        "extrarate": 0.1,
        },
    "beach": {
        "islands": 132,
        "landrate": .3,
        "lakes": 0,
        "lakerate": 0,
        "extralands": 12,
        "extrarate": 0.4,
        "smoothness": 0.8,
        "steepness": 0.7,
        },
    "block": {
        "islands": 72,
        "landrate": 1,
        "lakes": 30,
        "lakerate": .3,
        "special": "block",
        "smoothness": 1,
        "steepness": 2,
        },
    "calcite": {
        "islands": 240,
        "landrate": .4,
        "lakes": 180,
        "lakerate": .3,
        "smoothness": 0.5,
        "steepness": 1.5,
        },
    "cold": {
        "islands": 24,
        "landrate": 1,
        "lakes": 60,
        "lakerate": .4,
        "extralands": 42,
        "extrarate": 0.15,
        "smoothness": 0.8,
        "steepness": 2.5,
        },
    "dark": {
        "islands": 36,
        "landrate": .6,
        "lakes": 24,
        "lakerate": .4,
        "extralands": 42,
        "extrarate": 0.15,
        "smoothness": 0.75
        },
    "elemental": {
        "islands": 60,
        "landrate": .8,
        "lakes": 60,
        "lakerate": .4,
        "smoothness": 0.1,
        "steepness": 2,
        },
    "hot": {
        "islands": 18,
        "landrate": .6,
        "lakes": 0,
        "lakerate": 0,
        "smoothness": 0.2,
        "steepness": 0.7,
        },
    "liquid": {
        "islands": 180,
        "landrate": .2,
        "lakes": 0,
        "lakerate": 0,
        "smoothness": 0.85,
        "steepness": 0.7,
        },
    "metal": {
        "islands": 54,
        "landrate": .5,
        "lakes": 90,
        "lakerate": .3,
        "smoothness": 0.95,
        "steepness": 1.75,
        },
    "nature": {
        "islands": 12,
        "landrate": 1,
        "lakes": 60,
        "lakerate": .4,
        "smoothness": 0.6,
        },
    "oil": {
        "islands": 48,
        "landrate": 1,
        "lakes": 90,
        "lakerate": .4,
        "smoothness": 0.7,
        "steepness": 0.9,
        },
    "radiant": {
        "islands": 240,
        "landrate": .1,
        "lakes": 0,
        "lakerate": 0,
        "smoothness": 0.6,
        },
    "science": {
        "islands": 12,
        "landrate": 1,
        "lakes": 60,
        "lakerate": .4,
        "special": "block",
        "smoothness": 0.6,
        "steepness": 1.7,
        },
    "stone": {
        "islands": 24,
        "landrate": .8,
        "lakes": 6,
        "lakerate": .3,
        "special": "center",
        "extralands": 48,
        "extrarate": 0.1,
        "smoothness": 0.6,
        },
    "sweet": {
        "islands": 72,
        "landrate": .5,
        "lakes": 36,
        "lakerate": .5,
        "extralands": 12,
        "extrarate": 0.4,
        "extraspecial": "center",
        "smoothness": 0.6,
        },
    "uranium": {
        "islands": 48,
        "landrate": .5,
        "lakes": 0,
        "lakerate": 0,
        "special": "dual",
        "extralands": 48,
        "extrarate": 0.1,
        "smoothness": 0.3,
        "steepness": 2,
        },
    "wealth": {
        "islands": 72,
        "landrate": .2,
        "lakes": 0,
        "lakerate": 0,
        "special": "dual",
        "extralands": 24,
        "extrarate": 0.1,
        "smoothness": 0.8,
        "steepnesss": 1.3,
        }
    }

landbases = {
    "amber": ["amber", "sun", "gold", "resin", "fossils", "topaz", "sulfur", "phosphor", "radiance", "bloom", "heat"],
    "barren": ["waste", "decay", "dust", "mist", "sulfur", "rust", "stone", "scrap", "trash", "ruin", "dreck", "dross"],
    "beach": ["sun", "fun", "volley", "oceans", "seas", "sand", "heat", "salt", "coast", "towels", "litter", "sharks", "clams", "shells", "umbrellas", "chaises", "glass"],
    "block": ["stone", "block", "blocks", "geometry", "angles", "cubes", "rectangular prisms", "edge", "edges", "boxes", "sections"],
    "calcite": ["minerals", "calcite", "crystal", "carbonate", "scalenohedra", "fluorescence", "chalk", "glass", "luster", "white", "limestone", "cement"],
    "cold": ["ice", "frost", "cold", "blizzards", "snow", "glaciers", "sleet", "slush", "powder", "banks", "gale", "wind"],
    "dark": ["darkness", "shade", "black", "dusk", "twilight", "murk", "smoke", "smog", "oil", "tar", "jet", "haze"],
    "elemental": ["iron", "metal", "tables", "poison", "base", "acid", "copper", "sulfur", "helium", "krypton", "xenon"],
    "hot": ["heat", "fire", "warmth", "fever", "flames", "blaze", "inferno", "coal", "burning", "lava", "magma"],
    "liquid": ["water", "liquid", "slush", "slurry", "broth", "soup", "flow", "goop", "elixir", "rain"],
    "metal": ["metal", "iron", "shine", "polish", "alloy", "ingots", "furnaces", "anvils"],
    "nature": ["trees", "bushes", "lush", "bounty", "green", "overgrowth", "growth", "forest", "jungle", "animals", "dew"],
    "oil": ["oil", "shale", "tar", "jet", "smog", "pollution", "fuel", "gas", "combustion", "grease", "slick", "tarnish", "haze"],
    "radiant": ["prisms", "neon", "pyramids", "light", "radiance", "sun", "bloom", "shine", "glare", "lamps", "lanterns", "rays", "color", "photons", "quartz"],
    "science": ["science", "acid", "base", "alkanes", "ether", "ketone", "phenol", "particles", "molecules", "method", "nuclei", "protons", "electrons", "neutrons", "neon", "krypton", "xenon"],
    "stone": ["stone", "rocks", "gravel", "ore", "minerals", "boulders", "quarries", "mines", "pebbles", "earth", "caves"],
    "sweet": ["little cubes", "tea", "sweetness", "frosting", "sugar", "candy", "caramel", "marshmallows", "glucose"],
    "uranium": ["uranium", "radiation", "poison", "emission", "ions", "particles", "electromagnetism", "photons", "neon"],
    "wealth": ["greed", "treasure", "wealth", "money", "gold", "diamonds", "opulence", "riches", "luxury", "bounty", "plenty", "hoards"]
    }

aspectbases = {
    "space": ["space", "frogs", "stars", "galaxies", "genesis", "planets"],
    "time": ["clockwork", "time", "clocks", "watches"],
    "mind": ["thought", "mind", "flow", "debate", "knowledge", "brains"],
    "heart": ["heart", "love", "bonds", "tea", "comrades", "respect", "friendship"],
    "hope": ["hope", "clouds", "future", "beauty", "dreams", "justice", "angels", "light"],
    "rage": ["anger", "pain", "animosity", "mirth", "frustration", "wrath"],
    "breath": ["wind", "zephyr", "gas", "breath", "gust", "tornadoes", "helium"],
    "blood": ["blood", "pulse", "veins", "arteries", "bonds", "crimson"],
    "life": ["life", "growth", "meadow", "plains", "trees", "plants"],
    "light": ["light", "radiance", "luck", "treasure", "bounty", "wishes", "bounty"],
    "doom": ["doom", "death", "destruction", "misfortune", "decay", "ruin", "tombs", "graves", "crypts"],
    "void": ["void", "nothing", "empty", "abyss", "silence", "hollow", "lack", "caves"]
    }

classes = {
    "thief": {"description": "(-) Steals ASPECT for themselves."},
    "rogue": {"description": "(+) Steals ASPECT for others."},
    "prince": {"description": "(-) Destroys ASPECT and destroys with ASPECT."},
    "bard": {"description": "(+) Allows ASPECT to be destroyed."},
    "knight": {"description": "(-) Exploits ASPECT to fight."},
    "page": {"description": "(+) Exploits ASPECT for others."},
    "mage": {"description": "(-) Sees ASPECT. Pursues ASPECT."},
    "seer": {"description": "(+) Sees ASPECT. Avoids ASPECT."},
    "witch": {"description": "(-) Manipulates ASPECT."},
    "heir": {"description": "(+) Becomes ASPECT."},
    "maid": {"description": "(-) Creates ASPECT."},
    "sylph": {"description": "(+) Restores using ASPECT, or restores ASPECT."}
    }

aspects = {
    "space": {"description": "(*) Represents the fabric of reality. Space players are big thinkers and innovators."},
    "time": {"description": "(*) Represents time. Time players are goal-focused fighters."},
    "mind": {"description": "Represents thought, thinking and the mind. Mind players are cerebral and thoughtful."},
    "heart": {"description": "Represents the soul. Heart players are very in-tune with their sense of self and their emotions."},
    "hope": {"description": "Represents justice and hope. Hope players tend to have a strong sense of morality."},
    "rage": {"description": "Represents chaos and negative emotions. Rage players are passionate and zealous."},
    "breath": {"description": "Represents freedom. Breath players are flexible and motivated, as well as natural leaders."},
    "blood": {"description": "Represents bonds and kinship. Blood players are leaders and prophets."},
    "life": {"description": "Represents life force and healing. Life players are empathetic, understanding, and concerned with the well-being of others."},
    "doom": {"description": "Represents death, fate and futility. Doom players are miserable sufferers given wisdom in their pain."},
    "light": {"description": "Represents fortune. Light players are knowledge-seekers, driven to learn and understand the world."},
    "void": {"description": "Represents the essence of lacking, nothingness, and the obfuscation of knowledge. Void players are mysterious secret-keepers."}
    }

aspectskills = {
    "space": {
        "distort": 10
        },
    "time": {
        "rewind": 10
        },
    "mind": {
        "educate": 10
    },
    "heart": {
        "emote": 10
        },
    "hope": {
        "pray": 10
        },
    "rage": {
        "seethe": 10
        },
    "breath": {
        "blow": 10
        },
    "blood": {
        "bleed": 10
        },
    "life": {
        "heal": 10
        },
    "light": {
        "charm": 10
        },
    "doom": {
        "curse": 10
        },
    "void": {
        "lessen": 10
        }
    }

aspectpassives = {
    "space": {
        "massive": 20
        },
    "time": {
        "warp": 20
        },
    "mind": {
        "thoughtful": 20
        },
    "heart": {
        "soulful": 20
        },
    "hope": {
        "savior": 20
        },
    "rage": {
        "cope": 20
        },
    "breath": {
        "gaseous": 20
        },
    "blood": {
        "circulation": 20
        },
    "life": {
        "livid": 20
        },
    "light": {
        "gambler": 20
        },
    "doom": {
        "edgy": 20
        },
    "void": {
        "empty": 20
        }
    }

classskills = {

    }

classpassives = {
    "space": {},
    "time": {},
    "mind": {},
    "heart": {},
    "hope": {},
    "rage": {},
    "breath": {},
    "blood": {},
    "life": {},
    "light": {},
    "doom": {},
    "void": {}
    }

for cls in classes:
    classskills[cls] = {
    "space": {},
    "time": {},
    "mind": {},
    "heart": {},
    "hope": {},
    "rage": {},
    "breath": {},
    "blood": {},
    "life": {},
    "light": {},
    "doom": {},
    "void": {}
    }
    classpassives[cls] = {
    "space": {},
    "time": {},
    "mind": {},
    "heart": {},
    "hope": {},
    "rage": {},
    "breath": {},
    "blood": {},
    "life": {},
    "light": {},
    "doom": {},
    "void": {}
    }

starting_tiles = ["B", "S"]

itemcategories = {
    "computers": ["lap top", "desktop computer"],
    "cleaning supplies": ["broom", "straw broom", "vacuum cleaner", "mop"],
    "tools": ["scissors", "shears", "chainsaw", "weed whacker", "crowbar", "ice pick", "hammer", "sledge hammer", "shovel", "hatchet",
        "axe", "flat-head screwdriver", "Phillips screwdriver", "magnetic screwdriver", "rake", "wooden plank", "chain", "bike chain", "extension cable",
        "rope", "hack saw", "pipe wrench"],
    "sports": ["baseball bat", "aluminum bat", "golf club", "basketball", "football", "dodgeball", "bowling ball", "hockey stick", "trophy", "boxing gloves"],
    "toys": ["yoyo", "rubber mallet", "jump rope"],
    "historical weapons": ["spear", "sword", "katana", "rapier", "zweihander", "sap", "caestus", "trident"],
    "statues": ["Abraham Lincoln bust", "Julius Caesar bust", "miniature The+Thinker statue", "woman-sized Statue+of Liberty"],
    "clothes": ["mittens", "gloves", "ice skates", "cowboy hat", "cowboy boots", "bandana"],
    "food": ["candy cane", "water bottle", "red faygo", "grape faygo", "cola faygo", "cotton+candy faygo", "kiwi+strawberry faygo"],
    "instruments": ["electric guitar", "acoustic guitar", "drum set", "flute", "saxophone", "grand piano"],
    }

allcategoryitems = []
for category in itemcategories:
    allcategoryitems += itemcategories[category]

itemcategoryrarities = {
    "anywhere": {
        "rare": ["empty captchalogue card"],
        "exotic": ["fancy+santa"]
        },
    "bedroom": {
        "always": ["bed", "dresser", "pillow", "blanket"],
        "common": itemcategories["computers"] + itemcategories["clothes"] + ["lamp", "desk lamp"],
        "uncommon": ["paper", "key chain", "clock"],
        "rare": itemcategories["food"],
        "exotic": ["pepper spray"]
        },
    "kitchen": {
        "always": ["refrigerator", "oven", "knife", "sink"],
        "common": itemcategories["food"] + ["table", "cup", "mug", "plate", "frying pan", "pot", "silver spoon", "silver fork", "spatula", "wooden spoon", "scissors", "rolling pin", "pizza cutter", "ladle"],
        "uncommon": itemcategories["cleaning supplies"] + ["shears", "safety scissors", "butcher knife"],
        "rare": ["golden spatula", "clock"]
        },
    "dining room": {
        "always": ["silver spoon", "silver fork", "plate", "table"],
        "common": ["knife", "cup", "mug"],
        "uncommon": ["lamp", "clock"] + itemcategories["food"],
        "rare": ["grandfather clock"]
        },
    "garage": {
        "common": itemcategories["tools"],
        "rare": ["halligan bar", "fire axe"]
        },
    "bathroom": {
        "always": ["plunger", "sink", "toilet", "bath tub"],
        "common": itemcategories["cleaning supplies"] + ["curling iron", "shower"],
        "exotic": ["grandfather clock"]
        },
    "foyer": {
        "common": ["walking cane", "umbrella", "table", "lamp", "bench"],
        "uncommon": itemcategories["statues"] + ["fire poker", "bull-penis cane", "fireplace", "arm chair"],
        "rare": itemcategories["historical weapons"] + ["piano wire", "grandfather clock", "grand piano"]
        },
    "living room": {
        "always": ["couch"],
        "common": ["table", "arm chair", "television"],
        "uncommon": itemcategories["food"] + ["walking cane", "umbrella"],
        "rare": itemcategories["statues"] + ["piano wire", "bull-penis cane", "fire poker", "grandfather clock"]
        },
    "laundry room": {
        "always": ["washing machine"],
        "common": itemcategories["clothes"] + ["clothing iron"]
        },
    "office": {
        "always": ["desktop computer", "table"],
        "common": ["scissors", "ballpoint pen", "#2 pencil", "paper", "clock"],
        "uncommon": ["ballpoint pen", "stapler", "fax machine", "copying machine"]
        },
    "workout room": {
        "always": ["5-pound dumbbell", "water bottle"],
        "common": ["5-pound dumbbell", "15-pound dumbbell", "water bottle"],
        "uncommon": ["rope", "boxing gloves", "15-pound dumbbell"],
        "rare": itemcategories["sports"] + ["steroid bottle"],
        "exotic": ["100-pound dumbbell", "steroid bottle"]
        },
    "cellar": {
        "common": ["table", "couch", "arm chair", "television", "bed", "dresser"] + itemcategories["cleaning supplies"],
        "uncommon": itemcategories["instruments"] + ["sewing needles", "knitting needles"],
        "rare": itemcategories["historical weapons"] + ["grandfather clock"]
        },
    "attic": {
        "common": ["table", "couch", "arm chair", "television", "bed", "dresser"] + itemcategories["cleaning supplies"],
        "uncommon": itemcategories["instruments"] + ["sewing needles", "knitting needles"],
        "rare": itemcategories["historical weapons"] + ["grandfather clock"]
        },
    "security": {
        "common": ["pepper spray", "stun gun"],
        "uncommon": ["heavy-duty taser", "sap"],
        "rare": ["shotgun", "pistol"],
        "exotic": [".44 magnum", "double-barreled shotgun"]
        },
    "game room": {
        "common": itemcategories["sports"] + ["pool cue"],
        "uncommon": itemcategories["toys"]
        },
    "anime": {
        "always": ["anime dvd", "anime poster"],
        "common": ["anime dvd", "anime poster", "manga"],
        "uncommon": ["miku figurine", "cheap piece-of-shit katana", "bodypillow"],
        "rare": ["katana", "shuriken"],
        "exotic": ["anime katana"]
        },
    "punk": {
        "always": ["edgy knife"],
        "common": ["edgy knife", "baseball bat", "electric guitar", "thrasher poster", "nirvana album"],
        "uncommon": ["brass knuckles", "acoustic guitar", "drum set"],
        "rare": itemcategories["instruments"],
        "exotic": ["pistol", "shotgun"]
        },
    "history": {
        "always": ["history book"],
        "common": itemcategories["statues"] + ["atlas", "history book"],
        "uncommon": itemcategories["statues"] + ["pitchfork"],
        "rare": itemcategories["historical weapons"]
        },
    "music": {
        "common": itemcategories["instruments"],
        "uncommon": ["headphones", "tuning fork", "thrasher poster", "nirvana album"]
        },
    "sports": {
        "common": itemcategories["sports"],
        "uncommon": ["water bottle"]
        },
    "garbage": {
        "common": ["paper", "empty wrapper", "water bottle", "empty soda can", "plastic bag"],
        "uncommon": allcategoryitems,
        "rare": allcategoryitems,
        "exotic": ["sord"]
        },
    "technology": {
        "common": ["lap top", "desktop computer", "smart phone", "graphics card"],
        "uncommon": ["virtual+reality headset", "rc drone", "gaming computer"]
        },
    "cowboy": {
        "common": ["walking cane", "cowboy hat", "cowboy boots", "bandana"],
        "uncommon": ["rope", "cowboy hat"],
        "rare": ["pistol"],
        "exotic": [".44 magnum"]
        },
    "clown": {
        "common": ["joker figurine", "clown poster", "red faygo", "grape faygo", "cola faygo"],
        "uncommon": ["clown shoes", "clown nose"],
        "rare": ["cotton+candy faygo", "kiwi+strawberry faygo"],
        "exotic": ["candy+apple faygo"]
        },
    "pathetic": {
        "common": ["red faygo", "grape faygo", "cola faygo", "paper", "empty wrapper", "water bottle"],
        "uncommon": ["gaming computer", "anime dvd", "anime poster", "edgy knife", "headphones"],
        "rare": allcategoryitems,
        "exotic": ["sord"]
        }
    }

interests = ["anime", "punk", "history", "music", "sports", "garbage", "technology", "cowboy", "clown", "pathetic"]

itemcategoryrarities["studio apartment"] = itemcategoryrarities["bedroom"].copy()
itemcategoryrarities["studio apartment"]["always"] = ["bed", "dresser", "pillow", "blanket", "refrigerator", "oven", "sink"]
