import asyncio
import discord
import random

from discord.ext import commands
from .utils import (
    is_valid_url, Stations, Playing
)


class RadioPlayer(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix
        self.playing = Playing()
        self.stations = Stations()

    async def join_or_move(self, ctx, channel):
        vc = ctx.voice_client
        try:
            # check if already connected to vc/no
            if vc:
                if vc.is_playing() is True:
                    await ctx.send(f"Radio sedang memutar stasiun radio lainnya, ketik `{self.prefix} stop` untuk menghentikan pemutaran terlebih dahulu.")
                    return
                if vc.channel.id != channel.id:
                    await vc.move_to(channel)
                    await ctx.send(f"Radio pindah ke: **{channel}**")
            else:
                await channel.connect()
                vc = ctx.voice_client
                await ctx.send(f"Radio terhubung ke: **{channel}**")
        except asyncio.TimeoutError:
            await ctx.send(f"Gagal terhubung ke: **<{channel}>** `Error connection timed out`, coba ganti server region kamu ke Negara lain, contoh: Japan")
            return
        return vc

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command(name="join")
    async def _join(self, ctx, *, channel: discord.VoiceChannel = None):
        """
        Menghubungkan bot ini ke Voice Channel

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
                await ctx.send("Silahkan pilih voice channel atau kamu harus masuk ke voice channel terlebih dahulu.")
                return

        await self.join_or_move(ctx, channel)
        return

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("list")
    async def _list(self, ctx):
        """
        Menampilan daftar stasiun radio yang tersedia
        """

        await ctx.send("Daftar stasiun radio yang tersedia:")

        self.stations.reload_station_list()
        stations_dict = self.stations.get_stations()
        stations_fmt = ""
        for station_name, station_attr in stations_dict.items():
            mark = "✓" if station_attr["status"] == 200 else "X"
            stations_fmt += f"📻 {station_name} {mark}\n"
        stations_fmt += "\n✓ = Stasiun radio dapat diputar\n"
        stations_fmt += "X = Stasiun radio sedang mengalami gangguan\n"
        stations_list = [k for k in stations_dict.keys()]

        await ctx.send(f"```{stations_fmt}```")
        await ctx.send(f"\nketik `{self.prefix} play <stasiun radio>` untuk memulai memutar, contoh: `{self.prefix} play {random.choice(stations_list)}`")
        await ctx.send(f"Stasiun favorit kamu tidak tersedia? ketik `{self.prefix} support` untuk gabung ke support server dan silahkan request di sana")
        await ctx.send(f"Kamu juga bisa bantu donasi untuk pengembangan bot ini di `{self.prefix} donate`")
        return

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command(name="play")
    async def _play(self, ctx, *station):
        """
        Memainkan stasiun radio berdasarkan pilihan kamu
        """

        if not station:
            await ctx.send(f"Silahkan pilih stasiun terlebih dahulu, ketik `{self.prefix} list` untuk melihat daftar stasiun radio")
            return

        station = " ".join(station[:])

        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Kamu harus berada di Voice Channel terlebih dahulu")
            return

        if is_valid_url(station) is True:
            source = station
        else:
            self.stations.reload_station_list()
            source = self.stations.get_stations_by_name(station)
            if source is None:
                await ctx.send(f"Stasiun **{station}** tidak terdaftar, ketik `{self.prefix} list` untuk melihat daftar stasiun radio")
                return
            source = source["url"]

        try:
            print(f"Initiate radio play on {ctx.guild.name} - {channel}, station: {station}")

            vc = await self.join_or_move(ctx, channel)
            if vc is None:
                return

            await ctx.send(f"Mulai memainkan **{station}** :loud_sound:")
            await asyncio.sleep(1)

            # this function is called after the audio source has been exhausted or an error occurred
            def _vc_end(error):
                self.playing.remove_from_play(ctx.guild.id)  # Remove from NP

                stop_msg = f"Berhenti memutar **{station}** :mute:"
                if error:
                    stop_msg += f" karena `{error}`"
                coroutine = ctx.send(stop_msg)
                fut = asyncio.run_coroutine_threadsafe(coroutine, self.bot.loop)
                try:
                    fut.result()
                except Exception as err:
                    print(f"Error sending vc end message: {str(err)}")
                return

            try:
                vc.play(discord.FFmpegOpusAudio(source), after=_vc_end)
                self.playing.add_to_play(ctx.guild.id, ctx.guild.name, station)  # Add to NP
            except Exception as e:
                print(f"Error playing {station} | {e}")
                await ctx.send(f"Terdapat gangguan pada server, gagal memutar **{station}**, coba ganti server region kamu ke Negara lain, contoh: Japan")

            already_promote = False

            # will keep looping until bot disconnected from VC
            while True:
                await asyncio.sleep(30)
                if vc.is_playing():
                    # send promo message once at a time in a session
                    if already_promote is False:
                        await ctx.send(f"Tahukan kamu? sekarang kamu bisa bantu donasi untuk pengembangan bot ini melalui link saweria di `{self.prefix} donate` :innocent:")
                    already_promote = True

                    await asyncio.sleep(5)
                    # if bot is alone in voice channel, it will stop the radio and leave
                    if len(channel.voice_states) < 2:
                        await ctx.send(f"Voice Channel **{channel}** kosong, radio akan berhenti dalam 10 detik ...")
                        await asyncio.sleep(10)
                        if len(channel.voice_states) < 2:
                            await ctx.send(f"Radio berhenti karena ditinggal sendiri di **{channel}**")
                            await vc.disconnect()
                            self.playing.remove_from_play(ctx.guild.id)
                            break
                else:
                    break

        except Exception as e:
            await ctx.send(f"Terdapat gangguan pada server:\n`{e}`")

    @commands.command("playing")
    @commands.guild_only()
    async def _playing(self, ctx):
        """
        Menampilkan stasiun radio yang sedang diputar
        """

        vc = ctx.voice_client

        if not vc:
            await ctx.send("Radio sedang tidak memutar apapun di server ini")
            return

        if vc.is_playing() is False:
            await ctx.send("Radio sedang tidak memutar apapun di server ini")
            return

        np = self.playing.current_play(ctx.guild.id)
        await ctx.send(f"Radio sedang memutar **{np['station']}** :loud_sound:")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("stop")
    async def _stop(self, ctx):
        """
        Menghentikan pemutaran radio
        """

        vc = ctx.voice_client

        if not vc:
            await ctx.send("Radio tidak berada di Voice Channel")
            return

        if vc.is_playing() is False:
            await ctx.send("Radio sedang tidak memutar apapun di server ini")
            return

        await ctx.send("Menghentikan radio ...")
        vc.stop()
        self.playing.remove_from_play(ctx.guild.id)

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("leave")
    async def _leave(self, ctx):
        """
        Memutuskan radio dari Voice Channel
        """

        vc = ctx.voice_client

        if not vc:
            await ctx.send("Radio tidak berada di Voice Channel")
            return

        if vc.is_playing() is True:
            await ctx.send(f"Radio sedang memutar stasiun radio, ketik `{self.prefix} stop` untuk menghentikan pemutaran terlebih dahulu.")
            return

        await vc.disconnect()
        self.playing.remove_from_play(ctx.guild.id)
        await ctx.send("Radio keluar dari Voice Channel")
