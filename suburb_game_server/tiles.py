import config
import random

import spawnlists

tiles: dict[str, "Tile"] = {}      # tile_char: Tile
# tiles "revise"able by sburb servers
server_tiles: dict[str, int] = {}       # tile_char: build_cost

anywhere_rare = ["empty captchalogue card"]
anywhere_exotic = ["fancy+santa"]

class Tile():
    def __init__(self, tile_char, name):
        self.tile_char = tile_char
        self.name = name
        self.solid = True       # tile can support other tiles
        self.supported = False      # tile can only be placed above a solid tile
        self.below_allowed = True # can be placed below itself even if it would be otherwise unsupported
        self.impassible = False     # cannot be moved into or fallen through
        self.infallible = False     # can be moved into, but not fallen through
        self.ramp = False       # tiles that can take you up and to the side
        self.ramp_direction = "not a ramp bro"      # for ramps, the direction they will send you upon falling into them
        self.stair = False      # tiles that allow you to go up and down, but prevent you from falling through
        self.automove = False       # tiles that, when moving into, will cause you to continue to move through a chain of themself without stopping
        self.door = False
        self.forbidden = False      # tiles that cannot be placed or modified by servers
        self.special = False        # tiles that are otherwise special for some reason
        self.build_cost = 10
        self.always_spawn = []
        self.common_spawn = []
        self.common_weight = 65
        self.uncommon_spawn = []
        self.uncommon_weight = 27
        self.rare_spawn = []
        self.rare_weight = 7
        self.exotic_spawn = []
        self.exotic_weight = 1
        self.loot_range: tuple[int, int] = (2, 6)
        tiles[tile_char] = self

    @property
    def deployable(self) -> bool:
        if self.impassible: return False
        if self.ramp: return False
        if self.automove: return False
        return True

    def is_special(self) -> bool:
        if self.impassible: return True
        if self.infallible: return True
        if self.ramp: return True
        if self.stair: return True
        if self.forbidden: return True
        if self.special: return True
        return False

    def get_loot_list(self) -> list[str]:
        spawnlist = spawnlists.SpawnList.find_spawnlist(self.name)
        if spawnlist is None: return []
        else: 
            loot = spawnlist.get_loot_list()
            return loot

def get_tile(tile_char) -> Tile:
    return tiles[tile_char]

debug_tile = Tile("*", "debug tile")
debug_tile.forbidden = True
debug_tile.solid = False

out_of_bounds = Tile("?", "out of bounds")
out_of_bounds.forbidden = True
out_of_bounds.impassible = True
out_of_bounds.solid = False

air = Tile(".", "air")
air.build_cost = 0
air.solid = False

wall = Tile("|", "wall")
wall.impassible = True

terrain = Tile("#", "terrain")
terrain.impassible = True
terrain.forbidden = True

terrain_change = Tile("_", "terrain_change")
terrain_change.ramp = True
terrain_change.ramp_direction = "both"
terrain_change.forbidden = True

# junction = Tile(";", "junction")

# floor = Tile("=", "floor")
# floor.impassible = True

left_ramp = Tile("\\", "left ramp")
left_ramp.ramp = True
left_ramp.ramp_direction = "left"
left_ramp.build_cost = 50

right_ramp = Tile("/", "right ramp")
right_ramp.ramp = True
right_ramp.ramp_direction = "right"
right_ramp.build_cost = 50

cross_ramp = Tile("X", "cross ramp")
cross_ramp.ramp = True
cross_ramp.ramp_direction = "both"
cross_ramp.infallible = True
cross_ramp.build_cost = 50
# todo: make cross-ramp tile
cross_ramp.forbidden = True

stairs = Tile("^", "stairs")
stairs.stair = True
stairs.infallible = True
stairs.build_cost = 200

stairwell = Tile("-", "stairwell")
stairwell.stair = True
stairwell.build_cost = 200

# ladder = Tile("=", "ladder")
# ladder.stair = True
# ladder.infallible = True
# ladder.build_cost = 200

rope = Tile("i", "rope")
rope.stair = True
rope.infallible = True
rope.build_cost = 150
rope.solid = False
rope.below_allowed = True

elevator_shaft = Tile("v", "elevator shaft")
elevator_shaft.stair = True
elevator_shaft.automove = True
elevator_shaft.infallible = True
elevator_shaft.build_cost = 600

elevator = Tile("e", "elevator")
elevator.stair = True
elevator.build_cost = 200

girder = Tile("+", "girder")
girder.infallible = True

pillar = Tile("I", "pillar")
pillar.infallible = True

left_door = Tile("<", "left door")
left_door.door = True
left_door.supported = True
left_door.build_cost = 2

right_door = Tile(">", "right door")
right_door.door = True
right_door.supported = True
right_door.build_cost = 2

left_window = Tile("[", "left window")
left_window.supported = True
left_window.build_cost = 2

right_window = Tile("]", "right window")
right_window.supported = True
right_window.build_cost = 2

bedroom = Tile("B", "bedroom")

bathroom = Tile("b", "bathroom")

foyer = Tile("F", "foyer")
foyer.stair = True

living_room = Tile("L", "living room")

laundry_room = Tile("l", "laundry_room")

kitchen = Tile("K", "kitchen")

garage = Tile("G", "garage")

cellar = Tile("C", "cellar")

dining_room = Tile("D", "dining room")

attic = Tile("A", "attic")

office = Tile("O", "office")

workout_room = Tile("W", "workout room")

game_room = Tile("g", "game room")

studio_apartment = Tile("S", "studio apartment")

security = Tile("s", "security")

stash = Tile("$", "stash")
stash.forbidden = True

nest = Tile("n", "nest")
nest.forbidden = True

stalactite = Tile("'", "stalactite")
stalactite.forbidden = True
stalactite.solid = False

return_gate = Tile("0", "return gate")
return_gate.forbidden = True
return_gate.special = True
return_gate.solid = False

first_gate = Tile("1", "first gate")
first_gate.forbidden = True
first_gate.special = True
first_gate.solid = False

second_gate = Tile("2", "second gate")
second_gate.forbidden = True
second_gate.special = True
second_gate.solid = False

third_gate = Tile("3", "third gate")
third_gate.forbidden = True
third_gate.special = True
third_gate.solid = False

fourth_gate = Tile("4", "fourth gate")
fourth_gate.forbidden = True
fourth_gate.special = True
fourth_gate.solid = False

fifth_gate = Tile("5", "fifth gate")
fifth_gate.forbidden = True
fifth_gate.special = True
fifth_gate.solid = False

sixth_gate = Tile("6", "sixth gate")
sixth_gate.forbidden = True
sixth_gate.special = True
sixth_gate.solid = False

seventh_gate = Tile("7", "seventh gate")
seventh_gate.forbidden = True
seventh_gate.special = True
seventh_gate.solid = False

for tile_name, tile in tiles.items():
    if not tile.forbidden:
        server_tiles[tile.tile_char] = tile.build_cost

if __name__ == "__main__":
    for tile_char in tiles:
        tile = tiles[tile_char]
        loot_list = tile.get_loot_list()
        if not loot_list: continue
        print(f"{tile.name} loot: {' - '.join(loot_list)}")