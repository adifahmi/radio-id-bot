import asyncio
import discord
import functools
import os
import datetime

from discord.ext import commands
from concurrent.futures import ThreadPoolExecutor
from tabulate import tabulate

from .utils import (
    chunk_list, get_page, Playing, run_sys_info,
    run_speedtest, run_ping, split_to_list, run_cmd,
    Stations, GuildInfo
)
from .external_api import dbox
from database import db_manager


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

        guild_obj = self.bot.guilds
        total_guild = len(guild_obj)
        chunk_guild = chunk_list(guild_obj, total_guild / 15)

        await ctx.send(f"Added by {total_guild} servers")
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

    @commands.is_owner()
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
        return

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

    @commands.is_owner()
    @commands.command("cmd", hidden=True)
    async def _cmd(self, ctx, *cmd_input):
        """
        Run custom command on host machine
        """

        if not cmd_input:
            await ctx.send("Empty cmd")
        cmd_input = " ".join(cmd_input[:])

        await ctx.send(f"Running `{cmd_input}` ...")
        loop = asyncio.get_event_loop()
        _, r_cmd = await loop.run_in_executor(ThreadPoolExecutor(), functools.partial(run_cmd, cmd_input))
        s_r_cmd = split_to_list(r_cmd, 1990)
        for m in s_r_cmd:
            await ctx.send(f"```{m}```")

    @commands.is_owner()
    @commands.command("upload_stats", hidden=True)
    async def _upload_stats(self, ctx, *params):
        """
        Show some stats of this bot (owner only)
        """

        if params is not None:
            params = " ".join(params[:])

        guild_obj = self.bot.guilds

        # prepare csv
        await ctx.send("Preparing data ...")
        gi = GuildInfo(guild_obj)
        file, filename = gi.generate_report_csv(params)

        await ctx.send("Uploading stats to dropbox")
        ul, ul_info = dbox.upload_file(file, filename)
        if ul_info['status_code'] != 200:
            await ctx.send(f"Failed to upload ```{str(ul_info['error'])}```")
            return
        await ctx.send(f"File uploaded at `{ul.get('path_display')}`")

        if "link" in params:
            await ctx.send("Generating link ...")
            gl, gl_info = dbox.create_share_link(ul.get('path_display'))
            if gl_info['status_code'] != 200:
                await ctx.send(f"Failed to get download link ```{str(gl_info['error'])}```")
            else:
                await ctx.send(f"Download link: {gl.get('url')}")

        return

    @commands.is_owner()
    @commands.command("save_db", hidden=True)
    async def _save_stats_db(self, ctx, *params):
        await ctx.send("Saving stats to sqlite ...")

        saved_to = 'database/guild.db'
        db = db_manager.DBase(saved_to)
        db.migration()

        loop = asyncio.get_event_loop()
        gi = GuildInfo(self.bot.guilds)

        extracted_guild = await loop.run_in_executor(
            ThreadPoolExecutor(),
            functools.partial(gi.extract_guild_obj, "")
        )
        fields = ",".join(gi.title)
        fields = f'({fields})'
        values = ""
        for g in extracted_guild.splitlines():
            comma = '' if values == "" else ','
            values += f'{comma}({g})'
        db.insert(
            table="guild",
            fields=fields,
            values=values
        )

        extracted_guild_details = await loop.run_in_executor(
            ThreadPoolExecutor(),
            functools.partial(gi.extract_guild_obj, True)
        )
        fields = ",".join(gi.title_details)
        fields = f'({fields})'
        values = ""
        for g in extracted_guild_details.splitlines():
            comma = '' if values == "" else ','
            values += f'{comma}({g})'
        db.insert(
            table="guild_details",
            fields=fields,
            values=values
        )
        db.close_conn()
        await ctx.send("Stats saved to sqlite ...")

        env = os.environ.get("ENVIRONMENT")
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
        filename = f"{env}/db/guild_{now}.db"

        with open(saved_to, 'rb') as f:
            ul, ul_info = dbox.upload_file(f.read(), filename)
            if ul_info['status_code'] != 200:
                await ctx.send(f"Failed to upload {filename} ```{str(ul_info['error'])}```")
                return
        await ctx.send(f"File uploaded at `{ul.get('path_display')}`")
