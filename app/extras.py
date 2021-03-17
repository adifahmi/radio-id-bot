import discord
import os
import datetime

from discord.ext import commands
from .utils import create_tempfile
from .external_api import ksoft, dbox


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

    @commands.is_owner()
    @commands.command("upload_stats", hidden=True)
    async def _upload_stats(self, ctx):
        """
        Show some stats of this bot (owner only)
        """

        guild_obj = self.bot.guilds
        total_guild = len(guild_obj)

        # prepare csv
        fmt_full_report = f"Added by {total_guild} servers\n\n"
        fmt_full_report += "id,name,member_cnt,guild_id\n"

        await ctx.send("Preparing data ...")
        total_member = 0
        num = 1
        for guild in guild_obj:
            fmt_full_report += f"{num},{guild.name},{guild.member_count},{guild.id}\n"
            total_member += guild.member_count
            num += 1

        fmt_full_report += f"\nTotal members: {total_member}"
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")

        file = create_tempfile(fmt_full_report)
        env = os.environ.get("ENVIRONMENT")
        filename = f"RadioID_{env}_{now}.csv"

        await ctx.send("Uploading stats to dropbox")
        ul, ul_info = dbox.upload_file(file, filename)
        if ul_info['status_code'] != 200:
            await ctx.send(f"Failed to upload ```{str(ul_info['error'])}```")
            return

        await ctx.send(f"File uploaded at `{ul.get('path_display')}`, getting link ...")

        gl, gl_info = dbox.create_share_link(ul.get('path_display'))
        if gl_info['status_code'] != 200:
            await ctx.send(f"Failed to get download link ```{str(gl_info['error'])}```")
        else:
            await ctx.send(f"Download link: {gl.get('url')}")

        return
