import discord
from discord.ext import commands

from db import queries
from utils.levels import get_level


def build_progress_bar(current: int, top: int, width: int = 8) -> str:
    if top == 0:
        filled = 0
    else:
        filled = min(width, int(width * current / top))
    return "█" * filled + "░" * (width - filled)


PERIOD_COLUMNS = {
    "Weekly": "weekly_xp",
    "Monthly": "monthly_xp",
    "All-Time": "total_xp",
}


async def build_leaderboard_embed(pool, period: str) -> discord.Embed:
    col = PERIOD_COLUMNS[period]
    rows = await queries.get_leaderboard(pool, col)

    embed = discord.Embed(title=f"🏆 {period} Leaderboard", color=discord.Color.gold())

    if not rows:
        embed.description = "No check-ins yet. Be the first to grind! 💪"
        return embed

    top_xp = rows[0][col]
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(rows):
        rank = medals[i] if i < 3 else f"**#{i+1}**"
        xp = row[col]
        level = get_level(row["total_xp"])
        bar = build_progress_bar(xp, top_xp)
        lines.append(f"{rank} {row['username']} — Lvl {level} | {xp} XP `{bar}`")

    embed.description = "\n".join(lines)
    return embed


class LeaderboardView(discord.ui.View):
    def __init__(self, pool):
        super().__init__(timeout=60)
        self.pool = pool

    @discord.ui.button(label="Weekly", style=discord.ButtonStyle.primary)
    async def weekly(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await build_leaderboard_embed(self.pool, "Weekly")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Monthly", style=discord.ButtonStyle.primary)
    async def monthly(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await build_leaderboard_embed(self.pool, "Monthly")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="All-Time", style=discord.ButtonStyle.primary)
    async def all_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await build_leaderboard_embed(self.pool, "All-Time")
        await interaction.response.edit_message(embed=embed, view=self)


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="leaderboard", description="View the XP leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        embed = await build_leaderboard_embed(self.bot.pool, "All-Time")
        view = LeaderboardView(self.bot.pool)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
