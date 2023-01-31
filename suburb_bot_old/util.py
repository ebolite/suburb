import os
import sys
import json
import asyncio
import discord
import datetime
import shutil
from discord.ext import tasks, commands
from dotenv import load_dotenv

bot = None

load_dotenv
if "dev" in sys.argv:
    homedir = os.getcwd()+"\devbranch"
    TOKEN = os.getenv('DISCORD_TOKEN_DEV')
    print(f"dev mode, setting homedir to {homedir}")
else:
    homedir = os.getcwd()
    TOKEN = os.getenv('DISCORD_TOKEN')

def backup():
    time = datetime.datetime.now()
    hrminute = str(time.time())[0:5]
    p = f"{homedir}\\backups\\{time.date()} - {hrminute.replace(':', '')}"
    if not os.path.exists(p):
        shutil.copytree(f"{homedir}\\json", p)
        print("Creating backup")
        return True
    else:
        print("Backup has already been made this minute")
        return False

def saveall():
    writejson(players, "players")
    writejson(sessions, "sessions")
    writejson(items, "items")
    writejson(acceptedbases, "acceptedbases")
    writejson(suggestedbases, "suggestedbases")
    print("saving instances")
    writejson(instances, "instances")
    print("saved instances successfully")
    writejson(npcs, "npcs")
    writejson(codes, "codes")

def writejson(obj=None, fn=None):
    if not os.path.exists(f"{homedir}\\json"):
        os.makedirs(f"{homedir}\\json")
        print(f"Created {homedir}\\json")
    os.chdir(f"{homedir}\\json")
    if fn != None:
        with open(f"{fn}.json", "w") as f:
            if obj == None:
                obj = eval(f"{fn}")
            if obj != None:
                if obj != {} and obj != None:
                    data = json.dump(obj, f, indent=4)
                    f = data

def readjson(obj, filename):
    try:
        os.chdir(f"{homedir}\\json")
        with open(f"{filename}.json", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"UNABLE TO READ JSON {filename}")
                input("CONTINUE")
                data = {}
            return data
    except FileNotFoundError:
        print(f"File not found when reading json: '{filename}.json'. Overwriting with {obj}.")
        writejson(obj, filename)
        return obj

def issetup():
    async def predicate(ctx):
        if str(ctx.author.id) not in players or "setup" not in players[str(ctx.author.id)]:
            await ctx.send("Your character has not been set up! Do `>menu` to set up your character.")
        return str(ctx.author.id) in players and "setup" in players[str(ctx.author.id)]
    return commands.check(predicate)

def deletecommand():
    async def predicate(ctx):
        await ctx.message.delete()
        return True
    return commands.check(predicate)

def cancellablecommand():
    async def predicate(ctx):
        await ctx.message.delete()
        return True
    return commands.check(predicate)

async def reactioncheck(message, author, reacts, removes=True): #reacts as list of reacts to add and check. message as a message that has been sent
    def check(reaction, user):
        return user == author and str(reaction.emoji) in reacts and reaction.message.id == message.id
    try:
        for react in reacts:
            await message.add_reaction(react)
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError as e:
        await message.clear_reactions()
        return None
    else:
        if removes:
            await message.clear_reactions()
        return reaction

async def nonereaction(message, author):
    def check(reaction, user):
        return user == author and str(reaction.emoji) == "◀" and reaction.message.id == message.id
    await message.add_reaction("◀")
    reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    await message.clear_reactions()
    return "none"

