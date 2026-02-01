import discord
from discord.ext import commands
from datetime import datetime
import asyncio

LOG_CHANNEL_ID = 1466641783105785886


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="purge")
    async def purge(self, ctx: commands.Context, amount: int):
        # 🔇 Silent permission check
        if not ctx.author.guild_permissions.manage_messages:
            return

        if amount < 1 or amount > 100:
            return

        # 🧹 Delete command message FIRST
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        # ⏱️ Small yield to avoid race condition
        await asyncio.sleep(0.1)

        try:
            deleted = await ctx.channel.purge(
                limit=amount,
                bulk=True
            )
        except (discord.Forbidden, discord.HTTPException):
            return

        # ✅ SINGLE, CORRECT RESPONSE
        msg = await ctx.channel.send(
            f"🧹 Deleted **{len(deleted)}** messages."
        )

        # Auto-delete confirmation
        await asyncio.sleep(3)
        try:
            await msg.delete()
        except discord.Forbidden:
            pass

        # 🧾 Log async (optional)
        asyncio.create_task(
            self._log_purge(
                ctx.guild,
                ctx.author,
                ctx.channel,
                len(deleted)
            )
        )

    async def _log_purge(self, guild, moderator, channel, count):
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            return

        embed = discord.Embed(
            title="🧹 Purge Executed",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Moderator", value=str(moderator), inline=False)
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Deleted", value=str(count), inline=True)

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass
