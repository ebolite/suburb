import random
from typing import Optional, Union
from string import ascii_letters
from copy import deepcopy
import difflib
import time

import util
import binaryoperations
import adjectiveorder
import sessions
import stateseffects
import database
import config
import skills

COMPOUND_NAME_CHANCE = 0.2 # chance for having compound names in && operations
INHERITANCE_BONUS_MULT = 1.25 # bonus for simply alchemizing items
INHERITANCE_MALUS_MULT = 0.75 # malus for being above softcap

class Components():
    def __init__(self, name: str):
        # names look like "(((baseball bat&&sledge hammer)&&(piano wire||ring))||shotgun)" so we have to find the midpoint for the components
        # if at any point all parentheses are closed (ignoring the first one), we are at the midpoint
        self.name = name
        components_name = name[1:]
        components_name = components_name[:-1]
        parentheses = 0
        operation = ""
        component_1 = ""
        component_2 = ""
        if "(" and ")" not in components_name:
            if "&&" in components_name:
                self.operation = "&&"
                components = components_name.split("&&")
            elif "||" in components_name:
                self.operation = "||"
                components = components_name.split("||")
            else:
                self.component_1 = None
                self.component_2 = None
                return
            self.component_1 = components[0]
            self.component_2 = components[1]
            return
        for index, char in enumerate(components_name):
            if char == "(": parentheses += 1
            if char == ")": parentheses -= 1
            component_1 += char
            if parentheses == 0:
                operation = components_name[index+1:][:2] # get next 2 characters
                component_2 = components_name[index+3:] # everything after that
                break
        self.component_1: Optional[str] = component_1
        self.component_2: Optional[str] = component_2
        self.operation: str = operation

    def get_all_components(self) -> list[str]:
        components_list = []
        if self.component_1 is None or self.component_2 is None: return []
        if self.component_1 in util.bases: components_list.append(self.component_1)
        else: components_list += Components(self.component_1).get_all_components()
        if self.component_2 in util.bases: components_list.append(self.component_2)
        else: components_list += Components(self.component_2).get_all_components()
        return components_list

class BaseStatistics():
    def __init__(self, base_name: str):
        descriptors = base_name.split(" ") # " " is a separator for descriptors in base name
        self.descriptors: list = list(descriptors)
        self.base: str = descriptors.pop() # last descriptor is the base
        self.adjectives: list = list(set(descriptors)) # everything else are adjectives, remove duplicates
        properties = deepcopy(util.bases[base_name])
        self.display_name = properties["display_name"]
        self.secretadjectives: list[str] = properties["secretadjectives"]
        self.power: int = properties["power"]
        self.inheritpower: int = properties["inheritpower"]
        self.size: int = properties["size"]
        self.kinds: list[str] = properties["kinds"]
        self.wearable: bool = properties["wearable"]
        self.description: str = properties["description"]
        self.cost: dict = properties["cost"]
        self.use: list[str] = properties["use"]
        self.onhit_states: dict = properties["onhit_states"]
        self.wear_states: dict = properties["wear_states"]
        self.consume_states: dict = properties["consume_states"]
        self.secret_states: dict = properties["secret_states"]
        self.forbiddencode: bool = properties["forbiddencode"]
        self.prototype_name: Optional[str] = properties["prototype_name"]
        self.creator: Optional[str] = properties["creator"]

