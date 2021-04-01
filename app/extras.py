import discord

from discord.ext import commands
from .external_api import ksoft
from .static import (
    RADIO_ID_LOGO_URL, BOT_NAME, BOT_DESC, BOT_GITHUB_URL,
    BOT_TOP_GG_URL, BOT_DBL_URL, BOT_SUPPORT_SERVER_INV, AUTHOR_TWITTER_URL,
    SAWERIA_URL, DONATE_IMAGE_URL, BOT_INVITE_LINK
)


class Extras(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("lyrics")
    async def _lyrics(self, ctx, *query):
        """
        Menampilkan lyrics lagu berdasarkan input
        """
        if not query:
            await ctx.send(f"Silahkan masukan artis dan judul lagu terlebih dahulu, contoh: `{self.prefix} lyrics Paramore Still into you`")
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
        return

    @commands.guild_only()
    @commands.command("ping")
    async def _ping(self, ctx):
        """
        Latensi bot ke server
        """

        lat = self.bot.latency
        await ctx.send(f"Latensi bot ke server ~{round(lat, 2)} detik")
        return

    @commands.command("about")
    async def _about(self, ctx):
        """
        Deskripsi tentang bot ini
        """

        embed = discord.Embed(
            title=BOT_NAME,
            url=BOT_GITHUB_URL,
            description=BOT_DESC,
            color=0x9395a5
        )
        embed.set_thumbnail(url=RADIO_ID_LOGO_URL)

        embed.add_field(name="Open source code", value=f"[Github]({BOT_GITHUB_URL})", inline=False)
        embed.add_field(name="Donasi (untuk hosting bot)", value=f"[Saweria]({SAWERIA_URL})", inline=False)
        embed.add_field(name="Vote this bot", value=f"[top.gg]({BOT_TOP_GG_URL}), [DBL]({BOT_DBL_URL})", inline=False)
        embed.add_field(name="Support server", value=f"[AF Home]({BOT_SUPPORT_SERVER_INV})", inline=False)
        embed.add_field(name="Contact me (for station-removal, etc)", value=f"[Twitter]({AUTHOR_TWITTER_URL})", inline=False)
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)
        return

    @commands.command("support")
    async def _support(self, ctx):
        """
        Link ke support server radio-id-bot
        """

        embed = discord.Embed(
            title="AF Home",
            url=BOT_SUPPORT_SERVER_INV,
            description="Join server AF Home untuk memberikan masukan",
            color=0x9395a5
        )
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)
        return

    @commands.command("donate")
    async def _donate(self, ctx):
        """
        Link donasi untuk pengembangan bot ini
        """

        embed = discord.Embed(
            title="Donasi",
            description="Dukung pengembangan dan biaya hosting bot ini dengan cara berdonasi melalui saweria",
            color=0x9395a5
        )
        embed.add_field(name="Saweria", value=f"[{SAWERIA_URL}]({SAWERIA_URL})", inline=False)
        embed.set_thumbnail(url=DONATE_IMAGE_URL)
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)
        return

    @commands.command("invite")
    async def _invite(self, ctx):
        """
        Link to invite this bot
        """

        embed = discord.Embed(
            title="Invite this bot",
            description="Link untuk memasukkan bot ini ke server discord",
            color=0x9395a5
        )
        embed.add_field(name="Direct link", value=f"[{BOT_INVITE_LINK}]({BOT_INVITE_LINK})", inline=False)
        embed.add_field(name="Top gg", value=f"[{BOT_TOP_GG_URL}]({BOT_TOP_GG_URL})", inline=False)
        embed.set_thumbnail(url=RADIO_ID_LOGO_URL)
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)
        return
