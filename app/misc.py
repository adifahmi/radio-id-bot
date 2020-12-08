import discord

from discord.ext import commands
from tabulate import tabulate

from .player import NOW_PLAYING
from .utils import chunk_list


class Misc(commands.Cog):
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
        total_guild = len(self.bot.guilds)
        await ctx.send(f"Added by {total_guild} servers")

        chunk_guild = chunk_list(self.bot.guilds, total_guild / 20)

        await ctx.send("List of servers:")
        total_member = 0
        num = 1
        for guilds in chunk_guild:
            guild_list = []
            for guild in guilds:
                guild_list.append([num, guild.name, guild.member_count])
                total_member += guild.member_count
                num += 1
            await ctx.send(f'```{tabulate(guild_list, tablefmt="fancy_grid")}```')

        await ctx.send(f"Total members: {total_member}")
        return

    @commands.is_owner()
    @commands.command("np", hidden=True)
    async def _np(self, ctx):
        """
        List of server playing radio and the station
        """
        await ctx.send(f"Playing on {len(NOW_PLAYING)} servers: ")
        for _, np in NOW_PLAYING.items():
            await ctx.send(f"• Playing **{np['station']}** on **{np['guild_name']}**\n")
        return

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
