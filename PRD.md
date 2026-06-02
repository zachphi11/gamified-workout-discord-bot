# PRD: Discord Workout Gamification Bot

## Problem Statement

Staying consistent with a workout routine is hard without accountability and motivation. Group chats and servers lack structured tools for tracking fitness habits, celebrating milestones, or fostering friendly competition. Users want a way to hold each other accountable in a Discord server they already use, without relying on a separate fitness app.

Beyond pure accountability, users want the experience to feel like a game — not just a spreadsheet. A flat XP counter and leaderboard eventually loses novelty. Users want a persistent fantasy world they are building through their workouts: gear to collect, pets to own, and eventually monsters to fight alongside their friends.

## Solution

A Discord bot that turns workout logging into an MMORPG. Users check in with a slash command each time they work out, earn XP (to level up) and gold (to spend), and compete on leaderboards — all within their existing Discord server. A fantasy shop lets players buy gear and pets that provide passive bonuses, rewarding long-term investment. Future raids will let the group cooperate to defeat bosses using the stats they have built up.

The bot runs 24/7 on Railway (no machine needs to stay on) and persists data in PostgreSQL.

## User Stories

### Base Bot (Existing)

1. As a server member, I want to log a workout with a single slash command, so that tracking my activity is frictionless.
2. As a server member, I want to type a free-text description of my workout, so that I am not constrained to a preset list of workout types.
3. As a server member, I want to earn XP every time I check in, so that I feel rewarded for showing up.
4. As a server member, I want the bot to prevent me from earning XP more than once per day, so that the system stays fair and resistant to farming.
5. As a server member, I want the bot to auto-create my profile on my first check-in, so that I do not have to run a separate registration command.
6. As a server member, I want to receive a randomized hype message (sometimes with a GIF) after each check-in, so that logging a workout feels fun rather than clinical.
7. As a server member, I want to build a streak by checking in consistently, so that I am motivated to maintain my habit.
8. As a server member, I want my streak to allow a 1-day gap (up to 2 calendar days between check-ins), so that planned rest days do not break my streak.
9. As a server member, I want the whole channel to be notified when I hit a streak milestone (3, 7, or 30 check-ins), so that I get recognition from the community.
10. As a server member, I want to level up as I accumulate XP, so that long-term dedication is visibly rewarded.
11. As a server member, I want the channel to be notified when I level up, so that the community shares in the achievement.
12. As a server member, I want to see my current level, total XP, XP needed for the next level, streak count, and recent workout history in a single command, so that I can assess my progress at a glance.
13. As a server member, I want to check another user's stats by mentioning them, so that I can compare progress with friends.
14. As a server member, I want to see the last 7 workouts I logged (with dates), so that I can review my recent activity.
15. As a server member, I want to view a leaderboard ranked by XP, so that I can see how I stack up against the rest of the server.
16. As a server member, I want to switch between Weekly, Monthly, and All-Time leaderboard views using interactive buttons, so that I can compare performance across different time horizons without running separate commands.
17. As a server member, I want the weekly leaderboard to reset every Monday at midnight Chicago time, so that everyone gets a fresh start each week.
18. As a server member, I want the monthly leaderboard to reset on the 1st of each month at midnight Chicago time, so that monthly competition is meaningful.
19. As a server member, I want my all-time XP to never reset, so that long-term effort is permanently recognized.
20. As a server admin, I want the bot hosted on Railway so that it runs 24/7 without requiring anyone's personal machine to be online.
21. As a server admin, I want bot credentials and database connection strings stored as Railway environment variables, so that secrets are never committed to the repository.

### Fantasy Economy (V1 — This PRD)

