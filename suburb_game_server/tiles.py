tiles = {}      # tile: Tile

class Tile():
    def __init__(self, tile_char, name):
        self.tile_char = tile_char
        self.name = name
        self.impassible = False     # cannot be moved into or fallen through
        self.infallible = False     # can be moved into, but not fallen through
        self.ramp = False       # tiles that can take you up and to the side
        self.ramp_direction = "not a ramp bro"      # for ramps, the direction they will send you upon falling into them
        self.stair = False      # tiles that allow you to go up and down, but prevent you from falling through
        self.automove = False       # tiles that, when moving into, will cause you to continue to move through a chain of themself without stopping
        self.door = False
        self.forbidden = False      # tiles that cannot be placed or modified by servers
        self.special = False        # tiles that are otherwise special for some reason
        tiles[tile_char] = self

    def is_special(self) -> bool:
        if self.impassible: return True
        if self.infallible: return True
        if self.ramp: return True
        if self.stair: return True
        if self.forbidden: return True
        if self.special: return True
        return False
    
debug_tile = Tile("*", "debug tile")
debug_tile.forbidden = True

out_of_bounds = Tile("?", "out of bounds")
out_of_bounds.forbidden = True
out_of_bounds.impassible = True

air = Tile(".", "air")

wall = Tile("|", "wall")
wall.impassible = True

terrain = Tile("#", "terrain")
terrain.impassible = True

junction = Tile(";", "junction")

# floor = Tile("=", "floor")
# floor.impassible = True

left_ramp = Tile("\\", "left ramp")
left_ramp.ramp = True
left_ramp.ramp_direction = "left"

right_ramp = Tile("/", "right ramp")
right_ramp.ramp = True
right_ramp.ramp_direction = "right"

girder = Tile("+", "girder")
girder.infallible = True

cross_ramp = Tile("X", "cross ramp")
cross_ramp.ramp = True
cross_ramp.ramp_direction = "both"
cross_ramp.infallible = True

stairs = Tile("^", "stairs")
stairs.stair = True
stairs.infallible = True

stairwell = Tile("-", "stairwell")
stairwell.stair = True

elevator_shaft = Tile("v", "elevator shaft")
elevator_shaft.stair = True
elevator_shaft.automove = True

elevator = Tile("e", "elevator")

left_door = Tile("<", "left door")
left_door.door = True

right_door = Tile(">", "right door")
right_door.door = True

left_window = Tile("[", "left window")

right_window = Tile("]", "right window")

bedroom = Tile("B", "bedroom")

bathroom = Tile("b", "bathroom")

foyer = Tile("F", "foyer")

living_room = Tile("L", "living room")

laundry_room = Tile("l", "laundry_room")

kitchen = Tile("K", "kitchen")

garage = Tile("G", "garage")

cellar = Tile("C", "cellar")

dining_room = Tile("D", "dining room")

pillar = Tile("I", "pillar")

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

stalagtite = Tile("'", "stalagtite")

return_gate = Tile("0", "return gate")
return_gate.forbidden = True
return_gate.special = True

first_gate = Tile("1", "first gate")
first_gate.forbidden = True
first_gate.special = True

second_gate = Tile("2", "second gate")
second_gate.forbidden = True
second_gate.special = True

third_gate = Tile("3", "third gate")
third_gate.forbidden = True
third_gate.special = True

fourth_gate = Tile("4", "fourth gate")
fourth_gate.forbidden = True
fourth_gate.special = True

fifth_gate = Tile("5", "fifth gate")
fifth_gate.forbidden = True
fifth_gate.special = True

sixth_gate = Tile("6", "sixth gate")
sixth_gate.forbidden = True
sixth_gate.special = True

seventh_gate = Tile("7", "seventh gate")
seventh_gate.forbidden = True
seventh_gate.special = True

