import discord

from discord.ext import commands
from .external_api import ksoft


class Extras(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("lyrics")
    async def _lyrics(self, ctx, *query):
        """
        Menampilkan lyric berdasarkan input
        """
        if not query:
            await ctx.send(f"Silahkan masukan judul lagi terlebih dahulu, contoh: `{self.prefix} lyrics Paramore Still Into You`")
            return
        else:
            query = " ".join(query[:])

        resp, info = ksoft.get_lyrics(query)
        if info["status_code"] == 500:
            await ctx.send("Gagal mendapatkan lyric :cry:")
            return

        if info["status_code"] == 404:
            await ctx.send("Lagu yang dicari tidak ditemukan :x:\ncoba ganti lagu lain")
            return

        if not resp["data"]:
            await ctx.send("Gagal mengekstrak lyric :x:")
            return

        top_result = resp["data"][0]
        song = f"{top_result['artist']} - {top_result['name']}"
        lyrics = top_result["lyrics"]
        if len(lyrics) > 2048:
            lyrics = f"{lyrics[:2040]} ..."

        embed = discord.Embed(title=song, description=lyrics)
        embed.set_footer(text="Lyrics provided by KSoft.Si")
        await ctx.send(embed=embed)