async def messagecheck(message, author, msgs, timeout=90, nodelete=False, noreaction=False): #msgs as list of messages to check for.
    channel = message.channel
    if msgs != None:
        msgs = list(msgs)
    if msgs != None:
        pls = msgs.copy()
        for i, msg in enumerate(pls): # add > to the options it can check for
            pls[i] = ">" + msg
        msgs += pls
    def check(m):
        if m.author == author and m.channel == channel and (msgs == None or m.content in msgs):
            return True
        elif nodelete == False and m.author == bot.user and m.channel == channel:
            return True
    try:
        if (msgs == None or "none" in msgs) and noreaction==False:
            onmessage = asyncio.create_task(bot.wait_for('message', timeout=timeout, check=check)) # put into tasks so we can run simultaneously
            backreaction = asyncio.create_task(nonereaction(message, author))
            done, pending = await asyncio.wait([onmessage, backreaction], return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                if t is backreaction:
                    onmessage.cancel()
                    return await backreaction
                else:
                    backreaction.cancel()
                    await message.clear_reactions()
                    m = await onmessage
        else:
            m = await bot.wait_for('message', timeout=timeout, check=check)
    except asyncio.TimeoutError as e:
        return None
    else:
        if m.author == bot.user:
            if m.content != "none":
                await message.delete()
                return None
            else:
                await message.delete()
                await m.delete()
                return "none"
        content = m.content
        if content[0] == ">": content = content.replace(">", "")
        await m.delete()
        return content

async def actionbreak(Player): # returns False if the specified Player has no actions remaining
    while True:
        if Player.Strife == None:
            return False
        try:
            bat = Player.Strife.battlers[Player.name]
            if bat.actions <= 0:
                return False
        except KeyError:
            return False
        await asyncio.sleep(1)

async def skillcheck(channel, Player): # checks for a valid skill of player in channel, return skill and targets as tuple ("skill", [targets])
    print(f"channel {channel} player {Player.id}")
    author = bot.get_user(int(Player.id))
    skills = Player.skills.copy()
    pls = skills.copy()
    for i, skill in enumerate(pls): # accept > in the front of skills as well
        pls[i] = ">" + skill
    skills += pls
    def check(m):
        if m.author == author and m.channel == channel:
            words = m.content.split(" ")
            if words[0] in skills:
                return True
            else:
                return False
        else:
            return False
    try:
        onmessage = asyncio.create_task(bot.wait_for('message', timeout=240.0, check=check))
        abreak = asyncio.create_task(actionbreak(Player))
        done, pending = await asyncio.wait([onmessage, abreak], return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            if t is abreak:
                onmessage.cancel()
                return (False, False)
            else:
                abreak.cancel()
                m = await onmessage
    except asyncio.TimeoutError as e:
        return (None, None)
    else:
        words = m.content.split(" ")
        skill = words.pop(0)
        skill = skill.replace(">", "")
        targets = []
        for word in words:
            targets.append(word)
        try:
            await m.delete()
            return (skill, targets)
        except discord.errors.NotFound:
            return await skillcheck(channel, Player)

players = {}
players = readjson(players, "players")

sessions = {} # key session name value: dict: {"password": "pass", "members": {}, "maps": {}}
sessions = readjson(sessions, "sessions")

items = {}
items = readjson(items, "items")

instances = {}
instances = readjson(instances, "instances")

npcs = {}
npcs = readjson(npcs, "npcs")

bases = {}
bases = readjson(bases, "bases")

acceptedbases = {}
acceptedbases = readjson(acceptedbases, "acceptedbases")

for base in acceptedbases:
    if base not in bases:
        bases[base] = acceptedbases[base]

suggestedbases = {}
suggestedbases = readjson(suggestedbases, "suggestedbases")

codes = {} # key: item code value: item name
codes = readjson(codes, "codes")

# cache = {} #key: user value: dict. key: grist value: amount stored
# cache = readjson(cache, "cache")

#
print(__name__)
if __name__ == "__main__": # if this file is being run, run the json editor
    bases = {}
    bases = readjson(bases, "bases")
    goto = ""
    for index, item in enumerate(bases):
        next = False
        for attr in bases[item]:
            while True:
                try:
                    if goto != "" and goto != item:
                        next = True
                        break
                    else:
                        goto = ""
                    os.system("cls")
                    print(f"Item {index}/{len(bases)}: {item}")
                    print(f"{attr}")
                    print("> to go to the next item. Type >name to go to a specific item.")
                    if attr == "power":
                        print("How much power should this item have? Ex: Paper: 1 Knife: 10 Baseball Bat: 20 Sword: 40 Gun: 100")
                    if attr == "weight":
                        print("How much weight should this item have? Ex: Paper: 1 Knife: 3 Baseball Bat: 10 Sword: 15 Bowling Ball: 35")
                    if attr == "size":
                        print("How much size should this item have? (Max wieldable is 20) Ex: Paper: 1 Knife: 2 Baseball Bat: 10 Sword: 10 Zweihander: 20")
                    if attr == "dicemin":
                        print("What should the dicemin be? Ex: Paper: 0.2 Knife: 0.7 Baseball Bat: 1 Sword: 1.1")
                    if attr == "dicemax":
                        print("What should the dicemax be? Ex: Paper: 0.5 Knife: 1 Baseball Bat: 1.3 Sword: 1.5")
                    if attr == "kinds":
                        if "glitchkind" in bases[item][attr]:
                            bases[item][attr].pop("glitchkind")
                        print("What kinds should this item be? None to go next.")
                        print(f"Current Kinds: {bases[item][attr]}")
                    if attr == "slots":
                        print("What slots should this item be equippable in? None to go next.")
                        print(f"Current slots: {bases[item][attr]}")
                    if attr == "tags":
                        print("What tags should this item have? None to go next.")
                        print(f"Current slots: {bases[item][attr]}")
                    if attr == "cost":
                        print("What grist should this item cost? None to go next.")
                        print(f"Current grists: {bases[item][attr]}")
                    if attr == "description":
                        print("What should the description be?")
                    if attr == "onhiteffect":
                        print("What on hit effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "weareffect":
                        print("What wear effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "consumeeffect":
                        print("What consume effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "secreteffect":
                        print("What secret effects should it have?")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr == "secretadjectives":
                        if "glitched" in bases[item][attr]:
                            bases[item][attr].remove("glitched")
                        print("What secret adjectives should it have? No input for none.")
                        print(f"Current effects: {bases[item][attr]}")
                    if attr != "base":
                        x = input("* ")
                    else:
                        print("base detected")
                        bases[item][attr] = True
                        x = ""
                        break
                    if x == "save":
                        writejson(bases, "bases")
                        print("Saved the item.")
                    if x != "" and x[0] == ">":
                        next = True
                        goto = x[1:]
                        break
                    if attr == "description":
                        bases[item][attr] = x
                        break
                    if attr == "secretadjectives":
                        if x != "":
                            bases[item][attr].append(x)
                        else:
                            break
                    if attr in ["power", "weight", "size"]:
                        bases[item][attr] = int(x)
                        break
                    if attr in ["dicemin", "dicemax"]:
                        bases[item][attr] = float(x)
                        break
                    if attr in ["onhiteffect", "weareffect", "consumeeffect", "secreteffect"]:
                        if x != "":
                            print("What power should the effect be at?")
                            y = input("* ")
                            power = float(y)
                            print("What adjective/base should the effect be inherited with? No input for none.")
                            z = input("* ")
                            if z != "":
                                bases[item][attr][x] = [power, str(z)]
                            else:
                                bases[item][attr][x] = [power]
                        else:
                            break
                    if attr in ["kinds", "slots", "tags"]:
                        if x != "":
                            print(f"What rate should that be inherited at?")
                            y = input("* ")
                            rate = float(y)
                            print(f"What adjective/base should that be inherited with? No input for none.")
                            z = input("* ")
                            if z != "":
                                bases[item][attr][x] = [rate, str(z)]
                            else:
                                bases[item][attr][x] = [rate]
                        else:
                            break
                    if attr == "cost":
                        if x != "":
                            print(f"What should the cost ratio be?")
                            y = input("* ")
                            cost = float(y)
                            bases[item][attr][x] = y
                        else:
                            break
                except (TypeError, ValueError) as e:
                    print(f"excepted error {e}")
            if next == True:
                break
    writejson(bases, "bases")
else:
    print("not main")
