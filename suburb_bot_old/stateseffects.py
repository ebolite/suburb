import skills
import explore
import alchemy

states = {}
effects = {}

class State:
    def __init__(self, name):
        self.name = name
        self.damagemult = "1" # damage taken mult
        self.dealmult = "1" # damage dealt mult
        self.dotformula = ""
        self.applyflavor = ""
        self.immunities = [] # what states this state will make you immune to
        self.calleffects = {}
        self.ondamageeffects = {}
        self.statadds = {}
        self.applyrolls = [] # first, inflictor, second, battler
        states[name] = self

    def apply(self, inflictor, battler, power=1, duration=None):
        immune = False
        for s in battler.states:
            stateobj = states[s]
            if self.name in stateobj.immunities:
                immune = True
        if immune == True: return f"{battler.name} is immune to '{self.name}'!"
        if self.applyrolls != []:
            inflictorroll = inflictor.roll(1, eval(self.applyrolls[0]))
            battlerroll = inflictor.roll(1, eval(self.applyrolls[1]))
            if battlerroll > inflictorroll:
                return f""
        if duration == None: duration = self.duration
        if self.name not in battler.states:
            battler.states[self.name] = {}
        if "duration" not in battler.states[self.name]:
            battler.states[self.name]["duration"] = duration
        else:
            battler.states[self.name]["duration"] += duration
        if "power" not in battler.states[self.name] or battler.states[self.name]["power"] < power:
            battler.states[self.name]["power"] = power
            battler.states[self.name]["inflictor"] = inflictor
        if "inflicted" not in battler.states[self.name]:
            battler.states[self.name]["inflicted"] = inflictor.Strife.turn
        return self.flavorformat(self.applyflavor, inflictor, battler)

    def call(self, battler):
        out = []
        inflictor = battler.states[self.name]["inflictor"]
        power = battler.states[self.name]["power"]
        if self.dotformula != "":
            damage = eval(self.dotformula) * power
            change = battler.damage(damage, nododge=True)
            if change > 0:
                out.append(f"{battler.name} was healed by {change} ({round((change/battler.vials['health']['maximum']) * 100)}%) from {self.name})!")
            elif change < 0:
                out.append(f"{battler.name} was damaged by {change * -1} ({round((change/battler.vials['health']['maximum']) * -100)}%) from {self.name}!")
        for eff in self.calleffects:
            effectobj = effects[eff]
            o = effectobj.effect(inflictor, battler, power=self.calleffects[eff])
            if o != "":
                out.append(o)
        if out != []:
            out = "\n".join(out)
            return out
        else:
            return ""

    def ondamage(self, battler): # procs when the inflicted gets hit
        out = []
        inflictor = battler.states[self.name]["inflictor"]
        power = battler.states[self.name]["power"]
        for eff in self.ondamageeffects:
            effectobj = effects[eff]
            o = effectobj.effect(inflictor, battler, power=self.ondamageeffects[eff])
            if o != "":
                out.append(o)
        if out != []:
            out = "\n".join(out)
            return out
        else:
            return ""

    def flavorformat(self, text, inflictor, target=None):
        text = text.replace("INFLICTOR", inflictor.name)
        if target != None:
            text = text.replace("TARGET", target.name)
        if type(inflictor) == explore.PlayerBattler:
            text = text.replace("THEY", inflictor.they)
            text = text.replace("THEM", inflictor.them)
            text = text.replace("THEIR", inflictor.their)
            text = text.replace("THEIRS", inflictor.theirs)
        else:
            text = text.replace("THEY", "it")
            text = text.replace("THEM", "it")
            text = text.replace("THEIR", "its")
            text = text.replace("THEIRS", "its")
        return text

abjure = State("abjure")
abjure.damagemult = "0.5"
abjure.duration = 1

stunned = State("stunned")
stunned.duration = 1
stunned.calleffects = {"stuncall": 1}
stunned.applyrolls = ["power * inflictor.getstat('POWER', True)", "battler.getstat('POWER')"]

stunimmune = State("stunimmune")
stunimmune.duration = 2
stunimmune.immunities = ["stunned"]

bleeding = State("bleeding")
bleeding.dotformula = "-0.4 * inflictor.getstat('POWER', True)"
bleeding.duration = 2

poisoning = State("poisoning")
poisoning.dotformula = "-0.3 * inflictor.getstat('POWER', True)"
poisoning.duration = 4

burning = State("burning")
burning.dotformula = "-0.8 * inflictor.getstat('POWER', True)"
burning.duration = 1

