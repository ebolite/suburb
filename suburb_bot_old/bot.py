import util
import alchemy
import config
import explore
import maps
import time
import sys
import traceback

import discord
import os
import asyncio
from dotenv import load_dotenv
from discord.ext import tasks, commands

intents = discord.Intents().all()

bot = commands.Bot(command_prefix=">", intents=intents)
# bot.remove_command('help')

load_dotenv()

@bot.event
async def on_ready():
    bot.add_cog(Basic(bot))
    bot.add_cog(alchemy.Alchemy(bot))
    bot.add_cog(alchemy.Suggest(bot))
    bot.add_cog(Grist(bot))
    bot.add_cog(explore.Explore(bot))
    bot.add_cog(maps.Maps(bot))
    print(f"{bot.user.name} has connected to Discord!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.errors.NotFound):
        pass
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr) #default exception behavior
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        util.bot = bot
        util.backup()
        self.saveloop.start()
        self.backups.start()

    @tasks.loop(minutes=60.0)
    async def backups(self):
        util.backup()

    @tasks.loop(seconds=60)
    async def saveloop(self):
        print("SAVING")
        util.saveall()
        print("SAVING COMPLETE")


    @commands.command(name="save")
    async def save(self, ctx):
        await util.saveall()
        util.backup()
        await ctx.send("Saved!")

    @util.deletecommand()
    @commands.command(name="menu")
    async def menu(self, ctx):
        player = explore.Player(ctx.author)
        message = None
        if player.session == None:
            await explore.Explore.assignsession(explore.Explore, ctx.author, ctx)
        if player.setup != True:
            await explore.Explore.createcharacter(explore.Explore, ctx.author, ctx)
        while True:
            emojis = [ # yes i know it's not the plural but i need a singular variable
                "♿", # EXPLORE
                "🌐", # EMBARK
                "💻", # EMULATE
                "❔", # ELUCIDATE
                "◀", # ESCAPE
                ]
            text = f"What will {player.name} do?"
            desc = """
♿ **>EXPLORE** your surroundings
🌐 **>EXPAND** to overmap menu options
💻 **EMULATE** a computing device
❔ **>ELUCIDATE** various matters
◀ **ESCAPE** this menu
            """
            embed = discord.Embed(color=config.sburbblue,title=">MENU",description=desc)
            if message == None:
                message = await ctx.send(content=text, embed=embed)
            else:
                await message.edit(content=text, embed=embed)
            r = await util.reactioncheck(message, ctx.author, emojis)
            if r == None or r.emoji == "◀":
                break
            emoji = str(r.emoji)
            if emoji == "♿":
                await message.delete()
                message = None
                await explore.Explore.explore(explore.Explore, ctx)
            elif emoji == "🌐":
                await message.delete()
                message = None
                await self.expandmenu(ctx)
            elif emoji == "💻":
                inst = self.computercheck(ctx)
                if inst == False:
                    await message.edit(content="There's no computer around here to interact with!", embed=None)
                    await asyncio.sleep(3)
                else:
                    await message.delete()
                    message = None
                    await inst.activate(ctx)
            elif emoji == "❔":
                await message.delete()
                message = None
                await self.elucidatemenu(ctx)
        if message != None:
            await message.delete()

    @staticmethod
    def computercheck(ctx):
        player = explore.Player(ctx.author)
        for card in player.sylladex:
            if card != {}:
                instname = card["item"]
                inst = alchemy.Instance(name=instname)
                if inst.Item.use != None and "computer" in inst.Item.use:
                    return inst
        else:
            for instname in player.Room.items:
                inst = alchemy.Instance(name=instname)
                if inst.Item.use != None and "computer" in inst.Item.use:
                    return inst
            else:
                return False

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="elucidate")
    async def elucidatemenu(self, ctx):
        player = explore.Player(ctx.author)
        message = None
        while True:
            emojis = [
                "📑", # >SYLLADEX
                "🚹", # SELF-INFLECT
                "⬇", # >SPREAD
                "<a:suburbspirograph:820899074986606613>", # >SESSION
                "◀", # ESCAPE
                ]
            text = f"What will {player.name} do?"
            desc = """
📑 **>SYLLADEX** (View items in it)
🚹 **SELF-INFLECT** (Do it)
⬇ **>SPREAD** (your stats around)
<a:suburbspirograph:820899074986606613> **>SESSION** (View it)
◀ **ESCAPE** this menu
            """
            embed = discord.Embed(color=config.sburbblue,title=">ELUCIDATE",description=desc)
            if message == None:
                message = await ctx.send(content=text, embed=embed)
            else:
                await message.edit(content=text, embed=embed)
            r = await util.reactioncheck(message, ctx.author, emojis)
            if r == None or r.emoji == "◀":
                break
            emoji = str(r.emoji)
            if emoji == "📑":
                await message.delete()
                message = None
                await alchemy.Alchemy.sylladex(alchemy.Alchemy, ctx)
            elif emoji == "🚹":
                await message.delete()
                message = None
                await explore.Explore.whois(explore.Explore, ctx)
            elif emoji == "⬇":
                await message.delete()
                message = None
                await explore.Explore.spread(explore.Explore, ctx)
            elif emoji == "<a:suburbspirograph:820899074986606613>":
                await message.delete()
                message = None
                await explore.Explore.session(explore.Explore, ctx)
        if message != None:
            await message.delete()

    @util.deletecommand()
    @util.issetup()
    @commands.command(name="expand")
    async def expandmenu(self, ctx):
        player = explore.Player(ctx.author)
        message = None
        while True:
            emojis = [
                "🌐", # EMBARK
                "❗", # ENCOUNTER
                "<a:suburbspirograph:820899074986606613>", # ENTER
                "◀", # ESCAPE
                ]
            text = f"What will {player.name} do?"
            desc = """
🌐 **EMBARK** to other tiles on your overmap
❗ **>ENCOUNTER** enemies and engage in strife
<a:suburbspirograph:820899074986606613> **ENTER** various gates
◀ **ESCAPE** this menu
            """
            embed = discord.Embed(color=config.sburbblue,title=">EMBARK",description=desc)
            if message == None:
                message = await ctx.send(content=text, embed=embed)
            else:
                await message.edit(content=text, embed=embed)
            r = await util.reactioncheck(message, ctx.author, emojis)
            if r == None or r.emoji == "◀":
                break
            emoji = str(r.emoji)
            if emoji == "🌐":
                await message.delete()
                message = None
                await explore.Explore.embark(explore.Explore, ctx)
            elif emoji == "❗":
                await message.delete()
                message = None
                await explore.Explore.encounter(explore.Explore, ctx)
            elif emoji == "<a:suburbspirograph:820899074986606613>":
                await message.delete()
                message = None
                await explore.Explore.enter(explore.Explore, ctx)
        if message != None:
            await message.delete()

class Grist(commands.Cog):
    def __init__(self, bot):
        print("init grist")
        self.bot = bot

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
