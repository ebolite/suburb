import os
import json
import random
import time
from pandas import DataFrame
from copy import deepcopy
import pymongo
from pymongo import MongoClient

import binaryoperations

homedir =  os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game_server" in subdirectories: # if this is being run in vscode lol
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

def readjson(obj, filename, dir=f"{homedir}\\json"):
    try:
        with open(f"{dir}/{filename}.json", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"UNABLE TO READ JSON {filename}")
                writejson(obj, filename, dir)
                data = {}
            return data
    except FileNotFoundError:
        print(f"File not found when reading json: '{filename}.json'. Overwriting with {obj}.")
        writejson(obj, filename, dir)
        return obj
    
serversettings = {
    "ip": "",
    "port": 0,
    "path_to_cert": "",
    "path_to_key": "",
    "db_connection_string": ""
}
serversettings = readjson(serversettings, "serversettings", homedir)

ip = serversettings["ip"]
port = serversettings["port"]
path_to_cert = serversettings["path_to_cert"]
path_to_key = serversettings["path_to_key"]
db_connection_string = serversettings["db_connection_string"]

if not path_to_cert or not path_to_key:
    print("serversettings.json must be filled out.")
    print("Please specify an ip address and port to host the server on.")
    print("Please specify a location for the cert and key of your server.")
    print("Please specify a connection string for MongoDB.")
    raise AssertionError

bases: dict[str, dict] = {}
bases: dict[str, dict] = readjson(bases, "bases")

for base_name, base_dict in bases.items():
    words = base_name.split(" ")
    base_name = words.pop()
    if len(words) == 0: adjectives = []
    else: adjectives = words
    base_dict["adjectives"] = adjectives
    if "kinds" in base_dict:
        base_dict["kinds"] = [kind_name for kind_name in base_dict["kinds"]]
writejson(bases, "bases")

base_names_adjectives = {}
for base_name, base_dict in bases.items():
    base_names_adjectives[base_name] = base_dict["adjectives"] + base_dict["secretadjectives"]
writejson(base_names_adjectives, "base_names_adjectives")

db_client = MongoClient(db_connection_string)

db_suburb = db_client["suburb"]

db_sessions = db_suburb["sessions"]
memory_sessions = {}

db_players = db_suburb["players"]
memory_players = {}

db_npcs = db_suburb["npcs"]
memory_npcs = {item_dict["_id"]:item_dict for item_dict in db_npcs.find({})}

db_items = db_suburb["items"]
memory_items = {item_dict["_id"]:item_dict for item_dict in db_items.find({})}

db_instances = db_suburb["instances"]
memory_instances = {instance_dict["_id"]:instance_dict for instance_dict in db_instances.find({})}

codes = {} # key: item code value: item name
codes = readjson(codes, "codes")

kinds: list[str] = []
for base in bases:
    for kind in bases[base]["kinds"]:
        if kind not in kinds:
            kinds.append(kind)
print(sorted(kinds))

def saveall():
    t = time.time()
    print("Saving...")
    def callback(session):
        sessions = session.client["suburb"]["sessions"]
        session_data = {item_dict["_id"]:item_dict for item_dict in sessions.find({})}
        players = session.client["suburb"]["players"]
        players_data = {item_dict["_id"]:item_dict for item_dict in players.find({})}
        npcs = session.client["suburb"]["npcs"]
        npcs_data = {item_dict["_id"]:item_dict for item_dict in npcs.find({})}
        items = session.client["suburb"]["items"]
        items_data = {item_dict["_id"]:item_dict for item_dict in items.find({})}
        instances = session.client["suburb"]["instances"]
        instances_data = {item_dict["_id"]:item_dict for item_dict in instances.find({})}
        global memory_sessions
        for session_name, session_dict in memory_sessions.copy().items():
            sessions.update_one({"_id": session_name}, {"$set": session_dict}, upsert=True, session=session)
        memory_sessions = {}

        global memory_players
        for player_name, player_dict in memory_players.copy().items():
            players.update_one({"_id": player_name}, {"$set": player_dict}, upsert=True, session=session)
        memory_players = {}

        global memory_npcs
        npcs_to_insert = []
        for npc_name, npc_dict in memory_npcs.copy().items():
            if npc_name not in npcs_data: npcs_to_insert.append(npc_dict)
            elif npc_dict != npcs_data[npc_name]:
                npcs.update_one({"_id": npc_name}, {"$set": npc_dict}, upsert=True, session=session)
        if npcs_to_insert: npcs.insert_many(npcs_to_insert, session=session)

        global memory_items
        items_to_insert = []
        for item_name, item_dict in memory_items.copy().items():
            if item_name not in items_data: items_to_insert.append(item_dict)
            elif item_dict != items_data[item_name]:
                items.update_one({"_id": item_name}, {"$set": item_dict}, upsert=True, session=session)
        if items_to_insert: items.insert_many(items_to_insert, session=session)

        global memory_instances
        instances_to_insert = []
        for instance_name, instance_dict in memory_instances.copy().items():
            if instance_name not in instances_data: instances_to_insert.append(instance_dict)
            elif instance_dict != instances_data[instance_name]:
                instances.update_one({"_id": instance_name}, {"$set": instance_dict}, upsert=True, session=session)
        if instances_to_insert: instances.insert_many(instances_to_insert, session=session)
        inserted = npcs_to_insert+items_to_insert+instances_to_insert
        if inserted: print(f"Inserted {len(inserted)}")
    with db_client.start_session() as session:
        session.with_transaction(callback)
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

if __name__ == "__main__": # if this file is being run, run the json editor
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