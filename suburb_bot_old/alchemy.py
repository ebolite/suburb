import discord
import json
import random
import asyncio
import string
from discord.ext import tasks, commands

import util
import binary
import config
import explore
import useitems

class Alchemy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def cachedisplay(player, page):
        max = page * 3
        min = max - 3
        if page == 3:
            max += 2
        text = ""
        for tier in range(min, max):
            text += f"**Tier {tier}**\n"
            for grist in config.grists:
                if grist not in player.cache: player.cache[grist] = 0
                if config.grists[grist]["tier"] == tier:
                    text += f"{config.grists[grist]['emoji']} `{grist}`{'*' if 'exotic' in config.grists[grist] and config.grists[grist]['exotic'] else ''} {player.cache[grist]}g\n"
            text += "\n"
        embed = discord.Embed(title=f"{player.name}'s Cache Page {page}", description = text, color=player.color)
        embed.set_footer(text=f"*: Exotic\nCurrent Cache Limit: {player.cachelimit}")
        return embed

    @commands.command(name="gristcache")
    async def gristcache(self, ctx, player=None):
        if player == None:
            player = explore.Player(ctx.author)
        embed = self.cachedisplay(player, 1)
        message = await ctx.send(embed=embed)
        react = None
        while True:
            react = await util.reactioncheck(message, ctx.author, ["1️⃣", "2️⃣", "3️⃣", "◀"])
            if react == None:
                await message.edit(content=f"Timed out.")
                break
            else:
                page = 1
                if react.emoji == "2️⃣":
                    page = 2
                if react.emoji == "3️⃣":
                    page = 3
                if react.emoji == "◀":
                    break
                embed = self.cachedisplay(player, page)
                await message.edit(embed=embed)
        await message.delete()

    @commands.command(name="sylladex")
    async def sylladex(self, ctx, portfolio=False):
        player = explore.Player(ctx.author)
        if portfolio == False:
            page = "captchalogue"
        else:
            page = "portfolio"
        message = None
        while True:
            text = ""
            if page == "captchalogue":
                embed = player.embedsylladex
                embed.set_footer(text=f"Type the index or name of an item to view more about that item.\nType `portfolio` to view your strife portfolio.\nType `none` to delete this message.")
                if message == None:
                    message = await ctx.send(content= "", embed=embed)
                else:
                    await message.edit(content= "", embed=embed)
                m = await util.messagecheck(message, ctx.author, None)
                if m == None or m == "none":
                    break
                elif m not in ["portfolio", ">portfolio"]:
                    print(f"m {m}")
                    name = player.itemcheck(m)
                    if name != False:
                        inst = Instance(name=name)
                        text = Alchemy.whatistext(self, inst.Item.name)
                        embed = discord.Embed(title=f"{inst.calledby}", description=text, color=config.sburbblue)
                        embed.set_footer(text=f"React with ✅ to move this item to your strife deck.\nReact with 🆗 to INTERACT with the item.\nReact with ❎ to go back to your sylladex.\nReact with 💹 to eject.")
                        await message.edit(embed=embed)
                        r = await util.reactioncheck(message, ctx.author, ["✅","🆗", "❎", "💹"])
                        if r == None:
                            break
                        if r.emoji == "✅":
                            for specibus in inst.Item.kinds:
                                if specibus in player.kinds:
                                    player.movetostrifedeck(name)
                                    break
                            else:
                                if {} in player.portfolio: # unassigned specibus
                                    await message.edit(content="You have no strife specibi allocated to kinds associated with this item, but you have unassigned specibi. Would you like to allocate one of your unallocated strife specibi? **(y/n)**")
                                    m = await util.messagecheck(message, ctx.author, ["y", "n"])
                                    if m == "y":
                                        text = f"What kind would you like to allocate your specibus to? Type `none` to escape.\n"
                                        for kind in inst.Item.kinds:
                                            text += f"`{kind}` "
                                        embed = discord.Embed(description=text, color=config.sburbblue)
                                        await message.edit(content="", embed=embed)
                                        m = await util.messagecheck(message, ctx.author, list(inst.Item.kinds) + ["none"])
                                        if m != "none":
                                            player.allocate(m)
                                            player.movetostrifedeck(name)
                                            await message.edit(content=f"Successfully allocated `{m}` and moved `{inst.Item.calledby}` to your strife deck. Navigate to your `portfolio` to wield it.", embed=None)
                                            await asyncio.sleep(5)
                                else:
                                    await message.edit(content="You have no strife specibi allocated to any kinds associated with this item, and no unallocated specibi. You cannot move this item to your strife deck.")
                                    await asyncio.sleep(5)
                        elif r.emoji == "🆗":
                            text = await inst.activate(ctx, util.bot)
                            await message.edit(content=text,embed=None)
                            await asyncio.sleep(3)
                        elif r.emoji == "💹":
                            player.ejectinstance(inst.name)
                            await message.edit(content=f"Ejected {inst.calledby}!",embed=None)
                            await asyncio.sleep(3)
                    else:
                        break
                    print(f"got item {name}")
                else:
                    page = "portfolio"
            elif page == "portfolio":
                text = ""
                print("in portfolio")
                for i, card in enumerate(player.portfolio):
                    if card != {}:
                        text += f"`{i}.` {player.portfolio[i]['kind']}\n"
                    else:
                        text += f"`{i}.` UNASSIGNED SPECIBUS\n"
                embed = discord.Embed(title=f"{player.name}'s Strife Portfolio", description=text, color=player.color)
                embed.set_footer(text=f"Type the index or name of a specibus to view its portion of the strife deck.\nType `captchalogue` to view your Captchalogue Deck.\nType `none` to delete this message.")
                if message == None:
                    message = await ctx.send(content="", embed=embed)
                else:
                    await message.edit(content="", embed=embed)
                m = await util.messagecheck(message, ctx.author, None)
                if m == None or m == "none":
                    break
                elif m not in ["captchalogue"]:
                    text = ""
                    specibusindex = player.specibuscheck(m)
                    if player.portfolio[specibusindex] != {}:
                        for i, name in enumerate(player.portfolio[specibusindex]["items"]):
                            inst = Instance(name=name)
                            text += f"`{i}.` {inst.Item.calledby}"
                            if inst.name == player.wielding:
                                text += " (WIELDING)"
                            text += "\n"
                        embed = discord.Embed(title=f"{player.portfolio[specibusindex]['kind']}",description=text, color=player.color)
                        embed.set_footer(text="Type the index or name of an item to view it.\nType `none` to escape.")
                        await message.edit(embed=embed)
                        m = await util.messagecheck(message, ctx.author, None)
                        if m == "none" or m == None:
                            break
                        name = player.strifedeckcheck(m, specibusindex)
                        if name != False:
                            inst = Instance(name=name)
                            text = Alchemy.whatistext(self, inst.Item.name)
                            embed = discord.Embed(title=f"{inst.Item.calledby}", description=text, color=config.sburbblue)
                            embed.set_footer(text=f"React with ✅ to wield this item.\nReact with ❎ to go back to your strife portfolio.\nReact with ⏪ to move this item out of your strife deck and into your Captchalogue Deck.")
                            await message.edit(embed=embed)
                            r = await util.reactioncheck(message, ctx.author, ["✅", "❎", "⏪"])
                            if r == None:
                                pass
                            elif r.emoji == "✅":
                                if inst.name == player.wielding:
                                    player.wielding = None
                                    await message.edit(content=f"Unwielded {inst.Item.calledby}!", embed=None)
                                else:
                                    player.wielding = inst.name
                                    await message.edit(content=f"Wielded {inst.Item.calledby}!", embed=None)
                                await asyncio.sleep(3)
                            elif r.emoji == "⏪":
                                if inst.name == player.wielding:
                                    player.wielding = None
                                player.movefromstrifedeck(inst.name)
                                await message.edit(content=f"Captchalogued {inst.calledby}!", embed=None)
                                await asyncio.sleep(3)
                        elif name == "none":
                            pass
                        else:
                            break
                    else:
                        await message.edit(content=f"That specibus is unassigned!", embed=None)
                        await asyncio.sleep(3)
                else:
                    page = "captchalogue"
        if message != None: await message.delete()
        await explore.Explore.explore(explore.Explore, ctx)

    # @commands.command(name="portfolio")
    # async def portfolio(self, ctx):
    #     await self.sylladex(ctx, True)

    @commands.command(name="findbase")
    async def findbase(self, ctx):
        await ctx.send(f"Your random base is `{random.choice(list(util.bases))}`!")

    # @commands.command(name="alchemize")
    # async def alchemize(self, ctx, *target): #format item1 &&/|| item2
    #     target = list(target)
    #     print(target)
    #     item1 = []
    #     item2 = []
    #     operation = ""
    #     text = ""
    #     for word in target.copy():
    #         if word != "&&" and word != "||":
    #             item1.append(word)
    #             target.remove(word)
    #         else:
    #             operation = word
    #             target.remove(word)
    #             break
    #     else:
    #         target = []
    #         text = f"You must use an operation! Format: item1 && item2 OR item1 || item2"
    #     if target != []:
    #         for word in target:
    #             item2.append(word)
    #         item1 = " ".join(item1)
    #         item2 = " ".join(item2)
    #         if operation == "&&":
    #             code = binary.codeand(Item(item1).code, Item(item2).code)
    #         else:
    #             code = binary.codeor(Item(item1).code, Item(item2).code)
    #         if code not in util.codes:
    #             newitem = Item(name=f"({item1}{operation}{item2})", c1=item1, c2=item2, operation=operation)
    #         else:
    #             newitem = Item(name=util.codes[code])
    #         text = f"Performing `{item1} {operation} {item2}`...\nResulted in {newitem.calledby}!\n`{newitem.name}`"
    #         await self.whatis(ctx, newitem.name)
    #     await ctx.send(text)

    # @commands.command(name="whatis")
    # async def whatis(self, ctx, *target):
    #     text = self.whatistext(" ".join(target))
    #     await ctx.send(text)

    @commands.command(name="gristtorrent")
    async def gristtorrent(self, ctx):
        player = explore.Player(ctx.author)
        message = None
        while True:
            text = ""
            title = f"GristTorrent"
            text += f"**LEECHING**\n"
            leeching = False
            for grist in player.leeching:
                text += f"{config.grists[grist]['emoji']} {int((player.rung / (config.grists[grist]['tier'] + 1)) / len(player.leeching))}g/r\n"
                leeching = True
            for grist in util.sessions[player.session]["gutter"].copy():
                if player.cache[grist] < player.cachelimit or player.cachelimit == 0:
                    text += f"{config.grists[grist]['emoji']} *{int(player.rung / (config.grists[grist]['tier'] + 1))}g/r*\*\n"
                    leeching = True
            if leeching == False: text += "`INACTIVE`"
            foot = "⏬ to begin or stop leeching grist. ⏫ to send grist to other players. ◀ to close.\n\*: passively leeching (does not impact leeching rate)"
            embed = discord.Embed(title=title, description=text, color=config.sburbblue)
            embed.set_footer(text=foot)
            if message == None:
                message = await ctx.send(content="", embed=embed)
            else:
                await message.edit(content="", embed=embed)
            r = await util.reactioncheck(message, ctx.author, ["⏬", "⏫", "◀"])
            if r == None: break
            if r.emoji == "⏬":
                page = 1
                while True:
                    embed = self.cachedisplay(player, page)
                    await message.edit(content="Type the name of the grist you want to leech. Type `1` `2` or `3` to go to a certain page. Type `none` to cancel.", embed=embed)
                    m = await util.messagecheck(message, ctx.author, list(config.grists)+["1", "2", "3"])
                    if m in ["1", "2", "3"]:
                        page = int(m)
                    elif m == "none":
                        break
                    else:
                        grist = m
                        break
                if grist == None: break
                if grist in player.leeching:
                    player.leeching.remove(grist)
                    await message.edit(content=f"Stopped leeching {config.grists[grist]['emoji']} `{grist}`.", embed=None)
                    await asyncio.sleep(3)
                else:
                    print(f"grist {grist}")
                    if grist in ["zilium", "rainbow"]:
                        await message.edit(content="You cannot torrent tier 10 grists. That's illegal.", embed=None)
                        await asyncio.sleep(3)
                        break
                    if player.cache[grist] < player.cachelimit or player.cachelimit == 0:
                        player.leeching.append(grist)
                        await message.edit(content=f"Now leeching {config.grists[grist]['emoji']} `{grist}`!", embed=None)
                        await asyncio.sleep(3)
                    else:
                        await message.edit(content=f"Your {config.grists[grist]['emoji']} `{grist}` cache is full and you cannot leech any more!", embed=None)
                        await asyncio.sleep(3)
            elif r.emoji == "⏫":
                page = 1
                while True:
                    embed = self.cachedisplay(player, page)
                    await message.edit(content="Type the name of the grist you want to send. Type `1` `2` or `3` to go to a certain page.", embed=embed)
                    m = await util.messagecheck(message, ctx.author, list(config.grists)+["1", "2", "3", "none"])
                    if m in ["1", "2", "3"]:
                        page = int(m)
                    elif m == "none":
                        break
                    else:
                        grist = m
                        break
                if m == None:
                    break
                while True:
                    await message.edit(content="Who would you like to send grist to? Use the name. `none` to cancel.", embed=None)
                    m = await util.messagecheck(message, ctx.author, None)
                    recipient = None
                    if m == "none":
                        break
                    for member in util.sessions[player.session]["members"]:
                        p = explore.Player(member)
                        if p.name == m:
                            recipient = p
                            break
                    else:
                        await message.edit(content=f"{m} is not a member of your session.")
                        await asyncio.sleep(3)
                    if type(recipient) == explore.Player: break
                if recipient == None: break
                while True:
                    await message.edit(content=f"How much {config.grists[grist]['emoji']} **{grist}** would you like to send {recipient.them}? You have: {config.grists[grist]['emoji']} `{player.cache[grist]}g.`")
                    m = await util.messagecheck(message, ctx.author, None)
                    try:
                        value = int(m)
                        if value < 0:
                            await message.edit(content=f"You cannot send someone negative grist.")
                            await asyncio.sleep(3)
                        elif value > player.cache[grist]:
                            await message.edit(content=f"You cannot send someone more grist than you have.")
                            await asyncio.sleep(3)
                        else:
                            break
                    except ValueError:
                        await message.edit(content=f"Use a number, not `{m}.`")
                        await asyncio.sleep(3)
                added = recipient.addgrist(grist, value)
                player.addgrist(grist, added * -1)
                if added < value:
                    await message.edit(content=f"{recipient.name}'s grist cache was filled! You could only send {recipient.them} {config.grists[grist]['emoji']} `{added}g.`")
                else:
                    await message.edit(content=f"Sent {recipient.name} {config.grists[grist]['emoji']} `{added}g.` {recipient.they.capitalize()} should say 'thank you.'")
                await asyncio.sleep(3)
            else:
                break
        if message != None: await message.delete()


    def whatistext(self, target):
        item = Item(target)
        text = f"**{item.calledby}**\n"
        if item.forbiddencode:
            text += f"`code:` *unreadable*\n"
        else:
            text += f"`code:` `{item.code}`\n"
        text += f"*{item.description}*\n"
        if item.base == False:
            text += f"Made with *{item.c1} {item.operation} {item.c2}*\n"
        for abstratus in item.kinds:
            text += f"`{abstratus}` "
        text += "\n"
        text += f"`power:` {item.power}\n"
        text += f"`roll range:` {int(item.dicemin * item.power)} - {int(item.dicemax * item.power)}\n"
        text += f"`weight:` {item.weight} \n`size`: {item.size}\n"
        if len(item.slots) != 0:
            text += f"Equipped In: "
            for slot in item.slots:
                text += f"`{item.slots[slot]}` "
            text += "\n"
        if item.tags != {}:
            text += f"Tags: "
            for tag in item.tags:
                text += f"`{tag}` "
            text += "\n"
        if item.onhiteffect != {}:
            text += f"On-hit effects: "
            for effect in item.onhiteffect:
                text += f"`{effect} {round(item.onhiteffect[effect][0], 2)}` "
            text += "\n"
        if item.weareffect != {} and item.slots != {}:
            text += f"Wear effects: "
            for effect in item.weareffect:
                text += f"`{effect} {round(item.weareffect[effect][0], 2)}` "
            text += "\n"
        if item.consumeeffect != {} and "consumable" in item.tags:
            text += f"Consume effects: "
            for effect in item.consumeeffect:
                text += f"`{effect} {round(item.consumeeffect[effect][0], 2)}` "
            text += "\n"
        # if item.secreteffect != {}:
        #     text += f"Secret effects: "
        #     for effect in item.secreteffect:
        #         text += f"`{effect} {int(item.secreteffect[effect][0] * item.power)}` "
        #     text += "\n"
        # if item.secretadjectives != []:
        #     text += f"Secret adjectives: "
        #     for adj in item.secretadjectives:
        #         text += f"`{adj}` "
        #     text += "\n"
        text += "Grist Cost: "
        for grist in item.cost:
            text += f"{config.grists[grist]['emoji']}{int(item.cost[grist] * item.power)} "
        return text


