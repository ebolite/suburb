import asyncio
import discord
from discord.ext import tasks, commands

import alchemy
import explore
import maps
import binary
import util
import config
import random
import serverclient
import npcs

validuses = {
}

async def crumple(instance, ctx):
    if instance.crumple == None:
        instance.crumple = False
    if instance.crumple == False:
        instance.crumple = True
        return f"You crumple the {instance.Item.calledby}."
    elif instance.crumple == True:
        instance.crumple = True
        return f"You uncrumple the {instance.Item.calledby}."

async def rumple(instance, ctx):
    if instance.rumple == None:
        instance.rumple = False
    if instance.rumple == False:
        instance.rumple = True
        return f"You rumple the {instance.Item.calledby}."
    elif instance.rumple == True:
        instance.rumple = True
        return f"You unrumple the {instance.Item.calledby}."

async def punchcard(instance, ctx, target):
    target = alchemy.Instance(name=target)
    user = explore.Player(ctx.author)
    valid = True
    text = f"{user.name} inserts the card for {user.their} {target.Item.calledby} into the PUNCH DESIGNIX.\n{user.they.capitalize()} may choose to either input a `>code` manually, or punch the code of an `>item` in {user.their} possession."
    message = await ctx.send(text)
    m = await util.messagecheck(message, ctx.author, ["code", "item"])
    if m == "code":
        await message.edit(content=f"What 8-digit code should {user.name} input? (`none` cancels)")
        m = await util.messagecheck(message, ctx.author, None)
        if m == "none": return f"Canceled punching."
        if len(m) == 8:
            for char in m:
                if char not in binary.bintable:
                    return f"`{m}` is not a valid code, because it uses invalid characters."
            else:
                code = m
                if code not in util.codes:
                    return f"`{m}` is not a code that currently corresponds to an object."
        else:
            return f"`{m}` is not a valid code, because it is not the correct length."
    else:
        embed = user.embedsylladex
        await message.edit(embed=embed, content=f"What item's code should {user.name} use? (The item must be in {user.their} Captchalogue Deck)")
        m = await util.messagecheck(message, ctx.author, None)
        instname = user.itemcheck(m)
        if instname != False:
            inst = alchemy.Instance(name=instname)
            if inst.Item.forbiddencode:
                await message.delete()
                return f"{inst.calledby}'s code cannot be read!"
            else:
                code = inst.Item.code
        else:
            await message.delete()
            return f"`{m}` is not an item {user.name} has in {user.their} Captchalogue Deck."
    if target.Item.name != "punched card" and  target.Item.name != "pre-punched card" and code != "00000000":
        user.removecard(target.name)
        target = alchemy.Instance(item="punched card")
        user.Room.addinstance(target.name)
    if target.punched == None:
        target.punched = "00000000"
    print(f"{target.punched} || {code}")
    newcode = binary.codeor(target.punched, code)
    if newcode not in util.codes:
        c1 = util.codes[target.punched]
        c2 = util.codes[code]
        newitem = alchemy.Item(name=f"({c1}||{c2})", c1=c1, c2=c2, operation="||") # generate the item first
        target.punched = newitem.code
        newcode = newitem.code
    else:
        target.punched = newcode
    await message.delete()
    return f"Success! Resulted in code `{newcode}` punched on {target.Item.calledby}."

