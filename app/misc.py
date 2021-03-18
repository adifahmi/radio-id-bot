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
    create_tempfile
)
from .external_api import dbox


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
        total_guild = len(guild_obj)

        # prepare csv
        await ctx.send("Preparing data ...")

        csv_guilds = ""
        total_member = 0
        num = 1
        for guild in guild_obj:
            csv_guilds += f'{num},"{guild.name}",{guild.member_count},{guild.id}\n'
            total_member += guild.member_count
            num += 1

        csv_report = f"Added by {total_guild} servers\n"
        csv_report += f"Total members: {total_member}\n\n"

        csv_report += "id,name,member_cnt,guild_id\n"
        csv_report += csv_guilds

        now = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
        file = create_tempfile(csv_report)
        env = os.environ.get("ENVIRONMENT")
        filename = f"RadioID_{env}_{now}.csv"

        await ctx.send("Uploading stats to dropbox")
        ul, ul_info = dbox.upload_file(file, filename)
        if ul_info['status_code'] != 200:
            await ctx.send(f"Failed to upload ```{str(ul_info['error'])}```")
            return
        await ctx.send(f"File uploaded at `{ul.get('path_display')}`")

        if params == "with link":
            await ctx.send("Generating link ...")
            gl, gl_info = dbox.create_share_link(ul.get('path_display'))
            if gl_info['status_code'] != 200:
                await ctx.send(f"Failed to get download link ```{str(gl_info['error'])}```")
            else:
                await ctx.send(f"Download link: {gl.get('url')}")

        return
