import os
import pickle

import client
VERSION = "PRE-ALPHA 0.7.5"
homedir = os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game" in subdirectories: # if this is being run in vscode lol
    homedir += "\\suburb_game"

def writepickle(obj=None, fn=None):
    if not os.path.exists(f"{homedir}\\pickle"):
        os.makedirs(f"{homedir}\\pickle")
        print(f"Created {homedir}\\pickle")
    os.chdir(f"{homedir}\\pickle")
    if fn != None:
        with open(f"{fn}.pickle", "wb") as f:
            if obj == None:
                obj = eval(f"{fn}")
            if obj != None:
                if obj != {} and obj != None:
                    data = pickle.dump(obj, f)
                    f = data

def readpickle(obj, filename):
    try:
        os.chdir(f"{homedir}\\pickle")
        with open(f"{filename}.pickle", "rb") as f:
            try:
                data = pickle.load(f)
                return data
            except EOFError:
                print(f"File failed to read: '{filename}.pickle'. Overwriting with {obj}.")
                return obj
    except FileNotFoundError:
        print(f"File not found when reading pickle: '{filename}.pickle'. Overwriting with {obj}.")
        writepickle(obj, filename)
        return obj

def filter_item_name(name: str) -> str:
    return name.replace("+", " ")

def captchalogue_instance(instance_name: str, modus_name: str):
    if "success" in client.requestplus("captchalogue", {"instance_name": instance_name, "modus_name": modus_name}): return True
    else: return False

sylladexes = {}
sylladex = readpickle(sylladexes, "sylladexes")