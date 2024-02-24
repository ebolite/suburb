from string import ascii_letters
from typing import Optional, Callable
from copy import deepcopy
import random
import math

import util
import config
import sessions
import strife
import skills
import alchemy
import database

underlings: dict[str, "Underling"] = {}
griefer_ai: dict[str, "GrieferAI"] = {}
npc_interactions: dict[str, "NpcInteraction"] = {}


class Underling:
    def __init__(self, monster_type: str):
        underlings[monster_type] = self
        self.monster_type: str = monster_type
        self.base_power: int = 1
        self.stat_ratios: dict[str, int] = {
            "spunk": 1,
            "vigor": 1,
            "tact": 1,
            "luck": 1,
            "savvy": 1,
            "mettle": 1,
        }
        self.actions = 1
        self.cluster_size = 1
        self.difficulty = 1
        # hostility is how strong players have to be to NOT fight them automatically
        self.hostility = 1.0
        self.variance = 0
        self.additional_skills = []
        self.onhit_states = {}
        self.wear_states = {}
        self.immune_states = []
        self.ai_type: str = "random"

    def make_npc(
        self, grist_name: str, grist_category: str, room: "sessions.Room"
    ) -> "Npc":
        grist_list = config.gristcategories[grist_category]
        tier: int = grist_list.index(grist_name) + 1
        power = self.base_power * (tier**2)
        nickname = f"{grist_name} {self.monster_type}"
        name = Npc.make_valid_name(nickname)
        npc = Npc(name)
        npc.type = self.monster_type
        npc.grist_type = grist_name
        npc.grist_category = grist_category
        npc.power = power
        npc.nickname = nickname
        npc.stat_ratios = self.stat_ratios.copy()
        npc.actions = self.actions
        npc.ai_type = self.ai_type
        npc.additional_skills = self.additional_skills.copy()
        npc.hostile = True
        npc.hostility = self.hostility
        npc.onhit_states = self.onhit_states.copy()
        npc.wear_states = self.wear_states.copy()
        if room.session.prototypes:
            prototyped_item_name = random.choice(room.session.prototypes)
            if prototyped_item_name is not None:
                npc.prototype_with_item(prototyped_item_name, nickname=True)
        npc.goto_room(room)
        return npc


class GrieferAI:
    name = "random"

    def __init__(self):
        griefer_ai[self.name] = self

    def ai_choose_skill(self, user: "strife.Griefer") -> Optional[str]:
        return user.get_random_submittable_skill()


GrieferAI()

imp = Underling("imp")
imp.stat_ratios["luck"] = 3
imp.cluster_size = 3
imp.difficulty = 1
imp.variance = 4
imp.hostility = 0
imp.ai_type = "imp"


class ImpAI(GrieferAI):
    name = "imp"

    def ai_choose_skill(self, user: "strife.Griefer") -> Optional[str]:
        if skills.skills["abuse"].is_submittable_by(user):
            return "abuse"
        return super().ai_choose_skill(user)


ImpAI()

ogre = Underling("ogre")
ogre.base_power = 16
ogre.stat_ratios["vigor"] = 3
ogre.stat_ratios["mettle"] = 2
ogre.stat_ratios["spunk"] = 2
ogre.stat_ratios["savvy"] = 0
ogre.wear_states = {"triggered": 1.0}
ogre.cluster_size = 2
ogre.difficulty = 1
ogre.ai_type = "ogre"


class OgreAI(GrieferAI):
    name = "ogre"

    def ai_choose_skill(self, user: "strife.Griefer") -> Optional[str]:
        damaging_skills = [
            skill for skill in user.known_skills_list if skill.damage_formula != "0"
        ]
        sorted_skills = sorted(
            damaging_skills,
            key=lambda skill: skill.evaluate_theoretical_damage(user),
            reverse=True,
        )
        for skill in sorted_skills:
            if skill.is_submittable_by(user):
                return skill.name
        else:
            return super().ai_choose_skill(user)