# todo: captchalogue code inheritance
class InheritedStatistics():
    def __init__(self, component_1: "Item", component_2: "Item", operation: str, guarantee_first_base=False):
        self.name = f"({component_1.name}{operation}{component_2.name})" # for seed
        self.component_1: Item = component_1
        self.component_2: Item = component_2
        self.operation = operation
        self.guarantee_first_base=guarantee_first_base
        self.base, self.adjectives, self.merged_bases, self.secretadjectives = self.get_descriptors()
        self.descriptors = self.adjectives + [self.base]
        self.forbiddencode = False
        self.prototype_name = None
        self.description = None
        self.creator = None
        self.display_name = None
        self.all_components = Components(self.name).get_all_components()
        self.gen_statistics()

    # how many unique items there are, multiple counts means negative entropy means bad
    @property
    def entropy(self) -> float:
        e = 0
        for component in set(self.all_components):
            if self.all_components.count(component) > 1:
                e -= 0.5
            else:
                e += 0.1
        return e
    
    @property
    def entropy_mult(self) -> float:
        if self.entropy >= 0: return 1 + self.entropy
        else: return 1/-(self.entropy+1)

    def get_descriptors(self, guaranteed_compound_name = False, depth = 0) -> tuple[str, list, list, list]:
        required_inheritors = []
        base = ""
        adjectives: list[str] = []
        merged_bases = []
        secretadjectives = []
        if len(self.component_1.descriptors) == 1: required_inheritors.append(self.component_1.descriptors[0])
        if len(self.component_2.descriptors) == 1: required_inheritors.append(self.component_2.descriptors[0])
        inheritable_bases = [self.component_1.base, self.component_2.base]
        if self.operation == "&&": # && has compound names sometimes
            random.seed(self.name+"compound_chance"+str(depth))
            if random.random() < COMPOUND_NAME_CHANCE or guaranteed_compound_name:
                merged_bases = list(inheritable_bases)
                inheritable_bases = []
                if self.component_1.base in required_inheritors: required_inheritors.remove(self.component_1.base)
                if self.component_2.base in required_inheritors: required_inheritors.remove(self.component_2.base)
                random.seed(self.name+"compound_choice"+str(depth))
                if random.random() < 0.5: inheritable_bases.append(f"{self.component_1.base}-{self.component_2.base}")
                else: inheritable_bases.append(f"{self.component_2.base}-{self.component_1.base}")
        inheritable_adjectives = self.component_1.adjectives + self.component_2.adjectives + self.component_1.secretadjectives + self.component_2.secretadjectives
        if self.guarantee_first_base:
            base = self.component_1.base
        else:
            random.seed(self.name+"base"+str(depth))
            base = random.choice(inheritable_bases)
        if base in required_inheritors: required_inheritors.remove(base)
        if base in inheritable_bases: inheritable_bases.remove(base)
        if len(inheritable_adjectives) < 1:
            inheritable_adjectives += inheritable_bases
        random.seed(self.name+"shuffle"+str(depth))
        inheritable_adjectives = list(set(inheritable_adjectives)) # remove duplicates
        random.shuffle(inheritable_adjectives)
        for adj in inheritable_adjectives:
            inherit_chance = 1 - (len(adjectives) / (((len(self.component_1.descriptors) + len(self.component_2.descriptors)) / 2)+1))
            inherit_chance -= (0.15 * len(adjectives)) # additional flat chance decrease based on how many adjectives it has already
            if adj in required_inheritors:
                required_inheritors.remove(adj)
                adjectives.append(adj)
                continue
            random.seed(self.name+"inherit"+adj+str(depth))
            if random.random() < inherit_chance:
                adjectives.append(adj)
        # secret adjectives
        secretadjectives = self.component_1.secretadjectives + self.component_2.secretadjectives
        for descriptor in [base] + adjectives:
            if descriptor in secretadjectives:
                secretadjectives.remove(descriptor)
        for descriptor in inheritable_adjectives: # unused adjectives have a 50% chance to become secrets
            if descriptor not in [base] + adjectives and descriptor != base:
                random.seed(self.name+descriptor+"secret")
                if random.random() < 0.5: secretadjectives.append(descriptor)
        # sort adjectives by englishness
        adjectives = adjectiveorder.sort_by_adjectives(adjectives)
        # check if this has the exact same name as one of its components
        new_name = adjectives+[base]
        component_1_name = self.component_1.adjectives+[self.component_1.base]
        component_2_name = self.component_2.adjectives+[self.component_2.base]
        if new_name == component_1_name or new_name == component_2_name and depth < 50:
            base, adjectives, merged_bases, secretadjectives = self.get_descriptors(depth=depth+1)
        # check if AND is different from OR, if they are the same, guarantee a compound base
        if self.operation == "&&" and not self.guarantee_first_base: # don't check this if first base is guaranteed
            or_object = InheritedStatistics(self.component_1, self.component_2, "||")
            adjectives_set = set(adjectives)
            or_adjectives_set = set(or_object.adjectives)
            if (base == or_object.base and 
                (adjectives_set.issubset(or_adjectives_set) or or_adjectives_set.issubset(adjectives_set))): # convert to set so names aren't just the same thing in different order
                base, adjectives, merged_bases, secretadjectives = self.get_descriptors(guaranteed_compound_name=True)
        return base, adjectives, merged_bases, secretadjectives

    def gen_statistics(self):
        self.size: int = self.inherit_stat_from_base(self.component_1.size, self.component_2.size)
        self.size += self.stat_adjust_from_base(self.component_1.size, self.component_2.size)
        # power
        total_power = (self.component_1.power
                          + self.component_1.inheritpower 
                          + self.component_2.power 
                          + self.component_2.inheritpower)
        average_power = total_power//2
        power_difference = abs((self.component_1.power + self.component_1.inheritpower)
                                - (self.component_2.power + self.component_2.inheritpower))
        if self.operation == "&&":
            self.power: int = total_power + average_power
        elif self.operation == "||":
            self.power: int = total_power + power_difference
        power_mult = self.entropy_mult
        self.power = int(self.power*power_mult)
        self.inheritpower: int = self.component_1.inheritpower + self.component_2.inheritpower
        # costs (dict of grist: float)
        self.cost: dict = self.component_1.cost.copy()
        for grist_name in self.component_2.cost:
            if grist_name not in self.cost:
                self.cost[grist_name] = self.component_2.cost[grist_name]
            else:
                self.cost[grist_name] += self.component_2.cost[grist_name]
        for grist_name, cost in self.cost.items():
            self.cost[grist_name] = int(cost*self.entropy_mult)
        # dict inherits
        self.onhit_states: dict = self.dictionary_inherit(self.component_1.onhit_states, self.component_2.onhit_states)
        self.wear_states: dict = self.dictionary_inherit(self.component_1.wear_states, self.component_2.wear_states)
        self.consume_states: dict = self.dictionary_inherit(self.component_1.consume_states, self.component_2.consume_states)
        self.secret_states: dict = self.dictionary_inherit(self.component_1.secret_states, self.component_2.secret_states)
        # secret effects
        for effect in self.secret_states.copy():
            random.seed(self.name+"secretstatesoption"+effect)
            option = random.choice(["consume_states", "onhit_states", "wear_states", "secret_states"]) # chance of staying dormant...
            if option == "consume_states" and len(self.consume_states) > 0:
                self.consume_states[effect] = self.secret_states.pop(effect)
            if option == "onhit_states" and len(self.onhit_states) > 0:
                self.onhit_states[effect] = self.secret_states.pop(effect)
            if option == "wear_states" and len(self.wear_states) > 0:
                self.wear_states[effect] = self.secret_states.pop(effect)
        # use effect
        if self.base == self.component_1.base: 
            self.use = self.component_1.use
            self.wearable = self.component_1.wearable
            self.kinds = self.component_1.kinds
        elif self.base == self.component_2.base: 
            self.use = self.component_2.use
            self.wearable = self.component_2.wearable
            self.kinds = self.component_2.kinds
        # if compound base
        else:
            self.use = self.component_1.use + self.component_2.use
            self.wearable = self.component_1.wearable or self.component_2.wearable
            self.kinds = self.component_1.kinds + self.component_2.kinds

    def dictionary_inherit(self, component_1_dict: dict, component_2_dict: dict) -> dict: # returns new dict
        new_dict = component_1_dict.copy()
        for state_name, potency in component_2_dict.items():
            if state_name in new_dict and potency > new_dict[state_name]:
                new_dict[state_name] = potency
            elif state_name not in new_dict:
                new_dict[state_name] = potency
        return new_dict

    def inherit_stat_from_base(self, component_1_stat: int, component_2_stat:int) -> int:
        if self.component_1.base == self.base: return component_1_stat
        if self.component_2.base == self.base: return component_2_stat
        return int((component_1_stat + component_2_stat) * 0.5) # compound base
    
    def stat_adjust_from_base(self, component_1_stat, component_2_stat) -> int:
        if self.component_1.base == self.base: base_stat = component_1_stat; mult_stat = component_2_stat
        elif self.component_2.base == self.base: base_stat = component_2_stat; mult_stat = component_1_stat
        else: return 0
        if base_stat == 0: base_stat = 1
        if mult_stat == 0: mult_stat = 1
        if base_stat > mult_stat: # adjust should be negative due to lower mult stat
            return int(-1 * (base_stat / mult_stat))
        else: # adjust should be positive due to higher mult stat
            return int(mult_stat / base_stat)

