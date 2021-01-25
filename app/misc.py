import asyncio
import discord
import os

from discord.ext import commands, tasks
from tabulate import tabulate

from .external_api.dbl import post_bot_server_count
from .utils import chunk_list, get_page, get_play_cnt, get_all_play
from .test import check_stream_url

RADIOID_SERVER_CHANNEL_ID = 787685233301782539  # Default channel ID of this bot support server
RADIOID_BOT_ID = 777757482687922198  # This bot ID


class Misc(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix
        self.post_server_cnt.start()

    @commands.is_owner()
    @commands.command("presence", hidden=True)
    async def _change_presence(self, ctx, *status):
        """
        Change status of this bot (owner only)
        """

        if not status:
            status = f"`{self.prefix} help` untuk memulai."
        else:
            status = " ".join(status[:])

        await self.self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status))

        await ctx.send(f"Status changed to:\n{status}")
        return

    async def page_reaction(self, msg, total_page, current_page):
        if total_page == 1:
            return
        if current_page == 1:
            await msg.add_reaction('⏩')
        elif current_page == total_page:
            await msg.add_reaction('⏪')
        else:
            await msg.add_reaction('⏪')
            await msg.add_reaction('⏩')
        return

    @commands.is_owner()
    @commands.command("stats", hidden=True)
    async def _stats(self, ctx):
        """
        Show some stats of this bot (owner only)
        """
        total_guild = len(self.bot.guilds)
        await ctx.send(f"Added by {total_guild} servers")

        chunk_guild = chunk_list(self.bot.guilds, total_guild / 15)

        await ctx.send("List of servers:")
        total_member = 0
        num = 1
        page = 1
        guild_table = {}
        for guilds in chunk_guild:
            guild_list = []
            for guild in guilds:
                guild_list.append([num, guild.name, guild.member_count])
                total_member += guild.member_count
                num += 1
            formatted_guilds = f'```{tabulate(guild_list, tablefmt="fancy_grid")}```'
            guild_table[page] = formatted_guilds
            page += 1

        total_page = len(guild_table)
        current_page = 1

        msg = await ctx.send(f"{guild_table[current_page]} Page {current_page} of {total_page}")
        await self.page_reaction(msg, total_page, current_page)

        await ctx.send(f"Total members: {total_member}")
        await asyncio.sleep(1)

        if total_page > 1:
            while True:
                try:
                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=5.0)
                    await msg.clear_reactions()
                    current_page = get_page(current_page, reaction)
                    await msg.edit(content=f"{guild_table[current_page]} Page {current_page} of {total_page}")
                    await self.page_reaction(msg, total_page, current_page)
                    await asyncio.sleep(1)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    break
                except Exception:
                    await msg.clear_reactions()
                    break

        return

    @commands.is_owner()
    @commands.command("np", hidden=True)
    async def _np(self, ctx):
        """
        List of server playing radio and the station
        """
        await ctx.send(f"Playing on {get_play_cnt()} servers: ")
        for _, np in get_all_play().items():
            await ctx.send(f"• Playing **{np['station']}** on **{np['guild_name']}**\n")
        return

    @commands.guild_only()
    @commands.command("ping")
    async def _ping(self, ctx):
        """
        Latensi bot ke server
        """

        lat = self.bot.latency
        await ctx.send(f"Latensi bot ke server ~{round(lat, 2)} detik")

    @commands.command("about")
    async def _about(self, ctx):
        """
        Deskripsi tentang bot ini
        """

        embed = discord.Embed(
            title="Radio Indonesia",
            url="https://github.com/AdiFahmi/radio-id-bot",
            description="Radio Indonesia adalah discord bot sederhana yang dibuat menggunakan library discord.py \
                untuk memainkan stasiun radio favorit kamu.",
            color=0x9395a5
        )
        embed.set_author(
            name="Created by AF",
            url="https://twitter.com/adifahmii",
            icon_url="https://cdn.discordapp.com/attachments/781466869688827904/802388113615486976/AF.png"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/781466869688827904/800918212816535552/radio-free-license-400.png")

        embed.add_field(name="Open source code", value="[Github](https://github.com/AdiFahmi/radio-id-bot)", inline=False)
        embed.add_field(name="Donasi", value="[Saweria](https://saweria.co/radioid)", inline=False)
        embed.add_field(name="Vote this bot", value="[top.gg](https://top.gg/bot/777757482687922198), [DBL](https://discordbotlist.com/bots/radio-indonesia)", inline=False)
        embed.add_field(name="Support server", value="[AF Home](https://discord.gg/tmY3Jx2THX)", inline=False)
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)

    @commands.command("support")
    async def _support(self, ctx):
        """
        Link ke support server radio-id-bot
        """

        embed = discord.Embed(
            title="AF Home",
            url="https://discord.gg/tmY3Jx2THX",
            description="Join server AF Home untuk memberikan masukan",
            color=0x9395a5
        )
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)

    @commands.command("donate")
    async def _donasi(self, ctx):
        """
        Link donasi untuk pengembangan bot ini
        """

        embed = discord.Embed(
            title="Saweria",
            url="https://saweria.co/radioid",
            description="Dukung pengembangan bot ini dengan cara berdonasi melalui saweria",
            color=0x9395a5
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/781466869688827904/800926776176017429/saweria2.png")
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)

    @tasks.loop(seconds=10800.0)
    async def post_server_cnt(self):
        if os.environ.get("ENVIRONMENT") == "dev":
            return

        channel = self.bot.get_channel(RADIOID_SERVER_CHANNEL_ID)
        total_guild_add = len(self.bot.guilds)
        await channel.send(f"Bot added by: {total_guild_add} servers")
        try:
            res, info = post_bot_server_count(RADIOID_BOT_ID, total_guild_add)
            if res is None:
                await channel.send(f"Failed to update bot server count\n```{info}```")
            else:
                await channel.send(f"Success update bot server count\n```{info}```")
        except Exception as e:
            await channel.send(f"Failed to update bot server count\n```{e}```")

    @post_server_cnt.before_loop
    async def before_post_server_cnt(self):
        await self.bot.wait_until_ready()

    @commands.guild_only()
    @commands.command("url-test")
    async def _check_url(self, ctx):
        """
        Periksa stasiun radio
        """

        await ctx.send("Memeriksa stasiun radio ...")

        stat_msgs, stats = check_stream_url()

        # String fomatting
        fmt_stat_msgs = []
        for msg, code in zip(stat_msgs, stats):
            if code != 200:
                msg += " :x:"
            else:
                msg += " :white_check_mark:"
            fmt_stat_msgs.append(msg)

        stat_msgs_fmt = '\n'.join(fmt_stat_msgs)

        await ctx.send(stat_msgs_fmt)
