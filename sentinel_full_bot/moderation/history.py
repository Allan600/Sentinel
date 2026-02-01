import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from utils.modlog import get_history

GUILD_ID = 969259122409218118


class History(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="history",
        description="View moderation history of a user"
    )
    async def history(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ Moderator permission required.",
                ephemeral=True
            )
            return

        records = get_history(user.id)

        if not records:
            await interaction.response.send_message(
                f"ℹ️ No moderation history for {user.mention}.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📜 Moderation History — {user}",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )

        for entry in records[-10:]:  # show last 10
            time = entry["timestamp"].strftime("%Y-%m-%d %H:%M")
            embed.add_field(
                name=f"{entry['action']} • {time}",
                value=(
                    f"**Moderator:** {entry['moderator']}\n"
                    f"**Reason:** {entry['reason']}"
                ),
                inline=False
            )

        embed.set_footer(text="Sentinel Mod History")

        await interaction.response.send_message(embed=embed, ephemeral=True)