def get_code_from_name(name: str) -> str: # from name
    if name in util.bases:
        code = util.bases[name]["code"]
    else:
        components = Components(name)
        if components.component_1 is None or components.component_2 is None: return "!!!!!!!!"
        operation = components.operation
        if operation == "&&":
            code = binaryoperations.codeand(get_code_from_name(components.component_1), get_code_from_name(components.component_2))
        else:
            code = binaryoperations.codeor(get_code_from_name(components.component_1), get_code_from_name(components.component_2))
    return code

def does_item_exist(name):
    print(f"checking if item exists {name}")
    if name in database.memory_items: return True
    else: return False

class Item(): # Items are the base of instants.
    # item re-instantiation should caused alchemized items to get their properties based on their substituents
    def __init__(self, name):
        code = get_code_from_name(name)
        if code in util.codes: # if this code already exists, give the item the code corresponds to instead
            name = util.codes[code]
        self.__dict__["_id"] = name
        if name not in database.memory_items:
            self.create_item(name)
            statistics = self.get_name_statistics(name)
            self.make_statistics(statistics)
            self.code = get_code_from_name(self.name)
            if self.code not in util.codes:
                util.codes[self.code] = self.name

    @classmethod
    def modify_alchemy(cls, base_component_name: str, modifier_component_name: str) -> "Item":
        name = f"({base_component_name}<-{modifier_component_name})"
        if name in database.memory_items: return Item(name)
        database.memory_items[name] = {}
        database.memory_items[name]["_id"] = name
        code = binaryoperations.random_valid_code()
        while code in util.codes: code = binaryoperations.random_valid_code()
        util.codes[code] = name
        item = Item(name)
        base_component = Item(base_component_name)
        modifier_component = Item(modifier_component_name)
        operation = random.choice(["&&", "||"])
        statistics = InheritedStatistics(base_component, modifier_component, operation, guarantee_first_base=True)
        item.make_statistics(statistics)
        item.code = code
        return item

    @classmethod
    def from_code(cls, code: str) -> "Item":
        if code in util.codes:
            return Item(util.codes[code])
        else: # paradox item
            component_1, component_2 = paradoxify(code)
            name = f"({component_1.name}??{component_2.name})"
            database.memory_items[name] = {}
            database.memory_items[name]["_id"] = name
            util.codes[code] = name
            item = Item(name)
            operation = random.choice(["&&", "||"])
            statistics = InheritedStatistics(component_1, component_2, operation)
            item.make_statistics(statistics)
            item.code = code
            return item

    def get_name_statistics(self, name) -> Union[BaseStatistics, InheritedStatistics]:
        if self.name in util.bases:
            statistics = BaseStatistics(name)
        else:
            components = Components(self.name)
            component_1 = Item(components.component_1)
            component_2 = Item(components.component_2)
            operation = components.operation
            statistics = InheritedStatistics(component_1, component_2, operation)
        return statistics

    def make_statistics(self, statistics: Union[BaseStatistics, InheritedStatistics]):
        self.descriptors = statistics.descriptors
        self.adjectives = statistics.adjectives
        self.base = statistics.base
        self.power = statistics.power
        self.inheritpower = statistics.inheritpower
        self.size = statistics.size
        self.kinds = statistics.kinds
        self.wearable = statistics.wearable
        self.description = statistics.description
        self.cost = statistics.cost
        self.use = statistics.use
        self.onhit_states = statistics.onhit_states
        self.wear_states = statistics.wear_states
        self.consume_states = statistics.consume_states
        self.secret_states = statistics.secret_states
        self.secretadjectives = statistics.secretadjectives
        self.forbiddencode = statistics.forbiddencode
        self.prototype_name = statistics.prototype_name
        self.creator = statistics.creator
        self.display_name = statistics.display_name

    def create_item(self, name):
        database.memory_items[name] = {}
        self._id = name

    @property
    def name(self):
        return self.__dict__["_id"]
    
    @name.setter
    def name(self, value):
        self.__dict__["_id"] = value

    @property
    def displayname(self):
        if self.display_name is not None: return self.display_name
        name = " ".join(self.adjectives+[self.base])
        out = name.replace("+", " ")
        return out
    
    @property
    def true_cost(self):
        out = {}
        for grist_name, value in self.cost.items():
            out[grist_name] = int(self.power*value)
        return out
    
    def __setattr__(self, attr, value):
        database.memory_items[self.__dict__["_id"]][attr] = value
        self.__dict__[attr] = value

    def __getattr__(self, attr):
        return database.memory_items[self.__dict__["_id"]][attr]

    def get_dict(self, raw=False):
        out = deepcopy(database.memory_items[self.__dict__["_id"]])
        if raw: return out
        out["name"] = self.__dict__["_id"]
        out["display_name"] = self.displayname
        onhit_states = {}
        wear_states = {}
        consume_states = {}
        for state_name, potency in self.onhit_states.items():
            if state_name not in stateseffects.states: print(f"!! INVALID STATE {state_name} !!"); continue
            state = stateseffects.states[state_name]
            onhit_states[state_name] = {
                "potency": potency,
                "duration": 2,
                "tooltip": state.tooltip,
                "passive": state.passive,
            }
        for state_name, potency in self.wear_states.items():
            if state_name not in stateseffects.states: print(f"!! INVALID STATE {state_name} !!"); continue
            state = stateseffects.states[state_name]
            wear_states[state_name] = {
                "potency": potency,
                "duration": 1,
                "tooltip": state.tooltip,
                "passive": state.passive,
            }
        for state_name, potency in self.consume_states.items():
            if state_name not in stateseffects.states: print(f"!! INVALID STATE {state_name} !!"); continue
            state = stateseffects.states[state_name]
            consume_states[state_name] = {
                "potency": potency,
                "duration": 3,
                "tooltip": state.tooltip,
                "passive": state.passive,
            }
        out["onhit_states"] = onhit_states
        out["wear_states"] = wear_states
        out["consume_states"] = consume_states
        return out

