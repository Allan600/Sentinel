import discord
from discord.ext import commands
from core.notify import notify_user

BASE_KICK_LIMIT = 5


class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")  # ✅ lowercase
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str):
        engine = self.bot.trust_engine
        logger = self.bot.mod_logger
        user = ctx.author

        trust_before = engine.get_trust(user.id, "moderation")
        limit = max(1, int(BASE_KICK_LIMIT * (trust_before / 100)))
        count = engine.record(user.id, "kick")

        if count > limit:
            engine.penalize(user.id, "moderation", 10)
            trust_after = engine.get_trust(user.id, "moderation")
            level = engine.escalation_level(user.id)

            await notify_user(
                bot=self.bot,
                guild=ctx.guild,
                member=member,
                action="kick blocked",
                reason=reason,
                actor_trust_before=trust_before,
                actor_trust_after=trust_after,
                escalation_level=level
            )

            await logger.log(
                ctx.guild,
                "KICK BLOCKED",
                user,
                str(member),
                reason,
                trust_before,
                trust_after,
                level
            )

            await ctx.send("🚨 Kick blocked due to abuse limits.")
            return

        await notify_user(
            bot=self.bot,
            guild=ctx.guild,
            member=member,
            action="kicked",
            reason=reason,
            actor_trust_before=trust_before
        )

        await member.kick(reason=f"{reason} | by moderation system")

        engine.reward(user.id, "moderation", 1)
        trust_after = engine.get_trust(user.id, "moderation")

        await logger.log(
            ctx.guild,
            "KICK",
            user,
            str(member),
            reason,
            trust_before,
            trust_after
        )

        await ctx.send(f"✅ {member} kicked.")