class Item():
    # item reinitialization should cause alchemized items to get their properties generated from their substituents
    def __init__(self, name, dict=None, reinit=False, c1=None, c2=None, operation=""): # dict is properties of the item. defined in baseitems. if dict is none will generate attributes given its consituents
        if type(name) == tuple:
            name = " ".join(name)
        self.__dict__["name"] = str(name)
        if self.name not in util.items: # generate from c1 c2 and operation
            util.items[self.name] = {}
            valid = True
            if c1 == None or c2 == None or operation == "": # names look like "(((baseball bat&&sledge hammer)&&(piano wire||ring))||shotgun)" so the challenge is finding the true operator and c1/c2
                print(f"generating components for {name}")
                depth = -1
                c1 = []
                c2 = ""
                operation = ""
                operationindex = 0
                for index, letter in enumerate(name): #find c1 and operation
                    if letter == "(":
                        depth += 1
                        c1.append(letter)
                    elif letter == ")":
                        depth -= 1
                        c1.append(letter)
                    elif depth == 0 and letter in ["&", "|"]: #valid operators, only when depth is 0
                        if letter == "&": operation = "&&"
                        elif letter == "|": operation = "||"
                        operationindex = index + 2 # index beginning of c2
                        break
                    else: c1.append(letter)
                else: # if no operator was found
                    valid = False
                c1 = "".join(c1)
                c1 = c1[1:]
                c2 = name[operationindex:] # get all characters but the ones until the operator
                c2 = c2[:-1]
                print(f"c1: {c1} operation: {operation} c2: {c2}")
            if valid == True:
                self.base = False
                self.valid = True
                self.c1 = c1
                self.c2 = c2
                self.operation = operation
                print(f"Trying to init {c1}")
                item1 = Item(c1)
                print(f"Trying to init {c2}")
                item2 = Item(c2)
                if operation == "||":
                    anti = Item(f"({c1}&&{c2})") # OR generates something that is different than AND
                truenames = [item1.truename, item2.truename]
                if operation == "||":
                    if anti.truename in truenames: truenames.remove(anti.truename)
                random.seed(self.name+self.operation)
                self.truename = random.choice(truenames)
                self.adjectives = []
                adjectives = item1.adjectives + item1.secretadjectives + item2.adjectives + item2.secretadjectives
                if operation == "&&":
                    random.seed(self.name+self.operation+"bases")
                    rng = random.random()
                    if rng < 0.2:
                        adjectives += [item1.truename, item2.truename] # AND operation rarely gets to have multiple bases
                        adjectives.remove(self.truename)
                        print(f"adjectives: {adjectives}")
                if operation == "||":
                    if len(anti.adjectives) < len(adjectives): # only remove adjectives if the resulting AND item doesn't use all of the adjectives
                        for a in anti.adjectives:
                            if a in adjectives: adjectives.remove(a)
                random.seed(self.name+self.operation)
                random.shuffle(adjectives)
                for a in adjectives:
                    random.seed(self.name+self.operation+a)
                    rng = random.random()
                    if rng < 0.5:
                        self.adjectives.append(a)
                if len(self.adjectives) == 0 and len(adjectives) > 0:
                    random.seed(self.name+self.operation)
                    self.adjectives.append(random.choice(adjectives))
                if self.samename([item1, item2]): #if the item generates with the same name as one of the components, make that not happen
                    self.adjectives = []
                    repeats = 0
                    adjectives = item1.adjectives + item2.adjectives
                    adjectives += [item1.truename, item2.truename]
                    adjectives.remove(self.truename)
                    random.seed(self.name+self.operation)
                    random.shuffle(adjectives)
                    while self.samename([item1, item2]) or len(self.adjectives) == 0: # while this item shares the same name as one of its parents or has no adjectives
                        self.adjectives = []
                        for a in adjectives:
                            random.seed(self.name+self.operation+a+str(repeats))
                            rng = random.random()
                            if rng < 0.75:
                                self.adjectives.append(a)
                        repeats += 1
                self.inherit()
                self.code
                print(f"Generated {self.calledby} {self.name}")
            else: # if the item is not a base but doesn't exist in the database (it is a shitpost)
                self.valid = False
                l = name.split(" ")
                truename = l.pop() # truename is last item of list
                adjectives = l # adjectives are the rest
                self.truename = truename
                self.adjectives = adjectives
                print(f"shitpost generated {name}")
        #util.writejson(util.items, "items") # keeping this for now but remove this later when a save function is added

    def __setattr__(self, attr, value):
        print(f"setting {attr} to {value}")
        util.items[self.name][attr] = value

    def __getattr__(self, attr):
        if attr in util.items[self.__dict__["name"]]:
            return util.items[self.__dict__["name"]][attr]
        else:
            return defaults[attr]

    def inherit(self): #generate attributes from components
        item1 = Item(self.c1)
        item2 = Item(self.c2)
        #weight and size
        for item in [item1, item2]:
            if self.truename == item.truename:
                if item == item1:
                    otheritem = item2
                else:
                    otheritem = item1
                weight = item.weight #get the weight / size of the base
                size = item.size
                if otheritem.weight > item.weight: # add a weight bonus or malus depending on the weight difference between the base and the other
                    weight += otheritem.weight / (item.weight + 1)
                else:
                    weight -= item.weight / (otheritem.weight + 1)
                size += otheritem.size / item.size
                if otheritem.size > item.size:
                    size += otheritem.size / (item.size + 1)
                else:
                    size -= item.size / (otheritem.size + 1)
        self.weight = int(weight)
        self.size = int(size)
        #merge descriptors
        baseadjs = [] # list of descriptors that have been merged
        descriptors = self.adjectives.copy()
        descriptors.append(self.truename)
        print(f"adjective {self.adjectives}")
        adjs = self.adjectives.copy()
        for adj in self.adjectives.copy():
            if adj == item1.truename or adj == item2.truename:
                baseadjs.append(adj)
                baseadjs.append(self.truename)
                descriptors.append(self.truename)
                self.truename = f"{adj}-{self.truename}"
                adjs.remove(adj)
                descriptors.append(adj)
        self.adjectives = adjs
        #power
        if self.operation == "&&": # AND is more powerful when items are similar in power.
            self.power = (item1.power + item1.inheritpower + item2.power + item2.inheritpower)
        elif self.operation == "||": # OR is more powerful when items are greatly different in power.
            ratio = (item1.power + item1.inheritpower + item2.power + item2.inheritpower) * 1.5
            if ratio > 1: ratio = 1 / ratio
            if ratio < 0: ratio = 0
            ratio = 1 - ratio
            if ratio < 0.5:
                ratio = 0.5
            self.power = ((item1.power + item2.power) * ratio)
        self.power = int(self.power)
        #dicemin
        self.dicemin = (item1.dicemin + item2.dicemin) / 2
        if self.dicemin < 0 and self.dicemin > -2.8: self.dicemin *= 1.2
        elif self.dicemin < 1: self.dicemin *= 0.8
        elif self.dicemin < 1.4: self.dicemin *= 1.1
        self.dicemin = round(self.dicemin, 2)
        #dicemax
        self.dicemmax = (item1.dicemax + item2.dicemax) / 2
        if self.dicemax < 0 and self.dicemax > -1.4: self.dicemax *= 1.2
        elif self.dicemax < 1: self.dicemax *= 1.2
        elif self.dicemax < 2: self.dicemax *= 1.1
        self.dicemax = round(self.dicemax, 2)
        #fixdice
        if self.dicemin > self.dicemax: #switch the two dice around if min is larger than max
            min = self.dicemin
            max = self.dicemax
            self.dicemin = max
            self.dicemax = min
        #cost
        self.cost = item1.cost.copy()
        for cost in item2.cost:
            self.cost[cost] = item2.cost[cost]
        #dictionary inherits
        for attr in ["kinds", "slots", "tags", "onhiteffect", "weareffect", "consumeeffect", "secreteffect"]:
            dict = {} # empty dict for attr, this is what the attr dict will be replaced with
            d = item1.__getattr__(attr).copy() # d is the combined dict of both items
            for key in item2.__getattr__(attr).copy(): # add all possible keys to dict
                if key not in d:
                    d[key] = item2.__getattr__(attr)[key]
            for key in d: # cycle through each key to be inherited
                if len(d[key]) > 1: #if there is a guaranteed inheritor
                    if d[key][1] in descriptors: # check if the guaranteed inheritance descriptor is in this item
                        dict[key] = d[key] # inherit the key
                        if d[key][1] in baseadjs: #if the adjective this was inherited from is a base and the base of this item was merged
                            dict[key][1] = self.truename #set the new inheritor to be the merged name
                if key not in dict: # if it wasn't inherited through guaranteed means
                    random.seed(self.name+key)
                    rng = random.random()
                    chance = d[key][0] - (.2 * len(dict)) #chance of inheriting a key decreases with more keys, d[key][0] is base chance
                    if rng < chance:
                        dict[key] = d[key] #inherit the keys
            self.__setattr__(attr, dict) # update dict
        #secreteffect
        secreteffect = self.secreteffect.copy()
        for effect in self.secreteffect.copy():
            random.seed(self.name+"secreteffect"+effect)
            rng = random.random()
            if rng < 0.5:
                random.seed(self.name+"choices"+effect)
                options = ["consumeeffect", "onhiteffect", "weareffect"]
                for option in options:
                    if len(self.__getattr__(option)) == 0:
                        options.remove(option)
                if len(options) == 0: options = ["consumeeffect", "onhiteffect", "weareffect"]
                random.seed(self.name+"options"+effect)
                choice = random.choice(options)
                dict = self.__getattr__(choice)
                dict[effect] = self.secreteffect[effect]
                self.__setattr__(choice, dict)
                del secreteffect[effect]
        self.secreteffect = secreteffect


    def samename(self, itemlist): # returns whether this item has the same truename + adjectives as any of the items in list
        for item in itemlist:
            if self.truename == item.truename and self.adjectives == item.adjectives:
                return True
        else:
            return False

    def randomadj(self): # returns a random adjective
        adjs = self.adjectives.copy()
        if len(self.secretadjectives) > 0:
            adjs += self.secretadjectives.copy()
        if len(adjs) != 0:
            return random.choice(adjs)
        else:
            return self.truename

    @property
    def calledby(self):
        name = ""
        for a in self.adjectives:
            name += f"{a} "
        name += self.truename
        name = name.upper()
        name = name.replace("+", " ")
        return name

    @property
    def code(self):
        if "code" not in util.items[self.__dict__["name"]]:
            if self.base: #if no components
                random.seed(self.name)
                code = random.choices(binary.reversebintable, k=8)
                code = "".join(code)
            else:
                item1 = Item(self.c1)
                item2 = Item(self.c2)
                code1 = item1.code
                code2 = item2.code
                if self.operation == "&&":
                    code = binary.codeand(code1, code2)
                elif self.operation == "||":
                    code = binary.codeor(code1, code2)
            util.codes[code] = self.name
            print(f"setting code of {self.name}")
        else:
            code = util.items[self.__dict__["name"]]["code"]
        return code

