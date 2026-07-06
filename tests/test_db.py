"""Integration tests for db/queries.py against a real PostgreSQL test database."""
import os
from datetime import date, timedelta

import asyncpg
import pytest
import pytest_asyncio

from db.database import run_migrations
from db import queries

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://workout_user:testpass@localhost/workout_test"
)


@pytest_asyncio.fixture
async def pool():
    p = await asyncpg.create_pool(TEST_DB_URL)
    async with p.acquire() as conn:
        await run_migrations(conn)
    yield p
    async with p.acquire() as conn:
        await conn.execute("DELETE FROM inventory")
        await conn.execute("DELETE FROM checkins")
        await conn.execute("DELETE FROM users")
    await p.close()


class TestUpsertUser:
    async def test_creates_new_user(self, pool):
        await queries.upsert_user(pool, "user1", "Alice")
        row = await queries.get_user(pool, "user1")
        assert row is not None
        assert row["username"] == "Alice"

    async def test_updates_username_on_conflict(self, pool):
        await queries.upsert_user(pool, "user1", "Alice")
        await queries.upsert_user(pool, "user1", "Alice Updated")
        row = await queries.get_user(pool, "user1")
        assert row["username"] == "Alice Updated"

    async def test_does_not_wipe_xp_on_upsert(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "leg day", 25, 1, today)
        await queries.upsert_user(pool, "user1", "Alice v2")
        row = await queries.get_user(pool, "user1")
        assert row["total_xp"] == 25


class TestLogCheckin:
    async def test_creates_checkin(self, pool):
        today = date.today()
        result = await queries.log_checkin(pool, "user1", "Alice", "push day", 25, 1, today)
        assert result is True
        row = await queries.get_user(pool, "user1")
        assert row["total_xp"] == 25

    async def test_daily_cap_rejects_second_checkin(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "push day", 25, 1, today)
        result = await queries.log_checkin(pool, "user1", "Alice", "pull day", 25, 2, today)
        assert result is False

    async def test_daily_cap_does_not_double_xp(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "push day", 25, 1, today)
        await queries.log_checkin(pool, "user1", "Alice", "pull day", 25, 2, today)
        row = await queries.get_user(pool, "user1")
        assert row["total_xp"] == 25

    async def test_xp_accumulates_across_days(self, pool):
        day1 = date.today() - timedelta(days=1)
        day2 = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "push day", 25, 1, day1)
        await queries.log_checkin(pool, "user1", "Alice", "pull day", 25, 2, day2)
        row = await queries.get_user(pool, "user1")
        assert row["total_xp"] == 50

    async def test_gold_earned_increments_user_gold(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "push day", 25, 1, today, gold_earned=10)
        row = await queries.get_user(pool, "user1")
        assert row["gold"] == 10

    async def test_gold_defaults_to_zero_when_not_provided(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "push day", 25, 1, today)
        row = await queries.get_user(pool, "user1")
        assert row["gold"] == 0


class TestLeaderboard:
    async def test_ordered_by_total_xp_descending(self, pool):
        day1 = date.today() - timedelta(days=2)
        day2 = date.today() - timedelta(days=1)
        day3 = date.today()
        await queries.log_checkin(pool, "userA", "Alice", "workout", 25, 1, day1)
        await queries.log_checkin(pool, "userB", "Bob", "workout", 25, 1, day2)
        await queries.log_checkin(pool, "userB", "Bob", "workout", 25, 2, day3)
        rows = await queries.get_leaderboard(pool, "total_xp")
        assert rows[0]["username"] == "Bob"
        assert rows[1]["username"] == "Alice"


class TestResets:
    async def test_reset_weekly_zeroes_weekly_xp(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today)
        await queries.reset_weekly_xp(pool)
        row = await queries.get_user(pool, "user1")
        assert row["weekly_xp"] == 0
        assert row["total_xp"] == 25
        assert row["monthly_xp"] == 25

    async def test_reset_monthly_zeroes_monthly_xp(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today)
        await queries.reset_monthly_xp(pool)
        row = await queries.get_user(pool, "user1")
        assert row["monthly_xp"] == 0
        assert row["total_xp"] == 25
        assert row["weekly_xp"] == 25