def does_instance_exist(name):
    if name in database.memory_instances: return True
    else: return False

class Instance():
    def __init__(self, identifier: Union[Item, str]):
        if isinstance(identifier, str):
            self.__dict__["_id"] = identifier
            name = identifier
        else: # get a random name instead
            name = identifier.name + random.choice(ascii_letters)
            while does_instance_exist(name):
                name += random.choice(ascii_letters)
            self.__dict__["_id"] = name
            self.create_instance(name)
            self.item_name = identifier.name
        if name not in database.memory_instances:
            self.create_instance(name)

    def create_instance(self, name):
        database.memory_instances[name] = {}
        self._id = name
        self.punched_code: str = ""
        self.punched_item_name: str = ""
        self.inserted: str = ""
        self.contained: str = ""
        self.combined: list[str] = []
        self.carved: str = "00000000"
        self.carved_item_name: str = "perfectly+generic object"
        self.computer_data: dict = {"installed_programs": []}
        self.color: tuple[int, int, int] = (157, 224, 255)

    @property
    def name(self):
        return self.__dict__["_id"]
    
    @name.setter
    def name(self, value):
        self.__dict__["_id"] = value

    def __setattr__(self, attr, value):
        database.memory_instances[self.__dict__["_id"]][attr] = value
        self.__dict__[attr] = value

    def __getattr__(self, attr):
        return database.memory_instances[self.__dict__["_id"]][attr]
    
    def get_dict(self):
        output = deepcopy(database.memory_instances[self.__dict__["_id"]])
        output["instance_name"] = self.__dict__["_id"]
        if output["contained"] != "":
            output["contained"] = Instance(output["contained"]).get_dict()
        if output["inserted"] != "":
            output["inserted"] = Instance(output["inserted"]).get_dict()
        if output["combined"] != []:
            output["combined"] = [Instance(i).get_dict() for i in output["combined"]]
        item_dict = self.item.get_dict()
        output["item_dict"] = item_dict
        return output
    
    # note this function does not remove the instance, it merely creates a card containing it
    def to_card(self) -> "Instance":
        item = Item("captchalogue card")
        instance = Instance(item)
        instance.contained = self.name
        return instance
    
    @property
    def item(self) -> Item:
        return Item(self.item_name)

