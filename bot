from Token import token

import os
import nextcord
from nextcord.ext import commands





intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix = "$", intents = intents)


# 一開始bot開機需載入全部程式檔案
@bot.event
async def on_ready():
    global background
    background = await bot.fetch_channel(1198978892749361152)
    await background.send("bot turned on")


# 載入指令程式檔案
@bot.command()
async def load(ctx, extension):
    if ctx.channel.id == 1198978892749361152:
        bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"{extension} loaded.")

# 卸載指令檔案
@bot.command()
async def unload(ctx, extension):
    if ctx.channel.id == 1198978892749361152:
        bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"{extension} unloaded.")

# 重新載入程式檔案
@bot.command()
async def reload(ctx, extension):
    if ctx.channel.id == 1198978892749361152:
        print(extension)
        bot.reload_extension(f"cogs.{extension}")
        await ctx.send(f"{extension} reloaded.")




def init_load(bot:commands.Bot):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            if filename != "__init__.py":
                bot.load_extension(f"cogs.{filename[:-3]}")


init_load(bot)  #必須在執行前新增，否則slash_command
bot.run(token)
