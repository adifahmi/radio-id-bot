import asyncio
import discord

from discord.ext import commands
from tabulate import tabulate

from .utils import chunk_list, get_page, Playing, Stations, get_sys_info, get_speedtest
from .static import (
    RADIO_ID_LOGO_URL, BOT_NAME, BOT_DESC, BOT_GITHUB_URL,
    BOT_TOP_GG_URL, BOT_DBL_URL, BOT_SUPPORT_SERVER_INV,
    AUTHOR_NAME, AUTHOR_TWITTER_URL, AUTHOR_ICON_URL,
    SAWERIA_URL, SAWERIA_LOGO_URL
)


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

        if total_page > 1:
            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=8.0)
                    # skip self bot reaction
                    if user.bot is True:
                        continue
                    await msg.clear_reactions()
                    current_page = get_page(current_page, reaction)
                    await msg.edit(content=f"{guild_table[current_page]} Page {current_page} of {total_page}")
                    await self.page_reaction(msg, total_page, current_page)
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

        playing = Playing()

        await ctx.send(f"Playing on {playing.get_play_count()} servers: ")
        for _, np in playing.get_all_play().items():
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
            title=BOT_NAME,
            url=BOT_GITHUB_URL,
            description=BOT_DESC,
            color=0x9395a5
        )
        embed.set_author(
            name=AUTHOR_NAME,
            url=AUTHOR_TWITTER_URL,
            icon_url=AUTHOR_ICON_URL
        )
        embed.set_thumbnail(url=RADIO_ID_LOGO_URL)

        embed.add_field(name="Open source code", value=f"[Github]({BOT_GITHUB_URL})", inline=False)
        embed.add_field(name="Donasi", value=f"[Saweria]({SAWERIA_URL})", inline=False)
        embed.add_field(name="Vote this bot", value=f"[top.gg]({BOT_TOP_GG_URL}), [DBL]({BOT_DBL_URL})", inline=False)
        embed.add_field(name="Support server", value=f"[AF Home]({BOT_SUPPORT_SERVER_INV})", inline=False)
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)

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

    @commands.command("donate")
    async def _donasi(self, ctx):
        """
        Link donasi untuk pengembangan bot ini
        """

        embed = discord.Embed(
            title="Saweria",
            url=SAWERIA_URL,
            description="Dukung pengembangan bot ini dengan cara berdonasi melalui saweria",
            color=0x9395a5
        )
        embed.set_thumbnail(url=SAWERIA_LOGO_URL)
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command("station-check")
    async def _check_url(self, ctx):
        """
        Periksa URL stream stasiun radio
        """

        await ctx.send("Memeriksa stasiun radio ...")

        station = Stations()
        station.update_station_status()
        stations_dict = station.get_stations()

        # String fomatting
        stations_fmt = ""
        for station_name, station_attr in stations_dict.items():
            mark = ":white_check_mark:" if station_attr["status"] == 200 else ":x:"
            stations_fmt += f"• Status for {station_name} is `{station_attr['status']}` {mark}\n"

        await ctx.send(stations_fmt)

    @commands.is_owner()
    @commands.command("htop")
    async def _htop(self, ctx):
        """
        Check machine of hosted bot information
        """

        init_msg = await ctx.send("Getting info from machine ...")
        await init_msg.edit(content=f"```{get_sys_info()}```")

    @commands.is_owner()
    @commands.command("speedtest")
    async def _speedtest(self, ctx):
        """
        Run speedtest command on host machine
        """

        init_msg = await ctx.send("Running long task ...")
        await init_msg.edit(content=f"```{get_speedtest()}```")