def display_item(item: Item):
    out = f"""{item.displayname}
    CODE: {item.code}
    POWER: {item.power}
    DICE: {round(item.dicemin, 2)} {round(item.dicemax, 2)}
    SIZE: {item.size} 
    """
    return out

def paradoxify(paradox_code: str) -> tuple[Item, Item]:
    codes = list(util.codes)
    left_code, right_code = difflib.get_close_matches(paradox_code, codes, n=2, cutoff=0)
    item_1_name = util.codes[left_code]
    item_2_name = util.codes[right_code]
    return Item(item_1_name), Item(item_2_name)

def alchemize(item_name1: str, item_name2: str, operation: str):
    return f"({item_name1}{operation}{item_name2})"

def alchemize_instance(code: str, player: "sessions.Player", room: "sessions.Room"):
    if code not in util.codes: print(f"code {code} not in codes"); return False
    new_item_name = util.codes[code]
    new_item = Item(new_item_name)
    if not player.pay_costs(new_item.true_cost): print("couldnt pay costs"); return False
    new_instance = Instance(new_item)
    if new_instance.item.name == "entry item":
        new_instance.color = player.color
    room.add_instance(new_instance.name)
    player.land.session.add_to_excursus(new_item.name)
    return True

defaults = {
    #"code": None, #todo: add procedural hex generation for items
    "base": True, # is this item a base?
    "display_name": None, # for proper named items
    "forbiddencode": False,
    "power": 1, # how powerful is the item?
    "inheritpower": 0, # how much extra power this item gives when it's alchemized
    # "weight": 1, # how much the thing weighs, will mostly be used for determining sylladex ejection damage
    "size": 1, # how big the thing is. determines if it's wieldable (size 20 or less)
    "kinds": {}, # the strife specibi that allow this item to be equipped and its weight (how likely it is to be inherited). if it is a list, the second item is the adjective/base that guarantees inheritance
    "wearable": False, # whether the item can be worn
    #"stats": {}, # what stats are boosted / decreased through equipping the item (wielding or wearing) in an appropriate slot. this is a dict of dicts, where key is stat and value is % of power boost
    #"nickname": "Broken", # the default given nickname of an item. should be set to something on generation
    "description": "None", # the description of the item (only for bases and items with set descriptions)
    "cost": {"build": 1}, # cost of item. key: grist type, value: % of power
    "use": [], # what this item does on use.
    "onhit_states": {}, # the effect of the item as applied to the enemy key: effect value: power ratio e.g. {"healing": [.01]}
    "wear_states": {}, # the effect of the item when worn in a slot or wielded
    "consume_states": {}, # a list of effects that this item will have when consumed. todo: valid effects page
    "secret_states": {}, # a list of effects that do nothing but may be turned into onhit, wear or consume effects upon alchemizing
    "attached_skills": [], # a list of skills this item teaches when worn/wielded
    "secretadjectives": [], # a list of adjectives that might be inherited but don't show up on the item
    "prototype_name": None, # either None or a word that will be used when prototyped for the first time(cowboy boots is "cowboy" for example)
    "creator": None,
}