weak = State("weak")
weak.duration = 2
weak.statadds = {"POWER": "inflictor.getstat('POWER', True) * -0.4"}

strong = State("strong")
strong.duration = 2
strong.statadds = {"POWER": "inflictor.getstat('POWER', True) * 0.4"}

numbed = State("numbed")
numbed.duration = 2
numbed.statadds = {"SAV": "inflictor.getstat('POWER', True) * -0.1"}

frozen = State("frozen")
frozen.duration = 2
frozen.statadds = {"SAV": "inflictor.getstat('POWER', True) * -0.07", "MET": "inflictor.getstat('POWER', True) * -0.07"}

sated = State("sated")
sated.duration = 2
sated.immunities = ["sate"]

blind = State("blind")
blind.duration = 2
blind.statadds = {"MET": "inflictor.getstat('POWER', True) * -0.07", "SPK": "inflictor.getstat('POWER', True) * -0.07"}

demoralized = State("demoralized")
demoralized.duration = 2
demoralized.statadds = {"SPK": "inflictor.getstat('POWER', True) * -0.1"}

inspired = State("inspired")
inspired.duration = 2
inspired.statadds = {"SPK": "inflictor.getstat('POWER', True) * 0.1"}

caffeinated = State("caffeinated")
caffeinated.duration = 4
caffeinated.statadds = {"SAV": "inflictor.getstat('POWER', True) * 0.07", "SPK": "inflictor.getstat('POWER', True) * 0.07"}

class Effect:
    def __init__(self, name):
        self.name = name
        self.stateapply = []
        self.customs = []
        self.eqtn = ""
        self.secondaryeqtn = ""
        effects[name] = self

    def effect(self, inflictor, battler, power=1):
        out = ""
        immune = False
        for s in battler.states:
            stateobj = states[s]
            if self.name in stateobj.immunities:
                immune = True
        if immune == True: return f"{battler.name} is immune to '{self.name}'!"
        if self.eqtn != "":
            dmg = eval(self.eqtn)
            change = battler.damage(dmg, nododge=True)
            if change > 0:
                Strife.logmessages.append(f"{target.name} was healed by {change} ({round((change/target.vials['health']['maximum']) * 100)}%)!")
            elif change < 0:
                Strife.logmessages.append(f"{target.name} was damaged by {change * -1} ({round((change/target.vials['health']['maximum']) * -100)}%)!")
        if self.secondaryeqtn != "":
            vials = []
            for vial in ["gambit", "horseshitometer", "mangrit", "inspiration"]:
                vials.append(vial)
            for vial in vials:
                battler.changevial(vial, eval(self.secondaryeqtn))
        if len(self.stateapply) != 0:
            for state in self.stateapply:
                stateobj = states[state]
                out += stateobj.apply(inflictor, battler, power)
        for custom in self.customs:
            out += custom(self, inflictor, battler, power)
        return out


applyabjure = Effect("applyabjure")
applyabjure.stateapply = ["abjure"]

stun = Effect("stun")
stun.stateapply = ["stunned"]

heal = Effect("heal")
heal.eqtn = "inflictor.getstat('POWER') * power"

damage = Effect("damage")
damage.eqtn = "-1 * inflictor.getstat('POWER') * power"

bleed = Effect("bleed")
bleed.stateapply = ["bleeding"]

poison = Effect("poison")
poison.stateapply = ["poisoning"]

ignite = Effect("ignite")
ignite.stateapply = ["burning"]

weakness = Effect("weakness")
weakness.stateapply = ["weak"]

strength = Effect("strength")
strength.stateapply = ["strong"]

numb = Effect("numb")
numb.stateapply = ["numbed"]

freeze = Effect("freeze")
freeze.stateapply = ["frozen"]

sate = Effect("sate")
sate.eqtn = "inflictor.getstat('POWER') * power * 1.5"

refresh = Effect("refresh")
refresh.secondaryeqtn = "inflictor.getstat('POWER') * power * 0.5"

blinding = Effect("blinding")
blinding.stateapply = ["blind"]

demoralize = Effect("demoralize")
demoralize.stateapply = ["demoralized"]

inspire = Effect("inspire")
inspire.stateapply = ["inspired"]

caffeinate = Effect("caffeinate")
caffeinate.stateapply = ["caffeinated"]

def stun(effect, inflictor, battler, power=1):
    battler.actions -= 1
    if "stunned" in battler.states: battler.states.pop("stunned")
    stateobj = states["stunimmune"]
    stateobj.apply(inflictor, battler)
    return f"{battler.name} was stunned and lost an action!"

stuncall = Effect("stuncall")
stuncall.customs = [stun]
