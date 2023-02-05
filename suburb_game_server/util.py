import os
import json
import random

import binaryoperations

homedir =  os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game_server" in subdirectories: # if this is being run in vscode lol
    homedir += "\\suburb_game_server"

def writejson(obj=None, fn=None):
    if not os.path.exists(f"{homedir}\\json"):
        os.makedirs(f"{homedir}\\json")
        print(f"Created {homedir}\\json")
    os.chdir(f"{homedir}\\json")
    if fn != None:
        with open(f"{fn}.json", "w") as f:
            if obj == None:
                obj = eval(f"{fn}")
            if obj != None:
                if obj != {} and obj != None:
                    data = json.dump(obj, f, indent=4)
                    f = data

def readjson(obj, filename):
    try:
        os.chdir(f"{homedir}\\json")
        with open(f"{filename}.json", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"UNABLE TO READ JSON {filename}")
                writejson(obj, f"{homedir}\\json\\failed\\{filename}")
                data = {}
            return data
    except FileNotFoundError:
        print(f"File not found when reading json: '{filename}.json'. Overwriting with {obj}.")
        writejson(obj, filename)
        return obj
    
sessions = {} 
sessions = readjson(sessions, "sessions")

players = {}
players = readjson(players, "players")

bases = {}
bases = readjson(bases, "bases")

items = {}
items = readjson(items, "items")

instances = {}
instances = readjson(instances, "instances")

codes = {} # key: item code value: item name
codes = readjson(codes, "codes")

def saveall():
    writejson(sessions, "sessions")
    writejson(players, "players")
    writejson(items, "items")
    writejson(instances, "instances")
    writejson(codes, "codes")

for base in bases:
    if "code" in bases[base]:
        code = bases[base]["code"]
    else:
        code = random.choices(binaryoperations.reversebintable, k=8)
        code = "".join(code)
        bases[base]["code"] = code
    codes[code] = base

if __name__ == "__main__": # if this file is being run, run the json editor
    bases = {}
    bases = readjson(bases, "bases")
    goto = ""
    for index, item in enumerate(bases):
        next = False
        for attr in bases[item]:
            while True:
                try:
                    if goto != "" and goto != item:
                        next = True
                        break
                    else:
                        goto = ""
                    os.system("cls")
                    print(f"Item {index}/{len(bases)}: {item}")
                    print(f"{attr}")
                    print("> to go to the next item. Type >name to go to a specific item.")
                    if attr == "power":
                        print("How much power should this item have? Ex: Paper: 1 Knife: 10 Baseball Bat: 20 Sword: 40 Gun: 100")
                    if attr == "weight":
                        print("How much weight should this item have? Ex: Paper: 1 Knife: 3 Baseball Bat: 10 Sword: 15 Bowling Ball: 35")
                    if attr == "size":
                        print("How much size should this item have? (Max wieldable is 20) Ex: Paper: 1 Knife: 2 Baseball Bat: 10 Sword: 10 Zweihander: 20")
                    if attr == "dicemin":
                        print("What should the dicemin be? Ex: Paper: 0.2 Knife: 0.7 Baseball Bat: 1 Sword: 1.1")
                    if attr == "dicemax":
                        print("What should the dicemax be? Ex: Paper: 0.5 Knife: 1 Baseball Bat: 1.3 Sword: 1.5")
                    if attr == "kinds":
                        if "glitchkind" in bases[item][attr]:
                            bases[item][attr].pop("glitchkind")
                        print("What kinds should this item be? None to go next.")
                        print(f"Current Kinds: {bases[item][attr]}")
                    if attr == "slots":
                        print("What slots should this item be equippable in? None to go next.")
                        print(f"Current slots: {bases[item][attr]}")
                    if attr == "tags":
                        print("What tags should this item have? None to go next.")
                        print(f"Current slots: {bases[item][attr]}")
                    if attr == "cost":
                        print("What grist should this item cost? None to go next.")
                        print(f"Current grists: {bases[item][attr]}")
                    if attr == "description":
                        print("What should the description be?")
                    if attr == "onhiteffect":
                        print("What on hit effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "weareffect":
                        print("What wear effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "consumeeffect":
                        print("What consume effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "secreteffect":
                        print("What secret effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "secretadjectives":
                        if "glitched" in bases[item][attr]:
                            bases[item][attr].remove("glitched")
                        print("What secret adjectives should it have? No input for none.")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr != "base":
                        x = input("* ")
                    else:
                        print("base detected")
                        bases[item][attr] = True
                        x = ""
                        break
                    if x == "save":
                        writejson(bases, "bases")
                        print("Saved the item.")
                    if x != "" and x[0] == ">":
                        next = True
                        goto = x[1:]
                        break
                    if attr == "description":
                        bases[item][attr] = x
                        break
                    if attr == "secretadjectives":
                        if x != "":
                            bases[item][attr].append(x)
                        else:
                            break
                    if attr in ["power", "weight", "size"]:
                        bases[item][attr] = int(x)
                        break
                    if attr in ["dicemin", "dicemax"]:
                        bases[item][attr] = float(x)
                        break
                    if attr in ["onhiteffect", "weareffect", "consumeeffect", "secreteffect"]:
                        if x != "":
                            print("What power should the effect be at?")
                            y = input("* ")
                            power = float(y)
                            print("What adjective/base should the effect be inherited with? No input for none.")
                            z = input("* ")
                            if z != "":
                                bases[item][attr][x] = [power, str(z)]
                            else:
                                bases[item][attr][x] = [power]
                        else:
                            break
                    if attr in ["kinds", "slots", "tags"]:
                        if x != "":
                            print(f"What rate should that be inherited at?")
                            y = input("* ")
                            rate = float(y)
                            print(f"What adjective/base should that be inherited with? No input for none.")
                            z = input("* ")
                            if z != "":
                                bases[item][attr][x] = [rate, str(z)]
                            else:
                                bases[item][attr][x] = [rate]
                        else:
                            break
                    if attr == "cost":
                        if x != "":
                            print(f"What should the cost ratio be?")
                            y = input("* ")
                            cost = float(y)
                            bases[item][attr][x] = y
                        else:
                            break
                except (TypeError, ValueError) as e:
                    print(f"excepted error {e}")
            if next == True:
                break
    writejson(bases, "bases")