class Instance():
    def __init__(self, name=None, item=None):
        if name != None:
            self.__dict__["name"] = name
        else:
            if type(item) == str:
                item = Item(item)
            name = item.name + random.choice(string.ascii_letters)
            while name in util.instances:
                name += random.choice(string.ascii_letters)
            self.__dict__["name"] = name
        if self.__dict__["name"] not in util.instances:
            util.instances[self.__dict__["name"]] = {}
        if type(item) == Item:
            self.item = item.name

    def __getattr__(self, attr):
        if attr in util.instances[self.__dict__["name"]]:
            return util.instances[self.__dict__["name"]][attr]
        else:
            return None

    def __setattr__(self, attr, value):
        util.instances[self.__dict__["name"]][attr] = value

    async def activate(self, ctx, room=False):
        if self.Item.use != None:
            validuses = self.Item.use.copy()
        else:
            validuses = []
        if self.punched != None and self.punched != "00000000":
            validuses.append("combine cards")
        if validuses == []:
            usename = False
        elif len(validuses) == 1:
            usename = validuses[0]
        else:
            text = f"How will you use it? (`none` cancels)\n"
            for i, u in enumerate(validuses):
                text+= f"`{i}. {u}` {useitems.validuses[u].description}\n"
            message = await ctx.send(text)
            m = await util.messagecheck(message, ctx.author, None)
            if m != "none":
                try:
                    i = int(m)
                    usename = validuses[i]
                except ValueError:
                    if m in validuses:
                        usename = m
                    else:
                        await message.delete()
                        return "Invalid usage."
            else:
                await message.delete()
                return "Canceled use."
            await message.delete()
        if usename != False:
            use = useitems.validuses[usename]
            user = explore.Player(ctx.author)
            if room == True and use.roomuse == False:
                return f"You must use that from your sylladex! Captchalogue it first."
            if use.targets != 0:
                if use.validtargets in ["sylladex", "both"]:
                    embed = user.embedsylladex
                else:
                    embed = None
                text = use.selectiontext
                text = text.replace("ITEM", f"{self.Item.calledby}")
                message = await ctx.send(text, embed=embed)
                targets = await util.messagecheck(message, ctx.author, None)
                await message.delete()
                if use.validtargets == "sylladex":
                    targets = user.itemcheck(targets)
                elif use.validtargets == "room":
                    targets = user.Room.roomcheck(targets)
                elif use.validtargets == "both":
                    if user.itemcheck(targets) != False:
                        targets = user.itemcheck(targets)
                    else:
                        targets = user.Room.roomcheck(targets)
            else:
                targets = True
            if targets != False:
                if use.targets == 0:
                    text = await use.func(self, ctx)
                else:
                    text = await use.func(self, ctx, targets)
                return text
            else:
                text = "Invalid target."
                if use.validtargets == "sylladex":
                    text += " Target item must be in your sylladex."
                elif use.validtargets == "room":
                    text += " Target item must be in the room."
                return text
        else:
            return f"A(n) {self.Item.calledby} can't be INTERACTed with."

    @property
    def calledby(self):
        cb = self.Item.calledby
        if self.punched != None and self.punched != "000000":
            cb += f" (`{self.punched}`)"
        if self.carved != None and self.carved != "000000":
            cb += f" {{`{self.carved}`}}"
        return cb

    @property
    def Item(self):
        try:
            return Item(self.item)
        except TypeError as e:
            print(f"{self.name} FAILED TO GET ITEM {self.item}")
            raise e

