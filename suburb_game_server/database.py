import time

from copy import deepcopy
import util

databasedir = util.homedir + "\\database"

memory_sessions = util.readjson({}, "sessions", databasedir)
memory_players = util.readjson({}, "players", databasedir)
memory_npcs = util.readjson({}, "npcs", databasedir)
memory_items = util.readjson({}, "items", databasedir)
memory_instances = util.readjson({}, "instances", databasedir)
memory_users = util.readjson({}, "users", databasedir)
assert memory_sessions is not None
assert memory_players is not None
assert memory_npcs is not None
assert memory_items is not None
assert memory_instances is not None
assert memory_users is not None


def save_databases():
    util.writejson(deepcopy(memory_sessions), "sessions", databasedir)
    util.writejson(deepcopy(memory_players), "players", databasedir)
    util.writejson(deepcopy(memory_npcs), "npcs", databasedir)
    util.writejson(deepcopy(memory_items), "items", databasedir)
    util.writejson(deepcopy(memory_instances), "instances", databasedir)
    util.writejson(deepcopy(memory_users), "users", databasedir)
