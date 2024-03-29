import os
import json
import random
import time
from pandas import DataFrame
from copy import deepcopy

import binaryoperations

homedir = os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game_server" in subdirectories:  # if this is being run in vscode lol
    homedir += "\\suburb_game_server"


def writejson(obj=None, fn=None, dir=f"{homedir}\\json"):
    if not os.path.exists(dir):
        os.makedirs(dir)
        print(f"Created {dir}")
    if fn != None:
        with open(f"{dir}/{fn}.json", "w") as f:
            if obj == None:
                obj = eval(f"{fn}")
            if obj != None:
                if obj != {} and obj != None:
                    data = json.dump(obj, f, indent=4)
                    f = data


def readjson(obj: dict, filename, dir=f"{homedir}\\json", overwrite=True) -> dict:
    try:
        with open(f"{dir}/{filename}.json", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"UNABLE TO READ JSON {filename}")
                if overwrite:
                    print(f"Overwriting with {obj}.")
                    writejson(obj, filename, dir)
                    data = obj
                else:
                    raise e
            return data
    except FileNotFoundError as e:
        print(f"File not found when reading json: '{filename}.json'.")
        if overwrite:
            print(f"Overwriting with {obj}.")
            writejson(obj, filename, dir)
            return obj
        else:
            raise e


serversettings = {
    "ip": "",
    "port": 0,
    "path_to_cert": "",
    "path_to_key": "",
}
serversettings = readjson(serversettings, "serversettings", homedir)

ip = serversettings["ip"]
port = serversettings["port"]
path_to_cert = serversettings["path_to_cert"]
path_to_key = serversettings["path_to_key"]

if not path_to_cert or not path_to_key:
    print("serversettings.json must be filled out.")
    print("Please specify an ip address and port to host the server on.")
    print("Please specify a location for the cert and key of your server.")
    raise AssertionError

bases: dict[str, dict] = {}
bases: dict[str, dict] = readjson(bases, "bases")

for base_name, base_dict in bases.items():
    words = base_name.split(" ")
    base_name = words.pop()
    if len(words) == 0:
        adjectives = []
    else:
        adjectives = words
    base_dict["adjectives"] = adjectives
    if "kinds" in base_dict:
        base_dict["kinds"] = [kind_name for kind_name in base_dict["kinds"]]
writejson(bases, "bases")

base_names_adjectives = {}
for base_name, base_dict in bases.items():
    base_names_adjectives[base_name] = (
        base_dict["adjectives"] + base_dict["secretadjectives"]
    )
writejson(base_names_adjectives, "base_names_adjectives")

codes = {}  # key: item code value: item name
codes = readjson(codes, "codes")


def get_base_submissions():
    base_submissions = {}
    base_submissions = readjson(base_submissions, "base_submissions")
    return base_submissions


def update_base_submissions(submissions_dict: dict):
    base_submissions = submissions_dict
    writejson(base_submissions, "base_submissions")


considered_submissions = {}
considered_submissions = readjson(considered_submissions, "considered_submissions")

spawnlists = {}
spawnlists = readjson(spawnlists, "spawnlists")

kinds: list[str] = []
for base in bases:
    for kind in bases[base]["kinds"]:
        if kind not in kinds:
            kinds.append(kind)

additional_kinds = [
    "plungerkind",
    "hosekind",
    "bookkind",
    "bustkind",
    "spadekind",
    "pipekind",
    "nailgunkind",
    "hairdryerkind",
    "lacrossstickkind",
    "throwingstarkind",
    "tongskind",
    "razorkind",
    "fireextinguisherkind",
    "branchkind",
    "bowlingpinkind",
    "bombkind",
    "woodwindkind",
    "staplerkind",
    "riflekind",
    "candlestickkind",
    "paddlekind",
    "bowkind",
    "barbedwirekind",
    "dartkind",
    "marblekind",
    "plierkind",
    "fireworkkind",
    "chiselkind",
    "aerosolkind",
    "shoekind",
    "puppetkind",
    "fankind",
    "brasskind",
    "rockkind",
    "scythekind",
    "dicekind",
    "cardkind",
    "puppetkind",
    "foodkind",
    "grimoirekind",
    "fabrickind",
    "plushkind",
    "firekind",
]

for kind in additional_kinds:
    if kind not in kinds:
        kinds.append(kind)

print(sorted(kinds))


def update_jsons():
    global bases
    global spawnlists
    bases = readjson(bases, "bases")
    spawnlists = readjson(spawnlists, "spawnlists")


def saveall():
    t = time.time()
    print("Saving...")
    writejson(codes, "codes")
    print(f"Save complete. Took {time.time()-t:.2f} seconds.")


for base in bases:
    if "code" in bases[base]:
        code = bases[base]["code"]
    else:
        code = random.choices(binaryoperations.reversebintable, k=8)
        code = "".join(code)
        bases[base]["code"] = code
    codes[code] = base

