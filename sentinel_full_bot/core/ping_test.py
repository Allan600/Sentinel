import discord
from discord.ext import commands
import platform

class PingTest(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green(),
            description=(
                f"**Gateway:** {round(self.bot.latency * 1000)} ms\n"
                f"**Python:** {platform.python_version()}\n"
                f"**discord.py:** {discord.__version__}"
            )
        )

        await ctx.send(embed=embed)