async def combinecards(instance, ctx):
    user = explore.Player(ctx.author)
    valid = True
    if instance.combine == None:
        text = f"What card should {user.name} combine {instance.calledby} with? (`none` to cancel)"
        embed = user.embedsylladex
        message = await ctx.send(text, embed=embed)
        m = await util.messagecheck(message, ctx.author, None)
        if m == "none": return f"Canceled combining."
        instname = user.itemcheck(m)
        if instname != False:
            inst = alchemy.Instance(name=instname)
            if inst.punched == None or inst.punched == "00000000":
                await message.delete()
                return f"{inst.calledby} is not a punched card, and cannot be combined!"
        else:
            await message.delete()
            return f"`{m}` is not an item {user.name} has in {user.their} Captchalogue Deck."
        await message.delete()
        user.removecard(instname)
        instance.combine = instname
        instance.oldpunched = instance.punched
        newcode = binary.codeand(instance.punched, inst.punched)
        if newcode not in util.codes:
            c1 = util.codes[instance.punched]
            c2 = util.codes[inst.punched]
            newitem = alchemy.Item(name=f"({c1}&&{c2})", c1=c1, c2=c2, operation="&&") # generate the item first
            instance.punched = newitem.code
            newcode = newitem.code
        else:
            instance.punched = newcode
        return f"Combined the two cards! New code: `{newcode}`"
    else:
        user.addcard()
        user.captchalogue(instance.combine) # give back other card
        instance.punched = instance.oldpunched
        instance.oldpunched = None
        return "Uncombined the two cards."

async def addcard(instance, ctx):
    user = explore.Player(ctx.author)
    user.addcard()
    user.removeinstance(instance.name)
    return f"{user.name} adds the empty captchalogue card to {user.their} sylladex."

async def cruxtrude(instance, ctx):
    if instance.opened == None:
        user = explore.Player(ctx.author)
        npc = npcs.Npc(type="kernelsprite")
        npc.team = "PLAYERS"
        npc.player = user.name
        user.Room.addnpc(npc.name)
        npc.follow(user)
        instance.opened = True
        return f"You open your CRUXTRUDER!\nA {npc.calledby} appears in the room!"
    else:
        user = explore.Player(ctx.author)
        inst = alchemy.Instance(item="cruxite dowel")
        user.Room.addinstance(inst.name)
        return f"{user.name} cruxtrudes a `CRUXITE DOWEL`!"

async def lathe(instance, ctx, target):
    user = explore.Player(ctx.author)
    target = alchemy.Instance(name=target)
    dowel = None
    for i, card in enumerate(user.sylladex):
        if card != {}:
            inst = alchemy.Instance(name=card["item"])
            if inst.Item.name == "cruxite dowel" and inst.carved == None:
                dowel = inst
                break
    else:
        return f"You have no uncarved cruxite dowels to carve!"
    if target.punched == None or target.punched == "00000000":
        return f"You try to carve the dowel, but because the card you used has no holes, the lathe does nothing."
    else:
        dowel.carved = target.punched
        return f"You carve the dowel with the code `{target.punched}`!"

async def alchemize(instance, ctx, target):
    user = explore.Player(ctx.author)
    target = alchemy.Instance(name=target)
    if target.Item.name != "cruxite dowel":
        return "You must insert cruxite dowels into the alchemiter!"
    code = target.carved
    if code == None:
        code = "00000000"
    if code not in util.codes:
        return f"That code `{code}` does not correspond to any item."
    itemname = util.codes[code]
    item = alchemy.Item(itemname)
    text = ""
    canalchemize = True
    for grist in item.cost:
        if item.cost[grist] != 0:
            text += f"{config.grists[grist]['emoji']} "
            if user.cache[grist] >= int(item.cost[grist] * item.power):
                text += f"~~{int(item.cost[grist] * item.power)}~~ "
            else:
                text += f"**{int(item.cost[grist] * item.power)}** "
                canalchemize = False
            text += "\n"
    if item.name in user.atheneum:
        title = f"{item.calledby}"
    else:
        title = "Unknown Item"
    embed = discord.Embed(title=title, description=text)
    if canalchemize:
        footer = f"Type `y` to alchemize this item or `n` to close this window."
    else:
        footer = f"You do not have enough grist to alchemize this item. Type `n` to close this window."
    embed.set_footer(text=footer)
    message = await ctx.send(embed=embed)
    if canalchemize == False:
        m = await util.messagecheck(message, ctx.author, ["n"])
        await message.delete()
        return ""
    else:
        m = await util.messagecheck(message, ctx.author, ["y", "n"])
        await message.delete()
        if m == "n":
            return ""
        else:
            for grist in item.cost:
                user.cache[grist] -= int(item.cost[grist] * item.power)
            inst = alchemy.Instance(item=item.name)
            user.Room.addinstance(inst.name)
            if inst.Item.name not in user.atheneum:
                user.atheneum.append(inst.Item.name)
            return f"The alchemiter successfully created {item.calledby}!"