OgreAI()

lich = Underling("lich")
lich.base_power = 20
lich.stat_ratios["savvy"] = 2
lich.stat_ratios["luck"] = 2
lich.stat_ratios["spunk"] = 2
lich.immune_states = ["bleed", "poison", "blind"]
lich.cluster_size = 1
lich.difficulty = 3
lich.additional_skills = ["abhor"]
lich.ai_type = "lich"


class LichAI(GrieferAI):
    name = "lich"

    def ai_choose_skill(self, user: "strife.Griefer") -> Optional[str]:
        if skills.skills["abhor"].is_submittable_by(user):
            return "abhor"
        return super().ai_choose_skill(user)


LichAI()

basilisk = Underling("basilisk")
basilisk.base_power = 26
basilisk.stat_ratios["savvy"] = 3
basilisk.stat_ratios["spunk"] = 2
basilisk.stat_ratios["vigor"] = 2
basilisk.onhit_states = {"poison": 1}
basilisk.cluster_size = 2
basilisk.actions = 2
basilisk.difficulty = 4

giclops = Underling("giclops")
giclops.base_power = 68
giclops.stat_ratios["mettle"] = 4
giclops.stat_ratios["vigor"] = 2
giclops.stat_ratios["spunk"] = 2
giclops.cluster_size = 1
giclops.difficulty = 5
giclops.ai_type = "giclops"
giclops.additional_skills = ["awreak", "abstain"]


class GiclopsAI(GrieferAI):
    name = "giclops"

    def ai_choose_skill(self, user: "strife.Griefer") -> Optional[str]:
        if skills.skills["awreak"].is_submittable_by(user):
            return "awreak"
        if random.random() < 0.5:
            return super().ai_choose_skill(user)
        else:
            return "abstain"


GiclopsAI()

acheron = Underling("acheron")
acheron.base_power = 111
acheron.stat_ratios["tact"] = 4
acheron.stat_ratios["spunk"] = 2
acheron.stat_ratios["mettle"] = 2
acheron.onhit_states = {"demoralize": 1.2}
acheron.cluster_size = 1
acheron.difficulty = 6
acheron.actions = 2
acheron.ai_type = "ogre"


def does_npc_exist(name):
    if name in database.memory_npcs:
        return True
    else:
        return False


