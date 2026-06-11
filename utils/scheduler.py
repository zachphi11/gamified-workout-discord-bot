import datetime
import os
from zoneinfo import ZoneInfo
from discord.ext import tasks

from db import queries

CHICAGO_TZ = ZoneInfo("America/Chicago")

_MIDNIGHT = datetime.time(hour=0, minute=0, tzinfo=CHICAGO_TZ)
_AFTERNOON = datetime.time(hour=11, minute=0, tzinfo=CHICAGO_TZ)


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


@tasks.loop(time=_AFTERNOON)
async def morning_reminder(bot):
    channel_id = int(os.environ.get("REMINDER_CHANNEL_ID", 0))
    if not channel_id:
        print("[scheduler] REMINDER_CHANNEL_ID not set")
        return
    try:
        channel = await bot.fetch_channel(channel_id)
    except Exception as e:
        print(f"[scheduler] Could not fetch channel {channel_id}: {e}")
        return
    role_id = int(os.environ.get("REMINDER_ROLE_ID", 0))
    mention = f"<@&{role_id}> " if role_id else ""
    await channel.send(
        f"{mention}🌅 Good morning! Time to get moving — log your workout with `/checkin`! 💪"
    )
    print(f"[scheduler] morning_reminder sent at {datetime.datetime.now(CHICAGO_TZ).isoformat()}")


@morning_reminder.error
async def on_morning_reminder_error(error):
    print(f"[scheduler] morning_reminder error: {error}")


def start_schedulers(pool, bot) -> None:
    weekly_reset.start(pool)
    monthly_reset.start(pool)
    morning_reminder.start(bot)
