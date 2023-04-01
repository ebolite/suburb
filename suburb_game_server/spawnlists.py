from typing import Optional

import config
import util
import random

tile_spawns = []
interests = []
COMMON_WEIGHT = 65
UNCOMMON_WEIGHT = 27
RARE_WEIGHT = 7
EXOTIC_WEIGHT = 1

class SpawnList():
    def __init__(self, name):
        self.__dict__["name"] = name
        if name not in util.spawnlists:
            print(name)
            raise AssertionError
        
    def __getattr__(self, attr):
        return util.spawnlists[self.__dict__["name"]][attr]
    
    def __setattr__(self, attr: str, value) -> None:
        util.spawnlists[self.__dict__["name"]][attr] = value
        
    @classmethod
    def find_spawnlist(cls, name: str) -> Optional["SpawnList"]:
        if name in util.spawnlists: return SpawnList(name)
        else: return None

    @classmethod
    def create_spawnlist(cls, name: str) -> Optional["SpawnList"]:
        if name in util.spawnlists: return None
        util.spawnlists[name] = {}
        spawnlist = cls(name)
        spawnlist.setup_defaults(name)
        return spawnlist

    def setup_defaults(self, name: str):
        self.spawnlist_type = "tile" # tile or interest
        self.always = []
        self.common = []
        self.uncommon = []
        self.rare = []
        self.exotic = []

    def set_loot(self, always=[], common=[], uncommon=[], rare=[], exotic=[]):
        self.always += always
        self.common += common
        self.uncommon += uncommon
        self.rare += rare
        self.exotic += exotic

    def get_loot_list(self, min_items=2, max_items=6) -> list[str]:
        output = []
        for item_name in self.always:
            output.append(item_name)
        possible_rarities = []
        rarities_weights = []
        if self.common:
            possible_rarities.append("common")
            rarities_weights.append(COMMON_WEIGHT)
        if self.uncommon:
            possible_rarities.append("uncommon")
            rarities_weights.append(UNCOMMON_WEIGHT)
        if self.rare:
            possible_rarities.append("rare")
            rarities_weights.append(RARE_WEIGHT)
        if self.exotic:
            possible_rarities.append("exotic")
            rarities_weights.append(EXOTIC_WEIGHT)
        num_items = random.randint(min_items, max_items)
        if num_items == 0: return output
        rarities = random.choices(possible_rarities, weights=rarities_weights, k=num_items)
        for rarity in rarities:
            match rarity:
                case "common":
                    output.append(random.choice(self.common))
                case "uncommon":
                    output.append(random.choice(self.uncommon))
                case "rare":
                    output.append(random.choice(self.rare))
                case "exotic":
                    output.append(random.choice(self.exotic))
        return output
    
if __name__ == "__main__":
    for tile_name in config.itemcategoryrarities:
        new_spawnlist = SpawnList.create_spawnlist(tile_name)
        if new_spawnlist is not None:
            rarities: dict = config.itemcategoryrarities[tile_name]
            always = rarities.get("always", [])
            common = rarities.get("common", [])
            uncommon = rarities.get("uncommon", [])
            rare = rarities.get("rare", [])
            exotic = rarities.get("exotic", [])
            new_spawnlist.set_loot(always, common, uncommon, rare, exotic)
    for interest_name in config.interests:
        interest_spawnlist = SpawnList(interest_name)
        interest_spawnlist.spawnlist_type = "interest"
    util.writejson(util.spawnlists, "spawnlists")