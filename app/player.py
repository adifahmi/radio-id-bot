import asyncio
import discord

from discord.ext import commands
from .static import get_radio_stream, get_radio_list

NOW_PLAYING = {}


class RadioPlayer(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix

    @commands.is_owner()
    @commands.command("presence", hidden=True)
    async def _change_presence(self, ctx, *status):
        """
        Change status of this bot (owner only)
        """

        if not status:
            status = f"`{self.prefix} help` to use this self.bot."
        else:
            status = " ".join(status[:])

        await self.self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status))

        await ctx.send(f"Status changed to:\n{status}")
        return

    @commands.is_owner()
    @commands.command("stats", hidden=True)
    async def _stats(self, ctx):
        """
        Show some stats of this bot (owner only)
        """

        await ctx.send(f"Added by {len(self.bot.guilds)} servers")

        total_member = 0
        guild_list_msg = "List of servers:\n"
        for guild in self.bot.guilds:
            guild_list_msg += f"• {guild.name} ({guild.member_count} members)\n"
            total_member += guild.member_count

        await ctx.send(f"{guild_list_msg}\n")
        await ctx.send(f"Total members: {total_member}")

        await ctx.send("==" * 30)
        print(f"NP {NOW_PLAYING}")
        for _, np in NOW_PLAYING.items():
            await ctx.send(f"Now playing {np['station']} on {np['guild_name']}\n")
        return

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

        message = "List of available stations:\n"
        message += "\n".join([f":radio: {radio}" for radio in get_radio_list()])
        message += f"\nuse `{self.prefix} play <station>` to start playing it"
        await ctx.send(message)
        return

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command(name="play")
    async def _play(self, ctx, station):
        """
        Play a radio station based on user input
        """

        try:
            source = get_radio_stream(station)

            if source is None:
                await ctx.send(f"Unknown station {station}, use `{self.prefix} list` to get list of available station")
                return

            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send("You need to be in voice channel")
                return

            print(f"Initiate radio play on {ctx.guild.name} - {channel}, station: {station}")

            vc = await self.join_or_move(ctx, channel)
            if vc is None:
                return

            await ctx.send(f"Start playing **{station}** :loud_sound:")
            await asyncio.sleep(1)

            # this function is called after the audio source has been exhausted or an error occurred
            def _vc_end(error):
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
                        NOW_PLAYING.pop(ctx.guild.id, None)  # Remove from NP
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

    @commands.guild_only()
    @commands.command("ping", hidden=True)
    async def _ping(self, ctx):
        """
        Check latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds
        """
        vc = ctx.voice_client

        if not vc:
            await ctx.send("Radio not in a voice channel")
            return

        latency = vc.latency
        await ctx.send(f"Radio bot voice latency is {latency} seconds")

    @commands.command("about")
    async def _about(self, ctx):
        """
        About this bot
        """

        embed = discord.Embed(
            title="Radio Indonesia",
            url="https://github.com/AdiFahmi/radio-id-bot",
            description="Radio-id-bot is a simple Discord Music Bot built with discord.py \
                to play a radio from some Indonesian radio-station.\
                    It's also open source on [Github](https://github.com/AdiFahmi/radio-id-bot)!",
            color=0x9395a5
        )
        embed.set_author(
            name="Adi Fahmi",
            url="https://twitter.com/adifahmii",
            icon_url="https://cdn.discordapp.com/attachments/781466869688827904/783697044233519134/radio_2.png"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/781466869688827904/783697044233519134/radio_2.png")
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)

    @_play.error
    async def info_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            try:
                ctx.author.voice.channel
            except AttributeError:
                await ctx.send("You need to be in voice channel")
                return
            await ctx.send(f"Please specify radio station, use `{self.prefix} list` to get list of available station")
