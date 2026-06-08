import datetime
import os
import pytz
from discord.ext import tasks

from db import queries

CHICAGO_TZ = pytz.timezone("America/Chicago")

_MIDNIGHT = datetime.time(hour=0, minute=0, tzinfo=CHICAGO_TZ)
_MORNING = datetime.time(hour=11, minute=0, tzinfo=CHICAGO_TZ)


@tasks.loop(time=_MIDNIGHT)
async def weekly_reset(pool):
    now = datetime.datetime.now(CHICAGO_TZ)
    if now.weekday() == 0:  # Monday
        await queries.reset_weekly_xp(pool)
        print(f"[scheduler] Weekly XP reset at {now.isoformat()}")


@tasks.loop(time=_MIDNIGHT)
async def monthly_reset(pool):
    now = datetime.datetime.now(CHICAGO_TZ)
    if now.day == 1:
        await queries.reset_monthly_xp(pool)
        print(f"[scheduler] Monthly XP reset at {now.isoformat()}")


@tasks.loop(time=_MORNING)
async def morning_reminder(bot):
    channel_id = int(os.environ.get("REMINDER_CHANNEL_ID", 0))
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(
            "🌅 Good morning! Time to get moving — log your workout with `/checkin`! 💪"
        )


def start_schedulers(pool, bot) -> None:
    weekly_reset.start(pool)
    monthly_reset.start(pool)
    morning_reminder.start(bot)
