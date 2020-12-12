import asyncio
import discord

from discord.ext import commands
from .static import get_radio_stream, get_radio_list
from .utils import is_valid_url

NOW_PLAYING = {}


class RadioPlayer(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix

    async def join_or_move(self, ctx, channel):
        vc = ctx.voice_client
        try:
            # check if already connected to vc/no
            if vc:
                if vc.is_playing() is True:
                    await ctx.send(f"Radio is playing a station, use `{self.prefix} stop` to stop current session.")
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
        return vc

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command(name="join")
    async def _join(self, ctx, *, channel: discord.VoiceChannel = None):
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

        await self.join_or_move(ctx, channel)
        return

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("list")
    async def _list(self, ctx):
        """
        Show list of available radio stations
        """

        await ctx.send("List of available stations:")
        radio_list = "\n".join([f"📻 {radio}" for radio in get_radio_list()])
        await ctx.send(f"```{radio_list}```")
        await ctx.send(f"\nuse `{self.prefix} play <station>` to start playing it")
        return

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command(name="play")
    async def _play(self, ctx, *station):
        """
        Play a radio station based on user input
        """
        if not station:
            await ctx.send(f"Please specify radio station, use `{self.prefix} list` to get list of available station")
            return

        station = " ".join(station[:])

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("You need to be in voice channel")
            return

        if is_valid_url(station) is True:
            source = station
        else:
            source = get_radio_stream(station)
            if source is None:
                await ctx.send(f"Unknown station **{station}**, use `{self.prefix} list` to get list of available station")
                return

        try:
            print(f"Initiate radio play on {ctx.guild.name} - {channel}, station: {station}")

            vc = await self.join_or_move(ctx, channel)
            if vc is None:
                return

            await ctx.send(f"Start playing **{station}** :loud_sound:")
            await asyncio.sleep(1)

            # this function is called after the audio source has been exhausted or an error occurred
            def _vc_end(error):
                NOW_PLAYING.pop(ctx.guild.id, None)  # Remove from NP
                stop_msg = "Radio stopped :mute:"
                if error:
                    stop_msg += f" because of {error}"
                coroutine = ctx.send(stop_msg)
                fut = asyncio.run_coroutine_threadsafe(coroutine, self.bot.loop)
                try:
                    fut.result()
                except Exception as err:
                    print(f"Error sending vc end message: {str(err)}")
                return

            try:
                vc.play(discord.FFmpegPCMAudio(source), after=_vc_end)
                NOW_PLAYING[ctx.guild.id] = {"station": station, "guild_name": ctx.guild.name}
            except Exception as e:
                print(f"Error playing {station} | {e}")
                await ctx.send(f"Error when trying to play {station}")

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
                        NOW_PLAYING.pop(ctx.guild.id, None)
                        break
                else:
                    break

        except Exception as e:
            await ctx.send(f"A client exception occured:\n`{e}`")

    @commands.command("playing")
    @commands.guild_only()
    async def _playing(self, ctx):
        """
        Get what's playing now, if any
        """
        vc = ctx.voice_client

        if not vc:
            await ctx.send("Radio is not playing anything")
            return

        if vc.is_playing() is False:
            await ctx.send("Radio is not playing anything")
            return

        np = NOW_PLAYING.get(ctx.guild.id)
        await ctx.send(f"Radio is playing **{np['station']}** :loud_sound:")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("stop")
    async def _stop(self, ctx):
        """
        Stop current radio play
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
        NOW_PLAYING.pop(ctx.guild.id, None)
        await asyncio.sleep(3)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("leave")
    async def _leave(self, ctx):
        """
        Disconnect from a voice channel, if in one
        """
        vc = ctx.voice_client

        if not vc:
            await ctx.send("Radio not in a voice channel")
            return

        await vc.disconnect()
        NOW_PLAYING.pop(ctx.guild.id, None)
        await asyncio.sleep(2)
        await ctx.send("Radio have left the voice channel")
