import config
import random
from copy import deepcopy

import spawnlists
import util
import sessions
import alchemy

tiles: dict[str, "Tile"] = {}  # tile_char: Tile
# tiles "revise"able by sburb servers
server_tiles: dict[str, int] = {}  # tile_char: build_cost

anywhere_rare = ["empty captchalogue card"]
anywhere_exotic = ["fancy+santa"]


class Tile:
    def __init__(self, tile_char, name):
        self.tile_char = tile_char
        self.name = name
        self.solid = True  # tile can support other tiles
        self.supported = False  # tile can only be placed above a solid tile
        self.below_allowed = (
            True  # can be placed below itself even if it would be otherwise unsupported
        )
        self.impassible = False  # cannot be moved into or fallen through
        self.infallible = False  # can be moved into, but not fallen through
        self.ramp = False  # tiles that can take you up and to the side
        self.ramp_direction = "not a ramp bro"  # for ramps, the direction they will send you upon falling into them
        self.stair = False  # tiles that allow you to go up and down, but prevent you from falling through
        self.automove = False  # tiles that, when moving into, will cause you to continue to move through a chain of themself without stopping
        self.door = False
        self.forbidden = False  # tiles that cannot be placed or modified by servers
        self.special = False  # tiles that are otherwise special for some reason
        self.debug = False  # cannot be placed by map editor
        self.ban_npc_spawn = False
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
        if self.impassible:
            return False
        if self.ramp:
            return False
        if self.automove:
            return False
        return True

    def is_special(self) -> bool:
        if self.impassible:
            return True
        if self.infallible:
            return True
        if self.ramp:
            return True
        if self.stair:
            return True
        if self.forbidden:
            return True
        if self.special:
            return True
        return False

    def get_loot_list(self, room: "sessions.Room") -> list[str]:
        spawnlist = spawnlists.SpawnList.find_spawnlist(self.name)
        if spawnlist is None:
            return []
        else:
            loot = spawnlist.get_loot_list()
            return loot


def get_tile(tile_char) -> Tile:
    return tiles[tile_char]


debug_tile = Tile("*", "debug tile")
debug_tile.forbidden = True
debug_tile.solid = False
debug_tile.debug = True

out_of_bounds = Tile("?", "out of bounds")
out_of_bounds.forbidden = True
out_of_bounds.impassible = True
out_of_bounds.solid = False
out_of_bounds.debug = True

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

# cross_ramp = Tile("X", "cross ramp")
# cross_ramp.ramp = True
# cross_ramp.ramp_direction = "both"
# cross_ramp.infallible = True
# cross_ramp.build_cost = 50
# # todo: make cross-ramp tile
# cross_ramp.forbidden = True

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
girder.ban_npc_spawn = True

pillar = Tile("I", "pillar")
pillar.infallible = True
pillar.ban_npc_spawn = True

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

laundry_room = Tile("l", "laundry room")

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


class LootTile(Tile):
    def __init__(self, tile_char, name, loot_type: str):
        super().__init__(tile_char, name)
        self.loot_type = loot_type

    def get_loot_list(self, room: "sessions.Room") -> list[str]:
        out = []
        out += self.special_loot(room)
        possible_items = list(util.bases.keys())
        num_random_bases = random.randint(2, 6)
        for i in range(num_random_bases):
            item = alchemy.Item(random.choice(possible_items))
            while item.forbiddencode:
                item = alchemy.Item(random.choice(possible_items))
            out.append(item.name)
        # 1-3 grystals
        num_grystals = random.randint(1, 3)
        possible_grist_types = self.get_possible_grist_types(room)
        for i in range(num_grystals):
            grist_type = random.choice(possible_grist_types)
            grystal_type = random.choice(self.get_possible_grystal_types())
            out.append(f"{grystal_type} {grist_type} grystal")
        return out

    def get_random_base_in_kinds(self, valid_kinds: list[str]):
        shuffled_bases = list(util.bases.keys())
        random.shuffle(shuffled_bases)
        for item_name in shuffled_bases:
            for kind in util.bases[item_name]["kinds"]:
                if kind in valid_kinds:
                    return item_name
        else:
            return None

    def special_loot(self, room: "sessions.Room") -> list[str]:
        # todo: not always generate special loot
        loot = []
        SPECIAL_RANGES = {
            "stash": (-10, 1),
            "trove": (-4, 1),
            "bounty": (0, 2),
        }
        min_specials, max_specials = SPECIAL_RANGES[self.loot_type]
        min_specials += room.map.height
        min_specials = min(min_specials, max_specials)
        num_specials = random.randint(min_specials, max_specials)
        if num_specials <= 0 or room.overmap.land is None:
            return []
        assert room.overmap.land.player is not None
        aspect = room.overmap.land.player.aspect
        bases = list(util.bases.keys())
        for i in range(num_specials):
            # 25% chance to be of a kind someone in the session has
            if random.random() < 0.25:
                session_kinds = []
                for player_name in room.overmap.session.starting_players:
                    player = sessions.Player(player_name)
                    subplayer = player.sub_players_list[0]
                    for kind in subplayer.strife_portfolio:
                        if kind not in session_kinds:
                            session_kinds.append(kind)
                base_item_name = self.get_random_base_in_kinds(session_kinds)
                if base_item_name is None:
                    base_item_name = "perfectly+generic object"
            else:
                base_item_name = random.choice(bases)
                while alchemy.Item(base_item_name).forbiddencode:
                    base_item_name = random.choice(bases)
            if random.random() > 0.5:
                operation = "||"
            else:
                operation = "&&"
            new_item_name = alchemy.alchemize(
                base_item_name, f"pure {aspect}", operation
            )
            loot.append(new_item_name)
        return loot

    def get_possible_grystal_types(self) -> list[str]:
        if self.loot_type == "bounty":
            return ["rough", "fine", "choice"]
        elif self.loot_type == "trove":
            return ["rough", "fine"]
        else:
            return ["rough"]

    def get_possible_grist_types(self, room: "sessions.Room") -> list[str]:
        max_tier = room.map.height + 3
        max_tier = min(max_tier, 9)
        possible_grist_types = [
            grist_name
            for grist_name in config.grists
            if config.grists[grist_name]["tier"] <= max_tier
        ]
        if room.overmap.land is not None:
            possible_grist_types += config.gristcategories[
                room.overmap.land.gristcategory
            ]
        return possible_grist_types


stash = LootTile("%", "stash", "stash")
stash.forbidden = True

trove = LootTile("&", "trove", "trove")
trove.forbidden = True

bounty = LootTile("$", "bounty", "bounty")
bounty.forbidden = True

nest = LootTile("n", "nest", "stash")
nest.forbidden = True

stalactite = Tile("'", "stalactite")
stalactite.forbidden = True
stalactite.solid = True
stalactite.impassible = True

return_gate = Tile("0", "return gate")
return_gate.forbidden = True
return_gate.special = True
return_gate.solid = False
return_gate.ban_npc_spawn = True

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
    ...
