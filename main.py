import os
import asyncio
import time
import discord

from dotenv import load_dotenv
from discord.ext import commands

from static import get_radio_stream, get_radio_list

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!radio ', description="A bot to play your Indonesian radio station")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='join')
async def _join(ctx, *, channel: discord.VoiceChannel=None):
    """
    Connect this bot to a voice channel
    This command also handles moving the bot to different channels.

    Params:
    - channel: discord.VoiceChannel [Optional]
        The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
        will be made.
    """
    if not channel:
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send('No channel to join. Please either specify a valid channel or join one.')
            return

    vc = ctx.voice_client

    if vc:
        if vc.channel.id == channel.id:
            return
        try:
            await vc.move_to(channel)
        except asyncio.TimeoutError:
            await ctx.send(f'Moving to channel: <{channel}> timed out.')
            return
    else:
        try:
            await channel.connect()
        except asyncio.TimeoutError:
            await ctx.send(f'Connecting to channel: <{channel}> timed out.')
            return

    await ctx.send(f'Connected to: **{channel}**', delete_after=10)


@bot.command('list')
async def _stop(ctx):
    """
    List of available radio stations
    """
    await ctx.send(", ".join(get_radio_list()))
    return


@bot.command(name='play')
async def _play(ctx, station, channel: discord.VoiceChannel=None):
    """
    Play a station based on user input
    """

    try:
        source = get_radio_stream(station)

        if source is None:
            await ctx.send("Radio is not available in list, use !radio list to get available station")
            return

        vc = ctx.voice_client
        if not vc:
            await ctx.send("Joinning a voice channel...")
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send('You need to be in voice channel')
                return

            try:
                await channel.connect()
            except asyncio.TimeoutError:
                await ctx.send(f'Connecting to channel: <{channel}> timed out.')
                return

            await ctx.send(f'Connected to: **{channel}**', delete_after=10)
        else:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                await ctx.send(f'Moving to channel: <{channel}> timed out.')
                return

        await ctx.send(f"Start playing {station} ...")

        ctx.voice_client.play(discord.FFmpegPCMAudio(source), after=lambda e: print("stopped/done"))

    except Exception as e:
        await ctx.send(f"A client exception occured:\n`{e}`")


@bot.command('stop')
async def _stop(ctx):
    """
    Stop and leave voice channel
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("Already stopped.")
        return

    vc.stop()
    await ctx.send("Stopping...")
    time.sleep(1)
    await vc.disconnect()
    await ctx.send("Leaving voice channel...")


@bot.command('leave')
async def _disconnect(ctx):
    """
    Disconnect from a voice channel, if in one
    """
    vc = ctx.voice_client

    if not vc:
        await ctx.send("I am not in a voice channel.")
        return

    await vc.disconnect()
    await ctx.send("I have left the voice channel!")


@_play.error
async def info_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Please specify radion station, use !radio list to get available station")

bot.run(TOKEN)
