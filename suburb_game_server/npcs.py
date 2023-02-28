import util

class Npc():
    @staticmethod
    def default(attr):
        match attr:
            case "power":
                return 0
            case _:
                return None

    def __init__(self, name):
        self.__dict__["name"] = name
        self.power: int

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        util.npcs[self.__dict__["name"]][attr] = value

    def __getattr__(self, attr):
        try:
            self.__dict__[attr] = util.npcs[self.__dict__["name"]][attr]
            return self.__dict__[attr]
        except KeyError as e:
            default = Npc.default(attr)
            if default is None: raise e
            else: return default

if __name__ == "__main__":
    npc = Npc("boy")
    npc.fuck