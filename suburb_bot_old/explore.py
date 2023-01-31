import discord
import json
import random
import asyncio
import os
import string
import math
from discord.ext import tasks, commands

import binary
import config
import alchemy
import maps
import util
import skills
import stateseffects
import aspects
import npcs

class Explore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="session")
    async def session(self, ctx):
        player = Player(ctx.author)
        if player.session != None:
            members = util.sessions[player.session]["members"].copy()
            sc = {}
            unassigned = []
            for member in members:
                m = Player(member)
                if m.client != None:
                    sc[member] = m.client
                elif m.server == None:
                    unassigned.append(member)
            text = f"Session `{player.session}`\nCurrent Chain (Server --> Client):\n"
            if len(sc) == 0: text += "`no connections`"
            for server in sc:
                s = Player(server)
                c = Player(sc[server])
                if s.name in text:
                    text = text.replace(s.name, f"{s.name} --> {c.name}")
                else:
                    text += f" {s.name} --> {c.name}"
            if len(unassigned) != 0:
                text += f"\nUnassigned: "
                for id in unassigned:
                    m = Player(id)
                    text += f"`{m.name}` "
        else:
            text = f"You are not in a session!"
        message = await ctx.send(text)
        await util.reactioncheck(message, ctx.author, "◀")
        await message.delete()

    @commands.command(name="whois")
    async def whois(self, ctx, target: discord.Member = None):
        if target == None: target = ctx.author
        player = Player(target)
        embed = None
        text = ""
        if player.setup == True:
            desc = "\n"
            map = player.Overmap
            desc += f"*{player.they}/{player.them}*\n\n"
            if player.wielding != None:
                inst = alchemy.Instance(player.wielding)
                desc += f"`Wielding:` {inst.Item.calledby}\n"
            if player.server != None:
                s = Player(player.server)
                desc += f"`Server Player:` {s.name}\n"
            if player.client != None:
                c = Player(player.client)
                desc += f"`Client Player:` {c.name}\n"
            if player.server != None or player.client != None: desc += "\n"
            desc += f"`Land:` {map.title}\n"
            desc += f"`Grist category:` {map.gristcategory}\n"
            for grist in config.gristcategories[map.gristcategory]:
                desc += f"{config.grists[grist]['emoji']} "
            desc += "\n\n**Stats**\n"
            desc += f"`ECHELADDER RUNG:` {player.rung}\n"
            for stat in player.stats:
                desc += f"`{stat}:` {player.stats[stat]}\n"
            embed = discord.Embed(title=f"`{player.name}` the {player.gameclass.capitalize()} of {player.aspect.capitalize()}\n", description=desc, color=player.color)
        else:
            text = "That player hasn't finished their setup yet!"

        message = await ctx.send(text, embed=embed)
        await util.reactioncheck(message, ctx.author, ["◀"])
        await message.delete()

    @commands.command(name="sessionassign")
    async def sessionassign(self, ctx): # performs assignsession again
        author = ctx.author
        await self.assignsession(author, ctx)

    @commands.command(name="character")
    async def character(self, ctx): # performs character creation again
        author = ctx.author
        await self.createcharacter(author, ctx)

    @commands.command(name="debugrung")
    async def debugrung(self, ctx, rung): # sets you to rung
        player = Player(ctx.author)
        player.rung = int(rung)
        await ctx.send(f"Set your ECHELADDER rung to {int(rung)}")

    @commands.command(name="debugclass")
    async def debugclass(self, ctx, cls): # sets you to cls
        player = Player(ctx.author)
        player.gameclass = cls
        await ctx.send(f"Set your class to {cls}")

    @commands.command(name="debugaspect")
    async def debugaspect(self, ctx, aspect): # sets you to aspect
        player = Player(ctx.author)
        player.aspect = aspect
        await ctx.send(f"Set your aspect to {aspect}")

    @commands.command(name="debugsecondary")
    async def debugsecondary(self, ctx, vial): # sets your secondary to vial
        player = Player(ctx.author)
        player.secondaryvial = vial
        await ctx.send(f"Set your secondary vial to {vial}")

    @commands.command(name="debugportfolio")
    async def debugportfolio(self, ctx): # resets your assigned specibi
        player = Player(ctx.author)
        player.portfolio = [{}, {}]
        await ctx.send(f"Cleared your portfolio.")

    async def assignsession(self, author, ctx):
        player = Player(author)
        message = await ctx.send(f"You are not in a session. Would you like to create a session or join an existing session? (create/join)")
        m = await util.messagecheck(message, author, ["create", "join"])
        decision = m
        if decision == "create":
            confirm = False
            while confirm == False:
                await message.edit(content=f"You will be the owner of your new session. You must assign a session name and password. What will the session name be?")
                m = await util.messagecheck(message, author, None)
                name = m
                if name not in util.sessions:
                    await message.edit(content=f"Your session name will be `{name}`. Is this okay? (y/n)")
                    m = await util.messagecheck(message, author, ["y", "n"])
                    if m == "y":
                        sessionname = name
                        confirm = True
                else:
                    await message.edit(content=f"That session name is already taken. Choose something else.")
                    await asyncio.sleep(5)
            confirm = False
            while confirm == False:
                await message.edit(content=f"What will the password of your session be? Don't pick any password you actually use, because this password will be stored in plaintext on the admin's harddrive.")
                m = await util.messagecheck(message, author, None)
                password = m
                await author.send(content=f"Your session details:\n`session name`: {sessionname}\n`session password`: {password}\nYou may want to pin this message so your friends can join you.")
                await message.edit(content=f"You have been DMed the password you've chosen. Is this the password you want to choose? (y/n)")
                m = await util.messagecheck(message, author, ["y", "n"])
                if m == "y":
                    confirm = True
            util.sessions[sessionname] = {}
            util.sessions[sessionname]["password"] = password
            util.sessions[sessionname]["members"] = [str(player.id)]
            util.sessions[sessionname]["overmaps"] = {}
            util.sessions[sessionname]["gutter"] = {}
            util.sessions[sessionname]["prototypes"] = {}
            player.session = sessionname
            await message.edit(content=f"Finished session setup and assigned you to session {sessionname}.")
        else:
            confirm = False
            while confirm == False:
                await message.edit(content=f"What is the name of the session you want to join?")
                m = await util.messagecheck(message, author, None)
                sessionname = m
                if sessionname in util.sessions:
                    confirm = True
                else:
                    await message.edit(content=f"That is not a valid session. Try something else.")
                    await asyncio.sleep(5)
            confirm = False
            while confirm == False:
                await message.edit(content=f"Type the password for `{sessionname}`.")
                m = await util.messagecheck(message, author, None)
                password = m
                if util.sessions[sessionname]["password"] == password:
                    util.sessions[sessionname]["members"].append(str(player.id))
                    player.session = sessionname
                    confirm = True
                else:
                    await message.edit(f"Incorrect password. Try again.")
                    await asyncio.sleep(5)
            await message.edit(content=f"Successfully joined session `{sessionname}`!")
        util.writejson(util.sessions, "sessions")
        util.writejson(util.players, "players")

    async def createcharacter(self, author, ctx):
        player = Player(author)
        confirm = False
        while confirm == False:
            message = await ctx.send(f"`A young being of indeterminate nature exists in some kind of area. What will this being's name be?`")
            m = await util.messagecheck(message, author, None, noreaction=True)
            name = m
            await message.edit(content=f"`This being's name will be {name}.`\nAre you sure? (y/n)")
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.name = name
                confirm = True
            else:
                await message.delete()
        confirm = False
        while confirm == False:
            await message.edit(content=f"`You think that 'being' is a noncomittal, inoffensive and far too general term, and that some other term might befit this 'being.'`\nWhat should this being be? Ex: girl, boy, woman, man, child, person")
            m = await util.messagecheck(message, author, None)
            noun = m
            await message.edit(content=f"`A young {noun} stands in a room. Or maybe the {noun} is sitting, or flying. We don't know. The name of this {noun} is {name}.`\nDoes this sound right? (y/n)")
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.noun = noun
                confirm = True
        confirm = False
        while confirm == False:
            await message.edit(content=f"`A young {noun} exists in some non-descriptive fashion in a room. Their name is {name}.`\nWait, 'they?' What pronouns should this {noun} go by? Format: `he/him/his/his` `she/her/her/hers` `they/them/their/theirs` `it/it/its/its` etc.")
            m = await util.messagecheck(message, author, None, noreaction=True)
            pronouns = m
            pronouns = pronouns.split("/")
            if len(pronouns) == 4:
                await message.edit(content=f"`A young {noun} stands in {pronouns[2]} bedroom. Today is a special day, as it is the anniversary of the day {pronouns[0]} was born. Surely the friends of {pronouns[3]} have sent {pronouns[1]} numerous gifts.`\nDoes this sound right? (y/n)")
                m = await util.messagecheck(message, author, ["y", "n"])
                if m == "y":
                    player.they = pronouns[0]
                    player.them = pronouns[1]
                    player.their = pronouns[2]
                    player.theirs = pronouns[3]
                    confirm = True
        confirm = False
        validinterests = config.interests.copy()
        while confirm == False:
            d = f"`This {noun} has a number of interests.`\nWhat will {player.their} first interest be?\n"
            for i in validinterests:
                d += f"`{i}` "
            await message.edit(content=d)
            m = await util.messagecheck(message, author, validinterests)
            interest = m
            await message.edit(content=f"{player.name}'s first interest will be {interest.upper()}.\nIs this okay? (y/n)")
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.interest1 = interest
                confirm = True
        validinterests.remove(interest)
        confirm = False
        while confirm == False:
            d = f"What will {player.their} second interest be?\n"
            for i in validinterests:
                d += f"`{i}` "
            await message.edit(content=d)
            m = await util.messagecheck(message, author, validinterests)
            interest = m
            await message.edit(content=f"{player.name}'s second interest will be {interest.upper()}.\nIs this okay? (y/n)")
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.interest2 = interest
                confirm = True
        confirm = False
        while confirm == False:
            d = f"**What aspect resonates the best with {player.name}?**\n"
            for aspect in config.aspects:
                d += f"`{aspect}` {config.aspects[aspect]['description']}\n"
            d += "*Each session is recommended to have at least one player of each aspect marked with (\*)*"
            await message.edit(content=d)
            m = await util.messagecheck(message, author, config.aspects.keys())
            aspect = m
            await message.edit(content=f"{player.name} will be a {aspect.upper()} player.\n{config.aspects[aspect]['description']}\nIs this okay? (y/n)")
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.aspect = aspect
                confirm = True
        confirm = False
        while confirm == False:
            d = f"**What class should {player.name} play as?**\n"
            for c in config.classes:
                d += f"`{c}` {config.classes[c]['description']}\n"
            d = d.replace("ASPECT", f"{player.aspect.upper()}")
            await message.edit(content=d)
            m = await util.messagecheck(message, author, config.classes.keys())
            c = m
            await message.edit(content=f"{player.name} will be the {c.upper()} of {player.aspect}.\nIs this okay? (y/n)")
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.gameclass = c
                confirm = True
        confirm = False
        while confirm == False:
            meters = ["gambit", "horseshitometer", "mangrit", "imagination"]
            d = f"**What SECONDARY VIAL should {player.name} have?**\n"
            d += "`gambit` PRANKSTER'S GAMBIT: Increases by dealing damage with HUMOROUS weapons. Decreases when taking damage from HUMOROUS weapons. Increases/decreases damage dealt with HUMOROUS weapons.\n\n"
            d += "`horseshitometer` FLIGHTY BROADS AND THEIR SNARKY HORSESHITOMETER: Increases by AUTO-PARRYING attacks. Decreases by having your attacks AUTO-PARRIED. Increases/decreases SAVVY, which affects your chance to dodge.\n\n"
            d += "`mangrit` MANGRIT: Increases each turn. Increases damage.\n\n"
            d += "`imagination` IMAGINATION: Increases proportional to ASPECT drained. Increases ASPECT generation.\n\n"
            await message.edit(content=d)
            m = await util.messagecheck(message, author, meters)
            v = m
            await message.edit(content=f"{player.name} will have a {m.upper()} METER.\nIs this okay? (y/n)")
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.secondaryvial = v
                confirm = True
        confirm = False
        await message.delete()
        while confirm == False:
            d = ""
            for type in config.gristcategories:
                d += f"`{type}` "
                for g in config.gristcategories[type]:
                    d += f"{config.grists[g]['emoji']} "
                d += "\n"
            lines = d.split("\n")
            d = ""
            for i in range(7):
                d += lines.pop(0) + "\n"
            embed = discord.Embed(title="Grist Categories", description = d, color=config.sburbblue)
            todelete = []
            message = await ctx.send(content=f"Soon this {noun} will be sent into a game with {player.their} friends. What should the type of {player.their} land be?", embed=embed)
            todelete.append(message)
            d = ""
            for i in range(7):
                d += lines.pop(0) + "\n"
            embed = discord.Embed(description = d, color=config.sburbblue)
            m = await ctx.send(embed=embed)
            todelete.append(m)
            d = ""
            while len(lines) != 0:
                d += lines.pop(0) + "\n"
            embed = discord.Embed(description = d, color=config.sburbblue)
            m = await ctx.send(embed=embed)
            todelete.append(m)
            m = await util.messagecheck(message, author, config.gristcategories.keys())
            category = m
            d = f"Your land will be `{category}` and have the following grist types:\n"
            for index, grist in enumerate(config.gristcategories[category]):
                d += f"Tier {index+1}: {config.grists[grist]['emoji']} {grist}\n"
            d += "Is this okay? (y/n)"
            message = await ctx.send(d)
            m = await util.messagecheck(message, author, ["y", "n"])
            if m == "y":
                player.gristcategory = category
                confirm = True
            for m in todelete:
                await m.delete()
        await ctx.send(content=f"Successfully set up your character.")
        m = maps.Overmap(player.session, f"{player.id}{player.session}", player)
        await ctx.send(f"Your land is the `{m.title}` ({m.acronym}).")
        player.overmap = m.name
        player.land = m.name
        player.__init__(author)
        player.Overmap.genlandname()
        computer = random.choice(config.itemcategories["computers"])
        player.Room.additem("Sburb disc")
        player.Room.additem(computer)
        for i in range(5):
            player.Room.addcategoryitem(player.interest1)
            player.Room.addcategoryitem(player.interest2)
        player.setup = True
        util.writejson(util.players, "players")
        util.writejson(util.sessions, "sessions")

    @staticmethod
    async def omapflash(message, ctx): # flash the window every so often with player location info and enemy location info
        player = Player(ctx.author)
        flash = True
        await asyncio.sleep(1)
        while True:
            desc = player.Overmap.displaymap(player, flash=flash)
            embed = discord.Embed(title=f"{player.Overmap.title}", description=desc, color=player.Overmap.color)
            embed.set_footer(text="w a s d to move.\nType `none` to delete.")
            await message.edit(embed=embed,content=None)
            await asyncio.sleep(1)
            flash = not flash

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="embark")
    async def embark(self, ctx):
        player = Player(ctx.author)
        overmap = player.Overmap
        desc = overmap.displaymap(player, flash=True)
        embed = discord.Embed(title=f"{overmap.title}", description=desc, color=overmap.color)
        canmove = False
        if player.Map.name != player.Overmap.housemap:
            embed.set_footer(text="w a s d to move.\nType `.` to wait.")
            canmove = True
        else:
            embed.set_footer(text="You can only move if you are not on a home tile.\nType `none` to delete.")
        message = await ctx.send(embed=embed,content=None)
        if canmove:
            while True:
                if message == None:
                    message = await ctx.send(f"{config.sburb} LOADING ...")
                flash = asyncio.create_task(self.omapflash(message, ctx))
                messagecheck = asyncio.create_task(util.messagecheck(message, ctx.author, ["w", "a", "s", "d", "." "none"]))
                done, pending = await asyncio.wait([messagecheck, flash], return_when=asyncio.FIRST_COMPLETED)
                for t in done:
                    if t is messagecheck:
                        flash.cancel()
                        m = await messagecheck
                    else:
                        break
                if m == "none" or m == None:
                    break
                if player.Strife == None:
                    if m != ".":
                        player.omove(m)
                    rng = random.random()
                    if rng < 0.2: # random encounter
                        await message.delete()
                        message = None
                        difficulty = player.Overmap.difficultymap[player.opos[1]][player.opos[0]]
                        enemies = npcs.encounterfromdifficulty(difficulty, player)
                        await Explore.startfight(Explore, ctx, enemies, [player], Map=player.Map)
                else:
                    await message.edit(content="You cannot move while in strife!", embed=None)
                    await asyncio.sleep(3)
        else:
            await util.messagecheck(message, ctx.author, ["none"])
        await message.delete()

    @staticmethod
    async def flash(message, ctx): # flash the window every so often with player location info and enemy location info
        player = Player(ctx.author)
        flash = True
        await asyncio.sleep(1)
        while True:
            embed = player.Map.mapembed(player, flash=flash)
            await message.edit(embed=embed)
            await asyncio.sleep(1)
            flash = not flash

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="explore")
    async def explore(self, ctx):
        author = ctx.author
        player = Player(ctx.author)
        message = None
        while True:
            player = Player(ctx.author)
            room = player.Room
            embed = player.Map.mapembed(player, flash=True)
            if message == None:
                message = await ctx.send(embed=embed)
            else:
                await message.edit(embed=embed)
            flash = asyncio.create_task(self.flash(message, ctx))
            messagecheck = asyncio.create_task(util.messagecheck(message, author, ["w", "a", "s", "d", "none", "update", "captcha"]))
            done, pending = await asyncio.wait([messagecheck, flash], return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                if t is messagecheck:
                    flash.cancel()
                    m = await messagecheck
                else:
                    break
            if m == "none" or m == None:
                break
            if m == "update":
                await message.delete()
                message = None
            else:
                if player.Strife == None:
                    embed = discord.Embed(title=f"{config.sburb} Moving...", description = embed.description, color=embed.color)
                    embed.set_footer(text=embed.footer.text)
                    await message.edit(embed=embed)
                    if m == None:
                        await message.edit(content=f"Timed out.")
                        break
                    else:
                        player.move(m)
                    if player.Room.enemycheck(player) == True:
                        await message.delete()
                        message = None
                        await Explore.strife(Explore, ctx)
                else:
                    await message.edit(content="You cannot move while you are strifing!", embed=None)
                    await asyncio.sleep(3)
        if message != None:
            await message.delete()

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="captcha")
    async def captcha(self, ctx, *target):
        name = " ".join(target)
        player = Player(ctx.author)
        room = player.Room
        n = room.namecheck(name)
        if n in room.items:
            inst = alchemy.Instance(n)
            if inst.Item.size <= 25:
                player.captchalogue(n)
                room.items.remove(n)
                message = await ctx.send(f"Captchalogued {name.upper()}! View it in your `>sylladex`!")
                await asyncio.sleep(3)
                await message.delete()
            else:
                message = await ctx.send(f"{inst.Item.calledby} is too large to CAPTCHAlogue! You may still INTERACT with it using `>interact`.")
                await asyncio.sleep(3)
                await message.delete()
        else:
            message = await ctx.send(f"`{name}` is not an item in the room!")
            await asyncio.sleep(3)
            await message.delete()
        await self.explore(ctx)

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="captchalogue")
    async def captchalogue(self, ctx, *target):
        await self.captcha(ctx, target)

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="interact")
    async def interact(self, ctx, *target):
        name = " ".join(target)
        player = Player(ctx.author)
        room = player.Room
        n = room.playercheck(name)
        if n != False:
            t = Player(n)
            player.follow(t)
            if player.following != None:
                await ctx.send(f"Now following {t.name}!")
                print(f"player following {player.following}. followers: {t.playerfollowers}")
            else:
                await ctx.send(f"Stopped following {t.name}!")
            await asyncio.sleep(3)
        else:
            n = room.npccheck(name)
            if n != False:
                npc = npcs.Npc(n)
                text = await npc.interact(ctx)
                await ctx.send(text)
                await asyncio.sleep(3)
            else:
                n = room.roomcheck(name)
                if n != False:
                    inst = alchemy.Instance(n)
                    text = await inst.activate(ctx, room=True)
                    await ctx.send(text)
                    await asyncio.sleep(3)
                else:
                    n = player.itemcheck(name)
                    if n != False:
                        inst = alchemy.Instance(n)
                        text = await inst.activate(ctx)
                        await ctx.send(text)
                        await asyncio.sleep(3)
                    else:
                        await ctx.send(f"{player.name.capitalize()} looks around, but there's no {name} for {player.them} to interact with in the room.")
        await self.explore(ctx)

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="encounter")
    async def encounter(self, ctx):
        enemies = []
        author = ctx.author
        player = Player(ctx.author)
        message = None
        while True:
            text = f"Your power: {player.power}\nEnemies to search for:\n"
            desc = ""
            for i in range(4):
                desc += f"{i+1}."
                try:
                    desc += f" `{enemies[i]['name']}` POWER: {enemies[i]['power']}"
                except IndexError:
                    pass
                desc += "\n"
            embed = discord.Embed(description=desc, color=config.sburbblue)
            embed.set_footer(text="React with a number to choose the number of enemies to add. React with ✅ to start the strife or react with ◀ to go back.")
            if message == None:
                message = await ctx.send(content=text, embed=embed)
            else:
                await message.edit(content=text, embed=embed)
            r = await util.reactioncheck(message, author, ["✅", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "◀"])
            if r == None or r.emoji == "◀":
                break
            elif r.emoji == "✅":
                if len(enemies) != 0:
                    await message.delete()
                    message = None
                    players = [player]
                    await Explore.startfight(self, ctx, enemies, players, Map=player.Map)
                    break
                else:
                    await message.edit(content=f"**Choose one or more enemies before fighting!**")
                    await asyncio.sleep(3)
            else:
                if r.emoji == "1️⃣": enemyindex = 1
                elif r.emoji == "2️⃣": enemyindex = 2
                elif r.emoji == "3️⃣": enemyindex = 3
                elif r.emoji == "4️⃣": enemyindex = 4
                desc = ""
                for enemy in config.enemies:
                    desc += f"`{enemy}` POWER: {npcs.npcs[enemy]['stats']['POWER']}\n"
                embed = discord.Embed(description=desc, color=config.sburbblue)
                await message.edit(content="Type the name of the enemy type you would like to add.", embed=embed)
                m = await util.messagecheck(message, author, config.enemies)
                t = m
                power = npcs.npcs[t]['stats']["POWER"]
                desc = ""
                for i, grist in enumerate(config.gristcategories[player.gristcategory]):
                    desc += f"`{grist}` **{t}**: POWER: {power*(i+1)}\n"
                embed = discord.Embed(description=desc, color=config.sburbblue)
                await message.edit(content=f"What tier of {t} would you like to fight?", embed=embed)
                m = await util.messagecheck(message, author, config.gristcategories[player.gristcategory].copy())
                tier = config.gristcategories[player.gristcategory].index(m) + 1
                name = f"{m.capitalize()} {t.capitalize()}"
                power = power * tier
                d = {"tier": tier, "type": t, "name": name, "power": power}
                for i in range(enemyindex):
                    if len(enemies) < 4:
                        enemies.append(d)
        if message != None:
            await message.delete()

    @staticmethod
    def clientserverdepth(player, clientserver, depth):
        r = None
        for i in range(depth):
            if clientserver == "client":
                player = player.Client
            else:
                player = player.Server
            if player == None:
                return None
        return player

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="enter")
    async def enter(self, ctx):
        player = Player(ctx.author)
        landowner = Player(player.Overmap.player)
        message = None
        gate = None
        gates = { # left: housegate right: landgate
            "0": [landowner, landowner],
            "1": [landowner, landowner],
            "2": [landowner.Client, landowner.Server],
            "3": [landowner, landowner],
            "4": [self.clientserverdepth(landowner, "client", 2), self.clientserverdepth(landowner, "server", 2)],
            "5": [landowner, landowner],
            "6": [self.clientserverdepth(landowner, "client", 3), self.clientserverdepth(landowner, "server", 3)],
            "7": [landowner, landowner] # not implemented, second gate leads to denizen
            }
        if player.entered != True:
            message = await ctx.send("You need to be ENTERED to enter a gate!")
            await asyncio.sleep(3)
        elif player.Map.map[player.pos[1]][player.pos[0]] in gates:
            gate = player.Map.map[player.pos[1]][player.pos[0]]
        elif player.Overmap.getmap(player.opos[0], player.opos[1]).name == player.Overmap.housemap and player.Overmap.houseentered != []:
            text = "Which gate would you like to enter?\n"
            for g in player.Overmap.houseentered:
                text += f"`{g}` "
            message = await ctx.send(text)
            m = await util.messagecheck(message, ctx.author, player.Overmap.houseentered)
            await message.delete()
            message = None
            if m != None and m != "none":
                gate = m
        elif player.Overmap.getmap(player.opos[0], player.opos[1]).overmaptile in gates:
            gate = player.Overmap.getmap(player.opos[0], player.opos[1]).overmaptile
        else:
            message = await ctx.send("You need to be standing on a GATE to enter it!")
            await asyncio.sleep(3)
        if gate != None:
            if gate == "0": # you're going through a return gate
                newmap = player.Overmap.getmap(name=player.Overmap.housemap)
                player.opos[0] = newmap.x
                player.opos[1] = newmap.y
                validspawn = random.choice(newmap.findtile("1"))
                player.pos[0] = validspawn[0]
                player.pos[1] = validspawn[1]
                message = await ctx.send("You enter the gate...")
                await asyncio.sleep(3)
            elif player.Overmap.getmap(player.opos[0], player.opos[1]).name == player.Overmap.housemap: # if you're going through a house gate
                destination = gates[gate][0]
                if destination != None and destination.entered == True:
                    if gate not in player.Overmap.houseentered:
                        player.Overmap.houseentered.append(gate)
                    if gate not in destination.Land.landentered:
                        destination.Land.landentered.append(gate)
                    player.overmap = destination.Land.name
                    newmap = destination.Land.getmap(name=destination.Land.gates[gate])
                    player.opos[0] = newmap.x
                    player.opos[1] = newmap.y
                    validspawn = random.choice(newmap.findtile("-"))
                    player.pos[0] = validspawn[0]
                    player.pos[1] = validspawn[1]
                    message = await ctx.send("You enter the gate...")
                    await asyncio.sleep(3)
                else:
                    message = await ctx.send("You can't enter the gate because its corresponding player has not entered yet!")
                    await asyncio.sleep(3)
            else: # you're going through a land gate
                destination = gates[gate][1]
                if destination != None and destination.entered == True:
                    if gate not in player.Overmap.landentered:
                        player.Overmap.landentered.append(gate)
                    if gate not in destination.Land.houseentered:
                        destination.Land.houseentered.append(gate)
                    player.overmap = destination.Land.name
                    newmap = destination.Land.getmap(name=destination.Land.housemap)
                    player.opos[0] = newmap.x
                    player.opos[1] = newmap.y
                    validspawn = random.choice(newmap.findtile(gate))
                    player.pos[0] = validspawn[0]
                    player.pos[1] = validspawn[1]
                    message = await ctx.send("You enter the gate...")
                    await asyncio.sleep(3)
                else:
                    message = await ctx.send("You can't enter the gate because its corresponding player has not entered yet!")
                    await asyncio.sleep(3)
        if message != None:
            await message.delete()
        await Explore.explore(Explore, ctx)

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="strife")
    async def strife(self, ctx): # fight every enemy in the room
        player = Player(ctx.author)
        if player.Room.strife != None and player.Room.strife != "":
            s = strifes[player.Room.strife]
            p = PlayerBattler(s, player)
            await s.initmessages()
            await ctx.send("You join a strife in combat somewhere! Head to that channel if you're not already in it!")
        elif player.Room.npcs != []:
            battlers = []
            for name in player.Room.npcs:
                npc = npcs.Npc(name=name)
                battlers.append(npc)
            await Explore.startfight(Explore, ctx, battlers, [player], Room=player.Room)
            await Explore.explore(Explore, ctx)
        else:
            message = await ctx.send("There are no NPCs to strife with here!")
            await asyncio.sleep(3)
            await message.delete()
            await Explore.explore(Explore, ctx)

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="abscond")
    async def abscond(self, ctx):
        player = Player(ctx.author)
        message = None
        if player.Strife != None:
            playerbat = player.Strife.battlers[player.name]
            if playerbat.actions > 0:
                highestsav = 0
                for name in player.Strife.battlers:
                    bat = player.Strife.battlers[name]
                    if bat.team != player.team:
                        if bat.getstat("SAV") > highestsav:
                            highestsav = bat.getstat("SAV")
                playerbat.actions -= 1
                chance = (playerbat.getstat("SAV") / highestsav) / 2
                chance += .2
                if random.random() < chance:
                    s = player.Strife
                    player.Strife.logmessages.append(f"**{player.name} absconds!!**")
                    await playerbat.leavecombat()
                    await s.initmessages()
                else:
                    message = await ctx.send("Can't abscond, bro!!")
                    await asyncio.sleep(3)
            else:
                message = await ctx.send("You can't abscond if you have no actions remaining!")
                await asyncio.sleep(3)
        else:
            message = await ctx.send("You can't abscond if you're not in a strife!")
            await asyncio.sleep(3)
        if message != None:
            await message.delete()

    async def startfight(self, ctx, battlers, players, Room=None, Map=None): #battlers as list of dicts containing "type" and "tier", players as a list of player objects
        s = Strife("", Room)
        for player in players:
            p = PlayerBattler(s, player)
        for battler in battlers:
            if type(battler) == dict:
                enemyNpc = npcs.Npc(type=battler["type"], tier=battler["tier"], map=Map)
            else:
                enemyNpc = battler
            b = EnemyBattler(s, enemyNpc)
        await s.initmessages(ctx)
        s.newturn()
        await s.updatemessages()
        await Explore.strifewindow(self, ctx, s)

    async def strifewindow(self, ctx, Strife): #display strife info and allow combat to happen
        while True:
            next = Strife.nextbattler
            valid = True
            while type(next) != PlayerBattler:
                await Strife.aiturn()
                await Strife.updatemessages()
                if Strife.valid == False:
                    break
                next = Strife.nextbattler
            if Strife.valid == False:
                await Strife.endbattle()
                break
            if Strife.turnmessage == None:
                Strife.turnmessage = await ctx.send(f"It is `{next.name}`'s turn next! What will {next.Player.they} do? `>skills` to view skills.")
            else:
                await Strife.turnmessage.edit(content=f"It is `{next.name}`'s turn next! What will {next.Player.they} do? `>skills` to view skills.")
            skill, targets = await util.skillcheck(Strife.turnmessage.channel, next.Player)
            if skill != None and skill != False:
                for i, t in enumerate(targets):
                    if t not in Strife.battlers:
                        try:
                            fighti = int(t)
                            try:
                                targets[i] = Strife.order[fighti]
                            except IndexError:
                                valid = t
                        except (TypeError, ValueError):
                            valid = t
                if type(valid) == bool:
                    s = skills.skills[skill]
                    e = s.usecheck(Strife, next)
                    if type(e) != str:
                        await Strife.turnmessage.edit(content=f"{config.sburb} LOADING...")
                        await s(Strife, next.name, targets)
                        await Strife.updatelog()
                        await Strife.updatemessages()
                    else:
                        er = await ctx.send(content=f"{next.name} cannot use `{skill}`! Reason: {e}")
                        await asyncio.sleep(3)
                        await er.delete()
                else:
                    mes = await ctx.send(f"`{valid}` is not in the battle!")
                    await asyncio.sleep(3)
                    await mes.delete()
                if Strife.valid == False:
                    await Strife.endbattle()
                    break

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="spread")
    async def spread(self, ctx):
        author = ctx.author
        player = Player(ctx.author)
        message = None
        while True:
            desc = f"Current stats:\n"
            for stat in player.levelupstats:
                desc += f"`{stat}:` {player.levelupstats[stat]}\n"
            text = f"**Available points: {player.pointsavailable}.**\nType a stat to view more info on it or level it up. Unassigned stat points will be automatically assigned according to your existing stat ratios.\nType `none` to go back."
            embed = discord.Embed(description=desc, color=player.color)
            if message == None:
                message = await ctx.send(content=text, embed=embed)
            else:
                await message.edit(content=text, embed=embed)
            s = list(map(lambda x: x.lower(), list(player.levelupstats.keys())))
            m = await util.messagecheck(message, author, list(player.levelupstats.keys())+s+["none"])
            if m != None:
                stat = m.upper()
            else:
                break
            if stat == "NONE":
                break
            valid = False
            while valid == False:
                statinfo = {
                    "SPK": "SPUNK - Increases the damage you deal. Associated with TIME.",
                    "VIG": "VIGOR - Increases your maximum HP. Associated with HEART.",
                    "TAC": "TACT - Increases your maximum VIM and SECONDARY VIALS, as well as regeneration of VIM, SECONDARY and ASPECT vials. These vials are associated with BLOOD, MIND and VOID respectively. This also increases your HOPE and RAGE meters' maximum values.",
                    "LUK": "LUCK - Rigs the odds of dice rolls in your favor. Dice are rolled, for example, whenever you deal damage with a weapon or attempt to AUTO-PARRY. Associated with LIGHT.",
                    "SAV": "SAVVY - Affects your position in the turn order. A higher SAVVY means you have better odds of AUTO-PARRYING attacks. Associated with BREATH.",
                    "MET": "METTLE - Decreases your damage taken. Associated with TIME."
                    }
                c = statinfo[stat] + "\n\n"
                c += f"**How much should {stat} be leveled up by? Available points: {player.pointsavailable}**"
                await message.edit(content=c)
                m = await util.messagecheck(message, author, None)
                if m == "none" or m == "0":
                    break
                try:
                    amount = int(m)
                    if amount <= player.pointsavailable:
                        if player.levelupstats[stat] + amount >= 0:
                            player.levelupstats[stat] += amount
                            valid = True
                        else:
                            await message.edit(content=f"You do not have enough {stat} to level it up by {amount}.")
                            await asyncio.sleep(5)
                    else:
                        await message.edit(content=f"You do not have enough points to level up {stat} by {amount}. Available points: {player.pointsavailable}")
                        await asyncio.sleep(5)
                except ValueError:
                    await message.edit(content=f"`{m}` is not a valid number. Try again.")
                    await asyncio.sleep(5)
            player.save()
        await message.delete()
        await self.explore(ctx)

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="skills")
    async def showskills(self, ctx):
        desc = ""
        player = Player(ctx.author)
        message = None
        while True:
            desc = ""
            for skill in player.skills:
                skillobj = skills.skills[skill]
                desc += f"`{skill}` - {skillobj.description}\n"
            embed = discord.Embed(title=f"{player.name} Skills", description=desc, color = player.color)
            embed.set_footer(text="Type a skill name to get a more detailed description of it. Type `none` to go back.")
            if message == None:
                message = await ctx.send(embed=embed)
            else:
                await message.edit(embed=embed)
            m = await util.messagecheck(message, ctx.author, player.skills+["none"])
            if m == "none" or m == None: break
            skillobj = skills.skills[m]
            desc = skillobj.describe()
            embed = discord.Embed(title=f"{m}", description=desc, color=player.color)
            embed.set_footer(text="Type `back` to return to skills.")
            await message.edit(embed=embed)
            await util.messagecheck(message, ctx.author, ["back"])
        if message != None:
            await message.delete()

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="passives")
    async def showpassives(self, ctx):
        desc = ""
        player = Player(ctx.author)
        desc = ""
        for passive in player.passives:
            passiveobj = skills.passives[passive]
            desc += f"`{passive}` - {passiveobj.description}\n"
        embed = discord.Embed(title=f"{player.name} Passives", description=desc, color=player.color)
        message = await ctx.send(embed=embed)
        await util.reactioncheck(message, ctx.author, ["◀"])
        await message.delete()

