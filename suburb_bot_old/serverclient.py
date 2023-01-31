import asyncio
import discord
from discord.ext import tasks, commands

import explore
import alchemy
import maps
import util
import config

async def sburb(ctx):
    server = explore.Player(ctx.author)
    client = explore.Player(server.client)
    message = None
    while True:
        viewport = maps.displayregion(client, width=12, height=6, flash=True)
        xstart = client.pos[0] - 12 # top left
        ystart = client.pos[1] - 6
        xend = client.pos[0] + 12
        yend = client.pos[1] + 6
        text = ""
        text += viewport+"\n\n"
        embed = discord.Embed(title=f"SBURB - {client.name}", description=text, color=config.sburbblue)
        emojis = [
            "<:select:821162951556857866>",
            "<:revise:821162951452655656>",
            "<:deploy:821162951624491057>",
            "<:phernaliaregistry:821162951469039636>",
            "<:build:816129883368718377>",
            "<:atheneum:821162951469826058>",
            "<:alchemize:821162951422640148>",
            "❔",
            "🔁",
            "◀"
            ]
        if message == None:
            message = await ctx.send(content="", embed=embed)
        else:
            await message.edit(content="", embed=embed)
        r = await util.reactioncheck(message, ctx.author, emojis)
        if r == "none" or r == None:
            break
        emoji = str(r.emoji)
        if emoji == "<:select:821162951556857866>": # select
            pass
        elif emoji == "<:revise:821162951452655656>": # revise
            await message.delete()
            message = None
            text = await revise(ctx, client, [xstart, xend], [ystart, yend])
            if text != None:
                await ctx.send(text)
        elif emoji == "<:deploy:821162951624491057>": # deploy
            await message.delete()
            message = None
            text = await deploy(ctx, client, [xstart, xend], [ystart, yend])
            if text != None:
                await ctx.send(text)
        elif emoji == "<:phernaliaregistry:821162951469039636>": # phernalia registry
            pass
        elif emoji == "<:build:816129883368718377>": # client grist cache
            await message.delete()
            message = None
            await alchemy.Alchemy.gristcache(alchemy.Alchemy, ctx, client)
        elif emoji == "<:atheneum:821162951469826058>": # client atheneum
            pass
        elif emoji == "<:alchemize:821162951422640148>": # alchemize
            pass
        elif emoji == "❔": # help
            pass
        elif emoji == "◀":
            break
    if message != None:
        await message.delete()

async def deploy(ctx, client, xrange, yrange):
    # choose item
    if client.deployed == None: client.deployed = []
    validitems = ["cruxtruder", "totem lathe", "alchemiter", "punch designix", "pre-punched card"]
    candeploy = []
    text = "What will you deploy? `none` escapes.\n"
    desc = ""
    for i in validitems:
        item = alchemy.Item(i)
        if item.name in client.deployed:
            desc += f"~~{item.name}~~:"
        else:
            desc += f"{item.name}: "
        deployable = True
        for g in item.cost:
            cost = int(item.cost[g] * item.power)
            desc += f"{config.grists[g]['emoji']} "
            if client.cache[g] < cost:
                deployable = False
                desc += f"**{cost}** ({client.cache[g]}) "
            else:
                desc += f"~~{cost}~~"
        if deployable == True: candeploy.append(i)
        desc += "\n"
    embed = discord.Embed(color=config.sburbblue, title="DEPLOY", description=desc)
    message = await ctx.send(content=text, embed=embed)
    m = await util.messagecheck(message, ctx.author, validitems+["none"])
    if m == "none":
        await message.delete()
        return None
    else:
        if m not in candeploy:
            await message.delete()
            return f"`{m}` costs too much grist to deploy!"
        if m in client.deployed:
            await message.delete()
            return f"You have already deployed one of those!"
    item = alchemy.Item(m)
    #todo : pre-punched card / entry
    # choose location
    map = []
    mapobj = client.Map
    for y in range(yrange[0], yrange[1]+1):
        line = []
        for x in range(xrange[0], xrange[1]+1):
            try:
                line.append(mapobj.map[y][x])
            except IndexError:
                pass
        if len(line) != 0: map.append(line)
    text = "\`\`\````\n"
    for y, line in enumerate(map):
        newline = ""
        for char in map[y]:
            newline += char
        text += f"{newline}\n"
    text += "``````"
    embed = discord.Embed(color=config.sburbblue, description=text)
    await message.edit(content=f"Copy the following text (with the \`\`\`s) and edit a `*` into the space that you want to deploy to. `none` to escape.", embed=embed)
    m = await util.messagecheck(message, ctx.author, None)
    if m == "none":
        await message.delete()
        return None
    old = m
    m = m.replace("```\n", "")
    m = m.replace("\n```", "")
    newmap = m.split("\n")
    if len(newmap) != len(map):
        await message.delete()
        return f"Your map is incorrectly sized vertically!\nYours: {len(newmap)} Required: {len(map)}\nYou typed:\n{old}"
    for y, line in enumerate(newmap):
        newmap[y] = list(line)
        if len(newmap[y]) != len(map[y]):
            await message.delete()
            return f"Your map is incorrectly sized horizontally!\nYours: {len(newmap[y])} Required: {len(map[y])}\nYou typed:\n{old}"
    # deploy
    for y, finaly in enumerate(range(yrange[0], yrange[1]+1)):
        for x, finalx in enumerate(range(xrange[0], xrange[1]+1)):
            try:
                if newmap[y][x] == "*":
                    if mapobj.map[finaly][finalx] in config.special:
                        await message.delete()
                        return f"You can only deploy onto passible tiles, not `{mapobj.map[finaly][finalx]}`!"
                    elif mapobj.map[finaly+1][finalx] not in config.impassible + config.infallible:
                        await message.delete()
                        return f"You can only deploy onto tiles that are above solid ground, not `{mapobj.map[finaly+1][finalx]}`!"
                    else:
                        for g in item.cost:
                            cost = int(item.cost[g] * item.power)
                            if client.cache[g] < cost:
                                await message.delete()
                                return f"{client.name} no longer has enough grist to deploy the {item.calledby}!"
                        room = mapobj.getroom(finalx, finaly)
                        inst = alchemy.Instance(item=item.name)
                        if item.name == "pre-punched card":
                            inst.punched = "I11w1a11"
                        room.addinstance(inst.name)
                        client.deployed.append(item.name)
                        await message.delete()
                        return f"Deployed the {item.calledby} successfully!"
            except IndexError:
                pass
    else:
        return f"You need to specify a location to deploy to by replacing a tile with `*`."


