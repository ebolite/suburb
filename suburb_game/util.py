import os
import json

VERSION = "v1.8.3-alpha"
homedir = os.getcwd()
subdirectories = next(os.walk("."))[1]
if "suburb_game" in subdirectories:  # if this is being run in vscode lol
    homedir += "/suburb_game"

import client


def writejson(obj=None, fn=None):
    if not os.path.exists(f"{homedir}/json"):
        os.makedirs(f"{homedir}/json")
        print(f"Created {homedir}/json")
    os.chdir(f"{homedir}/json")
    if fn != None:
        with open(f"{fn}.json", "w") as f:
            if obj == None:
                obj = eval(f"{fn}")
            if obj != None:
                if obj != {} and obj != None:
                    data = json.dump(obj, f, indent=4)
                    f = data
    os.chdir(homedir)


def readjson(obj, filename):
    try:
        os.chdir(f"{homedir}/json")
        with open(f"{filename}.json", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"UNABLE TO READ JSON {filename}")
                writejson(obj, f"{homedir}/json/failed/{filename}")
                data = {}
            os.chdir(homedir)
            return data
    except FileNotFoundError:
        print(
            f"File not found when reading json: '{filename}.json'. Overwriting with {obj}."
        )
        writejson(obj, filename)
        os.chdir(homedir)
        return obj


def filter_item_name(name: str) -> str:
    return name.replace("+", " ")


def shorten_item_name(old_name: str) -> str:
    words = old_name.replace("+", " ")
    if len(words) <= 2:
        return words
    words = words.replace("-", " ").split(" ")
    base = words.pop()
    text = ""
    for word in words:
        text += f"{word[0]}."
    new_name = f"{text} {base}"
    return new_name


def captchalogue_instance(instance_name: str, modus_name: str):
    if "success" in client.requestplus(
        "captchalogue", {"instance_name": instance_name, "modus_name": modus_name}
    ):
        return True
    else:
        return False


if not os.path.exists(f"{homedir}/sprites/captchas"):
    os.makedirs(f"{homedir}/sprites/captchas")
    print(f"Created {homedir}/sprites/captchas")

player_logs = {}
player_logs = readjson(player_logs, "player_logs")

log_window = None


def log(message: str):
    if client.dic["session_name"] not in player_logs:
        player_logs[client.dic["session_name"]] = []
    logs = player_logs[client.dic["session_name"]]
    if not message:
        return
    lines = split_into_max_length_lines(message, 45)
    for line in lines:
        logs.append(line)
    if log_window is not None:
        log_window.update_logs()
    writejson(player_logs, "player_logs")


def current_log() -> list[str]:
    if client.dic["session_name"] not in player_logs:
        player_logs[client.dic["session_name"]] = []
    return player_logs[client.dic["session_name"]]


def split_into_max_length_lines(text: str, max_length: int) -> list[str]:
    lines = [[]]
    index = 0
    for word in text.split(" "):
        if len(" ".join(lines[index])) + len(word) > max_length:
            index += 1
            lines.append([])
        lines[index].append(word)
    joined_lines: list[str] = [" ".join(line) for line in lines]
    return joined_lines


sylladexes = {}
sylladexes = readjson(sylladexes, "sylladexes")

last_client_data = {}
last_client_data = readjson(last_client_data, "last_client_data")

saved_items = {}
saved_items = readjson(saved_items, "saved_items")

saved_maps = {}
saved_maps = readjson(saved_maps, "saved_maps")

config = {}
config = readjson(config, "config")