async def computer(instance, ctx):
    message = None
    while True:
        valid = ["<:pesterchum:820863174307086337>", "<:build:816129883368718377>", "<:gristtorrent:820867320309088316>", "<:typheus:820874675931840522>"]
        if instance.installed != None and "sburb" in instance.installed:
            valid.append("<:suburb:820875159459463178>")
        valid += ["🔼", "⭕"]
        desc = ""
        for emoji in valid:
            if emoji == "<:pesterchum:820863174307086337>":
                desc += f"<:pesterchum:820863174307086337> **PESTERCHUM** A chat application.\n"
            if emoji == "<:build:816129883368718377>":
                desc += f"<:build:816129883368718377> **GRISTCACHE** View how much grist you have.\n"
            if emoji == "<:gristtorrent:820867320309088316>":
                desc += f"<:gristtorrent:820867320309088316> **GRISTTORRENT** Send grist or leech grist from the void.\n"
            if emoji == "<:typheus:820874675931840522>":
                desc += f"<:typheus:820874675931840522> **TYPHEUS** An internet browser.\n"
            if emoji == "<:suburb:820875159459463178>":
                desc += f"<:suburb:820875159459463178> **SBURB** A game that ends the world.\n"
            if emoji == "🔼":
                desc += f"🔼 **INSERT DISC** Insert a disc into your computer to install new software.\n"
            if emoji == "⭕":
                desc += f"⭕ **POWER DOWN**\n"
        embed = discord.Embed(title=f"{instance.Item.calledby}", description = desc)
        if message == None:
            message = await ctx.send(content=f"You boot up your {instance.Item.calledby}. You have a variety of APPLICATIONS to choose from.", embed=embed)
        else:
            await message.edit(content=f"You boot up your {instance.Item.calledby}. You have a variety of APPLICATIONS to choose from.", embed=embed)
        r = await util.reactioncheck(message, ctx.author, valid)
        if r == None: break
        else:
            emoji = str(r.emoji)
        if emoji == "<:pesterchum:820863174307086337>":
            await message.edit(content=f"You would open PESTERCHUM, but you already have a chat application to use. It's called DISCORD. You do, however, consider being a little more in-character and adding the Discord bot TupperBox to your server. If you were the type of person that enjoys roleplaying, you would think that's a good idea.", embed=None)
            await util.reactioncheck(message, ctx.author, ["◀"])
        elif emoji == "<:build:816129883368718377>":
            await message.delete()
            message = None
            await alchemy.Alchemy.gristcache(alchemy.Alchemy, ctx)
        elif emoji == "<:gristtorrent:820867320309088316>":
            await message.delete()
            message = None
            await alchemy.Alchemy.gristtorrent(alchemy.Alchemy, ctx)
        elif emoji == "<:typheus:820874675931840522>":
            embed = discord.Embed(title="HOMESTUCK")
            page = str(random.randint(0,8000))
            while len(page) < 5:
                page = "0" + page
            url = f"https://www.homestuck.com/images/storyfiles/hs2/{page}.gif"
            embed.set_image(url=url)
            await message.edit(content="",embed=embed)
            scathingcriticism = await ctx.send(content="You navigate to MSPAINT ADVENTURES and try to remember what page you were on last.\n...Is this what your idol D-CLUSSIE has been making recently? What is this horse shit?")
            await util.reactioncheck(message, ctx.author, ["◀"])
            await scathingcriticism.delete()
        elif emoji == "🔼":
            player = explore.Player(ctx.author)
            if player.itemcheck("Sburb disc") != False:
                if instance.installed == None or "sburb" not in instance.installed:
                    await message.edit(content="The SBURB DISC catches your eye. Insert it into the disc drive? (y/n)",embed=None)
                    m = await util.messagecheck(message, ctx.author, ["y", "n"])
                    if m == None or m == "n":
                        pass
                    else:
                        r = random.randint(10,20)
                        for i in range(r):
                            lines = ["<a:suburbspirograph:820899074986606613>"]
                            for i in range(5):
                                line = f"{random.choice(config.verbs)} {random.choice(config.nouns)}"
                                lines.append(f"`{line}`")
                            text = "\n".join(lines)
                            embed = discord.Embed(title="INSTALLING SBURB...", description=text, color=config.sburbblue)
                            await message.edit(content="", embed=embed)
                            await asyncio.sleep(random.randint(0,2))
                        await message.edit(content=f"Successfully installed SBURB onto your {instance.Item.calledby}!",embed=None)
                        if instance.installed == None: instance.installed = []
                        instance.installed.append("sburb")
                else:
                    await message.edit(content="Sburb is already installed on this device!",embed=None)
                    await asyncio.sleep(3)
            else:
                await message.edit(content="You don't have anything in your SYLLADEX to install! Maybe some EXPLORATION is in order...",embed=None)
                await asyncio.sleep(3)
        elif emoji == "<:suburb:820875159459463178>":
            player = explore.Player(ctx.author)
            while True:
                if player.client == None:
                    await message.edit(content="You boot up the SBURB server application. Connect to a client? (y/n)",embed=None)
                    m = await util.messagecheck(message, ctx.author, ["y", "n"])
                    if m == None or m == "n":
                        break
                    else:
                        client = None
                        while True:
                            await message.edit(content="Type the NAME of the client you would like to connect to. `none` to exit.",embed=None)
                            m = await util.messagecheck(message, ctx.author, None)
                            if m == None or m == "none":
                                break
                            else:
                                for member in util.sessions[player.session]["members"]:
                                    c = explore.Player(member)
                                    if c.name == m:
                                        print("found client")
                                        client = c
                                        break
                                else:
                                    await message.edit(content=f"`{m}` is not anyone in your session!",embed=None)
                                    await asyncio.sleep(3)
                                if client != None: break
                        if client == None: break
                        if client.server == None:
                            members = util.sessions[player.session]["members"].copy()
                            sc = {}
                            unassigned = []
                            for member in members:
                                m = explore.Player(member)
                                if m.client != None:
                                    sc[member] = m.client
                                elif m.server == None:
                                    unassigned.append(member)
                            text = "Current Chain (Server --> Client):\n"
                            if len(sc) == 0: text += "`no connections`"
                            for server in sc:
                                s = explore.Player(server)
                                c = explore.Player(sc[server])
                                if s.name in text:
                                    text = text.replace(s.name, f"{s.name} --> {c.name}")
                                else:
                                    text += f" {s.name} --> {c.name}"
                            if len(unassigned) != 0:
                                text += f"\nUnassigned: "
                                for id in unassigned:
                                    m = explore.Player(id)
                                    text += f"`{m.name}` "
                            text += f"\n\nConnecting you as the server to {client.name} will result in the following chain:\n"
                            sc[player.id] = client.id
                            if player.id in unassigned:
                                unassigned.remove(player.id)
                            if client.id in unassigned:
                                unassigned.remove(client.id)
                            text2 = ""
                            for server in sc:
                                s = explore.Player(server)
                                c = explore.Player(sc[server])
                                if s.name in text2:
                                    text2 = text2.replace(s.name, f"{s.name} --> {c.name}")
                                else:
                                    text2 += f" {s.name} --> {c.name}"
                            if len(unassigned) != 0:
                                text2 += f"\nUnassigned: "
                                for id in unassigned:
                                    m = explore.Player(id)
                                    text += f"{m.name} "
                            text2 += "\nWould you like to make the connection? (y/n)"
                            await message.edit(content=text+text2,embed=None)
                            m = await util.messagecheck(message, ctx.author, ["y", "n"])
                            if m == None or m == "n":
                                pass
                            else:
                                client.server = player.id
                                player.client = client.id
                                await message.edit(content=f"Connected you to {client.name} as {client.their} server player!",embed=None)
                                await asyncio.sleep(3)
                                break
                        else:
                            s = explore.Player(client.server)
                            await message.edit(content=f"{client.name} already has a server player: {s.name}",embed=None)
                            await asyncio.sleep(3)
                else:
                    if message != None:
                        await message.delete()
                        message = None
                    await serverclient.sburb(ctx) # sburb stuff here
                    break
        elif emoji == "⭕":
            break
    if message != None: await message.delete()
    return f"You power off the {instance.Item.calledby}."

