import discord
import os

from discord.ext import commands
from dotenv import load_dotenv
from player import RadioPlayer
from extras import Extras

load_dotenv()

PREFIX = "!radio"
TOKEN = os.getenv("DISCORD_TOKEN")
if os.environ.get("ENVIRONMENT") == "dev":
    PREFIX = "!r"
    TOKEN = os.getenv("DISCORD_TOKEN_DEV")

if TOKEN is None:
    print("CONFIG ERROR: Please state your discord bot token in .env")
    exit()


help_command = commands.DefaultHelpCommand(
    no_category='Basic'
)

bot = commands.Bot(command_prefix=f"{PREFIX} ", description="A bot to play Indonesian radio station", help_command=help_command)


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    print(f"Currently added by {len(bot.guilds)} servers")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"`{PREFIX} help` to use this bot."))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        cd = "{:.2f}".format(error.retry_after)
        await ctx.send(f"This command is on a {cd}s cooldown")
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{str(error)}, use `{PREFIX} help` to list available commands")
        return

    if isinstance(error, commands.ChannelNotFound):
        await ctx.send(str(error))
        return

    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(str(error))
        return

    if isinstance(error, commands.MissingRequiredArgument):
        return

    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(str(error))
        return

    await ctx.send(str(error))
    raise error


bot.add_cog(RadioPlayer(bot, PREFIX))
bot.add_cog(Extras(bot, PREFIX))
bot.run(TOKEN)