class TestBuyItem:
    async def test_deducts_gold_and_adds_to_inventory(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today, gold_earned=100)
        iron_ring = await queries.get_item_by_name(pool, "Iron Ring")
        result = await queries.buy_item(pool, "user1", iron_ring["id"], iron_ring["cost"])
        assert result is True
        row = await queries.get_user(pool, "user1")
        assert row["gold"] == 50  # 100 - 50
        inv = await queries.get_inventory(pool, "user1")
        assert len(inv) == 1
        assert inv[0]["name"] == "Iron Ring"

    async def test_returns_false_and_no_changes_when_insufficient_gold(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today, gold_earned=10)
        iron_ring = await queries.get_item_by_name(pool, "Iron Ring")
        result = await queries.buy_item(pool, "user1", iron_ring["id"], iron_ring["cost"])
        assert result is False
        row = await queries.get_user(pool, "user1")
        assert row["gold"] == 10  # unchanged
        inv = await queries.get_inventory(pool, "user1")
        assert len(inv) == 0


class TestEquipItem:
    async def test_sets_equipped_true(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today, gold_earned=100)
        iron_ring = await queries.get_item_by_name(pool, "Iron Ring")
        await queries.buy_item(pool, "user1", iron_ring["id"], iron_ring["cost"])
        await queries.equip_item(pool, "user1", iron_ring["id"], iron_ring["item_type"])
        equipped = await queries.get_equipped_items(pool, "user1")
        assert len(equipped) == 1
        assert equipped[0]["name"] == "Iron Ring"

    async def test_two_accessories_can_be_equipped_simultaneously(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today, gold_earned=500)
        iron_ring = await queries.get_item_by_name(pool, "Iron Ring")
        merchants_pouch = await queries.get_item_by_name(pool, "Merchant's Pouch")
        await queries.buy_item(pool, "user1", iron_ring["id"], iron_ring["cost"])
        await queries.buy_item(pool, "user1", merchants_pouch["id"], merchants_pouch["cost"])
        await queries.equip_item(pool, "user1", iron_ring["id"], iron_ring["item_type"])
        await queries.equip_item(pool, "user1", merchants_pouch["id"], merchants_pouch["item_type"])
        equipped = await queries.get_equipped_items(pool, "user1")
        equipped_names = [e["name"] for e in equipped]
        assert "Iron Ring" in equipped_names
        assert "Merchant's Pouch" in equipped_names

    async def test_third_accessory_unequips_oldest(self, pool):
        today = date.today()
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today, gold_earned=1500)
        iron_ring = await queries.get_item_by_name(pool, "Iron Ring")
        merchants_pouch = await queries.get_item_by_name(pool, "Merchant's Pouch")
        gold_crown = await queries.get_item_by_name(pool, "Gold Crown")
        await queries.buy_item(pool, "user1", iron_ring["id"], iron_ring["cost"])
        await queries.buy_item(pool, "user1", merchants_pouch["id"], merchants_pouch["cost"])
        await queries.buy_item(pool, "user1", gold_crown["id"], gold_crown["cost"])
        await queries.equip_item(pool, "user1", iron_ring["id"], iron_ring["item_type"])
        await queries.equip_item(pool, "user1", merchants_pouch["id"], merchants_pouch["item_type"])
        unequipped = await queries.equip_item(pool, "user1", gold_crown["id"], gold_crown["item_type"])
        assert unequipped == ["Iron Ring"]
        equipped = await queries.get_equipped_items(pool, "user1")
        equipped_names = [e["name"] for e in equipped]
        assert "Gold Crown" in equipped_names
        assert "Merchant's Pouch" in equipped_names
        assert "Iron Ring" not in equipped_names


class TestGetEquippedItems:
    async def test_returns_only_requesting_users_equipped_items(self, pool):
        today = date.today()
        day2 = date.today() - timedelta(days=1)
        await queries.log_checkin(pool, "user1", "Alice", "workout", 25, 1, today, gold_earned=100)
        await queries.log_checkin(pool, "user2", "Bob", "workout", 25, 1, day2, gold_earned=100)
        iron_ring = await queries.get_item_by_name(pool, "Iron Ring")
        await queries.buy_item(pool, "user1", iron_ring["id"], iron_ring["cost"])
        await queries.buy_item(pool, "user2", iron_ring["id"], iron_ring["cost"])
        await queries.equip_item(pool, "user1", iron_ring["id"], iron_ring["item_type"])
        await queries.equip_item(pool, "user2", iron_ring["id"], iron_ring["item_type"])
        user1_equipped = await queries.get_equipped_items(pool, "user1")
        assert len(user1_equipped) == 1
        user2_equipped = await queries.get_equipped_items(pool, "user2")
        assert len(user2_equipped) == 1
