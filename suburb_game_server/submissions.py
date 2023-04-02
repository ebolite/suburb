from copy import deepcopy

import util
import spawnlists

def accept_base(base_name: str, base_dict: dict):
    for spawnlist_name in base_dict["interests"]:
        spawnlist = spawnlists.SpawnList(spawnlist_name)
        match base_dict["interests_rarity"]:
            case "common":
                spawnlist.common.append(base_name)
            case "uncommon":
                spawnlist.uncommon.append(base_name)
            case "rare":
                spawnlist.rare.append(base_name)
            case "exotic":
                spawnlist.exotic.append(base_name)
    for spawnlist_name in base_dict["tiles"]:
        spawnlist = spawnlists.SpawnList(spawnlist_name)
        match base_dict["tiles_rarity"]:
            case "common":
                spawnlist.common.append(base_name)
            case "uncommon":
                spawnlist.uncommon.append(base_name)
            case "rare":
                spawnlist.rare.append(base_name)
            case "exotic":
                spawnlist.exotic.append(base_name)
    base_dict.pop("interests")
    base_dict.pop("interests_rarity")
    base_dict.pop("tiles")
    base_dict.pop("tiles_rarity")
    util.bases[base_name] = base_dict
    util.writejson(util.bases, "bases")
    util.writejson(util.spawnlists, "spawnlists")

if __name__ == "__main__":
    accept_considered = input("Accept all considered? (y/n) ")
    if accept_considered:
        for base_name in util.considered_submissions.copy():
            base_dict = util.considered_submissions[base_name].copy()
            accept_base(base_name, base_dict)
            util.considered_submissions.pop(base_name)
        util.writejson(util.considered_submissions, "considered_submissions")
        print("Accepted.")
    base_submissions = util.get_base_submissions()
    for base_name in deepcopy(base_submissions):
        print(f"-- {base_name} --")
        base_dict = deepcopy(base_submissions[base_name])
        for element in base_dict:
            print(f"{element}: {base_dict[element]}")
        print(f"(A)ccept, (C)onsider, (D)eny, (B)an")
        while True:
            reply = input()
            if reply.lower() in ["a", "c", "d", "b"]:
                break
            else: print("Invalid option.")
        reply = reply.lower()
        base_submissions.pop(base_name)
        util.update_base_submissions(base_submissions)
        match reply:
            case "a":
                print("Accepted.")
                accept_base(base_name, base_dict)
            case "c":
                print("Considered.")
                util.considered_submissions[base_name] = base_dict
                util.writejson(util.considered_submissions, "considered_submissions")
            case "d":
                print("Denied.")
                pass
            case "b":
                pass