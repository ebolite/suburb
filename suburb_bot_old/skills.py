import explore
import alchemy
import stateseffects
import aspects
import config
import util

skills = {}
passives = {}
weaponskills = {}
validskills = []
defaults = []
noenemy = []

class Skill():
    def __init__(self, name):
        self.name = name
        self.description = "tell maxim to add a description for this"
        self.beneficial = False
        self.allflavor = "" # what is printed before each individual target
        self.flavor = "" # what is printed on each target
        self.eqtn = "0" # if eqtn is empty, uses weapon dice instead.
        self.learnlevel = 0 # for weapon skills, what power should this be usable at?
        self.dmgmult = 1 # for dice roll stuff
        self.targets = 1
        self.targetself = False
        self.targetsall = False
        self.actioncost = 1
        self.cooldown = 0
        self.warmup = 0
        self.vimcost = "0"
        self.aspectcost = "0"
        self.trivialactioncost = 0
        self.enemyskill = True
        self.effects = {}
        self.damageeffects = False # whether damage must be dealt to apply effects
        self.custom = [] # exec these on each target
        validskills.append(name)
        skills[name] = self

    async def __call__(self, Strife, user, targetlist):
        user = Strife.battlers[user]
        targetlist = set(targetlist) # clear duplicates
        targetlist = list(targetlist)
        if self.targetself:
            targetlist = [user.name]
        if self.targetsall:
            if len(targetlist) != 0:
                t = Strife.battlers[targetlist[0]]
            else:
                if self.beneficial == True:
                    t = user
                else:
                    t = None
            for bat in Strife.battlers:
                b = Strife.battlers[bat]
                if t != None:
                    if b.team == t.team and b.name not in targetlist:
                        targetlist.append(b.name)
                else:
                    if b.team != user.team and b.name not in targetlist:
                        targetlist.append(b.name)
        #costs
        user.actions -= self.actioncost
        if user.trivialactions < self.trivialactioncost:
            user.trivialactions -= self.trivialactioncost
            negative = user.trivialactions
            user.trivialactions = 0
            user.actions += negative
        else:
            user.trivialactions -= self.trivialactioncost
        user.changevial("vim", -1 * int(eval(self.vimcost)))
        if "aspect" in user.vials:
            user.changevial("aspect", -1 * int(eval(self.aspectcost)))
        if self.cooldown != 0:
            user.cooldowns[self.name] = user.Strife.turn + self.cooldown
        #flavor
        if self.allflavor != "":
            m = self.flavorformat(self.allflavor, user)
            Strife.logmessages.append(m)
        for i in range(self.targets):
            if i >= len(targetlist):
                break
            target = Strife.battlers[targetlist[i]]
            #damage
            if self.eqtn != "0":
                if self.eqtn == "":
                    roll = user.roll(user.dicemin, user.dicemax)
                    dmg = -1 * user.roll(user.dicemin, user.dicemax)
                else:
                    dmg = eval(self.eqtn)
                if dmg < 0:
                    dmg *= user.dealmult
                    dmg += user.dealonhit
                if type(user) == explore.EnemyBattler:
                    dmg *= .85 # enemies do 15% less damage
                    ratio = user.getstat("POWER") / target.getstat("POWER")
                    if ratio > 1:
                        mult = .8 * (1/ratio) + .2
                        dmg *= mult
                if type(self.dmgmult) == str:
                    dmgmult = eval(self.dmgmult)
                else:
                    dmgmult = self.dmgmult
                dmg *= dmgmult
                change = target.damage(dmg)
                #flavor
                if self.flavor != "":
                    m = self.flavorformat(self.flavor, user, target)
                    Strife.logmessages.append(m)
                if change == "parry":
                    if "horseshitometer" in user.vials:
                        user.changevial("horseshitometer", dmg//4)
                    Strife.logmessages.append(f"{target.name} AUTO-PARRIES!")
                elif change > 0:
                    Strife.logmessages.append(f"{target.name} was healed by {change} ({round((change/target.vials['health']['maximum']) * 100)}%)!")
                elif change < 0:
                    Strife.logmessages.append(f"{target.name} was damaged by {change * -1} ({round((change/target.vials['health']['maximum']) * -100)}%)!")
                elif change == 0 and self.eqtn != "0":
                    Strife.logmessages.append(f"{target.name} was undamaged!")
                if user.wielding != None and type(change) != str and change != 0:
                    inst = alchemy.Instance(user.wielding)
                    if "gambit" in user.vials and "humorous" in inst.Item.tags:
                        user.changevial("gambit", -1 * change//2)
                    if "gambit" in target.vials and "humorous" in inst.Item.tags:
                        target.changevial("gambit", change//2)
                if user.wielding != None and type(change) != str and change < 0:
                    inst = alchemy.Instance(user.wielding)
                    for effect in inst.Item.onhiteffect:
                        if effect in stateseffects.effects:
                            effectobj = stateseffects.effects[effect]
                            p = inst.Item.onhiteffect[effect][0]
                            out = effectobj.effect(user, target, p)
                            if out != "":
                                Strife.logmessages.append(out)
                        else:
                            print(f"!!TRIED TO APPLY NON-VALID EFFECT {effect}!!")
            else: change = 0
            if len(self.effects) != 0 and change != "parry" and (self.damageeffects == False or change < 0):
                for effect in self.effects:
                    effectobj = stateseffects.effects[effect]
                    out = effectobj.effect(user, target, self.effects[effect])
                    if out != "": Strife.logmessages.append(out)
            if len(self.custom) != 0:
                for custom in self.custom:
                    out = eval(custom)
                    if out != "" and out != None: Strife.logmessages.append(out)

    def usecheck(self, Strife, user): #returns True if skill can be used
        if self.name in user.cooldowns:
            if user.cooldowns[self.name] > user.Strife.turn:
                return f"That skill is still on cooldown until turn {user.cooldowns[self.name]}."
        if user.Strife.turn < self.warmup:
            return f"That skill is still warming up! Can be used on turn {self.warmup}."
        if user.actions < self.actioncost:
            return f"Not enough actions. Have: {user.actions} Need: {self.actioncost}"
        if user.trivialactions < self.trivialactioncost:
            if user.actions + user.trivialactions < self.trivialactioncost:
                return f"Not enough trivial actions / actions. Have: {user.actions + user.trivialactions} Need: {self.trivialactioncost}"
        if user.vials["vim"]["value"] < int(eval(self.vimcost)):
            return f"Not enough VIM! Needs: {int(eval(self.vimcost))} ({round(eval(self.vimcost) / user.vials['vim']['maximum'] * 100)}%)"
        if "aspect" in user.vials and user.vials["aspect"]["value"] < int(eval(self.aspectcost)):
            return f"Not enough ASPECT! Needs: {int(eval(self.aspectcost))} ({round(eval(self.aspectcost) / user.vials['aspect']['maximum'] * 100)}%)"
        return True

    def flavorformat(self, text, user, target=None):
        text = text.replace("USER", user.name)
        if target != None:
            text = text.replace("TARGET", target.name)
        if type(user) == explore.PlayerBattler:
            text = text.replace("THEY", user.they)
            text = text.replace("THEM", user.them)
            text = text.replace("THEIR", user.their)
            text = text.replace("THEIRS", user.theirs)
        else:
            text = text.replace("THEY", "it")
            text = text.replace("THEM", "it")
            text = text.replace("THEIR", "its")
            text = text.replace("THEIRS", "its")
        return text

    def describe(self):
        text = ""
        text += f"{self.description}\n"
        if self.vimcost != "0":
            text += f"`vim cost` {self.vimcost}\n"
        if self.aspectcost != "0":
            text += f"`aspect cost` {self.aspectcost}\n"
        if self.actioncost != 1:
            text += f"`action cost` {self.actioncost}\n"
        if self.trivialactioncost != 0:
            text += f"`trivial action cost` {self.trivialactioncost}\n"
        if self.cooldown != 0:
            text += f"`cooldown` {self.cooldown}\n"
        if self.warmup != 0:
            text += f"`warmup` {self.warmup}\n"
        if self.dmgmult != 1:
            text += f"`damage multiplier` {self.dmgmult}\n"
        if self.targetself:
            text += f"`targets self`\n"
        for eff in self.effects:
            text += f"`{eff} {self.effects[eff]}` "
        return text

    @property
    def default(self):
        return self.name in defaults

    @default.setter
    def default(self, value):
        if value == True and self.name not in defaults:
            defaults.append(self.name)
        elif value == False and self.name in defaults:
            defaults.remove(self.name)

    @property
    def enemyskill(self):
        return not self.name in noenemy

    @enemyskill.setter
    def enemyskill(self, value):
        if value == True and self.name in noenemy:
            noenemy.remove(self.name)
        elif value == False and self.name not in noenemy:
            noenemy.append(self.name)


# flavor formatting:
# USER: user name
# TARGET: target name
# THEY: user they pronoun
# THEM: user them pronoun
# THEIR: user their pronoun
# THEIRS: user theirs pronoun

aggrieve = Skill("aggrieve")
aggrieve.description = "Deals non-weapon-based damage."
aggrieve.eqtn = "-0.7 * user.getstat('POWER')"
aggrieve.flavor = "USER aggrieves TARGET!"
aggrieve.default = True

aggress = Skill("aggress")
aggress.description = "Deals damage."
aggress.eqtn = ""
aggress.flavor = "USER aggresses TARGET!"
aggress.default = True

assail = Skill("assail")
assail.description = "Deals increased damage but costs VIM."
assail.eqtn = ""
assail.dmgmult = 1.5
assail.flavor = "USER assails TARGET!"
assail.default = True
assail.vimcost = "user.getstat('POWER') * 0.66"

assault = Skill("assault")
assault.description = "Deals highly increased damage but costs a lot of VIM."
assault.eqtn = ""
assault.dmgmult = 2
assault.flavor = "USER assaults TARGET!"
assault.default = True
assault.vimcost = "user.getstat('POWER') * 2"

abstain = Skill("abstain")
abstain.description = "Does nothing, but restores VIM and ASPECT."
abstain.eqtn = "0"
abstain.allflavor = "USER abstains!"
abstain.default = True
abstain.enemyskill = False
abstain.vimcost = "-1 * (user.getstat('TAC') + user.getstat('POWER'))"
abstain.aspectcost = "-0.5 * (user.getstat('TAC') + user.getstat('POWER'))"

abjure = Skill("abjure")
abjure.description = "Applies `abjure` which reduces damage by 50%."
abjure.eqtn = "0"
abjure.allflavor = "USER abjures!"
abjure.default = True
abjure.targetself = True
abjure.effects = {"applyabjure": 1}
abjure.cooldown = 3

abuse = Skill("abuse")
abuse.description = "Deals less damage than `aggress` but has a chance to apply `stunned`."
abuse.eqtn = ""
abuse.dmgmult = 0.7
abuse.effects = {"stun": 0.5}
abuse.damageeffects = True
abuse.flavor = "USER abuses TARGET!"
abuse.default = True
abuse.vimcost = "user.getstat('POWER') * 0.66"

# weapon skills

weaponskills = {
    "3dentkind": [
        "strike"
        ],
    "aerosolkind": [
        "spray"
        ],
    "appliancekind": [
        "slam"
        ],
    "axekind": [
        "slice",
        "cleave"
        ],
    "bagkind": [
        "suffocate"
        ],
    "ballkind": [
        "slam"
        ],
    "batkind": [
        "slam",
        "strike"
        ],
    "bladekind": [
        "slice",
        "strike"
        ],
    "bookkind": [
        "slam"
        ],
    "bottlekind": [
        "splash",
        "slam"
        ],
    "broomkind": [
        "slam",
        "satirize"
        ],
    "bustkindkind": [
        "slam",
        "satirize"
        ],
    "canekind": [
        "strike"
        ],
    "cankind": [
        "splash"
        ],
    "cardkind": [
        "slice"
        ],
    "chainkind": [
        "slam"
        ],
    "chainsawkind": [
        "slice"
        ],
    "cleaverkind": [
        "slice",
        "cleave"
        ],
    "cordkind": [
        "suffocate"
        ],
    "crowbarkind": [
        "slam",
        "strike"
        ]
    }

# level 0 skills

slice = Skill("slice")
slice.description = "Deals damage and applies BLEED of power 0.7."
slice.flavor = "USER slices TARGET!"
slice.eqtn = ""
slice.learnlevel = 0
slice.effects = {"bleed": 0.7}
slice.damageeffects = True
slice.vimcost = "user.getstat('POWER') * 0.5"

slam = Skill("slam")
slam.description = "Deals damage and applies STUN of power 0.7."
slam.flavor = "USER slams TARGET!"
slam.eqtn = ""
slam.learnlevel = 0
slam.effects = {"stun": 0.7}
slam.damageeffects = True
slam.vimcost = "user.getstat('POWER') * 0.5"

strike = Skill("strike")
strike.description = "Deals damage and applies DAMAGE of power 0.3."
strike.flavor = "USER strikes TARGET!"
strike.eqtn = ""
strike.learnlevel = 0
strike.effects = {"damage": 0.3}
strike.damageeffects = True
strike.vimcost = "user.getstat('POWER') * 0.5"

splash = Skill("splash")
splash.description = "Deals damage and applies DOUSE of power 1."
splash.flavor = "USER splashes TARGET with liquid!"
splash.eqtn = ""
splash.learnlevel = 0
splash.effects = {"douse": 1}
splash.damageeffects = True
splash.vimcost = "user.getstat('POWER') * 0.1"

spray = Skill("spray")
spray.description = "Deals damage and applies BLIND of power 0.7."
spray.flavor = "USER sprays TARGET!"
spray.eqtn = ""
spray.learnlevel = 0
spray.effects = {"blinding": 0.7}
spray.damageeffects = True
spray.vimcost = "user.getstat('POWER') * 0.5"

suffocate = Skill("suffocate")
suffocate.description = "Deals damage and applies NUMBED and WEAK of power 0.5."
suffocate.flavor = "USER suffocates TARGET!"
suffocate.eqtn = ""
suffocate.learnlevel = 0
suffocate.effects = {"numb": 0.5, "weakness": 0.5}
suffocate.damageeffects = True
suffocate.vimcost = "user.getstat('POWER') * 0.5"

satirize = Skill("satirize")
satirize.description = "Deals damage and applies DEMORALIZE of power 0.5."
satirize.flavor = "USER satirizes TARGET!"
satirize.eqtn = ""
satirize.learnlevel = 0
satirize.effects = {"demoralize": 0.5}
satirize.damageeffects = True
satirize.vimcost = "user.getstat('POWER') * 0.5"

# level 25 skills

cleave = Skill("cleave")
cleave.description = "Deals increased damage based off of the target's MISSING HEALTH."
cleave.eqtn = "aspects.doom.ratio(target) / 3"
cleave.learnlevel = 25
cleave.damageeffects = True
cleave.vimcost = "user.getstat('POWER') * 0.77"
cleave.cooldown = 2


# aspect skills

# space
distort = Skill("distort")
distort.description = "Deals non-weapon damage based on your SPACE."
distort.flavor = "USER distorts TARGET!"
distort.eqtn = "-1 * user.getstat('POWER') * aspects.space.ratio(user)"
distort.aspectcost = "user.getstat('POWER') * 0.4"
distort.cooldown = 2

# time
rewind = Skill("rewind")
rewind.description = "Increases your actions by 1 this turn."
rewind.allflavor = "USER rewinds!"
rewind.targetself = True
rewind.trivialactioncost = 1
rewind.actioncost = -1
rewind.aspectcost = "user.getstat('POWER') * 0.5"
rewind.cooldown = 2

# mind
educate = Skill("educate")
educate.description = "Increases the target's MIND."
educate.flavor = "USER educates TARGET!"
educate.cooldown = 2
educate.custom = ["aspects.mind.adjust(target, user.getstat('POWER'))"]
educate.aspectcost = "user.getstat('POWER') * 0.5"

# heart
emote = Skill("emote")
emote.description = "Increases the target's HEART."
emote.flavor = "USER emotes TARGET!"
emote.cooldown = 2
emote.custom = ["aspects.heart.adjust(target, user.getstat('POWER'))"]
emote.aspectcost = "user.getstat('POWER') * 0.5"

# hope
pray = Skill("pray")
pray.description = "Increases the target's HOPE."
pray.allflavor = "USER prays!"
pray.cooldown = 1
pray.actioncost = 0
pray.trivialactioncost = 1
pray.aspectcost = "user.getstat('POWER') * 0.2"
pray.custom = ["aspects.hope.adjust(target, user.getstat('POWER'))"]

# rage
seethe = Skill("seethe")
seethe.description = "Increases the target's RAGE."
seethe.allflavor = "USER seethes!"
seethe.cooldown = 1
seethe.actioncost = 0
seethe.trivialactioncost = 1
seethe.aspectcost = "user.getstat('POWER') * 0.2"
seethe.custom = ["aspects.rage.adjust(target, user.getstat('POWER'))"]

# breath
blow = Skill("blow")
blow.description = "Deals damage based purely on your SAVVY stat."
blow.flavor = "USER blows wind at TARGET!"
blow.eqtn = "user.getstat('SAV') * -3"
blow.aspectcost = "user.getstat('POWER') * 0.3"

# blood
bleed = Skill("bleed")
bleed.description = "Deals damage based on your BLOOD."
bleed.flavor = "USER attacks TARGET with blood!"
bleed.eqtn = ""
bleed.dmgmult = "aspects.blood.ratio(user)"
bleed.aspectcost = "user.getstat('POWER') * 0.5"
bleed.vimcost = "user.getstat('POWER') * 0.6"
bleed.cooldown = 2

# life
heal = Skill("heal")
heal.description = "Increases the target's LIFE."
heal.flavor = "USER heals TARGET!"
heal.cooldown = 2
heal.custom = ["aspects.life.adjust(target, user.getstat('POWER'))"]
heal.aspectcost = "user.getstat('POWER') * 0.5"

# light
charm = Skill("charm")
charm.description = "Increases the user's LIGHT."
charm.allflavor = "USER uses a charm!"
charm.targetself = True
charm.actioncost = 0
charm.trivialactioncost = 1
charm.custom = ["aspects.light.adjust(target, user.getstat('POWER'))"]
charm.aspectcost = "user.getstat('POWER') * 0.5"

# doom
curse = Skill("curse")
curse.description = "Increases the target's DOOM."
curse.flavor = "USER curses TARGET!"
curse.custom = ["aspects.doom.adjust(target, user.getstat('POWER'))"]
curse.aspectcost = "user.getstat('POWER') * 0.3"

# void
lessen = Skill("lessen")
lessen.description = "Increases the target's VOID."
lessen.flavor = "USER lessens TARGET!"
lessen.custom = ["aspects.void.adjust(target, user.getstat('POWER') * 2)"]
lessen.aspectcost = "user.getstat('POWER') * 0.2"

class Passive():
    def __init__(self, name):
        self.name = name
        self.description = "tell maxim to add a description"
        self.evadebonus = "0" # as 0-1
        self.statadds = {} # all = all base stats
        self.statmults = {} # all = all base stats
        self.customstart = None # exec on battle start
        self.customcall = None # exec each turn
        passives[name] = self

    def battlestart(self, battler):
        out = []
        if self.customstart != None:
            o = self.customstart(battler)
            if o != None and o != "":
                out.append(o)
        if out == []:
            return ""
        else:
            return "\n".join(out)

    def __call__(self, battler):
        out = []
        if self.customcall != None:
            o = self.customcall(battler)
            if o != None and o != "":
                out.append(o)
        if out == []:
            return ""
        else:
            return "\n".join(out)

# space
def massivef(battler):
    change = (aspects.space.ratio(battler) // (16 - ((battler.getstat('RUNG') * 4) / 413))) * battler.getstat("POWER", True)
    battler.vials["health"]["maximum"] += int(change)
    battler.changevial("health", change)

massive = Passive("massive")
massive.description = "Gain a boost to your maximum health based on your MET. Gains more power the higher your echeladder rung is."
massive.customstart = massivef

# time
def warpf(battler):
    battler.actions += 1 + (battler.getstat('RUNG') // 413)

warp = Passive("warp")
warp.description = "Gives an extra action at the start of combat. Gives an additional action every 413 echeladder rungs."
warp.customstart = warpf

# mind
def thoughtfulf(battler):
    value = battler.getstat('POWER', True) * 0.4 * (1 + (battler.getstat('RUNG') / 413))
    aspects.mind.adjust(battler, value)

thoughtful = Passive("thoughtful")
thoughtful.description = "Start the battle with a bit of your secondary gauge filled. Start with more the higher your echeladder rung is."
thoughtful.customstart = thoughtfulf

# heart
def soulfulf(battler):
     value = battler.getstat('POWER', True) * (aspects.heart.ratio(battler) / (4 - (battler.getstat('RUNG') / 413)))
     aspects.heart.maxadjust(battler, value)

soulful = Passive("soulful")
soulful.description = "Gain even more maximum health depending on your VIGOR. This bonus increases the higher your echeladder rung is."
soulful.customstart = soulfulf

# hope
def saviorf(battler):
    value = battler.getstat("POWER", True) * (0.4 * (1 + (battler.getstat('RUNG') / 413)))
    aspects.hope.adjust(battler, value)

savior = Passive("savior")
savior.description = "Generate HOPE each turn. This bonus increases the higher your echeladder rung is."
savior.customcall = saviorf

# rage
def copef(battler):
    value = battler.getstat("POWER", True) * (0.4 * (1 + (battler.getstat('RUNG') / 413)))
    aspects.rage.adjust(battler, value)

cope = Passive("cope")
cope.description = "Generate RAGE each turn. This bonus increases the higher your echeladder rung is."
cope.customcall = copef

# breath
#note: this is custom in the Battler.damage method
gaseous = Passive("gaseous")
gaseous.description = "Gain a flat chance to AUTO-PARRY attacks that would have otherwise hit you. This chance increases the higher your echeladder rung is."
gaseous.evadebonus = ".1 * (1 + (battler.getstat('RUNG') / 413))"

# blood
def circulationf(battler):
    value = battler.getstat("POWER", True) * (0.4 * (1 + (battler.getstat('RUNG') / 413)))
    aspects.blood.adjust(battler, value)

circulation = Passive("circulation")
circulation.description = "Generate BLOOD every turn. This bonus increases the higher your echeladder rung is."
circulation.customcall = circulationf

# life
livid = Passive("livid")
livid.description = "Gain a bonus to all stats based on how much LIFE you have left. This bonus increases the higher your echeladder rung is."
livid.statmults["all"] = "aspects.life.ratio(battler) / (32 / (1 + (battler.getstat('RUNG') / 413)))"

# light
#note: this is custom in the Battler.dicemin and Battler.dicemax methods
gambler = Passive("gambler")
gambler.description = "Your maximum attack dice rolls get larger, but your minimum dice rolls get smaller. This effect is more powerful the higher your echeladder rung is."

# doom
edgy = Passive("edgy")
edgy.description = "Gain a boost to your power based on your missing health. Gains additional power the higher your echeladder rung is."
edgy.statadds["POWER"] = "aspects.doom.ratio(battler) // (max(4-(battler.getstat('RUNG') / 413), 1))"

# void
def emptyf(battler):
    bonus = battler.getstat('POWER', True) * (((battler.getstat('RUNG') / 413) + 1) * .2)
    battler.vials["aspect"]["maximum"] += int(bonus)

empty = Passive("empty")
empty.description = "Gain a bonus to your maximum ASPECT at the start of battle, but ONLY the maximum. This bonus is higher the higher your echeladder rung is."
empty.customstart = emptyf


#CLASSES
for aname in aspects.aspects:
    aspect = aspects.aspects[aname]

    # THIEF

    # skill - steal

    def stealeffectfconstructor(aspect):
        def stealeffectf(effect, inflictor, battler, power=1):
            o = ""
            ratio = aspect.ratio(battler)
            o += aspect.adjust(battler, -0.7 * battler.getstat("POWER") * ratio)
            o += "\n"
            o += aspect.adjust(inflictor, 0.7 * min(inflictor.getstat("POWER") * 2, battler.getstat("POWER")) * ratio)
            if inflictor.Player.aspectbonus == None:
                inflictor.Player.aspectbonus = {}
            if aspect.name not in inflictor.Player.aspectbonus:
                inflictor.Player.aspectbonus[aspect.name] = 0
            if inflictor != battler:
                bonusincrease = int(.04 * battler.getstat("POWER") * ratio)
                inflictor.Player.aspectbonus[aspect.name] += bonusincrease
                o += f"\n{inflictor.name}'s BONUS {aspect.maxaspect} permanently increased by {bonusincrease}!"
            return o
        return stealeffectf

    stealeffect = stateseffects.Effect(f"{aspect.name} stealeffect")
    stealeffect.customs = [stealeffectfconstructor(aspect)]

    steal = Skill(f"{aspect.name}-steal")
    steal.description = f"Steals {aspect.aspect} from the target and gives it to the user. Has permanent effects."
    steal.effects = {f"{aspect.name} stealeffect": 1}
    steal.aspectcost = "user.getstat('POWER') * 0.3"
    steal.vimcost = "user.getstat('POWER') * 0.1"
    steal.flavor = f"USER steals TARGET's {aspect.aspect}!"
    steal.cooldown = 2

    config.classskills["thief"][aspect.name][f"{aspect.name}-steal"] = 30

    def thieffconstructor(aspect):
        def thieff(battler):
            if battler.Player.aspectbonus == None:
                battler.Player.aspectbonus = {}
            if aspect.name not in battler.Player.aspectbonus:
                battler.Player.aspectbonus[aspect.name] = 0
            out = f"{battler.name} gets {battler.their}  bonus from being the THIEF OF {aspect.aspect}!\n"
            out += aspect.maxadjust(battler, battler.Player.aspectbonus[aspect.name])
            return out
        return thieff

    thief = Passive(f"thief of {aspect.name}")
    thief.description = f"Gain a permanent bonus to your {aspect.maxaspect} based on how much {aspect.aspect} you have stolen."
    thief.customstart = thieffconstructor(aspect)

    config.classpassives["thief"][aspect.name][f"thief of {aspect.name}"] = 30

    # skill - robbery

    robbery = Skill(f"{aspect.name}-robbery")
    robbery.description = f"Deals damage based on how little {aspect.aspect} the target has."
    robbery.eqtn = ""
    robbery.dmgmult = f"aspects.{aspect.name}.inverseratio(target) / 1.5"
    robbery.aspectcost = "user.getstat('POWER') * 0.5"
    robbery.vimcost = "user.getstat('POWER') * 0.2"
    robbery.flavor = f"USER robs TARGET blind!"
    robbery.cooldown = 1

    config.classskills["thief"][aspect.name][f"{aspect.name}-robbery"] = 100

    # ROGUE

    # skill - loot
    def looteffectfconstructor(aspect):
        def looteffectf(effect, inflictor, battler, power=1):
            o = ""
            ratio = aspect.ratio(battler)
            o += aspect.adjust(battler, -0.5 * battler.getstat("POWER") * ratio)
            for bat in inflictor.Strife.battlers:
                b = inflictor.Strife.battlers[bat]
                if b.team == inflictor.team:
                    o += "\n"
                    o += aspect.adjust(b, 0.5 * min(b.getstat("POWER") * 2, battler.getstat("POWER")) * ratio)
            if inflictor != battler:
                bonusincrease = int(.02 * battler.getstat("POWER") * ratio)
                for id in util.sessions[inflictor.Player.session]["members"]:
                    p = explore.Player(id)
                    if p.aspectbonus == None:
                        p.aspectbonus = {}
                    if aspect.name not in p.aspectbonus:
                        p.aspectbonus[aspect.name] = 0
                    p.aspectbonus[aspect.name] += bonusincrease
                o += f"\nSession {inflictor.Player.session}'s BONUS {aspect.maxaspect} permanently increased by {bonusincrease}!"
            return o
        return looteffectf

    looteffect = stateseffects.Effect(f"{aspect.name} looteffect")
    looteffect.customs = [looteffectfconstructor(aspect)]

    loot = Skill(f"{aspect.name}-loot")
    loot.description = f"Loots {aspect.aspect} from the target and gives it to everyone in the user's session. Has permanent effects."
    loot.flavor = f"USER loots TARGET's {aspect.aspect}!"
    loot.effects = {f"{aspect.name} looteffect": 1}
    loot.aspectcost = "user.getstat('POWER') * 0.3"
    loot.cooldown = 2

    config.classskills["rogue"][aspect.name][f"{aspect.name}-loot"] = 30

    # passive - redistribution

    def roguefconstructor(aspect):
        def roguef(battler):
            for id in util.sessions[battler.Player.session]["members"]:
                b = explore.Player(id)
                if f"redistribution of {aspect.name}" not in b.freepassives and b.Player.aspect != aspect.name and b.Player.gameclass != "rogue":
                    b.freepassives.append(f"redistribution of {aspect.name}")
                if b.aspectbonus == None:
                    b.aspectbonus = {}
                if aspect.name not in b.aspectbonus:
                    b.aspectbonus[aspect.name] = 0
            out = f"{battler.name} gets {battler.their} bonus from the ROGUE OF {aspect.aspect}!\n"
            if aspect.adjust != aspect.maxadjust:
                aspect.adjust(battler, battler.Player.aspectbonus[aspect.name] // 2)
                out += aspect.maxadjust(battler, battler.Player.aspectbonus[aspect.name] // 2)
            else:
                out += aspect.maxadjust(battler, battler.Player.aspectbonus[aspect.name])
            return out
        return roguef

    rogue = Passive(f"redistribution of {aspect.name}")
    rogue.description = f"Everyone in the session gains a permanent bonus to their {aspect.maxaspect} based on how much {aspect.aspect} the ROGUE OF {aspect.aspect} has stolen."
    rogue.customstart = roguefconstructor(aspect)

    config.classpassives["rogue"][aspect.name][f"redistribution of {aspect.name}"] = 30

    # passive - savvy
    savvy = Passive(f"{aspect.name} savvy")
    savvy.description = f"Gain a chance to AUTO-PARRY attacks based on your {aspect.aspect}."
    savvy.evadebonus = f".07 * (aspects.{aspect.name}.ratio(battler))"

    config.classpassives["rogue"][aspect.name][f"{aspect.name} savvy"] = 100

    # skill - heist
    def heisteffectfconstructor(aspect):
        def heisteffectf(effect, inflictor, battler, power=1):
            o = ""
            ratio = aspect.ratio(battler)
            for bat in inflictor.Strife.battlers:
                b = inflictor.Strife.battlers[bat]
                if b.team == inflictor.team:
                    aspect.adjust(b, 0.5 * min(b.getstat("POWER") * 2, battler.getstat("POWER")) * ratio)
            o += aspect.adjust(battler, -0.5 * battler.getstat("POWER") * ratio)
            if inflictor != battler:
                bonusincrease = int(.02 * battler.getstat("POWER") * ratio)
                for id in util.sessions[inflictor.Player.session]["members"]:
                    b = explore.Player(id)
                    if b.aspectbonus == None:
                        b.aspectbonus = {}
                    if aspect.name not in b.aspectbonus:
                        b.aspectbonus[aspect.name] = 0
                    b.aspectbonus[aspect.name] += bonusincrease
            return o
        return heisteffectf

    heisteffect = stateseffects.Effect(f"{aspect.name} heisteffect")
    heisteffect.customs = [heisteffectfconstructor(aspect)]

    heist = Skill(f"{aspect.name}heist")
    heist.description = f"Steals {aspect.aspect} from the entire enemy team and gives it to everyone in the user's session."
    heist.targetsall = True
    heist.allflavor = f"USER initiates the {aspect.aspect} HEIST!"
    heist.effects = {f"{aspect.name} heisteffect": 1}
    heist.aspectcost = "user.getstat('POWER') * 0.6"
    heist.vimcost = "user.getstat('POWER') * 0.4"
    heist.cooldown = 3
    heist.warmup = 2

    config.classskills["rogue"][aspect.name][f"{aspect.name}heist"] = 413

    # PRINCE

    # skill - blast
    blast = Skill(f"{aspect.name}blast")
    blast.description = f"Reduces the target's {aspect.aspect}. Costs a trivial action."
    blast.eqtn = "0"
    blast.actioncost = 0
    blast.trivialactioncost = 1
    blast.aspectcost = "user.getstat('POWER') * 0.4"
    blast.vimcost = "user.getstat('POWER') * 0.4"
    blast.custom = [f"aspects.{aspect.name}.adjust(target, -1 * user.getstat('POWER'))"]
    blast.allflavor = f"USER creates a blast of {aspect.aspect}!"

    config.classskills["prince"][aspect.name][f"{aspect.name}blast"] = 30

    # skill - beam
    beam = Skill(f"{aspect.name}beam")
    beam.description = f"Deals a lot of damage based on your {aspect.aspect} and heavily reduces the target's {aspect.aspect}. Also reduces your {aspect.aspect}."
    beam.eqtn = ""
    beam.dmgmult = f"aspects.{aspect.name}.ratio(user)"
    beam.aspectcost = "user.getstat('POWER') * 0.8"
    beam.vimcost = "user.getstat('POWER') * 0.7"
    beam.custom = [f"aspects.{aspect.name}.adjust(target, -2 * user.getstat('POWER'))", f"aspects.{aspect.name}.adjust(user, -1 * user.getstat('POWER'))"]
    beam.flavor = f"USER hits TARGET with a concentrated beam of {aspect.aspect}!"
    beam.cooldown = 2

    config.classskills["prince"][aspect.name][f"{aspect.name}beam"] = 100

    # BARD

    # passive - tragedy
    def tragedyeffectfconstructor(aspect):
        def tragedyeffectf(effect, inflictor, battler, power=1):
            return aspect.adjust(battler, battler.getstat("POWER") / 5 * -1)
        return tragedyeffectf

    tragedyeffect = stateseffects.Effect(f"{aspect.name} curse") # procs when hit
    tragedyeffect.customs = [tragedyeffectfconstructor(aspect)]

    tragedystate = stateseffects.State(f"{aspect.name} cursed")
    tragedystate.duration = -1
    tragedystate.ondamageeffects = {f"{aspect.name} curse": 1}

    def tragedyfconstructor(aspect):
        def tragedyf(battler):
            for bat in battler.Strife.battlers:
                b = battler.Strife.battlers[bat]
                aspect.maxadjust(b, battler.power * -1)
            state = stateseffects.states[f"{aspect.name} cursed"]
            for bname in battler.Strife.battlers:
                b = battler.Strife.battlers[bname]
                state.apply(battler, b)
        return tragedyf

    tragedy = Passive(f"{aspect.name} tragedy")
    tragedy.description = f"Lowers everyone's {aspect.maxaspect} at the start of battle. While in battle, every time something is damaged, its {aspect.aspect} lowers."
    tragedy.customstart = tragedyfconstructor(aspect)

    config.classpassives["bard"][aspect.name][f"{aspect.name} tragedy"] = 30

    #skill - jest
    jest = Skill(f"{aspect.name}jest")
    jest.description = f"Deals damage based on how little {aspect.aspect} you have. Costs a trivial action."
    jest.eqtn = ""
    jest.dmgmult = f"0.25 * aspects.{aspect.name}.inverseratio(user)"
    jest.aspectcost = "user.getstat('POWER') * 0.3"
    jest.vimcost = "user.getstat('POWER') * 0.2"
    jest.flavor = f"USER hits TARGET with the funniest known jest of {aspect.aspect}!"
    jest.cooldown = 1

    config.classskills["bard"][aspect.name][f"{aspect.name}jest"] = 100

    # KNIGHT

    #skill - blade
    blade = Skill(f"{aspect.name}blade")
    blade.description = f"Deals more damage depending on your {aspect.aspect}."
    blade.eqtn = ""
    blade.dmgmult = f"aspects.{aspect.name}.ratio(user)"
    blade.aspectcost = "user.getstat('POWER') * 0.4"
    blade.vimcost = "user.getstat('POWER') * 0.4"
    blade.flavor = f"USER hits TARGET with a blade of {aspect.aspect}!"

    config.classskills["knight"][aspect.name][f"{aspect.name}blade"] = 30

    #passive - loophole
    def loopholefconstructor(aspect):
        def loopholef(battler):
            out = aspect.maxadjust(battler, battler.getstat("POWER", True) * aspect.ratio(battler) / 16)
            return out
        return loopholef

    loophole = Passive(f"{aspect.name} loophole")
    loophole.description = f"Each turn your {aspect.maxaspect} increases based on your {aspect.aspect}."
    loophole.customcall = loopholefconstructor(aspect)

    config.classpassives["knight"][aspect.name][f"{aspect.name} loophole"] = 100

    # PAGE

    #passive - lack of
    def lackfconstructor(aspect):
        def lackf(battler):
            return aspect.maxadjust(battler, battler.getstat("POWER", True) * -0.1)
        return lackf

    lack = Passive(f"lack of {aspect.name}")
    lack.description = f"Start the battle with less {aspect.maxaspect}."
    lack.customstart = lackfconstructor(aspect)

    config.classpassives["page"][aspect.name][f"lack of {aspect.name}"] = 1

    #passive - beacon of

    def beaconfconstructor(aspect):
        def beaconf(battler):
            page = None
            if "pages" not in util.sessions[battler.Player.session]:
                util.sessions[battler.Player.session]["pages"] = {}
            if aspect.name not in util.sessions[battler.Player.session]["pages"]:
                util.sessions[battler.Player.session]["pages"][aspect.name] = 0
            for id in util.sessions[battler.Player.session]["members"]:
                b = explore.Player(id)
                if f"beacon of {aspect.name}" not in b.freepassives:
                    b.freepassives.append(f"beacon of {aspect.name}")
                if b.aspect == aspect.name and b.gameclass == "page":
                    page = b
            if battler.Player.aspect != f"{aspect.name}" or battler.Player.gameclass != "page":
                if page != None:
                    out = f"{battler.name} gets {battler.their} bonus from the PAGE OF {aspect.aspect}!\n"
                    if aspect.maxadjust != aspect.adjust:
                        out += aspect.maxadjust(battler, util.sessions[battler.Player.session]["pages"][aspect.name] // 2) + "\n"
                        out += aspect.adjust(battler, util.sessions[battler.Player.session]["pages"][aspect.name] // 2)
                    else:
                        out += aspect.adjust(battler, util.sessions[battler.Player.session]["pages"][aspect.name])
                    return out
        return beaconf

    def beaconcallfconstructor(aspect):
        def beaconf(battler):
            if battler.Player.aspect == aspect.name and battler.Player.gameclass == "page":
                if "pages" not in util.sessions[battler.Player.session]:
                    util.sessions[battler.Player.session]["pages"] = {}
                if aspect.name not in util.sessions[battler.Player.session]["pages"]:
                    util.sessions[battler.Player.session]["pages"][aspect.name] = 0
                bonus = (battler.getstat("POWER") // 4) * aspect.ratio(battler)
                if bonus > util.sessions[battler.Player.session]["pages"][aspect.name]:
                    util.sessions[battler.Player.session]["pages"][aspect.name] = bonus
        return beaconf

    beacon = Passive(f"beacon of {aspect.name}")
    beacon.description = f"You give bonus {aspect.maxaspect} to all other members of your session based on your highest observed {aspect.aspect} RATIO."
    beacon.customcall = beaconcallfconstructor(aspect)
    beacon.customstart = beaconfconstructor(aspect)

    config.classpassives["page"][aspect.name][f"beacon of {aspect.name}"] = 30

    # skill - arrow
    arrow = Skill(f"{aspect.name}-arrow")
    arrow.description = f"Increases the target's {aspect.aspect}. Costs a trivial action."
    arrow.eqtn = "0"
    arrow.actioncost = 0
    arrow.trivialactioncost = 1
    arrow.custom = [f"aspects.{aspect.name}.adjust(target, 1 * user.getstat('POWER'))"]
    arrow.aspectcost = "user.getstat('POWER') * 0.4"
    arrow.vimcost = "user.getstat('POWER') * 0.2"
    arrow.allflavor = f"USER shoots an arrow of {aspect.aspect}!"
    arrow.cooldown = 1

    config.classskills["page"][aspect.name][f"{aspect.name}-arrow"] = 100

    # MAGE

    # skill - conjure

    def pursuiteffectfconstructor(aspect): # on call proc
        def pursuiteffectf(effect, inflictor, battler, power=1):
            return aspect.adjust(battler, (inflictor.getstat("POWER", True)))
        return pursuiteffectf

    pursuiteffect = stateseffects.Effect(f"pursuit of {aspect.name} proc") # procs each turn
    pursuiteffect.customs = [pursuiteffectfconstructor(aspect)]

    applypursuit = stateseffects.Effect(f"apply pursuit of {aspect.name}")
    applypursuit.stateapply = [f"pursuit of {aspect.name}"]

    pursuit = stateseffects.State(f"pursuit of {aspect.name}")
    pursuit.duration = 3
    pursuit.calleffects = {f"pursuit of {aspect.name} proc": 1}

    conjure = Skill(f"conjure-{aspect.name}")
    conjure.description = f"Applies a state that raises the target's {aspect.aspect} each turn. Costs a trivial action."
    conjure.eqtn = "0"
    conjure.actioncost = 0
    conjure.trivialactioncost = 1
    conjure.aspectcost = "user.getstat('POWER') * 0.3"
    conjure.allflavor = f"USER conjures {aspect.aspect}!"
    conjure.cooldown = 1
    conjure.effects = {f"apply pursuit of {aspect.name}": 1}

    config.classskills["mage"][aspect.name][f"conjure-{aspect.name}"] = 30

    # skill - foretell

    foretell = Skill(f"foretell-{aspect.name}")
    foretell.description = f"Deals damage to the target based on their {aspect.aspect}, then increases their {aspect.aspect}."
    foretell.eqtn = ""
    foretell.dmgmult = f"aspects.{aspect.name}.ratio(target)*1.5"
    foretell.custom = [f"aspects.{aspect.name}.adjust(target, 2 * user.getstat('POWER'))"]
    foretell.aspectcost = "user.getstat('POWER') * 0.5"
    foretell.flavor = f"USER foretells TARGET's {aspect.aspect}! It DOESN'T LOOK GOOD!"

    config.classskills["mage"][aspect.name][f"foretell-{aspect.name}"] = 100

    # SEER

    # skill - dispel

    def dispeleffectfconstructor(aspect):
        def dispeleffectf(effect, inflictor, battler, power=1):
            return aspect.adjust(battler, (inflictor.getstat("POWER", True) * -1))
        return dispeleffectf

    dispeleffect = stateseffects.Effect(f"dispelling {aspect.name} proc") # procs each turn
    dispeleffect.customs = [dispeleffectfconstructor(aspect)]

    applydispel = stateseffects.Effect(f"apply dispelling {aspect.name}")
    applydispel.stateapply = [f"dispelling {aspect.name}"]

    dispelstate = stateseffects.State(f"dispelling {aspect.name}")
    dispelstate.duration = 3
    dispelstate.calleffects = {f"dispelling {aspect.name} proc": 1}

    dispel = Skill(f"dispel-{aspect.name}")
    dispel.description = f"Applies a state that lowers the target's {aspect.aspect} each turn. Costs a trivial action."
    dispel.eqtn = "0"
    dispel.actioncost = 0
    dispel.trivialactioncost = 1
    dispel.aspectcost = "user.getstat('POWER') * 0.4"
    dispel.allflavor = f"USER dispels {aspect.aspect}!"
    dispel.cooldown = 1
    dispel.effects = {f"apply dispelling {aspect.name}": 1}

    config.classskills["seer"][aspect.name][f"dispel-{aspect.name}"] = 30

    # passive - light
    def lightapplyfconstructor(aspect):
        def lightapplyf(battler):
            for bat in battler.Strife.battlers:
                b = battler.Strife.battlers[bat]
                if b.team == battler.team:
                    state = stateseffects.states[f"{aspect.name} enlightened"]
                    if f"{aspect.name} enlightened" not in b.states:
                        state.apply(battler, b)
        return lightapplyf

    lightstate = stateseffects.State(f"{aspect.name} enlightened")
    lightstate.dealmult = f"1 + (aspects.{aspect.name}.ratio(inflictor) / 16)"
    lightstate.duration = -1

    light = Passive(f"light of {aspect.name}")
    light.description = f"All members of your team in combat gain an increased DAMAGE MULTIPLIER based on your {aspect.aspect}."
    light.customcall = lightapplyfconstructor(aspect)

    config.classpassives["seer"][aspect.name][f"light of {aspect.name}"] = 100

    # WITCH

    # skill - work

    work = Skill(f"{aspect.name}work")
    work.custom = [f"aspects.{aspect.name}.adjust(target, -2 * user.getstat('POWER'))", f"aspects.{aspect.name}.adjust(user, user.getstat('POWER'))"]
    work.description = f"Greatly reduces the {aspect.aspect} of the target, then increases the {aspect.aspect} of the user."

    play = Skill(f"{aspect.name}play")
    play.custom = [f"aspects.{aspect.name}.adjust(target, 2 * user.getstat('POWER'))", f"aspects.{aspect.name}.adjust(user, -1 * user.getstat('POWER'))"]
    play.description = f"Greatly increases the {aspect.aspect} of the target, then reduces the {aspect.aspect} of the user."

    config.classskills["witch"][aspect.name][f"{aspect.name}work"] = 30
    config.classskills["witch"][aspect.name][f"{aspect.name}play"] = 30

    # skill - hole
    def holefconstructor(aspect):
        def holef(effect, inflictor, battler, power=1):
            out = []
            power = inflictor.getstat("POWER", True) * -6
            for bat in battler.Strife.battlers:
                b = battler.Strife.battlers[bat]
                out.append(aspect.adjust(b, power))
            return "\n".join(out)
        return holef

    holeeffect = stateseffects.Effect(f"{aspect.name}-hole effect")
    holeeffect.customs = [holefconstructor(aspect)]

    hole = Skill(f"{aspect.name}-hole")
    hole.description = f"Lowers the {aspect.aspect} of every battler in combat by a lot."
    hole.targetself = True
    hole.eqtn = "0"
    hole.aspectcost = "user.getstat('POWER') * 0.7"
    hole.allflavor = f"USER opens the {aspect.aspect} hole!"
    hole.cooldown = 2
    hole.effects = {f"{aspect.name}-hole effect": 1}

    config.classskills["witch"][aspect.name][f"{aspect.name}-hole"] = 100

    # skill - gate
    def gatefconstructor(aspect):
        def gatef(effect, inflictor, battler, power=1):
            out = []
            power = inflictor.getstat("POWER", True) * 6
            for bat in battler.Strife.battlers:
                b = battler.Strife.battlers[bat]
                out.append(aspect.adjust(b, power))
            return "\n".join(out)
        return gatef

    gateeffect = stateseffects.Effect(f"{aspect.name}-gate effect")
    gateeffect.customs = [gatefconstructor(aspect)]

    gate = Skill(f"{aspect.name}-gate")
    gate.description = f"Raises the {aspect.aspect} of every battler in combat by a lot."
    gate.targetself = True
    gate.eqtn = "0"
    gate.aspectcost = "user.getstat('POWER') * 0.7"
    gate.allflavor = f"USER opens the {aspect.aspect} GATE!"
    gate.cooldown = 2
    gate.effects = {f"{aspect.name}-gate effect": 1}

    config.classskills["witch"][aspect.name][f"{aspect.name}-gate"] = 413

    # HEIR

    # passive - heir
    def heirfconstructor(aspect):
        def heirf(battler):
            o = f"{battler.name} is the HEIR OF {aspect.aspect}!\n"
            if aspect.maxadjust != aspect.adjust:
                o += aspect.maxadjust(battler, battler.getstat("POWER", True) // 2)
                o += "\n"
                o += aspect.adjust(battler, battler.getstat("POWER", True) // 2)
            else:
                o += aspect.adjust(battler, battler.getstat("POWER", True))
            return o
        return heirf

    heir = Passive(f"heir of {aspect.name}")
    heir.description = f"Gain {aspect.maxaspect}."
    heir.customstart = heirfconstructor(aspect)

    config.classpassives["heir"][aspect.name][f"heir of {aspect.name}"] = 30

    # passive - protected

    def protectedapplyfconstructor(aspect):
        def protectedapplyf(battler):
                state = stateseffects.states[f"protection of {aspect.name}"]
                state.apply(battler, battler)
        return protectedapplyf

    protection = stateseffects.State(f"protection of {aspect.name}")
    protection.damagemult = f"1 - min(aspects.{aspect.name}.ratio(inflictor) / 5, 0.8)"
    protection.duration = -1

    protected = Passive(f"protected by {aspect.name}")
    protected.description = f"Gain damage reduction based on your {aspect.aspect}."
    protected.customstart = protectedapplyfconstructor(aspect)

    config.classpassives["heir"][aspect.name][f"protected by {aspect.name}"] = 100

    # MAID

    # skill - clean

    clean = Skill(f"{aspect.name}clean")
    clean.description = f"Deals damage and gives you {aspect.aspect}."
    clean.eqtn = ""
    clean.custom = [f"aspects.{aspect.name}.adjust(user, user.getstat('POWER'))"]
    clean.aspectcost = "user.getstat('POWER') * 0.1"
    clean.vimcost = "user.getstat('POWER') * 0.1"

    config.classskills["maid"][aspect.name][f"{aspect.name}clean"] = 30

    # skill - cooking

    cooking = Skill(f"{aspect.name}-cooking")
    cooking.description = f"Gives the target a large amount of ASPECT."
    cooking.eqtn = "0"
    cooking.custom = [f"aspects.{aspect.name}.adjust(target, user.getstat('POWER') * 3)"]
    cooking.cooldown = 2
    cooking.aspectcost = "user.getstat('POWER') * 0.4"
    cooking.vimcost = "user.getstat('POWER') * 0.2"

    config.classskills["maid"][aspect.name][f"{aspect.name}-cooking"] = 100

    #skill - wipe

    wipe = Skill(f"{aspect.name}wipe")
    wipe.description = f"Does a large amount of damage based on the target's {aspect.aspect}."
    wipe.eqtn = ""
    wipe.dmgmult = f"aspects.{aspect.name}.ratio(target)"
    wipe.cooldown = 2
    wipe.aspectcost = "user.getstat('POWER') * 0.6"
    wipe.vimcost = "user.getstat('POWER') * 0.4"
    config.classskills["maid"][aspect.name][f"{aspect.name}wipe"] = 413

    # SYLPH

    # skill - salve

    salve = Skill(f"{aspect.name}salve")
    salve.description = f"Heals the target based on your {aspect.aspect}."
    salve.eqtn = f"user.getstat('POWER') * (aspects.{aspect.name}.ratio(user) / 1.5)"
    salve.cooldown = 2
    salve.aspectcost = f"user.getstat('POWER') * 0.3"

    config.classskills["sylph"][aspect.name][f"{aspect.name}salve"] = 30

    # passive - aura

    def aurafconstructor(aspect):
        def auraf(battler):
            for bat in battler.Strife.battlers:
                b = battler.Strife.battlers[bat]
                if b.team == battler.team:
                    b.damage(battler.getstat("POWER") * 0.25 * aspect.ratio(battler))
            return f"{battler.name}'s team was healed for {int(battler.getstat('POWER') * 0.25 * aspect.ratio(battler))} by {battler.their} aura!"
        return auraf

    aura = Passive(f"aura of {aspect.name}")
    aura.description = f"Heals your team every turn based on your {aspect.aspect}."
    aura.customcall = aurafconstructor(aspect)

    config.classpassives["sylph"][aspect.name][f"aura of {aspect.name}"] = 100

    # passive - line

    def linefconstructor(aspect):
        def linef(battler):
            for bat in battler.Strife.battlers:
                b = battler.Strife.battlers[bat]
                if b.team == battler.team:
                    aspect.adjust(b, battler.getstat("POWER") * .5)
        return linef

    line = Passive(f"{aspect.name}line")
    line.description = f"Increases your team's {aspect.aspect} every turn."
    line.customcall = linefconstructor(aspect)

    config.classpassives["sylph"][aspect.name][f"{aspect.name}line"] = 413