if __name__ == "__main__":  # if this file is being run, run the json editor
    pass
    # bases = {}
    # bases = readjson(bases, "bases")
    # goto = ""
    # for index, item in enumerate(bases):
    #     next = False
    #     for attr in bases[item]:
    #         while True:
    #             try:
    #                 if goto != "" and goto != item:
    #                     next = True
    #                     break
    #                 else:
    #                     goto = ""
    #                 os.system("cls")
    #                 print(f"Item {index}/{len(bases)}: {item}")
    #                 print(f"{attr}")
    #                 print("> to go to the next item. Type >name to go to a specific item.")
    #                 if attr == "power":
    #                     print("How much power should this item have? Ex: Paper: 1 Knife: 10 Baseball Bat: 20 Sword: 40 Gun: 100")
    #                 if attr == "weight":
    #                     print("How much weight should this item have? Ex: Paper: 1 Knife: 3 Baseball Bat: 10 Sword: 15 Bowling Ball: 35")
    #                 if attr == "size":
    #                     print("How much size should this item have? (Max wieldable is 20) Ex: Paper: 1 Knife: 2 Baseball Bat: 10 Sword: 10 Zweihander: 20")
    #                 if attr == "dicemin":
    #                     print("What should the dicemin be? Ex: Paper: 0.2 Knife: 0.7 Baseball Bat: 1 Sword: 1.1")
    #                 if attr == "dicemax":
    #                     print("What should the dicemax be? Ex: Paper: 0.5 Knife: 1 Baseball Bat: 1.3 Sword: 1.5")
    #                 if attr == "kinds":
    #                     if "glitchkind" in bases[item][attr]:
    #                         bases[item][attr].pop("glitchkind")
    #                     print("What kinds should this item be? None to go next.")
    #                     print(f"Current Kinds: {bases[item][attr]}")
    #                 if attr == "slots":
    #                     print("What slots should this item be equippable in? None to go next.")
    #                     print(f"Current slots: {bases[item][attr]}")
    #                 if attr == "tags":
    #                     print("What tags should this item have? None to go next.")
    #                     print(f"Current slots: {bases[item][attr]}")
    #                 if attr == "cost":
    #                     print("What grist should this item cost? None to go next.")
    #                     print(f"Current grists: {bases[item][attr]}")
    #                 if attr == "description":
    #                     print("What should the description be?")
    #                 if attr == "onhiteffect":
    #                     print("What on hit effects should it have?")
    #                     print(f"Current effects: {bases[item][attr]}")
    #                 if attr == "weareffect":
    #                     print("What wear effects should it have?")
    #                     print(f"Current effects: {bases[item][attr]}")
    #                 if attr == "consumeeffect":
    #                     print("What consume effects should it have?")
    #                     print(f"Current effects: {bases[item][attr]}")
    #                 if attr == "secreteffect":
    #                     print("What secret effects should it have?")
    #                     print(f"Current effects: {bases[item][attr]}")
    #                 if attr == "secretadjectives":
    #                     if "glitched" in bases[item][attr]:
    #                         bases[item][attr].remove("glitched")
    #                     print("What secret adjectives should it have? No input for none.")
    #                     print(f"Current effects: {bases[item][attr]}")
    #                 if attr != "base":
    #                     x = input("* ")
    #                 else:
    #                     print("base detected")
    #                     bases[item][attr] = True
    #                     x = ""
    #                     break
    #                 if x == "save":
    #                     writejson(bases, "bases")
    #                     print("Saved the item.")
    #                 if x != "" and x[0] == ">":
    #                     next = True
    #                     goto = x[1:]
    #                     break
    #                 if attr == "description":
    #                     bases[item][attr] = x
    #                     break
    #                 if attr == "secretadjectives":
    #                     if x != "":
    #                         bases[item][attr].append(x)
    #                     else:
    #                         break
    #                 if attr in ["power", "weight", "size"]:
    #                     bases[item][attr] = int(x)
    #                     break
    #                 if attr in ["dicemin", "dicemax"]:
    #                     bases[item][attr] = float(x)
    #                     break
    #                 if attr in ["onhiteffect", "weareffect", "consumeeffect", "secreteffect"]:
    #                     if x != "":
    #                         print("What power should the effect be at?")
    #                         y = input("* ")
    #                         power = float(y)
    #                         print("What adjective/base should the effect be inherited with? No input for none.")
    #                         z = input("* ")
    #                         if z != "":
    #                             bases[item][attr][x] = [power, str(z)]
    #                         else:
    #                             bases[item][attr][x] = [power]
    #                     else:
    #                         break
    #                 if attr in ["kinds", "slots", "tags"]:
    #                     if x != "":
    #                         print(f"What rate should that be inherited at?")
    #                         y = input("* ")
    #                         rate = float(y)
    #                         print(f"What adjective/base should that be inherited with? No input for none.")
    #                         z = input("* ")
    #                         if z != "":
    #                             bases[item][attr][x] = [rate, str(z)]
    #                         else:
    #                             bases[item][attr][x] = [rate]
    #                     else:
    #                         break
    #                 if attr == "cost":
    #                     if x != "":
    #                         print(f"What should the cost ratio be?")
    #                         y = input("* ")
    #                         cost = float(y)
    #                         bases[item][attr][x] = y
    #                     else:
    #                         break
    #             except (TypeError, ValueError) as e:
    #                 print(f"excepted error {e}")
    #         if next:
    #             break
    # writejson(bases, "bases")
