import discord
import os

from discord.ext import commands
from dotenv import load_dotenv
from app.player import RadioPlayer
from app.extras import Extras
from app.misc import Misc
from app.task import BotTask
from app.static import COMMANDS

load_dotenv()

PREFIX = "!radio"
TOKEN = os.getenv("DISCORD_TOKEN")
if os.environ.get("ENVIRONMENT") == "dev":
    PREFIX = "!r"
    TOKEN = os.getenv("DISCORD_TOKEN_DEV")

if TOKEN is None:
    print("CONFIG ERROR: Please state your discord bot token in .env")
    exit()

bot = commands.Bot(
    command_prefix=f"{PREFIX} ",
    description="Discord bot untuk memainkan radio favoritmu!",
    help_command=None
)


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    print(f"Currently added by {len(bot.guilds)} servers")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"`{PREFIX} help` untuk memulai."))


@bot.command('help')
async def _help(ctx):
    """
    List of commands
    """

    embed = discord.Embed(
        title="Daftar perintah yang tersedia",
        color=0x9395a5
    )

    for cmd, msg in COMMANDS.items():
        embed.add_field(name=f"{PREFIX} {cmd}", value=msg, inline=False)
        embed.set_footer(text="radio-id")
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if os.environ.get("ENVIRONMENT") == "dev":
        raise error

    if isinstance(error, commands.CommandOnCooldown):
        cd = "{:.2f}".format(error.retry_after)
        await ctx.send(f"Gunakan command ini lagi setelah {cd} detik")
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
        await ctx.send("MissingRequiredArgument")
        return

    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(str(error))
        return

    await ctx.send(str(error))
    raise error


bot.add_cog(RadioPlayer(bot, PREFIX))
bot.add_cog(Extras(bot, PREFIX))
bot.add_cog(Misc(bot, PREFIX))
bot.add_cog(BotTask(bot, PREFIX))
bot.run(TOKEN)
