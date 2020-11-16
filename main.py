import os
import asyncio
import time
import discord

from dotenv import load_dotenv
from discord.ext import commands

from static import get_radio_stream, get_radio_list

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!radio ", description="A bot to play your Indonesian radio station")

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    print(f"Currently added by {len(bot.guilds)} servers")


@bot.command(name="join")
async def _join(ctx, *, channel: discord.VoiceChannel=None):
    """
    Connect this bot to a voice channel

    Params:
    - channel: discord.VoiceChannel [Optional]
        The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
        will be made.
    """

    if not channel:
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("No channel to join. Please either specify a valid channel or join one.")
            return

    vc = ctx.voice_client
    try:
        # check if already connected to vc/no
        if vc:
            # check if on same channel as author
            if vc.channel.id != channel.id:
                await vc.move_to(channel)
                await ctx.send(f"Moved to: **{channel}**")
        else:
            await channel.connect()
            await ctx.send(f"Connected to: **{channel}**")
    except asyncio.TimeoutError:
        await ctx.send(f"Connecting to channel: <{channel}> timed out.")
        return


@bot.command("list")
async def _list(ctx):
    """
    List of available radio stations
    """

    stations = ", ".join(get_radio_list())
    await ctx.send(f"List of available radio {stations}")
    return


@bot.command(name="play")
async def _play(ctx, station, channel: discord.VoiceChannel=None):
    """
    Play a radio station based on user input
    """

    try:
        source = get_radio_stream(station)

        if source is None:
            await ctx.send(f"Unknown station {station}, use !radio list to get available station")
            return

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("You need to be in voice channel")
            return

        print(f"Initiate radio play on {channel}, station: {station}")

        vc = ctx.voice_client
        try:
            # check if already connected to vc/no
            if vc:
                # check if on same channel as author
                if vc.channel.id != channel.id:
                    await vc.move_to(channel)
                    await ctx.send(f"Moved to: **{channel}**")
            else:
                await channel.connect()
                await ctx.send(f"Connected to: **{channel}**")
        except asyncio.TimeoutError:
            await ctx.send(f"Connecting to channel: <{channel}> timed out.")
            return

        await ctx.send(f"Start playing {station} ...")
        vc.play(discord.FFmpegPCMAudio(source), after=lambda e: print("Media play stopped/done"))
    except Exception as e:
        await ctx.send(f"A client exception occured:\n`{e}`")


@bot.command("stop")
async def _stop(ctx):
    """
    Stop current radio
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Already stopped.")
        return

    await ctx.send("Stopping...")
    vc.stop()
    time.sleep(3)
    await ctx.send("Radio stopped!")


@bot.command("leave")
async def _disconnect(ctx):
    """
    Disconnect from a voice channel, if in one
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Radio not in a voice channel.")
        return

    await vc.disconnect()
    time.sleep(2)
    await ctx.send("Radio have left the voice channel!")


@_play.error
async def info_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        try:
            ctx.author.voice.channel
        except AttributeError:
            await ctx.send("You need to be in voice channel")
            return
        await ctx.send(f"Please specify radio station, use !radio list to get available station")

bot.run(TOKEN)
