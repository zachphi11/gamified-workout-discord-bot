import discord
from discord.ext import commands
from datetime import datetime
import pytz

from db import queries
from utils.levels import get_level, LEVEL_THRESHOLDS
from utils.streak import compute_new_streak
from utils.hype import get_hype
from utils.shop import compute_gold_earned, compute_streak_bonus

CHICAGO_TZ = pytz.timezone("America/Chicago")
XP_PER_CHECKIN = 25
STREAK_MILESTONES = {3, 7, 30}


class CheckinCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="checkin", description="Log a workout and earn XP")
    @discord.app_commands.describe(workout="Describe your workout (e.g. 'leg day', 'ran 5k')")
    async def checkin(self, interaction: discord.Interaction, workout: str):
        today = datetime.now(CHICAGO_TZ).date()
        user_id = str(interaction.user.id)
        username = interaction.user.display_name

        existing = await queries.get_user(self.bot.pool, user_id)
        old_xp = existing["total_xp"] if existing else 0
        old_streak = existing["streak"] if existing else 0
        last_checkin = existing["last_checkin"] if existing else None

        if last_checkin == today:
            await interaction.response.send_message(
                "You already checked in today! Come back tomorrow. 💤",
                ephemeral=True,
            )
            return

        new_streak = compute_new_streak(last_checkin, old_streak, today)

        equipped_items = await queries.get_equipped_items(self.bot.pool, user_id)
        gold_earned = compute_gold_earned([dict(item) for item in equipped_items]) + compute_streak_bonus(new_streak)

        logged = await queries.log_checkin(
            self.bot.pool, user_id, username, workout, XP_PER_CHECKIN, new_streak, today,
            gold_earned=gold_earned,
        )

        if not logged:
            await interaction.response.send_message(
                "You already checked in today! Come back tomorrow. 💤",
                ephemeral=True,
            )
            return

        new_xp = old_xp + XP_PER_CHECKIN
        old_level = get_level(old_xp)
        new_level = get_level(new_xp)

        hype = get_hype()
        lines = [
            f"**{username}** checked in: *{workout}* · +{XP_PER_CHECKIN} XP 🏋️ · +{gold_earned}g 💰",
            f"Streak: {new_streak} day{'s' if new_streak != 1 else ''} | Level {new_level} | Total XP: {new_xp}",
            "",
            hype["text"],
        ]
        if "gif_url" in hype:
            lines.append(hype["gif_url"])

        await interaction.response.send_message("\n".join(lines))

        if new_level > old_level:
            await interaction.followup.send(
                f"🎉 **LEVEL UP!** {username} reached **Level {new_level}**! Keep grinding! 🚀"
            )

        if new_streak in STREAK_MILESTONES:
            await interaction.followup.send(
                f"🔥 **STREAK MILESTONE!** {username} has hit a **{new_streak}-day streak!** Unstoppable! 🔥"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(CheckinCog(bot))