# special items (loot items)
for grist_name in config.grists:
    # make grystals (consumable grist items)
    # rough grystal
    rough_grystal_dict = deepcopy(defaults)
    rough_grystal_dict.update({
        "displayname": f"rough {grist_name} grystal",
        "forbiddencode": True,
        "power": 100,
        "size": 1,
        "description": f"A rough grystal. When consumed, this gives 1000 {grist_name} grist.",
        "cost": {grist_name: 10},
        "use": ["collect"],
        "prototype_name": grist_name,
        "secret_states": {"leech": 0.5},
        "adjectives": [grist_name.replace(" ","+"), "rough"],
        "secretadjectives": ["gristy", "abstract", "meta", "resourceful", "glitchy"],
        "creator": "ebolite",
    })
    if grist_name in ["rainbow", "zilium"]: 
        rough_grystal_dict["description"] = f"A rough grystal. When consumed, this gives 1 {grist_name} grist.",
        rough_grystal_dict["cost"] = {grist_name: 0.01}
    util.bases[f"rough {grist_name} grystal"] = deepcopy(rough_grystal_dict)
    # fine grystal
    fine_grystal_dict = deepcopy(defaults)
    fine_grystal_dict.update({
        "displayname": f"fine {grist_name} grystal",
        "forbiddencode": True,
        "power": 100,
        "size": 1,
        "description": f"A fine grystal. When consumed, this gives 10000 {grist_name} grist.",
        "cost": {grist_name.replace(" ","+"): 100},
        "use": ["collect"],
        "prototype_name": grist_name,
        "secret_states": {"leech": 1},
        "adjectives": [grist_name.replace(" ","+"), "fine"],
        "secretadjectives": ["gristy", "abstract", "meta", "resourceful", "glitchy"],
        "creator": "ebolite",
    })
    if grist_name in ["rainbow", "zilium"]: 
        fine_grystal_dict["description"] = f"A fine grystal. When consumed, this gives 2 {grist_name} grist.",
        fine_grystal_dict["cost"] = {grist_name: 0.02}
    util.bases[f"fine {grist_name} grystal"] = deepcopy(fine_grystal_dict)
    # choice grystal
    choice_grystal_dict = deepcopy(defaults)
    choice_grystal_dict.update({
        "displayname": f"choice {grist_name} grystal",
        "forbiddencode": True,
        "power": 100,
        "size": 1,
        "description": f"A choice grystal. When consumed, this gives 100000 {grist_name} grist.",
        "cost": {grist_name: 1000},
        "use": ["collect"],
        "prototype_name": grist_name,
        "secret_states": {"leech": 2},
        "adjectives": [grist_name.replace(" ","+"), "choice"],
        "secretadjectives": ["gristy", "abstract", "meta", "resourceful", "glitchy"],
        "creator": "ebolite",
    })
    if grist_name in ["rainbow", "zilium"]: 
        fine_grystal_dict["description"] = f"A choice grystal. When consumed, this gives 3 {grist_name} grist.",
        fine_grystal_dict["cost"] = {grist_name: 0.03}
    util.bases[f"choice {grist_name} grystal"] = deepcopy(choice_grystal_dict)

