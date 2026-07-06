from datetime import date
import asyncpg


async def get_user(pool: asyncpg.Pool, user_id: str) -> asyncpg.Record | None:
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)


async def upsert_user(pool: asyncpg.Pool, user_id: str, username: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username
            """,
            user_id,
            username,
        )


async def log_checkin(
    pool: asyncpg.Pool,
    user_id: str,
    username: str,
    workout: str,
    xp_earned: int,
    new_streak: int,
    today: date,
    gold_earned: int = 0,
) -> bool:
    """Insert a check-in and update user stats. Returns False if already checked in today."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            existing = await conn.fetchrow(
                "SELECT last_checkin FROM users WHERE user_id = $1",
                user_id,
            )
            if existing and existing["last_checkin"] == today:
                return False

            await conn.execute(
                """
                INSERT INTO users (user_id, username, total_xp, weekly_xp, monthly_xp, streak, last_checkin, gold)
                VALUES ($1, $2, $3, $3, $3, $4, $5, $6)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    total_xp = users.total_xp + $3,
                    weekly_xp = users.weekly_xp + $3,
                    monthly_xp = users.monthly_xp + $3,
                    streak = $4,
                    last_checkin = $5,
                    gold = users.gold + $6
                """,
                user_id,
                username,
                xp_earned,
                new_streak,
                today,
                gold_earned,
            )
            await conn.execute(
                "INSERT INTO checkins (user_id, workout, xp_earned) VALUES ($1, $2, $3)",
                user_id,
                workout,
                xp_earned,
            )
            return True


async def get_recent_checkins(pool: asyncpg.Pool, user_id: str, limit: int = 7) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT workout, checked_in_at
            FROM checkins
            WHERE user_id = $1
            ORDER BY checked_in_at DESC
            LIMIT $2
            """,
            user_id,
            limit,
        )


async def get_leaderboard(pool: asyncpg.Pool, period: str, limit: int = 10) -> list[asyncpg.Record]:
    allowed = {"total_xp", "weekly_xp", "monthly_xp"}
    if period not in allowed:
        raise ValueError(f"Invalid period column: {period}")
    async with pool.acquire() as conn:
        return await conn.fetch(
            f"SELECT user_id, username, total_xp, weekly_xp, monthly_xp FROM users ORDER BY {period} DESC LIMIT $1",
            limit,
        )


async def reset_weekly_xp(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET weekly_xp = 0")


async def reset_monthly_xp(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET monthly_xp = 0")


async def get_item_by_name(pool: asyncpg.Pool, name: str) -> asyncpg.Record | None:
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM items WHERE LOWER(name) = LOWER($1)", name)


async def get_inventory(pool: asyncpg.Pool, user_id: str) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT i.id AS inventory_id, items.id AS item_id, items.name, items.description,
                   items.item_type, items.cost, items.level_required, items.effect_type,
                   items.effect_value, i.equipped, i.acquired_at
            FROM inventory i
            JOIN items ON items.id = i.item_id
            WHERE i.user_id = $1
            ORDER BY items.item_type, items.name
            """,
            user_id,
        )


async def get_equipped_items(pool: asyncpg.Pool, user_id: str) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT items.id AS item_id, items.name, items.item_type, items.effect_type,
                   items.effect_value
            FROM inventory i
            JOIN items ON items.id = i.item_id
            WHERE i.user_id = $1 AND i.equipped = TRUE
            """,
            user_id,
        )


async def buy_item(pool: asyncpg.Pool, user_id: str, item_id: int, cost: int) -> bool:
    """Atomically deduct gold and add item to inventory. Returns False if insufficient gold."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT gold FROM users WHERE user_id = $1 FOR UPDATE", user_id
            )
            if row is None or row["gold"] < cost:
                return False
            await conn.execute(
                "UPDATE users SET gold = gold - $1 WHERE user_id = $2", cost, user_id
            )
            await conn.execute(
                "INSERT INTO inventory (user_id, item_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                user_id,
                item_id,
            )
            return True


SLOT_LIMITS: dict[str, int] = {"accessory": 2}


async def equip_item(pool: asyncpg.Pool, user_id: str, item_id: int, item_type: str) -> list[str]:
    """Equip an item, unequipping the oldest if the slot is full. Returns names of unequipped items."""
    slot_limit = SLOT_LIMITS.get(item_type, 1)
    async with pool.acquire() as conn:
        async with conn.transaction():
            currently_equipped = await conn.fetch(
                """
                SELECT i.item_id, items.name
                FROM inventory i
                JOIN items ON items.id = i.item_id
                WHERE i.user_id = $1 AND i.equipped = TRUE AND items.item_type = $2
                ORDER BY i.acquired_at ASC
                """,
                user_id,
                item_type,
            )
            unequipped = []
            overflow = len(currently_equipped) - slot_limit + 1
            if overflow > 0:
                for row in currently_equipped[:overflow]:
                    await conn.execute(
                        "UPDATE inventory SET equipped = FALSE WHERE user_id = $1 AND item_id = $2",
                        user_id,
                        row["item_id"],
                    )
                    unequipped.append(row["name"])
            await conn.execute(
                "UPDATE inventory SET equipped = TRUE WHERE user_id = $1 AND item_id = $2",
                user_id,
                item_id,
            )
            return unequipped
