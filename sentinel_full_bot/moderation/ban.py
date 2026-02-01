import discord
from discord.ext import commands
from core.notify import notify_user

BASE_BAN_LIMIT = 3


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str):
        engine = self.bot.trust_engine
        logger = self.bot.mod_logger
        user = ctx.author

        trust_before = engine.get_trust(user.id, "moderation")
        limit = max(1, int(BASE_BAN_LIMIT * (trust_before / 100)))
        count = engine.record(user.id, "ban")

        if count > limit:
            engine.penalize(user.id, "moderation", 15)
            trust_after = engine.get_trust(user.id, "moderation")
            level = engine.escalation_level(user.id)

            await notify_user(
                bot=self.bot,
                guild=ctx.guild,
                member=member,
                action="ban blocked",
                reason=reason,
                actor_trust_before=trust_before,
                actor_trust_after=trust_after,
                escalation_level=level
            )

            await logger.log(
                ctx.guild,
                "BAN BLOCKED",
                user,
                str(member),
                reason,
                trust_before,
                trust_after,
                level
            )

            await ctx.send("🚨 Ban blocked due to abuse limits.")
            return

        await notify_user(
            bot=self.bot,
            guild=ctx.guild,
            member=member,
            action="banned",
            reason=reason,
            actor_trust_before=trust_before
        )

        await member.ban(reason=f"{reason} | by moderation system")

        engine.reward(user.id, "moderation", 1)
        trust_after = engine.get_trust(user.id, "moderation")

        await logger.log(
            ctx.guild,
            "BAN",
            user,
            str(member),
            reason,
            trust_before,
            trust_after
        )

        await ctx.send(f"✅ {member} banned.")
