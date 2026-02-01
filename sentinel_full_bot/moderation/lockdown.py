import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Literal

# 🔴 MUST MATCH main.py EXACTLY
GUILD_ID = 969259122409218118

class Lockdown(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="lockdown",
        description="Lock or unlock the server with a reason"
    )
    @app_commands.describe(
        mode="on = lock server, off = unlock server",
        reason="Reason for lockdown or unlock"
    )
    async def Lockdown(
        self,
        interaction: discord.Interaction,
        mode: Literal["on", "off"],
        reason: str
    ):

        guild = interaction.guild
        await interaction.response.defer(thinking=True)

        # 🔒 Lock / unlock all text channels
        for channel in guild.text_channels:
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.send_messages = False if mode == "on" else None

                await channel.set_permissions(
                    guild.default_role,
                    overwrite=overwrite,
                    reason=f"Lockdown {mode.upper()} by {interaction.user} | {reason}"
                )
            except discord.Forbidden:
                continue

        # 📢 Embed announcement
        embed = discord.Embed(
            title="🔒 SERVER LOCKDOWN" if mode == "on" else "🔓 LOCKDOWN LIFTED",
            color=discord.Color.red() if mode == "on" else discord.Color.green(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="Action", value=mode.upper(), inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="Sentinel Security System")

        # Send to #general if exists, else current channel
        general = discord.utils.get(guild.text_channels, name="general")
        await (general or interaction.channel).send(embed=embed)

        # 🖨️ Console log (DB-ready)
        print(
            f"[LOCKDOWN] {guild.name} | "
            f"{mode.upper()} | "
            f"By: {interaction.user} | "
            f"Reason: {reason}"
        )

        await interaction.followup.send(
            "✅ Lockdown command executed.",
            ephemeral=True
        )