# special pure aspect items
for _, aspect in skills.aspects.items():
    pure_aspect_dict = deepcopy(defaults)
    pure_aspect_dict.update({
        "forbiddencode": True,
        "power": 100,
        "inheritpower": 100,
        "size": 1,
        "description": f"Pure, condensed {aspect.name}.",
        "cost": config.aspect_grists[aspect.name].copy(),
        "adjectives": ["pure"],
        "secretadjectives": config.aspect_secretadjectives[aspect.name].copy(),
        "creator": "ebolite",
        "prototype_name": aspect.name,
    })
    pure_aspect_dict["secret_states"] = {f"subtract {aspect.name}": 1, f"add {aspect.name}": 1}
    if aspect.beneficial:
        pure_aspect_dict["onhit_states"] = {f"subtract {aspect.name}": 0.5}
        pure_aspect_dict["wear_states"] = {f"add {aspect.name}": 0.5}
        pure_aspect_dict["consume_states"] = {f"add {aspect.name}": 0.5}
    else:
        pure_aspect_dict["onhit_states"] = {f"add {aspect.name}": 0.5}
        pure_aspect_dict["wear_states"] = {f"subtract {aspect.name}": 0.5}
        pure_aspect_dict["consume_states"] = {f"subtract {aspect.name}": 0.5}
    util.bases[f"pure {aspect.name}"] = deepcopy(pure_aspect_dict)