22. As a server member, I want to earn gold every time I check in, so that my workouts fund my character's progression beyond levels.
23. As a server member, I want my level to gate what items I can buy, so that higher-level players have access to more powerful gear as a reward for long-term dedication.
24. As a server member, I want to browse a fantasy shop with weapons, armor, accessories, and pets, so that I can plan what to save up for.
25. As a server member, I want the shop to show each item's cost, level requirement, and effect, so that I can make informed purchasing decisions.
26. As a server member, I want to buy an item from the shop using my gold, so that I can equip it and gain its passive bonus.
27. As a server member, I want to be prevented from buying an item if I don't have enough gold or haven't reached the required level, so that the economy stays meaningful.
28. As a server member, I want to view my inventory and see which items I own and which are equipped, so that I can manage my character loadout.
29. As a server member, I want to equip or unequip an item from my inventory, so that I can change which bonuses are active.
30. As a server member, I want equipping a new item to automatically unequip any existing item in the same slot, so that I don't have to manually unequip before equipping.
31. As a server member, I want utility gear (rings, amulets) to increase the gold I earn per check-in, so that investing in gear accelerates my economy.
32. As a server member, I want pets to provide passive gold bonuses, so that owning a companion has a tangible in-game benefit.
33. As a server member, I want combat gear (weapons, armor) to be available in the shop even before raids exist, so that I can prepare my character for future content.
34. As a server member, I want to see my current gold balance in my stats, so that I know how close I am to my next purchase.
35. As a server member, I want my check-in response to show how much gold I earned this check-in (including bonuses from equipped gear), so that I can see the value of my investments immediately.
36. As a server member, I want gold to never be deducted from my XP or affect my level, so that spending in the shop never sets me back on the leaderboard.

## Implementation Decisions

### Currency Model

Gold is a **separate currency** from XP. XP drives levels and leaderboard rank; gold drives the shop. Spending gold never reduces a user's level or XP totals. Level is used as a **gate** on shop purchases (you must be Level N to buy an item), but gold is what you actually spend.

### Gold Economy

- Base rate: **10 gold per check-in**
- Equipped utility gear and pets stack additively on top of the base rate
- Example loadout at max utility gear: ~29 gold per check-in
- Entry-tier items (50g) are reachable in ~5 bare check-ins; top-tier pets (1500g) require sustained play

### Item Catalog

Ten items seed the shop at startup. Items fall into four slot types: `weapon`, `armor`, `accessory`, `pet`. Effect types are `gold_bonus` (active in V1) and `raid_damage` / `raid_defense` (placeholder — inactive until V2 raids ship).

| Name | Slot | Level | Cost | Effect |
|---|---|---|---|---|
| Slime | pet | 1 | 100g | +1 gold/check-in |
| Wooden Sword | weapon | 1 | 75g | +5% raid damage (V2) |
| Iron Ring | accessory | 1 | 50g | +2 gold/check-in |
| Lucky Charm | accessory | 2 | 120g | +1 streak grace day |
| Merchant's Pouch | accessory | 3 | 200g | +5 gold/check-in |
| Wolf Pup | pet | 4 | 350g | +4 gold/check-in |
| Iron Shield | armor | 4 | 300g | +10% raid defense (V2) |
| Gold Crown | accessory | 6 | 800g | +12 gold/check-in |
| Enchanted Staff | weapon | 7 | 1200g | +15% raid damage (V2) |
| Dragon Hatchling | pet | 8 | 1500g | +8 gold/check-in |

### Equipment Slots

Four slots, one item equipped per slot at a time: `weapon`, `armor`, `accessory`, `pet`. Equipping a new item into an occupied slot automatically unequips the previous item.

### Modules

**Gold Utility (`utils/shop.py`)** — deep module
Pure, stateless. Holds `GOLD_PER_CHECKIN` constant and exposes `compute_gold_earned(equipped_items: list[dict]) -> int`. Sums the base rate plus `effect_value` for all equipped items whose `effect_type` is `gold_bonus`. No I/O, no Discord dependency — fully unit-testable.

**Shop Cog (`cogs/shop.py`)** — thin Discord UI layer
Four slash commands:
- `/shop [category]` — paginated embed with category filter buttons (Weapons / Armor / Accessories / Pets). Footer shows user's level and gold. Items the user already owns are marked. Items above the user's level are shown but marked as locked.
- `/buy <item_name>` — validates level requirement and gold balance, deducts gold, adds item to inventory.
- `/inventory` — embed grouped by slot, equipped items marked with ✅.
- `/equip <item_name>` — toggles equip/unequip; auto-unequips the slot's current occupant if needed.

**DB Layer additions (`db/queries.py`)**
New functions: `get_equipped_items(user_id)`, `get_inventory(user_id)`, `get_item_by_name(name)`, `buy_item(user_id, item_id, cost)` (transactional — atomically deducts gold and inserts inventory row; returns `False` if insufficient gold), `equip_item(user_id, item_id, item_type)` (transactional — unequips same-slot item then equips new one).

