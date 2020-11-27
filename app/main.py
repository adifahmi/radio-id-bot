import asyncio
import discord
import os

from discord.ext import commands
from dotenv import load_dotenv
from static import get_radio_stream, get_radio_list

load_dotenv()

PREFIX = "!radio "
TOKEN = os.getenv("DISCORD_TOKEN")
if os.environ.get("ENVIRONMENT") == "dev":
    PREFIX = "!r "
    TOKEN = os.getenv("DISCORD_TOKEN_DEV")

if TOKEN is None:
    print("CONFIG ERROR: Please state your discord bot token in .env")
    exit()

bot = commands.Bot(command_prefix=PREFIX, description="A bot to play Indonesian radio station")


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    print(f"Currently added by {len(bot.guilds)} servers")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"type `{PREFIX}help` to use this bot."))


@commands.is_owner()
@bot.command("stats")
async def _stats(ctx):
    """
    Misc stats of the bot
    """
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"type `{PREFIX}help` to use this bot."))

    await ctx.send(f"Added by {len(bot.guilds)} servers")

    total_member = 0
    guild_list_msg = "List of servers:\n"
    for guild in bot.guilds:
        guild_list_msg += f"• {guild.name} ({guild.member_count} members)\n"
        for member in guild.members:
            total_member += 1

    await ctx.send(f"{guild_list_msg}\n")
    await ctx.send(f"Total members: {total_member}")
    return


@commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
@bot.command(name="join")
async def _join(ctx, *, channel: discord.VoiceChannel = None):
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
                await ctx.send(f"Already joined **{channel}**")
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


@commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
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

        await ctx.send(f"Start playing **{station}** :loud_sound:")
        await asyncio.sleep(1)

        # this function is called after the audio source has been exhausted or an error occurred
        def _vc_end(error):
            stop_msg = "Radio stopped :mute:"
            if error:
                stop_msg += f" because of {error}"
            coroutine = ctx.send(stop_msg)
            fut = asyncio.run_coroutine_threadsafe(coroutine, bot.loop)
            try:
                fut.result()
            except Exception as err:
                print(f"Error sending vc end message: {str(err)}")
            return

        try:
            vc.play(discord.FFmpegPCMAudio(source), after=_vc_end)
        except Exception as e:
            print(f"Error playing {station} | {e}")
            await ctx.send(f"Error when trying to play {station}")

        # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your favorit station!"))

        # Handle lonely bot
        # if bot is alone in voice channel, it will stop the radio and leave
        while True:
            await asyncio.sleep(10)
            if vc.is_playing():
                await asyncio.sleep(5)
                if len(channel.voice_states) < 2:
                    await ctx.send(f"No one on **{channel}**, radio will leave in 3s")
                    await asyncio.sleep(3)
                    await vc.disconnect()
                    break
            else:
                break

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
    await asyncio.sleep(3)


@commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
@bot.command("leave")
async def _leave(ctx):
    """
    Disconnect from a voice channel, if in one
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Radio not in a voice channel")
        return

    await vc.disconnect()
    await asyncio.sleep(2)
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
        await ctx.send("Please specify radio station, use `!radio list` to get list of available station")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        cd = "{:.2f}".format(error.retry_after)
        await ctx.send(f"This command is on a {cd}s cooldown")
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{str(error)}, use `!radio help` to list available commands")
        return

    if isinstance(error, commands.ChannelNotFound):
        await ctx.send(str(error))
        return

    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(str(error))
        return

    if isinstance(error, commands.MissingRequiredArgument):
        return

    await ctx.send(str(error))
    raise error


bot.run(TOKEN)
