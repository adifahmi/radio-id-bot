import os
import asyncio
import time
import discord

from dotenv import load_dotenv
from discord.ext import commands

from static import get_radio_stream, get_radio_list

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
    print("Please state your discord bot token in .env")
    exit()

bot = commands.Bot(command_prefix="!radio ", description="A bot to play Indonesian radio station")

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    print(f"Currently added by {len(bot.guilds)} servers")


@commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
@bot.command(name="join")
async def _join(ctx, *, channel: discord.VoiceChannel=None):
    """
    Connect this bot to a voice channel

    Params:
    - channel: discord.VoiceChannel [Optional]
        The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
        will be made.
    """

    # if channel is not passed, will try to connect to same channel as author
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
            # check if bot is not on same channel as author
            # then move it
            if vc.channel.id != channel.id:
                await vc.move_to(channel)
                await ctx.send(f"Moved to: **{channel}**")
        else:
            await channel.connect()
            await ctx.send(f"Connected to: **{channel}**")
    except asyncio.TimeoutError:
        await ctx.send(f"Connecting to channel: <{channel}> timed out.")
        return


@commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
@bot.command("list")
async def _list(ctx):
    """
    List of available radio stations
    """

    message = "List of available stations:\n"
    message += "\n".join([f":radio: {radio}" for radio in get_radio_list()])
    message += "\nuse `!radio play {station}` to start playing it"
    await ctx.send(message)
    return


@commands.cooldown(rate=1, per=10, type=commands.BucketType.guild)
@bot.command(name="play")
async def _play(ctx, station):
    """
    Play a radio station based on user input
    """

    try:
        source = get_radio_stream(station)

        if source is None:
            await ctx.send(f"Unknown station {station}, use `!radio list` to get list of available station")
            return

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("You need to be in voice channel")
            return

        print(f"Initiate radio play on {ctx.guild.name} - {channel}, station: {station}")

        vc = ctx.voice_client

        try:
            # check if already connected to vc/no
            if vc:
                if vc.is_playing() is True:
                    await ctx.send("Radio is already playing a station, use `!radio stop` to stop current station and reinitiate `!radio play`")
                    return
                if vc.channel.id != channel.id:
                    await vc.move_to(channel)
                    await ctx.send(f"Moved to: **{channel}**")
            else:
                await channel.connect()
                vc = ctx.voice_client
                await ctx.send(f"Connected to: **{channel}**")
        except asyncio.TimeoutError:
            await ctx.send(f"Connecting to channel: <{channel}> timed out")
            return

        await ctx.send(f"Start playing {station} :loud_sound:")
        time.sleep(1)
        vc.play(discord.FFmpegPCMAudio(source), after=lambda e: print("Media play stop"))
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=station))
    except Exception as e:
        await ctx.send(f"A client exception occured:\n`{e}`")


@bot.command("playing")
async def _playing(ctx):
    """
    Get what's playing now, if any
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Radio not in a voice channel")
        return

    if vc.is_playing() is False:
        await ctx.send("Radio not playing anything")
        return
    
    print(vc.source)
    await ctx.send(f"Radio is playing {vc.source}")


@commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
@bot.command("stop")
async def _stop(ctx):
    """
    Stop current radio
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Radio not in a voice channel")
        return
    
    if vc.is_playing() is False:
        await ctx.send("Radio not playing anything")
        return

    await ctx.send("Stopping...")
    vc.stop()
    time.sleep(3)
    await bot.change_presence(activity=None, status=discord.Status.online)
    await ctx.send("Radio stopped")


@commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
@bot.command("leave")
async def _disconnect(ctx):
    """
    Disconnect from a voice channel, if in one
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Radio not in a voice channel")
        return

    await vc.disconnect()
    time.sleep(2)
    await bot.change_presence(activity=None, status=discord.Status.online)
    await ctx.send("Radio have left the voice channel")


@bot.command("ping")
async def _ping(ctx):
    """
    Check latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Radio not in a voice channel")
        return
    
    latency = vc.latency
    await ctx.send(f"Radio bot voice latency is {latency} seconds")


@bot.command("about")
async def _about(ctx):
    """
    Print contact info
    """
    embed = discord.Embed()
    embed.description = "Created by [AF](https://twitter.com/adifahmii), source code is available on [Github](https://github.com/AdiFahmi/radio-id-bot)"
    await ctx.send(embed=embed)


@_play.error
async def info_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        try:
            ctx.author.voice.channel
        except AttributeError:
            await ctx.send("You need to be in voice channel")
            return
        await ctx.send(f"Please specify radio station, use `!radio list` to get list of available station")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on a %.2fs cooldown" % error.retry_after)
        return
    raise error

bot.run(TOKEN)