explorecommands = {}

class ExploreCommand():
    def __init__(self, name, command):
        self.name = name
        explorecommands[name] = self
        self.command = command

    async def __call__(*args, **kwargs):
        await self.command(args, kwargs)

class Player():
    def __init__(self, author):
        if type(author) != str:
            id = str(author.id)
        else:
            id = author
        if id not in util.players: util.players[id] = {}
        self.__dict__["id"] = id
        if self.opos == None and self.overmap != None:
            print("initializing opos")
            self.opos = [0, 0] # pos in x, y
            house = self.Overmap.getmap(name=self.Overmap.housemap)
            self.opos[0] = house.x
            self.opos[1] = house.y
            print(f"setting pos to housemap position at {house.x}, {house.y}")
        if self.pos == None and self.overmap != None:
            print("initializing pos")
            self.pos = [0, 0]
            self.pos = random.choice(self.Overmap.getmap(name=self.Overmap.housemap).validspawns()) # pos in x, y
        if "team" not in util.players[id]:
            self.team = "PLAYERS"
        if "levelupstats" not in util.players[id]:
            self.levelupstats = {
                "SPK": 0,
                "VIG": 0,
                "TAC": 0,
                "LUK": 0,
                "SAV": 0,
                "MET": 0
            }
        if "rung" not in util.players[id]:
            self.rung = 1
        if "sylladex" not in util.players[id]:
            self.sylladex = [{}, {}, {}, {}] #list of dicts {} which represent cards
        if "portfolio" not in util.players[id]:
            self.portfolio = [{}, {}] # unassigned specibi.
        if "cache" not in util.players[id]:
            self.cache = {}
            for grist in config.grists:
                self.cache[grist] = 0
            self.cache["build"] = 100
        if "atheneum" not in util.players[id]:
            self.atheneum = []
        if "leeching" not in util.players[id]:
            self.leeching = []
        if "freepassives" not in util.players[id]:
            self.freepassives = []
        if "entered" not in util.players[id]:
            self.entered = False
        if "followers" not in util.players[id]:
            self.followers = []
        if "playerfollowers" not in util.players[id]:
            self.playerfollowers = []
        if "follow" not in util.players[id]:
            self.follow = None
        # todo: remove this line and have worlds and stuff

    def __setattr__(self, attr, value):
        util.players[self.__dict__["id"]][attr] = value

    def __getattr__(self, attr):
        try:
            return util.players[self.__dict__["id"]][attr]
        except KeyError:
            return None

    def captchalogue(self, name): # adds a captchalogue card of the item to your sylladex
        for i, card in enumerate(self.sylladex):
            if card == {}: # blank card
                self.sylladex[i]["item"] = name
                if name not in self.atheneum:
                    self.atheneum.append(name)
                break
        else:
            rng = random.randint(0, len(self.sylladex)-1) # temp randomness
            toeject = self.sylladex[rng]["item"]
            self.ejectinstance(toeject)
            self.captchalogue(name)

    def ejectinstance(self, instname): # ejects the instance out of your sylladex and into the room
        for i, card in enumerate(self.sylladex):
            if card != {}:
                if card["item"] == instname:
                    self.sylladex[i] = {}
                    self.Room.addinstance(instname)
                    break

    def removeinstance(self, instname): # removes the named instance from its card
        for i, card in enumerate(self.sylladex):
            if card != {}:
                if card["item"] == instname:
                    self.sylladex[i] = {}
                    break

    def removecard(self, instname): # removes the WHOLE card containing the instance instname
        for i, card in enumerate(self.sylladex.copy()):
            if card != {}:
                if card["item"] == instname:
                    return self.sylladex.pop(i)

    def addcard(self): # adds a new card to your sylladex
        self.sylladex.append({})

    def movetostrifedeck(self, name): # moves an item from your captchalogue deck to your strife deck
        inst = alchemy.Instance(name=name)
        for i, card in enumerate(self.portfolio):
            if card != {} and card["kind"] in inst.Item.kinds:
                self.portfolio[i]["items"].append(name)
                break
        for i, card in enumerate(self.sylladex):
            if card != {} and card["item"] == name:
                self.sylladex[i] = {}
                break

    def movefromstrifedeck(self, name): # moves an item out of your strife deck
        inst = alchemy.Instance(name=name)
        for i, specibi in enumerate(self.portfolio):
            if specibi != {} and inst.name in specibi["items"]:
                self.portfolio[i]["items"].remove(inst.name)
                self.captchalogue(inst.name)
                break

    @property
    def embedsylladex(self):
        text = ""
        for i, d in enumerate(self.sylladex):
            if d == {}:
                text += f"`{i}.` EMPTY CARD\n"
            else:
                inst = alchemy.Instance(name=d["item"])
                text += f"`{i}.` {inst.calledby}\n"
        embed = discord.Embed(title=f"{self.name}'s Captchalogue Deck", description=text, color=self.color)
        return embed

    @property
    def pointsavailable(self):
        points = 0
        for stat in self.levelupstats:
            points += self.levelupstats[stat]
        return self.rung + 9 - points

    @property
    def totalpoints(self):
        return self.rung + 9

    @property
    def power(self):
        power = 9
        power += self.rung
        power += self.equippower
        # todo // add equipment
        return power

    @property
    def equippower(self): #power bonus from equipped items
        bonus = 0
        if self.wielding != None:
            i = alchemy.Instance(self.wielding)
            bonus += i.Item.power
        return bonus

    @property
    def stats(self):
        stats = ["SPK", "VIG", "TAC", "LUK", "SAV", "MET"]
        d = {"POWER": self.power}
        for stat in stats:
            d[stat] = self.getstat(stat)
        return d

    @property
    def skills(self):
        s = skills.defaults.copy()
        for skill in config.aspectskills[self.aspect]:
            if self.rung >= config.aspectskills[self.aspect][skill]:
                s.append(skill)
        for skill in config.classskills[self.gameclass][self.aspect]:
            if self.rung >= config.classskills[self.gameclass][self.aspect][skill]:
                s.append(skill)
        return s

    @property
    def passives(self):
        out = []
        for passive in self.freepassives:
            out.append(passive)
        for passive in config.aspectpassives[self.aspect]:
            if self.rung >= config.aspectpassives[self.aspect][passive]:
                out.append(passive)
        for passive in config.classpassives[self.gameclass][self.aspect]:
            if self.rung >= config.classpassives[self.gameclass][self.aspect][passive]:
                out.append(passive)
        return out

    def getstat(self, stat):
        if stat != "POWER":
            value = 1
            value += self.levelupstats[stat]
            if self.pointsavailable > 0:
                total = 0
                for stat in self.levelupstats:
                    total += self.levelupstats[stat]
                if total != 0:
                    value += int(self.pointsavailable * (value / total)) # try to put extra points into the correct stats
                else:
                    value += int(self.pointsavailable / 6)
            value += (value / self.totalpoints) * self.equippower
            return int(value)
        else:
            return self.power

    @property
    def dicemin(self):
        if self.wielding != None:
            inst = alchemy.Instance(self.wielding)
            return int(inst.Item.dicemin * self.power)
        else:
            return int(0.3 * self.power)

    @property
    def dicemax(self):
        if self.wielding != None:
            inst = alchemy.Instance(self.wielding)
            return int(inst.Item.dicemax * self.power)
        else:
            return int(1.0 * self.power)

    @property
    def cachelimit(self):
        if self.rung >= 1025:
            return 0
        else:
            power = max(self.rung / 100, 1)
            mult = 2 ** power
            return int(mult * self.rung) + 100

    def addgrist(self, type, amount):
        old = self.cache[type]
        self.cache[type] += amount
        if self.cache[type] > self.cachelimit and self.cachelimit != 0:
            self.cache[type] = self.cachelimit
        self.cache[type] = int(self.cache[type])
        return self.cache[type] - old # return change in grist

    @property
    def Server(self): # returns the player object server
        if self.server != None:
            s = Player(self.server)
            return s
        else:
            return None

    @property
    def Client(self): # returns the player object server
        if self.client != None:
            s = Player(self.client)
            return s
        else:
            return None

    @property
    def Overmap(self):
        overmap = maps.Overmap(self.session, self.overmap, self)
        return overmap

    @property
    def Land(self):
        land = maps.Overmap(self.session, self.land, self)
        return land

    @property
    def Map(self):
        map = self.Overmap.getmap(self.opos[0], self.opos[1])
        return map

    @property
    def Room(self):
        return maps.Room(self.Map, self.pos[0], self.pos[1])

    @property
    def Strife(self):
        if self.strife != None and self.strife in strifes:
            return strifes[self.strife]
        else:
            return None

    @property
    def kinds(self): # returns list of specibi kinds
        spec = []
        for card in self.portfolio:
            if card != {}:
                if card["kind"] not in spec:
                    spec.append(card["kind"])
        return spec

    def itemcheck(self, name): # returns the true name of an instance in your sylladex
        newname = False
        for card in self.sylladex:
            if card != {}:
                instname = card["item"]
                inst = alchemy.Instance(name=instname)
                if inst.Item.calledby == name.upper():
                    newname = instname
        try:
            num = int(name)
            newname = self.sylladex[num]["item"]
        except (ValueError, KeyError):
            pass
        return newname

    def specibuscheck(self, kind): # returns the index of a specibus given a kind
        for i, card in enumerate(self.portfolio):
            if card != {}:
                if card["kind"] == kind:
                    return i
        try:
            num = int(kind)
            try:
                self.portfolio[num]
                return num
            except IndexError:
                return None
        except ValueError:
            return None

    def strifedeckcheck(self, name, i): # returns the true name of an instance in a strife deck
        newname = False
        for n in self.portfolio[i]["items"]:
            item = alchemy.Instance(name=n)
            if item.Item.calledby == name.upper():
                newname = n
        try:
            num = int(name)
            newname = self.portfolio[i]["items"][num]
        except (ValueError, KeyError):
            pass
        return newname

    def allocate(self, kind): # allocates a specibus to the chosen kind
        for i, card in enumerate(self.portfolio):
            if card == {}:
                self.portfolio[i] = {"kind": kind, "items": []}
                break

    def rungsfrompower(self, power): # gives a number of rungs based on the enemy power
        rungs = 0
        bonus = int(math.log(power, 10))
        if power > self.power * 4:
            rungs += 4 + bonus
        if power > self.power * 3:
            rungs += 3 + bonus
        if power > self.power * 2:
            rungs += 2 + bonus
        if power > self.power * 1.5:
            rungs += 1 + bonus
        if power > self.power * 0.8:
            rungs += 1 + bonus
        rungs += 1 + bonus
        self.ascendrungs(rungs)

    def ascendrungs(self, rungs):
        for rung in range(self.rung, self.rung+rungs):
            leeching = self.leeching.copy() # so that the grist is still split even if it gets capped
            for grist in leeching:
                value = int((rung / (config.grists[grist]['tier'] + 1)) / len(leeching))
                if self.addgrist(grist, value) < value:
                    self.leeching.remove(grist)
            for grist in util.sessions[self.session]["gutter"]:
                value = int(rung / (config.grists[grist]['tier'] + 1))
                if value > util.sessions[self.session]["gutter"][grist]:
                    value = util.sessions[self.session]["gutter"][grist]
                util.sessions[self.session]["gutter"][grist] -= self.addgrist(grist, value)
        for grist in util.sessions[self.session]["gutter"].copy():
            if util.sessions[self.session]["gutter"][grist] == 0:
                util.sessions[self.session]["gutter"].pop(grist)
        self.rung += rungs

    @staticmethod
    def save(): #saves players
        util.writejson(util.players, "players")

    @property
    def color(self):
        return config.aspectcolors[self.aspect]

    def mapchar(self, x=0, y=0): # get the character on the map relative to self
        try:
            return self.Map.map[self.pos[1]+y][self.pos[0]+x] # map positions are y, x so this reverses it
        except IndexError:
            return "#"

    def omapchar(self, x=0, y=0): # get the character on the overmap relative to self
        newx = None
        newy = None
        if self.opos[0] + x >= 0:
            if self.opos[0] + x < len(self.Overmap.map[0]):
                newx = self.opos[0] + x
            else:
                newx = 0
        else:
            newx = len(self.Overmap.map[0]) - 1
        if self.opos[1] + y >= 0:
            if self.opos[1] + y < len(self.Overmap.map):
                newy = self.opos[1] + y
            else:
                newy = 0
        return self.Overmap.map[newy][newx] # map positions are y, x so this reverses it

    def gotoroom(self, room):
        print(f"in gotoroom of {self.name}")
        self.pos[0] = room.x
        self.pos[1] = room.y
        self.map = room.Map.name
        self.overmap = room.Overmap.name
        self.session = room.Overmap.session
        self.followersfollow()

    def followersfollow(self):
        for f in self.followers:
            follower = npcs.Npc(name=f)
            follower.gotoroom(self.Room)
        print(f"in followersfollow {self.playerfollowers}")
        for f in self.playerfollowers:
            p = Player(f)
            print(p.name)
            p.gotoroom(self.Room)

    def follow(self, target):
        print(f"self following {self.following} target name {target.name}")
        if self.following == target.name:
            self.unfollow()
        else:
            self.unfollow()
            print(f"target followers {target.playerfollowers}")
            if self.id not in target.playerfollowers:
                target.playerfollowers.append(self.id)
                print(f"appended {target.playerfollowers}")
            self.following = target.name

    def unfollow(self):
        if self.following != None: # unfollow current following
            p = Player(self.following)
            if self.id in p.playerfollowers:
                p.playerfollowers.remove(self.id)
            self.following = None

    def changepos(self, x, y): # move the character in the x or y direction
        if self.pos[0] + x >= 0 and self.pos[0] + x < len(self.Map.map[0]):
            self.pos[0] += x
        if self.pos[1] + y >= 0 and self.pos[1] + y < len(self.Map.map):
            self.pos[1] += y
        self.followersfollow()

    def changeopos(self, x, y): # move the character in the x or y direction
        if self.opos[0] + x >= 0:
            if self.opos[0] + x < len(self.Overmap.map[0]):
                self.opos[0] += x
            else:
                self.opos[0] = 0
        else:
            self.opos[0] = len(self.Overmap.map[0]) - 1
        if self.opos[1] + y >= 0:
            if self.opos[1] + y < len(self.Overmap.map):
                self.opos[1] += y
            else:
                self.opos[1] = 0
        else:
            self.opos[1] = len(self.Overmap.map) - 1

    def omove(self, direction):
        self.unfollow()
        if direction == "w":
            self.changeopos(0, -1)
            while self.omapchar(0, 0) == "~":
                self.changeopos(0, -1)
        elif direction == "s":
            self.changeopos(0, 1)
            while self.omapchar(0, 0) == "~":
                self.changeopos(0, 1)
        elif direction == "a":
            self.changeopos(-1, 0)
            while self.omapchar(0, 0) == "~":
                self.changeopos(-1, 0)
        elif direction == "d":
            self.changeopos(1, 0)
            while self.omapchar(0, 0) == "~":
                self.changeopos(1, 0)

    def move(self, direction):
        if direction == "w":
            while self.mapchar(0, -1) in config.stairs:
                self.changepos(0, -1)
            if self.mapchar(0, 0) in config.stairs and (self.mapchar(0, -1) not in config.impassible or self.mapchar(0, -1) in config.stairs):
                self.changepos(0, -1)
        elif direction == "s":
            while self.mapchar(0, 1) in config.stairs:
                self.changepos(0, 1)
            if self.mapchar(0, 0) in config.stairs and (self.mapchar(0, 1) not in config.impassible or self.mapchar(0, 1) in config.stairs):
                self.changepos(0, 1)
        elif direction == "a":
            if self.mapchar(-1, 0) not in config.impassible:
                if self.mapchar(-1, 0) in config.ramps:
                    while self.mapchar(-1, 0) in ["\\", "X"] and self.mapchar(-1, -1) not in config.impassible:
                        self.changepos(-1, 0)
                        self.changepos(0, -1)
                    if self.mapchar(-1, 0) not in config.impassible:
                        self.changepos(-1, 0)
                else:
                    self.changepos(-1, 0)
                    while self.mapchar(0, 0) in config.doors and self.mapchar(-1, 0) not in config.impassible:
                        self.changepos(-1, 0)
        elif direction == "d":
            if self.mapchar(1, 0) not in config.impassible:
                if self.mapchar(1, 0) in config.ramps:
                    while self.mapchar(1, 0) in ["/", "X"] and self.mapchar(1, -1) not in config.impassible:
                        self.changepos(1, 0)
                        self.changepos(0, -1)
                    if self.mapchar(1, 0) not in config.impassible:
                        self.changepos(1, 0)
                else:
                    self.changepos(1, 0)
                    while self.mapchar(0, 0) in config.doors and self.mapchar(1, 0) not in config.impassible:
                        self.changepos(1, 0)
        self.fall()

    def fall(self):
        while self.mapchar(0, 1) not in config.impassible + config.infallible:
            if self.mapchar(0, 1) in config.ramps:
                if self.mapchar(0, 1) == "\\": #fall down and to the right
                    while self.mapchar(0, 1) == "\\" and self.mapchar(1, 1) not in config.impassible:
                        self.changepos(1, 0)
                        self.changepos(0, 1)
                elif self.mapchar(0, 1) == "/": #fall down and to the left
                    while self.mapchar(0, 1) == "/" and self.mapchar(-1, 1) not in config.impassible:
                        self.changepos(-1, 0)
                        self.changepos(0, 1)
            else:
                self.changepos(0, 1)

