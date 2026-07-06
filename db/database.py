import os
import asyncpg


CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    total_xp INT DEFAULT 0,
    weekly_xp INT DEFAULT 0,
    monthly_xp INT DEFAULT 0,
    streak INT DEFAULT 0,
    last_checkin DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
"""

CREATE_CHECKINS = """
CREATE TABLE IF NOT EXISTS checkins (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    workout TEXT NOT NULL,
    xp_earned INT NOT NULL,
    checked_in_at TIMESTAMPTZ DEFAULT NOW()
)
"""

ADD_GOLD_COLUMN = "ALTER TABLE users ADD COLUMN IF NOT EXISTS gold INT DEFAULT 0"

CREATE_ITEMS = """
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    item_type TEXT NOT NULL,
    cost INT NOT NULL,
    level_required INT NOT NULL DEFAULT 1,
    effect_type TEXT NOT NULL,
    effect_value INT NOT NULL DEFAULT 0
)
"""

CREATE_INVENTORY = """
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    item_id INT NOT NULL REFERENCES items(id),
    equipped BOOLEAN DEFAULT FALSE,
    acquired_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, item_id)
)
"""

SEED_ITEMS = """
INSERT INTO items (name, description, item_type, cost, level_required, effect_type, effect_value)
VALUES
    ('Slime', 'A friendly slime companion that brings you extra gold.', 'pet', 100, 1, 'gold_bonus', 1),
    ('Wooden Sword', 'A basic sword. The bonus activates in raids (coming soon).', 'weapon', 75, 1, 'raid_damage', 5),
    ('Iron Ring', 'A sturdy ring that boosts your gold earnings.', 'accessory', 50, 1, 'gold_bonus', 2),
    ('Lucky Charm', 'Grants an extra day of streak grace.', 'accessory', 120, 2, 'streak_grace', 1),
    ('Merchant''s Pouch', 'A well-worn pouch that significantly boosts gold.', 'accessory', 200, 3, 'gold_bonus', 5),
    ('Wolf Pup', 'A loyal wolf pup that finds extra gold for you.', 'pet', 350, 4, 'gold_bonus', 4),
    ('Iron Shield', 'Sturdy defense. The bonus activates in raids (coming soon).', 'offhand', 300, 4, 'raid_defense', 10),
    ('Gold Crown', 'A gleaming crown that greatly multiplies your gold.', 'head', 800, 6, 'gold_bonus', 12),
    ('Enchanted Staff', 'A powerful staff. The bonus activates in raids (coming soon).', 'weapon', 1200, 7, 'raid_damage', 15),
    ('Dragon Hatchling', 'A young dragon that hoards gold on your behalf.', 'pet', 1500, 8, 'gold_bonus', 8)
ON CONFLICT (name) DO NOTHING
"""

MIGRATE_IRON_SHIELD_TO_OFFHAND = """
UPDATE items SET item_type = 'offhand' WHERE name = 'Iron Shield' AND item_type = 'armor'
"""

MIGRATE_GOLD_CROWN_TO_HEAD = """
UPDATE items SET item_type = 'head' WHERE name = 'Gold Crown' AND item_type = 'accessory'
"""

SEED_NEW_SLOT_ITEMS = """
INSERT INTO items (name, description, item_type, cost, level_required, effect_type, effect_value)
VALUES
    ('Leather Cap',      'A simple cap that keeps coin purses nearby.',          'head',    60,   1, 'gold_bonus',   1),
    ('Iron Helm',        'A sturdy helm. Bonus activates in raids (coming soon).','head',   280,  4, 'raid_defense', 8),
    ('Enchanted Hood',   'A hood humming with magic that draws gold to you.',    'head',    950,  7, 'gold_bonus',   7),
    ('Wooden Shield',    'A basic shield. Bonus activates in raids (coming soon).','offhand',80,  1, 'raid_defense', 4),
    ('Tower Shield',     'A massive shield. Bonus activates in raids (coming soon).','offhand',1100,6,'raid_defense',15),
    ('Leather Vest',     'Light armor that keeps you agile.',                    'chest',   100,  2, 'raid_defense', 5),
    ('Iron Chestplate',  'Solid iron protection. Bonus activates in raids (coming soon).','chest',550,5,'raid_defense',12),
    ('Dragon Scale Armor','Scales from a dragon. Bonus activates in raids (coming soon).','chest',2000,9,'raid_defense',20),
    ('Worn Boots',       'Battered boots that somehow attract loose coins.',     'boots',   40,   1, 'gold_bonus',   1),
    ('Swift Boots',      'Light boots that help you find gold on the road.',     'boots',   380,  4, 'gold_bonus',   3),
    ('Enchanted Boots',  'Boots that shimmer with gold-finding magic.',          'boots',   1400, 8, 'gold_bonus',   8)
ON CONFLICT (name) DO NOTHING
"""


async def run_migrations(conn: asyncpg.Connection) -> None:
    await conn.execute(CREATE_USERS)
    await conn.execute(ADD_GOLD_COLUMN)
    await conn.execute(CREATE_CHECKINS)
    await conn.execute(CREATE_ITEMS)
    await conn.execute(CREATE_INVENTORY)
    await conn.execute(SEED_ITEMS)
    await conn.execute(MIGRATE_IRON_SHIELD_TO_OFFHAND)
    await conn.execute(MIGRATE_GOLD_CROWN_TO_HEAD)
    await conn.execute(SEED_NEW_SLOT_ITEMS)


async def create_pool() -> asyncpg.Pool:
    database_url = os.environ["DATABASE_URL"]
    pool = await asyncpg.create_pool(database_url)
    async with pool.acquire() as conn:
        await run_migrations(conn)
    return pool