class Npc:
    @staticmethod
    def make_valid_name(name):
        new_name = name
        while does_npc_exist(new_name):
            new_name += random.choice(ascii_letters)
        return new_name

    def __init__(self, name: str):
        self.__dict__["_id"] = name
        if name not in database.memory_npcs:  # load the session into memory
            self.create_npc(name)

    def create_npc(self, name):
        database.memory_npcs[name] = {}
        self._id = name
        self.session_name = None
        self.overmap_name = None
        self.map_name = None
        self.room_name = None
        self.power: int = 0
        self.nickname: str = name
        self.type: str = ""
        self.grist_category: Optional[str] = None
        self.grist_type: Optional[str] = None
        self.color: Optional[list] = None
        self.hostile = True
        self.hostility = 1.0
        self.ai_type: str = "random"
        self.stat_ratios: dict[str, int] = {
            "spunk": 1,
            "vigor": 1,
            "tact": 1,
            "luck": 1,
            "savvy": 1,
            "mettle": 1,
        }
        self.permanent_stat_bonuses: dict[str, int] = {
            "spunk": 0,
            "vigor": 0,
            "tact": 0,
            "luck": 0,
            "savvy": 0,
            "mettle": 0,
        }
        self.actions = 1
        self.additional_skills: list[str] = []
        self.onhit_states = {}
        self.wear_states = {}
        self.immune_states = []
        self.interactions = ["talk"]
        self.invulnerable = False
        self.prototypes = []
        self.following: Optional[str] = None

    def __setattr__(self, attr, value):
        self.__dict__[attr] = value
        database.memory_npcs[self.__dict__["_id"]][attr] = value

    def __getattr__(self, attr):
        self.__dict__[attr] = database.memory_npcs[self.__dict__["_id"]][attr]
        return self.__dict__[attr]

    def get_dict(self) -> dict:
        out = deepcopy(database.memory_npcs[self.__dict__["_id"]])
        return out

    def make_spoils(self, num_players: int) -> dict:
        if self.grist_category is None or self.grist_type is None:
            return {}
        spoils_dict = {}
        grist_list = config.gristcategories[self.grist_category]
        grist_index = grist_list.index(self.grist_type)
        tier = config.grists[self.grist_type]["tier"]
        spoils_dict["build"] = self.power
        spoils_dict[self.grist_type] = self.power
        for i in reversed(range(grist_index)):
            next_grist = grist_list[i]
            tier = config.grists[next_grist]["tier"]
            amount = (self.power // (tier)) // (i * 0.5 + 2)
            if amount == 0:
                break
            spoils_dict[next_grist] = amount
        for grist_name, amount in spoils_dict.copy().items():
            if num_players == 0:
                continue
            new_amount = amount * (0.5 + random.random())
            new_amount = math.ceil(new_amount / num_players)
            spoils_dict[grist_name] = new_amount
        return spoils_dict

    def prototype_with_item(
        self,
        item_name: str,
        inherit_all_skills=False,
        nickname=False,
        additive_power=False,
    ):
        item = alchemy.Item(item_name)
        if additive_power:
            self.power += item.power + item.inheritpower
        else:
            power_mult = 1 + (item.power + item.inheritpower) / 100
            self.power = int(self.power * power_mult)
        # inherit onhits and wears
        inherited_onhits = item.onhit_states.copy()
        inherited_wears = item.wear_states.copy()
        for state_name, potency in item.secret_states.items():
            if random.random() < 0.25:  # only a chance to inherit secret states
                choice = random.choice(["onhit", "wear"])
                if choice == "onhit":
                    if state_name not in inherited_onhits:
                        inherited_onhits[state_name] = potency
                    elif inherited_onhits[state_name] < potency:
                        inherited_onhits[state_name] = potency
                else:
                    if state_name not in inherited_wears:
                        inherited_wears[state_name] = potency
                    elif inherited_wears[state_name] < potency:
                        inherited_wears[state_name] = potency
        for state_name, potency in inherited_onhits.items():
            if state_name not in self.onhit_states:
                self.onhit_states[state_name] = potency
            elif self.onhit_states[state_name] < potency:
                self.onhit_states[state_name] = potency
        for state_name, potency in inherited_wears.items():
            if state_name not in self.wear_states:
                self.wear_states[state_name] = potency
            elif self.wear_states[state_name] < potency:
                self.wear_states[state_name] = potency
        # inherit specibus skills
        for kind_name in item.kinds:
            if kind_name in skills.abstratus_skills:
                for skill_name, required_rung in skills.abstratus_skills[
                    kind_name
                ].items():
                    if inherit_all_skills or self.power >= required_rung * 10:
                        if skill_name not in self.additional_skills:
                            self.additional_skills.append(skill_name)
        # nickname
        if nickname:
            new_adjective = random.choice(item.adjectives + item.secretadjectives)
            self.nickname = f"{new_adjective.replace('+',' ')} {self.nickname}"

    @property
    def name(self):
        return self.__dict__["_id"]

    def follow(self, player: "sessions.SubPlayer"):
        self.unfollow()
        player.npc_followers.append(self.name)
        self.following = player.name

    def unfollow(self):
        if self.following is not None:
            following_player = sessions.SubPlayer.from_name(self.following)
            following_player.npc_followers.remove(self.name)
            self.following = None

    def goto_room(self, room: "sessions.Room"):
        if self.session_name is not None and self.session != room.session:
            if self.name in self.session.current_players:
                self.session.current_players.remove(self.name)
        if self.room_name is not None:
            if self.room.strife is not None and self.name in self.room.strife.griefers:
                return
            self.room.remove_npc(self)
        self.session_name = room.session.name
        self.overmap_name = room.overmap.name
        self.map_name = room.map.name
        self.room_name = room.name
        room.add_npc(self)

    @property
    def session(self) -> "sessions.Session":
        assert self.session_name is not None
        return sessions.Session(self.session_name)

    @property
    def overmap(self) -> "sessions.Overmap":
        assert self.overmap_name is not None
        return sessions.Overmap(self.overmap_name, self.session)

    @property
    def map(self) -> "sessions.Map":
        assert self.map_name is not None
        return sessions.Map(self.map_name, self.session, self.overmap)

    @property
    def room(self) -> "sessions.Room":
        assert self.room_name is not None
        return sessions.Room(self.room_name, self.session, self.overmap, self.map)


class KernelAI(GrieferAI):
    name = "kernel"

    def ai_choose_skill(self, user: "strife.Griefer") -> Optional[str]:
        return "abstain"


KernelAI()


class SpriteAI(GrieferAI):
    name = "sprite"

    def ai_choose_skill(self, user: "strife.Griefer") -> Optional[str]:
        if skills.skills["amend"].is_submittable_by(user):
            return "amend"
        return super().ai_choose_skill(user)


SpriteAI()


class KernelSprite(Npc):
    @classmethod
    def spawn_new(cls, player: "sessions.SubPlayer"):
        name = Npc.make_valid_name("kernel")
        sprite = cls(name)
        sprite.type = "kernelsprite"
        sprite.hostile = False
        sprite.power = 1
        sprite.nickname = "kernelsprite"
        sprite.invulnerable = True
        sprite.additional_skills.append("abstain")
        sprite.interactions.append("prototype")
        sprite.ai_type = "kernel"
        sprite.follow(player)
        sprite.goto_room(player.room)
        return sprite


class Consort(Npc):
    @classmethod
    def spawn_new(cls, player: "sessions.SubPlayer"):
        consort_type = "salamander"  # todo: type is selected by players
        name = Npc.make_valid_name(consort_type)
        consort = cls(name)
        consort.type = f"consort_{consort_type}"
        consort.hostile = False
        consort.power = 1
        consort.nickname = consort_type  # todo: random adjective
        consort.invulnerable = True
        consort.interactions.append("follow")
        consort.color = player.color  # todo: color is separate from player color
        return consort


class NpcInteraction:
    def __init__(self, name):
        self.name = name
        npc_interactions[self.name] = self

    def use(
        self,
        player: "sessions.SubPlayer",
        target: "Npc",
        additional_data: dict[str, str],
    ):
        pass


class NpcTalk(NpcInteraction):
    def use(
        self,
        player: "sessions.SubPlayer",
        target: "Npc",
        additional_data: dict[str, str],
    ):
        if target.type == "kernelsprite":
            symbols = list("•❤♫☎°♨✈✣☏■■■☀➑➑➑✂✉✉☼☆★☁☁♕♕♕♕♠♠✪░░▒▒▓▓██■¿.!≡")
            out = []
            for i in range(random.randint(10, 30)):
                out.append(random.choice(symbols))
            return f'KERNELSPRITE: {"".join(out)}'
        elif target.type == "sprite":
            possible_questions = [
                "about what the point of the game is",
                "what happens if you don't win",
                "why alchemy is like this",
                "who made this game",
                f"what being the {player.title} means",
                "if it can just bring you to the Seventh Gate",
                "if your actions even really matter",
                "when the Reckoning is going to happen",
                "what's up with the gold and purple planets",
                "what the fuck a dream self is",
                "where your guardian is",
                "if you made a mistake prototyping it",
            ]
            possible_responses = [
                ", and it dodges the question.",
                ", and it casually avoids answering you.",
                ", and it responds with some asshole riddle.",
                ", and it tells you that you're not ready to know that yet.",
                ", and it almost tells you, but quickly realizes that it shouldn't.",
                ", and it tells you, but its explanation is impossible to follow.",
                ", but it apparently wasn't listening.",
                ", and it responds with an infuriatingly vague answer.",
            ]
            possible_lines = [
                f"{target.nickname.capitalize()} says some nonsense about an Ultimate Riddle or some shit.",
                f'{target.nickname.capitalize()} is talking about some "{player.title}." Sounds like a loser.',
                f"{target.nickname.capitalize()} is being coy with some riddlesome bullshit again.",
                f"{target.nickname.capitalize()} gives you a riddle you're not bothering to solve.",
                f"{target.nickname.capitalize()} says something about The Choice but you're not really listening.",
            ]
            for question in possible_questions:
                for response in possible_responses:
                    possible_lines.append(
                        f"You ask {target.nickname.capitalize()} {question}{response}"
                    )
            return random.choice(possible_lines)
        else:
            return f"The {target.nickname} does not seem like one for friendly conversation."


NpcTalk("talk")


class NpcFollow(NpcInteraction):
    def use(
        self,
        player: "sessions.SubPlayer",
        target: "Npc",
        additional_data: dict[str, str],
    ):
        if target.following == player.name:
            target.unfollow()
            return f"{target.nickname.capitalize()} is no longer following you!"
        else:
            target.follow(player)
            return f"{target.nickname.capitalize()} is now following you!"


NpcFollow("follow")


class NpcPrototype(NpcInteraction):
    def use(
        self,
        player: "sessions.SubPlayer",
        target: "KernelSprite",
        additional_data: dict[str, str],
    ):
        instance_name = additional_data["instance_name"]
        if (
            instance_name not in player.sylladex
            and instance_name not in player.room.instances
        ):
            return False
        instance = alchemy.Instance(instance_name)
        prototyped_item = instance.item
        old_name = target.nickname
        if (
            player.entered
            and prototyped_item.power + prototyped_item.inheritpower > 200
        ):
            return f"{target.nickname.capitalize()} dodges the {prototyped_item.displayname}!"
        if target.type == "kernelsprite":
            target.type = "sprite"
            target.ai_type = "sprite"
            target.additional_skills.append("amend")
            target.interactions.append("follow")
            target.color = player.color
            player.prototyped_before_entry = True
            if prototyped_item.prototype_name is not None:
                sprite_name = prototyped_item.prototype_name.replace("+", "").lower()
            else:
                sprite_name = prototyped_item.base.replace("+", "").lower()
            target.nickname = f"{sprite_name}sprite"
            target.prototypes.append(prototyped_item.name)
            target.prototype_with_item(
                prototyped_item.name, inherit_all_skills=True, additive_power=True
            )
            if instance_name in player.sylladex:
                player.sylladex.remove(instance_name)
            elif instance_name in player.room.instances:
                player.room.remove_instance(instance_name)
            if not player.entered:
                player.session.prototypes.append(prototyped_item.name)
            return f"{old_name.upper()} became {target.nickname.upper()}!"
        else:  # sprite was already prototyped
            if prototyped_item.name in target.prototypes:
                target.nickname = f"2x{target.nickname}"
            else:
                sprite_adjective = (
                    random.choice(
                        prototyped_item.adjectives + prototyped_item.secretadjectives
                    )
                    .replace("+", "")
                    .lower()
                )
                target.nickname = f"{sprite_adjective}{target.nickname}"
            target.interactions.remove("prototype")
            target.prototypes.append(prototyped_item.name)
            target.prototype_with_item(
                prototyped_item.name, inherit_all_skills=True, additive_power=True
            )
            if instance_name in player.sylladex:
                player.sylladex.remove(instance_name)
            elif instance_name in player.room.instances:
                player.room.remove_instance(instance_name)
            if not player.entered:
                player.session.prototypes.append(prototyped_item.name)
            return f"{old_name.upper()} became {target.nickname.upper()}!"


NpcPrototype("prototype")

if __name__ == "__main__":
    print(griefer_ai)