class Strife(): #
    def __init__(self, name, Room=None):
        self.name = name
        if Room != None:
            Room.strife = self.name
            self.Room = Room
        else:
            self.Room = None
        self.battlers = {}
        self.turn = 0
        self.messages = []
        self.logmessage = None # the message that appears above all of the turn order messages
        self.logmessages = []
        self.turnmessage = None # the message that appears below all of the turn order messages
        self.order = []
        strifes[self.name] = self

    async def initmessages(self, ctx=None):
        if ctx != None:
            self.ctx = ctx
        if self.logmessage != None:
            await self.logmessage.delete()
        message = await self.ctx.send("**STRIFE LOG**\n...")
        self.logmessage = message
        for message in self.messages.copy():
            self.messages.remove(message)
            await message.delete()
        for battler in self.battlers:
            b = self.battlers[battler]
            embed = b.embedbattle()
            message = await self.ctx.send(embed=embed)
            self.messages.append(message)
        if self.turnmessage != None:
            tmessagecontent = self.turnmessage.content
            await self.turnmessage.delete()
            self.turnmessage = await self.ctx.send(tmessagecontent)
        await self.setturnorder()
        await self.updatelog()

    async def setturnorder(self):
        self.order = list(self.battlers.keys())
        sortfunc = lambda x: self.battlers[x].getstat("SAV")
        self.order.sort(reverse=True, key=sortfunc)
        await self.updatemessages()

    async def updatemessages(self):
        for name in self.order:#update messages
            b = self.battlers[name]
            await b.updatemessage()

    async def updatelog(self):
        text = "**STRIFE LOG**\n"
        while len(self.logmessages) > 20:
            self.logmessages.pop(0)
        if len(self.logmessages) != 0:
            for message in self.logmessages:
                if "**" not in message:
                    text += "`" + message + "`\n"
                else:
                    text += message + "\n"
        else:
            text += "..."
        await self.logmessage.edit(content=text)

    @property
    def nextbattler(self):
        for name in self.order:
            if self.battlers[name].actions <= 0:
                pass
            else:
                return self.battlers[name]
        else:
            self.newturn()

    @property
    def valid(self):
        teams = []
        for battler in self.battlers:
            b = self.battlers[battler]
            if b.team not in teams:
                teams.append(b.team)
        if len(teams) > 1:
            return True
        else:
            return False

    def newturn(self):
        self.turn += 1
        for battler in self.battlers:
            b = self.battlers[battler]
            b.actions = b.maxactions
            b.trivialactions = b.maxtrivialactions
            b.newturn()
        self.logmessages.append(f"**TURN {self.turn}**")
        if self.turn == 1:
            for battler in self.battlers:
                b = self.battlers[battler]
                passivetext = []
                for passive in b.passives:
                    passiveobj = skills.passives[passive]
                    o = passiveobj.battlestart(b)
                    if o != None and o != "":
                        passivetext.append(o)
                if passivetext != []:
                    passivetext = "\n".join(passivetext)
                    self.logmessages.append(passivetext)

    async def aiturn(self): # cause enemies to do actions
        while type(self.nextbattler) == EnemyBattler and self.valid:
            await self.nextbattler.ai()
        await self.updatemessages()
        await self.updatelog()

    async def endbattle(self):
        self.logmessages.append(f"**THE BATTLE IS OVER!**")
        for b in self.battlers.values():
            if type(b) == PlayerBattler:
                b.Player.strife = None
                if b.Player.rung > b.stats["RUNG"]:
                    self.logmessages.append(f"{b.name} ascended {b.Player.rung - b.stats['RUNG']} rungs on {b.their} ECHELADDER!")
                if len(b.skills) < len(b.Player.skills):
                    text = f"**{b.name} learned new skills: "
                    newskills = list(filter(lambda x: x not in b.skills, b.Player.skills))
                    for skill in newskills:
                        text += f"`{skill}` "
                    text += "**"
                    self.logmessages.append(text)
                if len(b.passives) < len(b.Player.passives):
                    text = f"**{b.name} learned new passives: "
                    newpassives = list(filter(lambda x: x not in b.passives, b.Player.passives))
                    for passive in newpassives:
                        text += f"`{passive}` "
                    text += "**"
                    self.logmessages.append(text)
        await self.updatelog()
        for message in self.messages:
            await message.delete()
        if self.turnmessage != None:
            await self.turnmessage.delete()
        if self.Room != None:
            self.Room.strife = None

