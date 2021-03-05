import asyncio
import discord
import functools

from discord.ext import commands
from concurrent.futures import ThreadPoolExecutor
from tabulate import tabulate

from .utils import (
    chunk_list, get_page, Playing, Stations, run_sys_info,
    run_speedtest, run_ping, split_to_list
)
from .static import (
    RADIO_ID_LOGO_URL, BOT_NAME, BOT_DESC, BOT_GITHUB_URL,
    BOT_TOP_GG_URL, BOT_DBL_URL, BOT_SUPPORT_SERVER_INV,
    AUTHOR_NAME, AUTHOR_TWITTER_URL, AUTHOR_ICON_URL,
    SAWERIA_URL, DONATE_IMAGE_URL, PAYPAL_URL
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
    async def _np(self, ctx, details=None):
        """
        List of server playing radio and the station
        """

        playing = Playing()

        await ctx.send(f"Playing on {playing.get_play_count()} servers")

        if details == "list":
            all_play = playing.get_all_play().copy()
            for _, np in all_play.items():
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
        embed.add_field(name="Donasi", value=f"[Saweria]({SAWERIA_URL}), [Paypal]({PAYPAL_URL})", inline=False)
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
    async def _donate(self, ctx):
        """
        Link donasi untuk pengembangan bot ini
        """

        embed = discord.Embed(
            title="Donasi",
            description="Dukung pengembangan dan biaya hosting bot ini dengan cara berdonasi melalui saweria atau paypal",
            color=0x9395a5
        )
        embed.add_field(name="Saweria", value=f"[{SAWERIA_URL}]({SAWERIA_URL})", inline=False)
        embed.add_field(name="Paypal", value=f"[{PAYPAL_URL}]({PAYPAL_URL})", inline=False)
        embed.set_thumbnail(url=DONATE_IMAGE_URL)
        embed.set_footer(text="radio-id")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command("station-check")
    async def _check_url(self, ctx):
        """
        Periksa URL stream stasiun radio
        """

        init_msg = await ctx.send("Memeriksa stasiun radio ...")

        station = Stations()
        s_dict = station.stations
        for idx, (station_name, station_attr) in enumerate(s_dict.items()):
            await init_msg.edit(content=f"Memeriksa stasiun radio ({idx + 1}/{len(s_dict)})")
            url = station_attr["url"]
            stat = station.check_station_url(url)
            station.stations[station_name]["status"] = stat
        stations_dict = station.get_stations()

        # String fomatting
        stations_fmt = ""
        for station_name, station_attr in stations_dict.items():
            mark = "✅" if station_attr["status"] == 200 else "❌"
            stations_fmt += f"• Status for {station_name} is `{station_attr['status']}` {mark}\n"

        await ctx.send(f"Station url info: ```{stations_fmt}```")

    @commands.is_owner()
    @commands.command("htop", hidden=True)
    async def _htop(self, ctx):
        """
        Get host machine name, cpu, cpu usage, ram and ram usage
        """

        init_msg = await ctx.send("Getting info from machine ...")
        loop = asyncio.get_event_loop()
        s_info = await loop.run_in_executor(ThreadPoolExecutor(), run_sys_info)
        await init_msg.edit(content=f"```{s_info}```")

    @commands.is_owner()
    @commands.command("speedtest", hidden=True)
    async def _speedtest(self, ctx):
        """
        Run speedtest command on host machine
        """
        init_msg = await ctx.send("Running speedtest ...")
        loop = asyncio.get_event_loop()
        s_test = await loop.run_in_executor(ThreadPoolExecutor(), run_speedtest)
        await init_msg.edit(content=f"```{s_test}```")

    @commands.is_owner()
    @commands.command("ping-to", hidden=True)
    async def _ping_to(self, ctx, host, times):
        """
        Run ping command on host machine to custom host
        """

        try:
            times = int(times)
        except ValueError:
            await ctx.send("Fix your ping command, eg: ping google.com 4")
            return

        if times > 50:
            times = 50

        await ctx.send(f"Start pinging to {host} {times} times ...")
        loop = asyncio.get_event_loop()
        s_ping = await loop.run_in_executor(ThreadPoolExecutor(), functools.partial(run_ping, host, times))
        s_ping = split_to_list(s_ping, 1990)
        for m in s_ping:
            await ctx.send(f"```{m}```")
