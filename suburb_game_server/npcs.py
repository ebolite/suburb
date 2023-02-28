import util

class Npc():
    _defaults = {
        "power": 0,
    }

    def __init__(self, name):
        self.__dict__["name"] = name
        if name not in util.npcs:
            util.npcs[name] = {}
        self.power: int

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.npcs[self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        try:
            self.__dict__[attr] = util.npcs[self.__dict__["name"]][attr]
            return self.__dict__[attr]
        except KeyError as e:
            try:
                return self._defaults[attr]
            except KeyError:
                raise e

if __name__ == "__main__":
    npc = Npc("boy")
    npc.power += 1
    print(npc.power)