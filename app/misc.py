import discord

from discord.ext import commands


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

        await ctx.send(f"Added by {len(self.bot.guilds)} servers")

        total_member = 0
        guild_list_msg = "List of servers:\n"
        for guild in self.bot.guilds:
            guild_list_msg += f"• {guild.name} ({guild.member_count} members)\n"
            total_member += guild.member_count

        await ctx.send(f"{guild_list_msg}\n")
        await ctx.send(f"Total members: {total_member}")

        # await ctx.send("==" * 30)
        # print(f"NP {NOW_PLAYING}")
        # for _, np in NOW_PLAYING.items():
        #     await ctx.send(f"Now playing {np['station']} on {np['guild_name']}\n")
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
