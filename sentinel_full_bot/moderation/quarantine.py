import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os

# 🔴 MUST MATCH main.py
GUILD_ID = 969259122409218118
OWNER_ID = 814466767598256150

LOG_CHANNEL_ID = 1466641783105785886

QUARANTINE_ROLE_NAME = "Quarantined"
NOTICE_CHANNEL_NAME = "server-quarantine"

# 📁 Stable data directory (absolute)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def snapshot_path(guild_id: int) -> str:
    return os.path.join(DATA_DIR, f"quarantine_{guild_id}.json")


def is_owner(user: discord.User) -> bool:
    return user.id == OWNER_ID


class Quarantine(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ======================================================
    # 🔒 QUARANTINE
    # ======================================================
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="quarantine",
        description="OWNER ONLY: Remove all roles and quarantine the server"
    )
    @app_commands.describe(reason="Reason for quarantine")
    async def quarantine(self, interaction: discord.Interaction, reason: str):
        if not is_owner(interaction.user):
            await interaction.response.send_message(
                "❌ Owner only command.",
                ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        guild = interaction.guild

        quarantine_role = discord.utils.get(guild.roles, name=QUARANTINE_ROLE_NAME)
        if not quarantine_role:
            await interaction.edit_original_response(
                content=f"❌ Role `{QUARANTINE_ROLE_NAME}` not found."
            )
            return

        # 🧠 Snapshot
        snapshot = {
            "guild_id": guild.id,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "members": {}
        }

        for member in guild.members:
            if member.bot:
                continue

            original_roles = [
                role.id for role in member.roles
                if role != guild.default_role
            ]

            snapshot["members"][str(member.id)] = original_roles

            try:
                await member.edit(
                    roles=[quarantine_role],
                    reason="SERVER QUARANTINE"
                )
            except discord.Forbidden:
                continue

        path = snapshot_path(guild.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

        # 📢 Notice channel (safe)
        notice = discord.utils.get(guild.text_channels, name=NOTICE_CHANNEL_NAME)

        if not notice:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    read_message_history=True,
                    send_messages=False,
                    add_reactions=False
                )
            }

            notice = await guild.create_text_channel(
                name=NOTICE_CHANNEL_NAME,
                overwrites=overwrites,
                reason="Quarantine notice channel"
            )

        embed = discord.Embed(
            title="🚨 Server Quarantined",
            description=(
                "**This server is temporarily locked.**\n\n"
                f"**Reason:** {reason}\n\n"
                "All member roles have been removed.\n"
                "Please wait for restoration by the owner."
            ),
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Sentinel Security System")

        await notice.send(embed=embed)

        # 📜 Log + upload JSON
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                content="📦 **Quarantine snapshot created**",
                file=discord.File(
                    path,
                    filename=f"quarantine_{guild.id}.json"
                )
            )

        await interaction.edit_original_response(
            content="🚨 **Server quarantined successfully.**"
        )

    # ======================================================
    # 🔓 RESTORE
    # ======================================================
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="restore",
        description="OWNER ONLY: Restore server from quarantine"
    )
    async def restore(self, interaction: discord.Interaction):
        if not is_owner(interaction.user):
            await interaction.response.send_message(
                "❌ Owner only command.",
                ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        path = snapshot_path(guild.id)

        if not os.path.exists(path):
            await interaction.edit_original_response(
                content="❌ No quarantine snapshot found."
            )
            return

        with open(path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        for member_id, role_ids in snapshot["members"].items():
            member = guild.get_member(int(member_id))
            if not member:
                continue

            roles = [
                guild.get_role(rid)
                for rid in role_ids
                if guild.get_role(rid)
            ]

            try:
                await member.edit(
                    roles=roles,
                    reason="QUARANTINE RESTORE"
                )
            except discord.Forbidden:
                continue

        # 🧹 Remove notice channel
        notice = discord.utils.get(guild.text_channels, name=NOTICE_CHANNEL_NAME)
        if notice:
            try:
                await notice.delete(reason="Quarantine restored")
            except discord.Forbidden:
                pass

        os.remove(path)

        # 📜 Log restore
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send("✅ **Server restored from quarantine**")

        await interaction.edit_original_response(
            content="✅ **Server fully restored. All roles reassigned.**"
        )