class Battler():
    def __init__(self, name, vials, Strife):
        Strife.battlers[name] = self
        Strife.order.append(name)
        self.Strife = Strife
        self.vials = {}
        self.states = {}
        self.cooldowns = {}
        self.healmult = 1
        for vial in vials:
            self.vials[vial] = {}
            self.vials[vial]["maximum"] = int(eval(config.vials[vial]["formula"]))
            if vial == "health" and type(self) == PlayerBattler:
                self.vials[vial]["maximum"] *= 1.5
                self.vials[vial]["maximum"] = int(self.vials[vial]["maximum"])
            self.vials[vial]["value"] = int(self.vials[vial]["maximum"] * config.vials[vial]["initial"])

    def getstat(self, stat, nopassive=False):
        value = self.stats[stat]
        if stat == "LUK":
            value += (self.vials["hope"]["value"] - (self.vials["hope"]["maximum"] // 2)) // 2
        if stat == "SAV" and "horseshitometer" in self.vials:
            value += (self.vials["horseshitometer"]["value"] - (self.vials["horseshitometer"]["maximum"] // 2)) // 2
        if nopassive == False:
            for state in self.states:
                stateobj = stateseffects.states[state]
                inflictor = self.states[state]["inflictor"]
                power = self.states[state]["power"]
                battler = self
                if stat in stateobj.statadds:
                    add = int(eval(stateobj.statadds[stat]) * power)
                    value += add
            for passive in self.passives:
                passiveobj = skills.passives[passive]
                battler = self
                if stat in passiveobj.statadds:
                    add = eval(passiveobj.statadds[stat])
                    value += add
                if stat in passiveobj.statmults:
                    value *= eval(passiveobj.statmults[stat])
                allstats = ["SPK", "TAC", "MET", "LUK", "VIG", "SAV"]
                if "all" in passiveobj.statadds and stat in allstats:
                    add = eval(passiveobj.statadds["all"])
                    value += add
                if "all" in passiveobj.statmults and stat in allstats:
                    value *= eval(passiveobj.statmults["all"])
        return int(value)

    def embedbattle(self):
        desc = f"POWER: {self.getstat('POWER')}\n"
        for vial in self.vials:
            if vial in ["health", "aspect", "vim", "gambit", "mangrit", "horseshitometer", "imagination"] or self.vials[vial]["value"] != int(self.vials[vial]["maximum"] * config.vials[vial]["initial"]):
                desc += f"{self.displayvial(vial)} {vial.upper()} {round(self.vials[vial]['value']/self.vials[vial]['maximum']*100)}%\n"
        desc += f"ACTIONS: **{self.actions}**"
        if self.maxtrivialactions != 0: desc += f" | TRIVIAL ACTIONS: **{self.trivialactions}**"
        desc += "\n"
        if len(self.states) != 0:
            for state in self.states:
                desc += f"`{state}"
                if self.states[state]["duration"] > 0:
                    desc += f" {self.states[state]['duration']}"
                if self.states[state]["power"] != 1: desc += f" ({self.states[state]['power']})"
                desc += "` "
        embed = discord.Embed(title=f"{self.fightindex}. {self.name}", description=desc, color=config.sburbblue)
        return embed

    def displayvial(self, vial):
        self.vialcheck(vial)
        value = self.vials[vial]["value"]
        maximum = self.vials[vial]["maximum"]
        ratio = (value/maximum) - .01
        text = ""
        #start
        if ratio > .9: #full
            text += f"{config.vialemoji[vial]['startfilled']}"
        elif ratio > .8: #half
            text += f"{config.vialemoji[vial]['starthalffilled']}"
        else:
            text += f"<:startempty:817700649432383519>"
        #middle
        for i in range(3):
            if ratio > .7 - (.2 * i):
                text += f"{config.vialemoji[vial]['middlefilled']}"
            elif ratio > .6 - (.2 * i):
                text += f"{config.vialemoji[vial]['middlehalffilled']}"
            else:
                text += "<:middleempty:817700649843163146>"
        #end
        if ratio > .1:
            text += f"{config.vialemoji[vial]['endfilled']}"
        elif ratio > 0:
            text += f"{config.vialemoji[vial]['endhalffilled']}"
        else:
            text += "<:endempty:817700649265266709>"
        return text

    def vialcheck(self, vial):
        if self.vials[vial]["value"] > self.vials[vial]["maximum"]:
            self.vials[vial]["value"] = self.vials[vial]["maximum"]
        if self.vials[vial]["value"] < 0:
            self.vials[vial]["value"] = 0

    async def updatemessage(self):
        if await self.deathcheck() == False:
            message = self.message
            embed = self.embedbattle()
            if message.embeds[0] != embed:
                await message.edit(embed=embed)

    def damage(self, value, nododge = False):
        old = self.vials["health"]["value"]
        value = int(value)
        if value < 0:
            if type(self) == PlayerBattler:
                d = self.roll(1, self.getstat("SAV")*4)
            else:
                d = self.roll(1, self.getstat("SAV")*3, -1) #enemies dodge less
            d *= -1
            bonusevade = 0
            battler = self
            for passive in self.passives:
                passiveobj = skills.passives[passive]
                bonusevade += eval(passiveobj.evadebonus)
            if bonusevade > 0.9:
                bonusevade = 0.9
            if random.random() < bonusevade:
                d -= value
            if nododge == True or d >= value:
                mult = self.receivemult
                value *= mult
                for state in self.states:
                    stateobj = stateseffects.states[state]
                    out = stateobj.ondamage(self)
                    if out != "":
                        self.Strife.logmessages.append(out)
            else:
                if "horseshitometer" in self.vials:
                    self.changevial("horseshitometer", -1 * value // 4)
                return "parry"
        elif value > 0:
            value *= self.healmult
        value = int(value)
        self.changevial("health", value)
        return self.vials["health"]["value"] - old

    def changevial(self, vial, value):
        old = self.vials[vial]["value"]
        self.vials[vial]["value"] += int(value)
        self.vialcheck(vial)
        change = self.vials[vial]["value"] - old
        if vial == "aspect" and "imagination" in self.vials:
            if change < 0:
                self.changevial("imagination", change*-1)
        if vial == "health" and self.vials[vial]["value"] == 0:
            if self.vials["hope"]["value"] > (self.vials["hope"]["maximum"] // 2):
                self.vials[vial]["value"] = 1
                hopechange = self.changevial("hope", value + change)
                hopehpchange = self.changevial("health", hopechange * -1)
                change = change + hopehpchange
                self.Strife.logmessages.append(f"**__{self.name.upper()} DEFIES FATE WITH HOPE!!__**")
        return change

    async def ai(self): # perform ai actions
        while self.actions > 0:
            validskills = self.skills.copy()
            validtargets = list(self.Strife.battlers.values())
            for skill in validskills.copy():
                s = skills.skills[skill]
                invalid = [
                    type(s.usecheck(self.Strife, self)) == str
                ]
                if any(invalid): validskills.remove(skill)
            random.seed()
            skill = random.choice(validskills)
            skill = skills.skills[skill]
            for target in validtargets.copy():
                invalid = [
                    skill.beneficial and target.team != self.team,
                    (not skill.beneficial) and target.team == self.team
                ]
                if any(invalid): validtargets.remove(target)
            random.seed()
            random.shuffle(validtargets)
            targets = []
            for i in range(skill.targets):
                if len(validtargets) != 0:
                    targets.append(validtargets.pop(0).name)
                else:
                    break
            await skill(self.Strife, self.name, targets)

    async def deathcheck(self):
        if self.vials["health"]["value"] <= 0:
            self.Strife.logmessages.append(f"**{self.name} died!**")
            await self.leavecombat()
            if type(self) == EnemyBattler:
                self.Npc.die()
            self.rewardpcs()
            return True
        else:
            return False

    async def leavecombat(self):
        self.Strife.battlers.pop(self.name)
        i = self.Strife.order.index(self.name)
        self.Strife.order.remove(self.name)
        await self.Strife.messages[i].delete()
        self.Strife.messages.pop(i)
        if type(self) == PlayerBattler:
            self.Player.strife = None

    def rewardpcs(self):
        if type(self) == EnemyBattler:
            category = self.Npc.OriginalOvermap.gristcategory
            power = npcs.npcs[self.type]["stats"]["POWER"]
            drops = {"build": power//2}
            for i in range(5):
                if self.tier-1-i < 0: break
                grist = config.gristcategories[category][self.tier-1-i]
                reward = int(power / (i + 1))
                if reward == 0: break
                drops[grist] = reward
            text = ""
            for grist in drops:
                text += f"{config.grists[grist]['emoji']} {drops[grist]} "
            self.Strife.logmessages.append("**"+text+"**")
            for b in self.Strife.battlers.values():
                if type(b) == PlayerBattler:
                    b.Player.rungsfrompower(self.power)
                    for grist in drops:
                        d = drops[grist]
                        given = b.Player.addgrist(grist, drops[grist])
                        if d > given:
                            if grist not in util.sessions[b.Player.session]["gutter"]:
                                util.sessions[b.Player.session]["gutter"][grist] =0
                            util.sessions[b.Player.session]["gutter"][grist] += d-given


    def roll(self, min, max, dicebonus=0):
        final = 0
        worse = False
        min = int(min)
        max = int(max)
        bonusrolls = int(self.lukrolls)
        bonusrolls += dicebonus
        if random.random() < self.lukrolls - bonusrolls:
            bonusrolls += 1
        if bonusrolls < 0:
            worse = True
            bonusrolls *= -1
            final = None
        if max <= min:
            final = min
            return int(final)
        else:
            for i in range(bonusrolls+1):
                random.seed()
                roll = random.randint(min, max)
                if worse == False:
                    if roll > final: final = roll
                else:
                    if final == None: final = roll
                    if roll < final: final = roll
            return int(final)

    def newturn(self):
        out = []
        for vial in self.vials:
            if "regen" in config.vials[vial]:
                self.changevial(vial, eval(config.vials[vial]["regen"]))
            if vial == "aspect" and "imagination" in self.vials:
                self.vials[vial]["value"] += self.vials["imagination"]["value"]//5 # not changevial due to recursion
                self.vialcheck(vial)
        for state in self.states.copy():
            stateobj = stateseffects.states[state]
            o = stateobj.call(self)
            if o != None and o != "":
                out.append(o)
            if state in self.states:
                if self.states[state]["inflicted"] + 1 != self.Strife.turn:
                    self.states[state]["duration"] -= 1
                    if self.states[state]["duration"] == 0:
                        self.states.pop(state)
        for passive in self.passives:
            passiveobj = skills.passives[passive]
            o = passiveobj(self)
            if o != None and o != "":
                out.append(o)
        if out != []:
            self.Strife.logmessages.append("\n".join(out))

    @property
    def lukrolls(self): # number of extra rolls
        ratio = self.getstat("LUK") / self.power
        rolls = -1 + round(ratio / .15)
        return rolls

    @property
    def metmult(self): # % of damage taken based on met-power ratio
        ratio = self.getstat("MET") / self.power
        reduction = -1.8 * (1 / (ratio + 1)) + 1.8 #curve slows down as ratio rises
        if reduction > .95: reduction = .95
        return reduction

    @property
    def receivemult(self): # receive more or less damage from states
        rate = 1
        rate *= (1 - self.metmult)
        for state in self.states:
            stateobj = stateseffects.states[state]
            inflictor = self.states[state]["inflictor"]
            power = self.states[state]["power"]
            battler = self
            rate *= eval(stateobj.damagemult)
        rage = self.ragepercent
        if rage > .5:
            rate *= rage + .5
        elif rage < .5:
            rate *= (-1 * ((rage-.5)**2)) + 1
        hope = self.hopepercent
        if hope > .5:
            rate *= (-1 * hope) + 1.5
        return rate

    @property
    def dealmult(self): # do more damage due to rage
        rate = 1
        for state in self.states:
            stateobj = stateseffects.states[state]
            inflictor = self.states[state]["inflictor"]
            power = self.states[state]["power"]
            battler = self
            rate *= eval(stateobj.dealmult)
        rate *= self.spkmult
        rage = self.ragepercent
        if rage > .5:
            rate *= rage * 2
        elif rage < .5:
            rate *= (-1 * ((rage-.5)**2)) + 1
        hope = self.hopepercent
        if hope < .5:
            rate *= (0.5 * hope) + 0.75
        if rate < 0.05:
            rate = 0.05
        return rate

    @property
    def dealonhit(self): # do more or less damage due to rage
        value = 0
        value += self.vials["rage"]["value"] - (self.vials["rage"]["maximum"] // 2)
        if "gambit" in self.vials and self.wielding != None:
            inst = alchemy.Instance(name=self.wielding)
            if "humorous" in inst.Item.tags:
                value += self.vials["gambit"]["value"] - (self.vials["gambit"]["maximum"] // 3)
        if "mangrit" in self.vials:
            value += self.vials["mangrit"]["value"]
        return int(value * -1)

    @property
    def ragepercent(self): # % rage meter
        return self.vials["rage"]["value"] / self.vials["rage"]["maximum"]

    @property
    def hopepercent(self): # % hope meter
        return self.vials["hope"]["value"] / self.vials["hope"]["maximum"]

    @property
    def spkmult(self): # multiplier to damage
        ratio = self.getstat("SPK") / self.power
        mult = -3.5 * (1 / (ratio + 1)) + 4 #curve slows down as ratio rises
        return mult

    @property
    def fightindex(self):
        return self.Strife.order.index(self.name)

    @property
    def health(self):
        return self.vials["health"]["value"]

    @property
    def message(self):
        i = self.Strife.order.index(self.name)
        return self.Strife.messages[i]

    @property
    def they(self):
        if type(self) == PlayerBattler:
            return self.Player.they
        else:
            return "it"

    @property
    def them(self):
        if type(self) == PlayerBattler:
            return self.Player.them
        else:
            return "it"

    @property
    def their(self):
        if type(self) == PlayerBattler:
            return self.Player.their
        else:
            return "its"

    @property
    def theirs(self):
        if type(self) == PlayerBattler:
            return self.Player.theirs
        else:
            return "its"

class PlayerBattler(Battler): #battlers are not stored anywhere, so we can assign a player object as an attribute. battlers are init freshly at the start of strife
    def __init__(self, Strife, player):
        self.name = player.name
        self.Player = player
        self.session = player.session
        player.strife = Strife.name
        vials = ["health", "vim", "aspect"]
        if player.secondaryvial != None:
            vials.append(player.secondaryvial)
        vials += ["hope", "rage"]
        self.stats = player.stats.copy()
        self.stats["RUNG"] = player.rung
        self.power = player.power # "power" is initial power
        self.maxactions = 1
        self.actions = 1
        self.maxtrivialactions = 1
        self.trivialactions = 1
        self.team = player.team
        self.skills = self.Player.skills.copy()
        self.passives = self.Player.passives.copy()
        super().__init__(self.name, vials, Strife=Strife)

    @property
    def dicemin(self):
        min = self.Player.dicemin
        if "gambler" in self.passives:
            min /= 1.4 + (self.getstat("RUNG") / 413)
        return int(min)

    @property
    def dicemax(self):
        max = self.Player.dicemax
        if "gambler" in self.passives:
            max *= 1.4 + (self.getstat("RUNG") / 413)
        return int(max)

    @property
    def wielding(self):
        return self.Player.wielding

class EnemyBattler(Battler):
    def __init__(self, Strife, Npc):
        self.Npc = Npc
        vials = Npc.vials
        self.stats = Npc.stats
        self.power = self.stats["POWER"]
        self.name = Npc.calledby
        while self.name in Strife.battlers:
            random.seed()
            self.name = f"{Npc.calledby} {random.choice(string.ascii_letters).upper()}{random.choice(string.ascii_letters).upper()}"
        self.maxactions = 1
        self.actions = 1
        self.maxtrivialactions = 0
        self.trivialactions = 0
        self.team = Npc.team
        self.type = Npc.type
        self.tier = Npc.tier
        self.passives = Npc.passives
        #todo // add power increase from prototyped shit at random.
        super().__init__(self.name, vials, Strife=Strife)

    @property
    def skills(self):
        s = skills.defaults.copy()
        for skill in skills.noenemy:
            if skill in s:
                s.remove(skill)
        return s

    @property
    def dicemin(self):
        return int(0.7 * self.getstat("POWER"))

    @property
    def dicemax(self):
        return int(1.3 * self.getstat("POWER"))

    @property
    def wielding(self):
        return None

strifes = {} # key: name value: obj