async def revise(ctx, client, xrange, yrange):
    map = []
    mapobj = client.Map
    for y in range(yrange[0], yrange[1]+1):
        line = []
        for x in range(xrange[0], xrange[1]+1):
            try:
                line.append(mapobj.map[y][x])
            except IndexError:
                pass
        if len(line) != 0: map.append(line)
    text = "\`\`\````\n"
    for y, line in enumerate(map):
        newline = ""
        for char in line:
            newline += char
        text += f"{newline}\n"
    text += "``````"
    embed = discord.Embed(color=config.sburbblue, description=text)
    message = await ctx.send(content=f"Copy the following text (with the \`\`\`s) and reply with an edited version. You have up to 10 minutes to edit. Type `none` to escape.", embed=embed)
    m = await util.messagecheck(message, ctx.author, None, timeout=600)
    if m == "none" or m == None:
        await message.delete()
        return None
    old = m
    m = m.replace("```\n", "")
    m = m.replace("\n```", "")
    newmap = m.split("\n")
    if len(newmap) != len(map):
        await message.delete()
        for line in map:
            print(f"'{''.join(line)}'")
        # for line in newmap:
        #     print(line)
        # for line in map:
        #     print("".join(line))
        return f"Your map is incorrectly sized vertically!\nYours: {len(newmap)} Required: {len(map)}\nYou typed:\n{old}"
    for y, line in enumerate(newmap):
        newmap[y] = list(line)
        if len(newmap[y]) != len(map[y]):
            print(line)
            print(newmap[y])
            await message.delete()
            return f"Your map is incorrectly sized horizontally!\nYours: {len(newmap[y])} Required: {len(map[y])}\nYou typed:\n{old}"
    # detect changes
    changes = 0
    for y, line in enumerate(map):
        for x, char in enumerate(map[y]):
            if newmap[y][x] != char:
                changes += 1
                if newmap[y][x] in config.forbidden:
                    await message.delete()
                    print(f"forbidden tiles {config.forbidden}")
                    return f"You cannot add the tile `{newmap[y][x]}` ({config.maptiles[newmap[y][x]]})!\nYou typed:\n{old}"
                elif char in config.forbidden:
                    await message.delete()
                    print(f"forbidden tiles {config.forbidden}")
                    return f"You cannot remove the tile `{char}` ({config.maptiles[newmap[y][x]]})!\nYou typed:\n{old}"
                elif char != ".":
                    changes += 1
    cost = 5 * changes
    if client.cache["build"] < cost:
        await message.delete()
        return f"Cannot revise! These changes would cost {config.grists['build']['emoji']} **{cost}**, but {client.name} only has {config.grists['build']['emoji']} {client.cache['build']}.\nYou typed:\n{old}"
    else:
        embed = discord.Embed(color=config.sburbblue, description=old)
        await message.edit(content=f"These changes will cost {client.name} {config.grists['build']['emoji']} **{cost}**.\n{client.their.capitalize()} grist cache currently holds {client.name} {config.grists['build']['emoji']} {client.cache['build']}, which would leave {client.them} with {config.grists['build']['emoji']} {client.cache['build'] - cost}. Proceed? (y/n)", embed=embed)
        m = await util.messagecheck(message, ctx.author, ["y", "n"])
        if m == None or m == "n":
            return None
        else:
            client.addgrist("build", cost * -1)
    # apply  changes
    for y, finaly in enumerate(range(yrange[0], yrange[1]+1)):
        for x, finalx in enumerate(range(xrange[0], xrange[1]+1)):
            try:
                mapobj.map[finaly][finalx] = newmap[y][x]
            except IndexError:
                pass
    await message.delete()
    return f"Revised the area for {config.grists['build']['emoji']} **{cost}**. Remaining grist: {config.grists['build']['emoji']} {client.cache['build']}"
