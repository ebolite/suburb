from copy import deepcopy
from typing import Optional

import util
import sessions
from sessions import Room

class Griefer():
    def __init__(self, name, strife: "Strife"):
        self.__dict__["name"] = name
        self.__dict__["session_name"] = strife.session.name
        self.__dict__["overmap_name"] = strife.overmap.name
        self.__dict__["map_name"] = strife.map.name
        self.__dict__["room_name"] = strife.room.name
        if name not in util.sessions[strife.session.name]["overmaps"][strife.overmap.name]["maps"][strife.map.name]["rooms"][strife.room.name]["strife_dict"]["griefers"]:
            strife.griefers[name] = {}
            self.base_power: int = 0
            self.stat_ratios = {
                "spunk": 1,
                "vigor": 1,
                "tact": 1,
                "luck": 1,
                "savvy": 1,
                "mettle": 1,
            }
            self.player_name: Optional[str] = None


    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["overmaps"][self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["map_name"]]
         ["rooms"][self.__dict__["room_name"]]
         ["strife_dict"]["griefers"]
         [self.__dict__["name"]][attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["map_name"]]
                               ["rooms"][self.__dict__["room_name"]]
                               ["strife_dict"]["griefers"]
                               [self.__dict__["name"]][attr])
        return self.__dict__[attr]
    
    def get_dict(self) -> dict:
        out = deepcopy(util.sessions[self.__dict__["session_name"]]
                        ["overmaps"][self.__dict__["overmap_name"]]
                        ["maps"][self.__dict__["map_name"]]
                        ["rooms"][self.__dict__["room_name"]]
                        ["strife_dict"]["griefers"]
                        [self.__dict__["name"]])
        return out
    
    @property
    def session(self) -> "sessions.Session":
        return sessions.Session(self.__dict__["session_name"])
    
    @property
    def overmap(self) -> "sessions.Overmap":
        return sessions.Overmap(self.__dict__["overmap_name"], self.session)
    
    @property
    def map(self) -> "sessions.Map":
        return sessions.Map(self.__dict__["map_name"], self.session, self.overmap)
    
    @property
    def room(self) -> "sessions.Room":
        return sessions.Room(self.__dict__["room_name"], self.session, self.overmap, self.map)
    
    @property
    def strife(self) -> "Strife":
        return Strife(self.room)

# each room can only have one Strife in it
class Strife():
    def __init__(self, room: "Room"):
        self.__dict__["session_name"] = room.session.name
        self.__dict__["overmap_name"] = room.overmap.name
        self.__dict__["map_name"] = room.map.name
        self.__dict__["room_name"] = room.name
        if "strife_dict" not in util.sessions[room.session.name]["overmaps"][room.overmap.name]["maps"][room.map.name]["rooms"][room.name]:
            room.strife_dict = {}
            self.griefers = {}
            self.turn_num: int = 0
            # key: griefer name value: list of Skill dict (skill name and target/s)
            self.submitted_actions: dict[str, list[dict]] = {}

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        (util.sessions[self.__dict__["session_name"]]
         ["overmaps"][self.__dict__["overmap_name"]]
         ["maps"][self.__dict__["map_name"]]
         ["rooms"][self.__dict__["room_name"]]
         ["strife_dict"][attr]) = value

    def __getattr__(self, attr):
        self.__dict__[attr] = (util.sessions[self.__dict__["session_name"]]
                               ["overmaps"][self.__dict__["overmap_name"]]
                               ["maps"][self.__dict__["map_name"]]
                               ["rooms"][self.__dict__["room_name"]]
                               ["strife_dict"][attr])
        return self.__dict__[attr]
    
    def get_dict(self) -> dict:
        out = deepcopy(util.sessions[self.__dict__["session_name"]]
                        ["overmaps"][self.__dict__["overmap_name"]]
                        ["maps"][self.__dict__["map_name"]]
                        ["rooms"][self.__dict__["room_name"]]
                        ["strife_dict"])
        for griefer_name in self.griefers:
            out["griefers"][griefer_name] = self.get_griefer(griefer_name).get_dict()
        return out
    
    def get_griefer(self, name: str) -> "Griefer":
        return Griefer(name, self)

    @property
    def session(self) -> "sessions.Session":
        return sessions.Session(self.__dict__["session_name"])
    
    @property
    def overmap(self) -> "sessions.Overmap":
        return sessions.Overmap(self.__dict__["overmap_name"], self.session)
    
    @property
    def map(self) -> "sessions.Map":
        return sessions.Map(self.__dict__["map_name"], self.session, self.overmap)
    
    @property
    def room(self) -> "sessions.Room":
        return sessions.Room(self.__dict__["room_name"], self.session, self.overmap, self.map)