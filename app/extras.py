import discord

from discord.ext import commands
from external_api import ksoft


class Extras(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.guild)
    @commands.guild_only()
    @commands.command("lyrics")
    async def _lyrics(self, ctx, *query):
        """
        Get lyrics by query
        """
        if not query:
            await ctx.send(f"Please provide a query `{self.prefix} lyrics <song name or artist - song name>`")
            return
        else:
            query = " ".join(query[:])

        resp, info = ksoft.get_lyrics(query)
        if info["status_code"] == 500:
            await ctx.send("Error fetching result :cry:")
            return

        if info["status_code"] == 404:
            await ctx.send(f"No matching lyrics found :x:\nplease provide more info `{self.prefix} lyrics <artist - song name>`")
            return

        if not resp["data"]:
            await ctx.send("Error fetching response :x:")
            return

        top_result = resp["data"][0]
        song = f"{top_result['artist']} - {top_result['name']}"
        lyrics = top_result["lyrics"]
        if len(lyrics) > 2048:
            lyrics = f"{lyrics[:2040]} ..."

        embed = discord.Embed(title=song, description=lyrics)
        embed.set_footer(text="Lyrics provided by KSoft.Si")
        await ctx.send(embed=embed)
