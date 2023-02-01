import random
import string

import util
import binary
import config

COMPOUND_NAME_CHANCE = 0.2 # chance for having compound names in && operations

class Components():
    def __init__(self, name: str):
        # names look like "(((baseball bat&&sledge hammer)&&(piano wire||ring))||shotgun)" so we have to find the midpoint for the components
        # if at any point all parentheses are closed (ignoring the first one), we are at the midpoint
        self.name = name
        components_name = name[1:]
        components_name = components_name[:-1]
        print(components_name)
        parentheses = 0
        operation = ""
        component_1 = ""
        component_2 = ""
        if "(" and ")" not in components_name:
            if "&&" in components_name:
                self.operation = "&&"
                components = components_name.split("&&")
            else:
                self.operation = "||"
                components = components_name.split("||")
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
        self.component_1: str = component_1
        self.component_2: str = component_2
        self.operation: str = operation

class BaseDescriptors():
    def __init__(self, base_name: str):
        descriptors = list(util.bases[base_name]["adjectives"])
        descriptors += base_name.split(" ") # " " is a separator for descriptors in base name
        self.descriptors = list(descriptors)
        self.base = descriptors.pop() # last descriptor is the base
        self.adjectives = list(set(descriptors)) # everything else are adjectives, remove duplicates

class InheritedDescriptors():
    def __init__(self, component_1: "Item", component_2: "Item", operation, guaranteed_compound_name = False):
        name = f"({component_1.name}{operation}{component_2.name})" # for seed
        required_inheritors = []
        base = ""
        adjectives = []
        if len(component_1.descriptors) == 1: required_inheritors.append(component_1.descriptors[0])
        if len(component_2.descriptors) == 1: required_inheritors.append(component_2.descriptors[0])
        inheritable_bases = [component_1.base, component_2.base]
        if operation == "&&": # && has compound names sometimes
            random.seed(name+"compound_chance")
            if random.random() < COMPOUND_NAME_CHANCE or guaranteed_compound_name:
                inheritable_bases = []
                if component_1.base in required_inheritors: required_inheritors.remove(component_1.base)
                if component_2.base in required_inheritors: required_inheritors.remove(component_2.base)
                random.seed(name+"compound_choice")
                if random.random() < 0.5: inheritable_bases.append(f"{component_1.base}-{component_2.base}")
                else: inheritable_bases.append(f"{component_2.base}-{component_1.base}")
        inheritable_adjectives = component_1.adjectives + component_2.adjectives
        random.seed(name+"base")
        base = random.choice(inheritable_bases)
        if base in required_inheritors: required_inheritors.remove(base)
        if base in inheritable_bases: inheritable_bases.remove(base)
        inheritable_adjectives += inheritable_bases
        random.seed(name+"shuffle")
        random.shuffle(inheritable_adjectives)
        for adj in inheritable_adjectives:
            inherit_chance = 1 - (len(adjectives) / len(inheritable_adjectives)) # chance decreases as more adjectives are choses
            inherit_chance -= (0.1 * len(adjectives)) # additional flat chance decrease based on how many adjectives it has already
            if adj in required_inheritors:
                required_inheritors.remove(adj)
                adjectives.append(adj)
                continue
            random.seed(name+"inherit"+adj)
            if random.random() < inherit_chance:
                adjectives.append(adj)
        self.base = base
        self.adjectives = adjectives
        # check if AND is different from OR, if they are the same, guarantee a compound base
        if operation == "&&":
            or_descriptors = InheritedDescriptors(component_1, component_2, "||")
            adjectives_set = set(self.adjectives)
            or_adjectives_set = set(or_descriptors.adjectives)
            if (self.base == or_descriptors.base and 
                (adjectives_set.issubset(or_adjectives_set) or or_adjectives_set.issubset(adjectives_set))): # convert to set so names aren't just the same thing in different order
                guaranteed_compound_descriptors = InheritedDescriptors(component_1, component_2, operation, guaranteed_compound_name=True)
                self.base = guaranteed_compound_descriptors.base
                self.adjectives = guaranteed_compound_descriptors.adjectives

class Item(): # Items are the base of instants.
    # item re-instantiation should caused alchemized items to get their properties based on their substituents
    def __init__(self, name):
        self.name = name
        if self.name not in util.items:
            if self.name in util.bases:
                descriptors = BaseDescriptors(name)
                self.descriptors = descriptors.descriptors
                self.adjectives = descriptors.adjectives
                self.base = descriptors.base
            else:
                components = Components(self.name)
                component_1 = Item(components.component_1)
                component_2 = Item(components.component_2)
                operation = components.operation
                descriptors = InheritedDescriptors(component_1, component_2, operation)
                self.descriptors = descriptors.adjectives + [descriptors.base]
                self.adjectives = descriptors.adjectives
                self.base = descriptors.base

defaults = {
    #"code": None, #todo: add procedural hex generation for items
    "base": True, # is this item a base?
    "forbiddencode": False,
    "power": 1, # how powerful is the item?
    "inheritpower": 0, # how much extra power this item gives when it's alchemized
    "dicemin": .7, # the minimum dice roll as a fraction of power
    "dicemax": 1, # the maximum dice roll as a fraction of power
    "weight": 1, # how much the thing weighs, will mostly be used for determining sylladex ejection damage
    "size": 1, # how big the thing is. determines if it's wieldable (size 20 or less)
    "kinds": {}, # the strife specibi that allow this item to be equipped and its weight (how likely it is to be inherited). if it is a list, the second item is the adjective/base that guarantees inheritance
    "slots": {}, # what slots the item can be equipped in (wearable slots) and how likely they are to be inherited along with adjectives/bases that guarantee inheritance
    "tags": {"mundane": [0]}, # what true/false statements apply (if in list, they are true) e.g "blunt" (blunt damage), "funny," "monochrome," "consumable," "enemyconsumable" and how likely they are to be inherited
    #"stats": {}, # what stats are boosted / decreased through equipping the item (wielding or wearing) in an appropriate slot. this is a dict of dicts, where key is stat and value is % of power boost
    #"nickname": "Broken", # the default given nickname of an item. should be set to something on generation
    "description": "None", # the description of the item (only for bases and items with set descriptions)
    "cost": {"build": 1}, # cost of item. key: grist type, value: % of power
    "use": None, # what this item does on use. can only have one thing.
    "onhiteffect": {}, # the effect of the item as applied to the enemy key: effect value: power ratio e.g. {"healing": [.01]}
    "weareffect": {}, # the effect of the item when worn in a slot or wielded
    "consumeeffect": {}, # a list of effects that this item will have when consumed. todo: valid effects page
    "secreteffect": {}, # a list of effects that do nothing but may be turned into onhit, wear or consume effects upon alchemizing
    "secretadjectives": [] # a list of adjectives that might be inherited but don't show up on the item
}