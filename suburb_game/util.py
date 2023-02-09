import os
import json
VERSION = "PRE-ALPHA 0.7.4"
homedir = os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game" in subdirectories: # if this is being run in vscode lol
    homedir += "\\suburb_game"

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

def filter_item_name(name: str) -> str:
    return name.replace("+", " ")