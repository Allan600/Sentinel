from typing import List
import asyncio
import discord
from discord.app_commands.models import AppCommand
from discord.ext import commands

from config import TOKEN
from database.db import connect

# moderation / core cogs
from moderation.purge import Purge
from moderation.spam import SpamHandler
from moderation.lockdown import Lockdown
from moderation.history import History
from moderation.quarantine import Quarantine
from moderation.ban import Ban
from moderation.kick import Kick
from core.restart import Restart    

from core.ping_test import PingTest
from core.eval_prefix import EvalPrefix

# 🔥 AI audit / permission manager
from moderation.ai_manage import AIManage


# 🔴 MUST MATCH ALL COMMAND FILES
GUILD_ID = 969259122409218118


# ⚡ WINDOWS EVENT LOOP FIX (VERY IMPORTANT)
asyncio.set_event_loop_policy(
    asyncio.WindowsSelectorEventLoopPolicy()
)


# ⚡ LOW-LATENCY INTENTS
intents = discord.Intents(
    guilds=True,
    members=True,
    messages=True,
    message_content=True,
    moderation=True
)


class SentinelBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

        # one spam handler instance
        self.spam_handler = SpamHandler()

        # AI audit state (used by !ai_apply)
        self.last_ai_plan = None

    async def setup_hook(self):
        # Database (safe startup)
        try:
            await connect()
        except Exception as e:
            print("DB skipped:", e)

        # Load cogs (ONCE)
        await self.add_cog(Lockdown(self))
        await self.add_cog(Purge(self))
        await self.add_cog(History(self))
        await self.add_cog(Quarantine(self))
        await self.add_cog(EvalPrefix(self))
        await self.add_cog(PingTest(self))
        await self.add_cog(Kick(self))
        await self.add_cog(Ban(self))
        await self.add_cog(Restart(self))   

        # 🔥 AI permission auditor
        await self.add_cog(AIManage(self))

    async def on_ready(self):
        print(f"🛡️ Sentinel online as {self.user}")

        # Guild slash sync
        guild = discord.Object(id=GUILD_ID)
        synced: List[AppCommand] = await self.tree.sync(guild=guild)

        print("⚡ Guild slash commands synced successfully:")
        for cmd in synced:
            print(f"  • /{cmd.name}")

    async def on_message(self, message: discord.Message):
        # ultra-fast exit
        if message.author.bot or not message.guild:
            return

        await self.spam_handler.handle_message(message)
        await self.process_commands(message)


# Run bot
bot = SentinelBot()
bot.run(TOKEN)