async def enter(instance, ctx):
    player = explore.Player(ctx.author)
    if player.entered == True:
        return f"You have already entered the Medium! You can't enter again!"
    message = await ctx.send("Are you sure you want to enter the Medium? If you prototype your KERNELSPRITE after you enter it will have no effect on the BATTLEFIELD. (y/n)")
    m = await util.messagecheck(message, ctx.author, ["y", "n", "none"])
    await message.delete()
    if m != "y":
        return f"Canceled entry."
    for y, line in enumerate(player.Map.map):
        for x, char in enumerate(line):
            if player.Map.map[y][x] not in config.special+["."]:
                random.seed(f"{player.Map.name}{x}{y}spawnenemy")
                rng = random.random()
                if rng < 0.3:
                    random.seed(f"{player.Map.name}{x}{y}number")
                    number = random.randint(1,4)
                    room = player.Map.getroom(x=x, y=y)
                    for enemy in range(number):
                        random.seed(f"{player.Map.name}{x}{y}type")
                        rng = random.random()
                        if rng < 0.05:
                            type = "ogre"
                            tier = 1
                        else:
                            type = "imp"
                            tier = random.randint(1,5)
                        npc = room.addnpc(type=type, tier=tier)
                        print(f"adding npc {npc.calledby} at {x}, {y}")
    player.entered = True
    player.removeinstance(instance.name)
    return f"You find yourself in the {player.Overmap.title}."