class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kinds")
    async def kinds(self, ctx):
        kindslist = []
        for b in util.bases:
            for k in util.bases[b]["kinds"]:
                if k not in kindslist:
                    kindslist.append(k)
        kindslist = sorted(kindslist)
        page = 0
        message = None
        while True:
            desc = ""
            for i in range(0+20*page,20+20*page):
                try:
                    desc += f"`{kindslist[i]}`\n"
                except IndexError:
                    pass
            embed = discord.Embed(title=f"Kinds page {page}", description=desc, color=config.sburbblue)
            embed.set_footer(text=f"Type a number to go to that page. Type `none` to close.")
            if message == None:
                message = await ctx.send(embed=embed)
            else:
                await message.edit(embed=embed)
            m = await util.messagecheck(message, ctx.author, None)
            if m == "none" or m == None:
                break
            try:
                page = int(m)
            except TypeError:
                pass
        if message != None:
            await message.delete()

    @commands.command(name="suggest")
    async def suggest(self, ctx):
        message = ctx.send("What will the name of the item be? `none` to cancel.")
        m = await util.messagecheck(message, ctx.author, None)
        if m != None and m != "none":
            hiddenattrs = ["base", "forbiddencode", "use"]
            name = m
            item = deepcopy(defaults) # new item is the default item
            while True:
                desc = "**What property would you like to edit? `done` to finish.**\n"
                for attr in item:
                    if attr not in hiddenattrs:
                        desc += f"`{attr}`: {item[attr]}\n"
                embed = discord.Embed(title=f"{name}", description=desc, color=config.sburbblue)
                embed.set_footer(text="It is suggested to start by choosing secret adjectives.")
                await message.edit(content=None,embed=embed)
                m = await util.messagecheck(message, ctx.author, list(item.keys())+["done"])
                if m == "done":
                    pass
                elif m in ["power", "inheritpower", "weight", "size"]: # set the attribute to the number(int)
                    helptext = {
                        "power": """Power is tied to size and LITERAL POWER of the object. Power should get a bit higher if the object is larger.
                        Examples:
                        `paper` - 1
                        `knife` - 10
                        `baseball bat` - 20
                        `table` - 30
                        `sword` - 40
                        `gun` - 100
                        `candy apple faygo` - 105""",
                        "inheritpower": """Inherit power is the power that this item will give to items it alchemizes with. This represents the METAPHORICAL POWER of an object.
                        Basically, if you think this item would be particularly powerful to alchemize with, this stat should be higher.
                        Usually 0-5, but if the object is particularly hard to alchemize with it might be a bit higher.
                        Examples:
                        `washing machine` - 10
                        `anime dvd` - 15
                        `ballpoint pen` - 25 (the pen is mightier than the sword)
                        `steroid bottle` - 45
                        `clock` - 100
                        `copying machine` - 250
                        `grandfather clock` - 413
                        """,
                        "weight": """The weight of an object. Should be similar to the size of the object.
                        Doesn't need to be precise.
                        Examples:
                        `paper` - 1
                        `sburb disc` - 2
                        `lap top` - 8
                        `baseball bat` - 10
                        `desktop computer` - 15
                        `totem lathe` - 200
                        `cruxtruder` - 500
                        """,
                        "size": """The size of an object. Should be similar to the weight of the object.
                        Doesn't need to be precise, but by default players can't weild anything over 20 size.
                        Examples:
                        `paper` - 1
                        `pistol` - 4
                        `lamp` - 10
                        `zweihander` - 20
                        `table` - 30
                        `washing machine` - 50
                        `cruxtruder` - 500
                        """
                        }
                elif m in ["dicemin", "dicemax"]: # set the attribute to number(float)
                    helptext = {
                    "dicemin": """The minimum dice roll for the item as a fraction of its POWER.
                    For things that aren't obviously good weapons this should be less than 1.
                    This should almost never be over 1.3.
                    Keep in mind that inconsistent weapons can have wider ranges of values.
                    Examples:
                    `paper` **0.2** - 0.5
                    `lap top` **0.3** - 0.7
                    `pizza cutter` **0.6** - 0.9
                    `baseball bat` **1.0** - 1.3
                    `chainsaw` **1.0** - 1.6
                    `pepper spray` **1.1** - 1.4
                    `sledge hammer` **0.7** - 2.0
                    `pistol` **0.2** - 2.3
                    `shotgun` **0.8** - 2.3
                    """,
                    "dicemax": """The maximum dice roll for the item as a fraction of its POWER.
                    For things that aren't obviously good weapons this should be less than 1.2.
                    This should almost never be over 2.
                    Keep in mind that inconsistent weapons can have wider ranges of values.
                    Examples:
                    `paper` 0.2 - **0.5**
                    `lap top` 0.3 - **0.7**
                    `pizza cutter` 0.6 - **0.9**
                    `baseball bat` 1.0 - **1.3**
                    `chainsaw` 1.0 - **1.6**
                    `pepper spray` 1.1 - **1.4**
                    `sledge hammer` 0.7 - **2.0**
                    `pistol` 0.2 - **2.3**
                    `shotgun` 0.8 - **2.3**
                    """
                    }
                # set the attribute to a dictionary whose values are lists of [inheritchance, "guaranteed inheritor"]
                elif m in ["kinds", "slots", "tags"]:
                    helptext = {
                    "kinds": """The kind of the object as used as a weapon.
                    If possible, try to use existing kinds (viewable using the >kind command **in another channel**) but feel free to add a new kind.
                    Format: `bladekind`
                    """,
                    "slots": """The equippable slot. Can be `head` `body` or `accessory`.
                    """
                    }
                # set the attribute to a dictionary whose values are lists of [power, "guaranteed inheritor"]
                elif m in ["onhiteffect", "weareffect", "consumeeffect", "secreteffect"]:
                    pass
                elif m == "cost":
                    pass
                elif m == "secretadjectives":
                    pass
                elif m == "description":
                    pass
        await message.delete()

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

for base in util.bases:
    for attr in defaults:
        if attr not in util.bases[base]:
            util.bases[base][attr] = defaults[attr]
    l = base.split(" ")
    truename = l.pop() # truename is last item of list
    adjectives = l # adjectives are the rest
    util.bases[base]["truename"] = truename
    util.bases[base]["adjectives"] = adjectives
    if "mundane" in util.bases[base]["tags"]:
        util.bases[base]["tags"]["mundane"][0] = 0
    util.items[base] = util.bases[base]
    if "code" in util.items[base]:
        util.codes[util.items[base]["code"]] = base
    else:
        item = Item(base)
        code = item.code # generate the codes for base items
print(util.codes)
util.writejson(util.bases, "bases")
util.writejson(util.items, "items")
