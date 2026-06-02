import datetime
import pytz
from discord.ext import tasks

from db import queries

CHICAGO_TZ = pytz.timezone("America/Chicago")

# Midnight Chicago time
_MIDNIGHT = datetime.time(hour=0, minute=0, tzinfo=CHICAGO_TZ)


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


def start_schedulers(pool) -> None:
    weekly_reset.start(pool)
    monthly_reset.start(pool)
