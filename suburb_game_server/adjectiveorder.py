import util
import random

# adjective order:
order = {
    0: "determiner", # your, my, these
    1: "size", # big, small
    2: "opinion", # delicious, funny, lovely
    3: "age", # old, newest
    4: "shape", # round, square, geometric
    5: "color", # blue, green, silver
    6: "origin or material", # american, velvet, african, denim
    7: "qualifier", # *vampire* bat, *pickup* truck, *hound* dog
}
reversed_order_dic = {value : key for (key, value) in order.items()}

adjective_types = {}
adjective_types = util.readjson(adjective_types, "adjective_types")
normal_adjectives = []
for base in util.bases:
    for adj in util.bases[base]["adjectives"]:
        if adj not in normal_adjectives: normal_adjectives.append(adj)
secret_adjectives = []
for base in util.bases:
    for adj in util.bases[base]["secretadjectives"]:
        if adj not in secret_adjectives: secret_adjectives.append(adj)

def sort_by_adjectives(to_sort:list) -> list:
    def sort_function(name: str):
        if name in adjective_types:
            adjective_type = adjective_types[name]
        else:
            if adj in secret_adjectives:
                adjective_type = "opinion"
            elif adj in normal_adjectives:
                adjective_type = "qualifier"
            else:
                adjective_type = "opinion"
        return reversed_order_dic[adjective_type]
    sorted = to_sort.copy()
    sorted.sort(key=sort_function)
    return sorted

untyped_adjectives = []
adjective_bases = {}
for base in util.bases:
    for adj in util.bases[base]["adjectives"]+util.bases[base]["secretadjectives"]:
        if adj not in adjective_types and adj not in untyped_adjectives:
            untyped_adjectives.append(adj)
            adjective_bases[adj] = base
random.shuffle(untyped_adjectives)

if __name__ == "__main__":
    for base in util.bases:
        for adj in util.bases[base]["adjectives"]+util.bases[base]["secretadjectives"]:
            if adj not in adjective_types:
                untyped_adjectives.append(adj)
                adjective_bases[adj] = base
    random.shuffle(untyped_adjectives)
    for adj in untyped_adjectives.copy():
        print(f"""
        {adj.replace("+", " ")} (as {adjective_bases[adj]})
        0. determiner (your, my, these)
        1. opinion (delicious, funny, lovely)
        2. size (big, small, tiny)
        3. age (old, young, new, classical)
        4. shape (square, round, triangular)
        5. color (you know what a color is dipshit)
        6. origin or material (American, velvet, African)
        7. qualifier (/pickup/ truck, /vampire/ bat, /hound/ dog)
        enter nothing to skip if you're unsure
        ({len(adjective_types)} done, {len(untyped_adjectives)} remaining)
        """)
        num = input()
        try:
            num = int(num)
            adjective_types[adj] = order[num]
            untyped_adjectives.remove(adj)
            util.writejson(adjective_types, "adjective_types")
        except ValueError:
            continue
else:
    if len(untyped_adjectives) > 0: print(f"!!! {len(untyped_adjectives)} adjectives are untyped! Run adjectiveorder.py to fix! !!!")