class Use():
    def __init__(self, name):
        self.name = name
        validuses[name] = self
        self.func = None
        self.targets = 0
        self.selectiontext = "Specify an item to use ITEM with."
        self.validtargets = "sylladex" # sylladex, room, both and code
        self.roomuse = True

usecrumple = Use("crumple")
usecrumple.func = crumple
usecrumple.description = "Crumples the item. Does nothing."

userumple = Use("rumple")
userumple.func = rumple
userumple.description = "Rumples the item. Also does nothing."

usepunchcard = Use("punch card")
usepunchcard.func = punchcard
usepunchcard.description = "Allows codes to be punched onto cards."
usepunchcard.targets = 1

usecombinecards = Use("combine cards")
usecombinecards.func = combinecards
usecombinecards.description = "Combine the codes of two punched cards."
usecombinecards.selectiontext = "Insert the card you wish to punch."
usecombinecards.targets = 0

useaddcard = Use("add card")
useaddcard.func = addcard
useaddcard.description = "Consumes the item to add an empty captchalogue card to the sylladex."
useaddcard.targets = 0
useaddcard.roomuse = False

usecruxtruder = Use("cruxtrude")
usecruxtruder.func = cruxtrude
usecruxtruder.description = "Creates an uncarved cruxite dowel."
usecruxtruder.targets = 0

usetotemlathe = Use("lathe")
usetotemlathe.func = lathe
usetotemlathe.description = "Lathe a code into a cruxite dowel."
usetotemlathe.targets = 1
usetotemlathe.selectiontext = "What code should be lathed into the dowel?"

usealchemiter = Use("alchemize")
usealchemiter.func = alchemize
usealchemiter.description = "Create new items using grist."
usealchemiter.targets = 1
usealchemiter.selectiontext = "Insert the dowel to alchemize."

usecomputer = Use("computer")
usecomputer.func = computer
usecomputer.description = "Use the various apps on your computer."
usecomputer.targets = 0

useenter = Use("enter")
useenter.func = enter
useenter.description = "Enter the Medium."
useenter.targets = 0
useenter.roomuse = False