missing_states = set()

for base, base_dict in util.bases.items():
    for default in defaults:
        if default not in base_dict:
            base_dict[default] = defaults[default]
            print(f"base {base} missing default {default}")
    for key in ["onhit_states", "wear_states", "consume_states", "secret_states"]:
        for state_name in base_dict[key]:
            if state_name not in stateseffects.states:
                missing_states.add(state_name)
            if isinstance(base_dict[key][state_name], list):
                base_dict[key][state_name] = base_dict[key][state_name][0]
    if "build" not in base_dict["cost"]:
        base_dict["cost"]["build"] = 0.5
    if "prototype_name" not in base_dict:
        base_dict["prototype_name"] = None
    if "weight" in base_dict:
        base_dict.pop("weight")
    if "code" not in base_dict:
        code = binaryoperations.random_valid_code()
        while code in util.codes:
            code = binaryoperations.random_valid_code()
        base_dict["code"] = code
    code = base_dict["code"]
    util.codes[code] = base
util.writejson(util.bases, "bases")

if len(missing_states) > 0:
    print("!!! MISSING STATES !!!")
    print(" ".join(list(missing_states)))

if __name__ == "__main__":
    t = time.time()
    paradox_code = "bDaaT!eF"
    codes = list(util.codes)
    left_code, right_code = difflib.get_close_matches(paradox_code, codes, n=2, cutoff=0)
    print(f"left code {left_code} ({util.codes[left_code]}) right code {right_code} ({util.codes[right_code]}) took {time.time()-t:.2f} secs")
    # name_desc = {}
    # for base in util.bases:
    #     name_desc[base] = {"description": util.bases[base]["description"]}
    # util.writejson(name_desc, "base_item_list")
    # def loop(base1: Item, base2: Item):
    #     merge_and = Item(alchemize(base1.name, base2.name,"&&"))
    #     merge_or = Item(alchemize(base1.name, base2.name, "||"))
    #     print(merge_and.name)
    #     print(Components(merge_and.name).get_all_components())
    #     print(display_item(merge_and))
    #     print(merge_or.name)
    #     print(Components(merge_or.name).get_all_components())
    #     print(display_item(merge_or))
    #     input()
    #     loop(random.choice([merge_and, merge_or]), Item(random.choice(list(util.bases.keys()))))
    # initial_base1 = Item(random.choice(list(util.bases.keys())))
    # initial_base2 = Item(random.choice(list(util.bases.keys())))
    # loop(initial_base1, initial_base2)