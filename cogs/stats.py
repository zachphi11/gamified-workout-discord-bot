import discord
from discord.ext import commands
from datetime import timezone

from db import queries
from utils.levels import get_level, LEVEL_THRESHOLDS


def build_progress_bar(current: int, target: int, width: int = 10) -> str:
    if target == 0:
        filled = width
    else:
        filled = min(width, int(width * current / target))
    return "█" * filled + "░" * (width - filled)


class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="stats", description="View your workout stats (or another user's)")
    @discord.app_commands.describe(user="The user to look up (defaults to you)")
    async def stats(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        user_id = str(target.id)

        row = await queries.get_user(self.bot.pool, user_id)
        if row is None:
            await interaction.response.send_message(
                f"{target.display_name} hasn't checked in yet. Time to start! 💪",
                ephemeral=True,
            )
            return

        total_xp = row["total_xp"]
        level = get_level(total_xp)
        streak = row["streak"]

        if level >= 10:
            xp_to_next = "MAX"
            bar = build_progress_bar(1, 1)
        else:
            next_threshold = LEVEL_THRESHOLDS[level]
            current_threshold = LEVEL_THRESHOLDS[level - 1]
            xp_in_level = total_xp - current_threshold
            xp_needed = next_threshold - current_threshold
            bar = build_progress_bar(xp_in_level, xp_needed)
            xp_to_next = str(next_threshold - total_xp)

        recent = await queries.get_recent_checkins(self.bot.pool, user_id, limit=7)

        embed = discord.Embed(
            title=f"{target.display_name}'s Stats",
            color=discord.Color.blurple(),
        )
        gold = row["gold"]
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Total XP", value=str(total_xp), inline=True)
        embed.add_field(name="Streak", value=f"{streak} day{'s' if streak != 1 else ''}", inline=True)
        embed.add_field(name="Gold", value=f"{gold}g 💰", inline=True)
        embed.add_field(
            name="Progress to Next Level",
            value=f"`{bar}` {xp_to_next} XP to go" if xp_to_next != "MAX" else f"`{bar}` MAX LEVEL",
            inline=False,
        )

        if recent:
            history_lines = []
            for r in recent:
                dt = r["checked_in_at"].astimezone(timezone.utc)
                history_lines.append(f"• {dt.strftime('%b %d')} — {r['workout']}")
            embed.add_field(name="Last 7 Workouts", value="\n".join(history_lines), inline=False)
        else:
            embed.add_field(name="Last 7 Workouts", value="No workouts yet", inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