`log_checkin` is extended to accept and persist `gold_earned`, updating `users.gold` in the same transaction as XP.

**Schema (`db/database.py`)**
- `ALTER TABLE users ADD COLUMN IF NOT EXISTS gold INT DEFAULT 0` — safe to run on startup, no-ops if column exists.
- New `items` table: id, name, description, item_type, cost, level_required, effect_type, effect_value.
- New `inventory` table: id, user_id (FK), item_id (FK), equipped, acquired_at. Unique constraint on (user_id, item_id).
- Seed insert: `INSERT INTO items ... ON CONFLICT (name) DO NOTHING` — idempotent on every startup.

**Check-in flow (`cogs/checkin.py`)**
After resolving XP as today, fetch the user's equipped items, call `compute_gold_earned`, pass the result to `log_checkin`. Append `+{gold_earned}g 💰` to the check-in response line.

**Stats (`cogs/stats.py`)**
Add a `Gold: {gold}g 💰` line to the stats embed.

### Hosting / Migration

No manual migration step. All schema changes use `IF NOT EXISTS` or `ON CONFLICT DO NOTHING`, so the bot self-migrates on next Railway deploy.

## Testing Decisions

Good tests verify external behavior — what a function returns or what side effect it produces — not how it achieves that internally. Tests should not assert on SQL string contents, internal call order, or private attributes.

**`utils/shop.py` — unit tests**
- `compute_gold_earned([])` returns base rate (10)
- `compute_gold_earned` with one gold_bonus item returns base + item's effect_value
- `compute_gold_earned` with multiple gold_bonus items stacks them additively
- Items with non-gold effect types (raid_damage, etc.) do not contribute to gold total
- Prior art: follows the same pattern as `tests/test_levels.py` — pure function, no fixtures needed

**`db/queries.py` (gold additions) — integration tests**
Tests run against a real PostgreSQL test database (same pattern as `tests/test_db.py`). Cover:
- `buy_item` deducts correct gold and inserts inventory row
- `buy_item` returns `False` and makes no changes when gold is insufficient (atomic failure)
- `equip_item` sets equipped=True on the target item
- `equip_item` unequips the previous occupant of the same slot
- `get_equipped_items` returns only equipped items for the requesting user
- `log_checkin` persists gold_earned and increments users.gold correctly

**`cogs/shop.py` — Discord interaction tests**
Mock `discord.Interaction` and the DB pool. Cover:
- `/buy` with sufficient gold and correct level returns success embed and deducts gold
- `/buy` with insufficient gold returns ephemeral error, no DB changes
- `/buy` below required level returns ephemeral level-gate error
- `/equip` on an owned item sets it equipped and returns confirmation
- `/equip` when slot is occupied auto-unequips old item
- `/inventory` returns embed listing all owned items

## Out of Scope

- **V2 Raids** — cooperative boss fights where gear bonuses activate. Tracked separately.
- **Pet training / evolution** — pets leveling up by being attached to workouts. Deferred post-V2.
- Weighted XP or gold by workout type or duration.
- Workout categories, tags, or preset dropdown options.
- Per-server configuration (custom XP rates, level thresholds, gold rates).
- A web dashboard or UI beyond Discord embeds.
- User opt-out / account deletion commands.
- Admin commands to manually adjust gold, XP, or inventory.
- DM-based interactions (all commands work in server channels only).
- Support for multiple Discord servers with isolated data per guild.
- PvP — players spending gold to attack each other.

## Further Notes

- The bot uses discord.py application commands (slash commands) exclusively — no prefix commands.
- `asyncpg` handles async PostgreSQL access, pairing cleanly with discord.py's event loop.
- Railway's free hobby tier supports persistent worker processes; no Dockerfile needed — Nixpacks auto-detects Python from `requirements.txt`.
- The bot token should never appear in logs. Use `python-dotenv` locally and Railway env vars in production.
- Gold amounts in embeds should always include the `g` suffix (e.g., `150g`) for clarity.
- Combat gear sold in V1 should clearly communicate in its description that the bonus activates "in raids (coming soon)" so users understand they are investing in future content.
