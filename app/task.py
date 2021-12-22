import asyncio
import topgg
import os
import functools

from concurrent.futures import ThreadPoolExecutor
from discord.ext import commands, tasks
from .static import RADIOID_SERVER_CHANNEL_ID
from .utils import Stations, Playing, GuildInfo, get_emoji_by_number
from .external_api import dbox


class BotTask(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix
        self.token = os.getenv("DBL_TOKEN")  # set this to your DBL token
        self.topggpy = topgg.DBLClient(self.bot, self.token)
        self.post_server_cnt.start()
        self.update_station_stat.start()
        self.whos_playing.start()
        self.post_bot_stats.start()

    @tasks.loop(hours=3)
    async def post_server_cnt(self):
        if os.environ.get("ENVIRONMENT") == "dev":
            print("Task post_server_cnt skipped")
            return

        print("Init task post_server_cnt")

        channel = self.bot.get_channel(RADIOID_SERVER_CHANNEL_ID)

        try:
            await self.topggpy.post_guild_count()
            await channel.send(f"Bot added by: {get_emoji_by_number(self.topggpy.guild_count)} servers")
        except Exception as e:
            await channel.send(f"Failed to update bot server count\n```{e}```")

    @post_server_cnt.before_loop
    async def before_post_server_cnt(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=50)
    async def update_station_stat(self):
        if os.environ.get("ENVIRONMENT") == "dev":
            print("Task update_station_stat skipped")
            return

        print("Init task update_station_stat")

        channel = self.bot.get_channel(RADIOID_SERVER_CHANNEL_ID)

        station = Stations()
        loop = asyncio.get_event_loop()
        stat_info_dict = await loop.run_in_executor(ThreadPoolExecutor(), station.update_station_status)
        stats_fmt = ""
        for k, v in stat_info_dict.items():
            stats_fmt += f"• {k}: {v}\n"
        await channel.send(f"URL radio stream status:\n```{stats_fmt}```")

    @update_station_stat.before_loop
    async def before_update_station_stat(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=55)
    async def whos_playing(self):
        if os.environ.get("ENVIRONMENT") == "dev":
            print("Task whos_playing skipped")
            return

        print("Init task whos_playing skipped")

        channel = self.bot.get_channel(RADIOID_SERVER_CHANNEL_ID)
        playing = Playing()

        playing_fmt = ""
        all_play = playing.get_all_play().copy()
        for _, v in all_play.items():
            playing_fmt += f"• {v['guild_name']}: {v['station']}\n"

        if playing_fmt == "":
            playing_fmt = "🕸️"

        await channel.send(f"Playing on {get_emoji_by_number(playing.get_play_count())} servers:\n```{playing_fmt}```")

    @whos_playing.before_loop
    async def before_whos_playing(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=25)
    async def post_bot_stats(self):
        if os.environ.get("ENVIRONMENT") == "dev":
            print("Task post_bot_stats skipped")
            return

        print("Init task post_bot_stats")

        channel = self.bot.get_channel(RADIOID_SERVER_CHANNEL_ID)

        loop = asyncio.get_event_loop()
        gi = GuildInfo(self.bot.guilds)

        await channel.send("Uploading summary stats to dropbox ...")
        file, filename = await loop.run_in_executor(ThreadPoolExecutor(), functools.partial(gi.generate_report_csv, ""))
        ul, ul_info = dbox.upload_file(file, filename)
        if ul_info['status_code'] != 200:
            await channel.send(f"Failed to upload ```{str(ul_info['error'])}```")
            return
        await channel.send(f"Summary stats uploaded at `{ul.get('path_display')}`")

        await channel.send("Uploading details stats to dropbox ...")
        file, filename = await loop.run_in_executor(ThreadPoolExecutor(), functools.partial(gi.generate_report_csv, "details"))
        ul, ul_info = dbox.upload_file(file, filename)
        if ul_info['status_code'] != 200:
            await channel.send(f"Failed to upload ```{str(ul_info['error'])}```")
            return
        await channel.send(f"Details stats uploaded at `{ul.get('path_display')}`")

    @post_bot_stats.before_loop
    async def before_post_bot_stats(self):
        await self.bot.wait_until_ready()
