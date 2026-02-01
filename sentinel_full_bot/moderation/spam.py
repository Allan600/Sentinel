import discord
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from utils.modlog import log_action


# 🔧 SPAM CONFIG
SPAM_LIMIT = 5           # messages
SPAM_INTERVAL = 5        # seconds
AUTO_PURGE_LIMIT = 20
TIMEOUT_MINUTES = 5

# 🧾 LOG CHANNEL
AUTO_PURGE_LOG_CHANNEL_ID = 1466641783105785886


def is_staff(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return (
        perms.administrator
        or perms.manage_messages
        or perms.ban_members
        or perms.kick_members
        or perms.moderate_members
    )


class SpamHandler:
    def __init__(self):
        # user_id -> deque[timestamps]
        self.user_messages: dict[int, deque[float]] = defaultdict(deque)

    async def handle_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if not isinstance(message.author, discord.Member):
            return

        # 🚫 Ignore staff completely
        if is_staff(message.author):
            return

        now = time.monotonic()  # faster & safer than time.time()
        user_id = message.author.id
        timestamps = self.user_messages[user_id]

        # ⏱️ Remove old timestamps (O(1) amortized)
        while timestamps and now - timestamps[0] > SPAM_INTERVAL:
            timestamps.popleft()

        timestamps.append(now)

        # 🚨 Spam detected
        if len(timestamps) >= SPAM_LIMIT:
            timestamps.clear()
            await self._handle_spam(message)

    async def _handle_spam(self, message: discord.Message):
        guild = message.guild
        channel = message.channel
        member = message.author

        # 🧹 Auto purge
        try:
            deleted = await channel.purge(
                limit=AUTO_PURGE_LIMIT,
                check=lambda m: m.author.id == member.id
            )
        except (discord.Forbidden, discord.HTTPException):
            deleted = []

        # ⏳ Timeout
        try:
            until = discord.utils.utcnow() + timedelta(minutes=TIMEOUT_MINUTES)
            await member.timeout(
                until,
                reason="Automatic spam detection"
            )

            log_action(
                action="AUTO_SPAM",
                target_id=member.id,
                moderator="SYSTEM",
                reason="Automatic spam detection",
                extra={
                    "purged": len(deleted),
                    "timeout_minutes": TIMEOUT_MINUTES,
                    "channel": channel.name
                }
            )

        except (discord.Forbidden, discord.HTTPException):
            pass

        # 📜 Log to channel
        log_channel = guild.get_channel(AUTO_PURGE_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🚨 Auto Spam Action",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="User",
                value=f"{member} ({member.id})",
                inline=False
            )
            embed.add_field(
                name="Channel",
                value=channel.mention,
                inline=True
            )
            embed.add_field(
                name="Messages Purged",
                value=str(len(deleted)),
                inline=True
            )
            embed.add_field(
                name="Timeout",
                value=f"{TIMEOUT_MINUTES} minutes",
                inline=True
            )

            embed.set_footer(text="Sentinel Auto-Moderation")

            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass

        # 🖨️ Console log
        print(
            f"[AUTO-SPAM] {member} | "
            f"Purged {len(deleted)} msgs | "
            f"Timeout {TIMEOUT_MINUTES}m | "
            f"#{channel.name}"
        )
