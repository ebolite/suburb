import os
VERSION = "0.0.3"
homedir = os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game" in subdirectories: # if this is being run in vscode lol
    homedir += "\\suburb_game"

def filter_item_name(name: str) -> str:
    return name.replace("+", " ")