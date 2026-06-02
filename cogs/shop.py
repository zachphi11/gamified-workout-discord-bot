import discord
from discord.ext import commands

from db import queries
from utils.levels import get_level

CATEGORY_LABELS = {
    "weapon": "Weapons",
    "armor": "Armor",
    "accessory": "Accessories",
    "pet": "Pets",
}

EFFECT_DESCRIPTIONS = {
    "gold_bonus": lambda v: f"+{v} gold/check-in",
    "raid_damage": lambda v: f"+{v}% raid damage (coming soon)",
    "raid_defense": lambda v: f"+{v}% raid defense (coming soon)",
    "streak_grace": lambda v: f"+{v} streak grace day",
}


def _effect_text(effect_type: str, effect_value: int) -> str:
    formatter = EFFECT_DESCRIPTIONS.get(effect_type)
    return formatter(effect_value) if formatter else f"{effect_type}: {effect_value}"


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="shop", description="Browse the fantasy shop")
    @discord.app_commands.describe(category="Filter by category: weapon, armor, accessory, pet")
    async def shop(self, interaction: discord.Interaction, category: str = None):
        user_id = str(interaction.user.id)
        row = await queries.get_user(self.bot.pool, user_id)
        gold = row["gold"] if row else 0
        total_xp = row["total_xp"] if row else 0
        level = get_level(total_xp)

        async with self.bot.pool.acquire() as conn:
            if category and category in CATEGORY_LABELS:
                items = await conn.fetch(
                    "SELECT * FROM items WHERE item_type = $1 ORDER BY level_required, cost",
                    category,
                )
            else:
                items = await conn.fetch("SELECT * FROM items ORDER BY item_type, level_required, cost")

        inv = await queries.get_inventory(self.bot.pool, user_id)
        owned_ids = {r["item_id"] for r in inv}

        embed = discord.Embed(title="⚔️ Fantasy Shop", color=discord.Color.gold())
        embed.set_footer(text=f"Your level: {level} | Your gold: {gold}g")

        for item in items:
            owned = item["id"] in owned_ids
            locked = item["level_required"] > level
            effect = _effect_text(item["effect_type"], item["effect_value"])
            status = " 🔒 (locked)" if locked else (" ✅ owned" if owned else "")
            embed.add_field(
                name=f"{item['name']} — {item['cost']}g (Lv.{item['level_required']}){status}",
                value=f"{item['description']}\n*{effect}*",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="buy", description="Buy an item from the shop")
    @discord.app_commands.describe(item_name="The name of the item to buy")
    async def buy(self, interaction: discord.Interaction, item_name: str):
        user_id = str(interaction.user.id)
        item = await queries.get_item_by_name(self.bot.pool, item_name)
        if item is None:
            await interaction.response.send_message(
                f"No item named **{item_name}** exists in the shop.", ephemeral=True
            )
            return

        row = await queries.get_user(self.bot.pool, user_id)
        gold = row["gold"] if row else 0
        total_xp = row["total_xp"] if row else 0
        level = get_level(total_xp)

        if level < item["level_required"]:
            await interaction.response.send_message(
                f"You need to be **Level {item['level_required']}** to buy **{item['name']}**. "
                f"You are Level {level}.",
                ephemeral=True,
            )
            return

        if gold < item["cost"]:
            await interaction.response.send_message(
                f"Not enough gold! **{item['name']}** costs **{item['cost']}g** but you only have **{gold}g**.",
                ephemeral=True,
            )
            return

        success = await queries.buy_item(self.bot.pool, user_id, item["id"], item["cost"])
        if not success:
            await interaction.response.send_message(
                "Purchase failed — you may not have enough gold.", ephemeral=True
            )
            return

        effect = _effect_text(item["effect_type"], item["effect_value"])
        embed = discord.Embed(
            title="🛍️ Purchase Successful!",
            description=f"You bought **{item['name']}** for **{item['cost']}g**!\n*{effect}*",
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Remaining gold: {gold - item['cost']}g")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        inv = await queries.get_inventory(self.bot.pool, user_id)

        embed = discord.Embed(title="🎒 Your Inventory", color=discord.Color.blurple())

        if not inv:
            embed.description = "Your inventory is empty. Use `/shop` to browse items!"
            await interaction.response.send_message(embed=embed)
            return

        by_slot: dict[str, list] = {}
        for item in inv:
            slot = item["item_type"]
            by_slot.setdefault(slot, []).append(item)

        for slot, slot_items in by_slot.items():
            lines = []
            for item in slot_items:
                equipped_mark = " ✅" if item["equipped"] else ""
                effect = _effect_text(item["effect_type"], item["effect_value"])
                lines.append(f"**{item['name']}**{equipped_mark} — *{effect}*")
            embed.add_field(
                name=CATEGORY_LABELS.get(slot, slot.title()),
                value="\n".join(lines),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="equip", description="Equip or unequip an item")
    @discord.app_commands.describe(item_name="The name of the item to equip")
    async def equip(self, interaction: discord.Interaction, item_name: str):
        user_id = str(interaction.user.id)
        inv = await queries.get_inventory(self.bot.pool, user_id)

        owned = {item["name"]: item for item in inv}
        if item_name not in owned:
            await interaction.response.send_message(
                f"You don't own **{item_name}**. Use `/buy` to purchase it first.", ephemeral=True
            )
            return

        item = owned[item_name]
        await queries.equip_item(self.bot.pool, user_id, item["item_id"], item["item_type"])

        slot_label = CATEGORY_LABELS.get(item["item_type"], item["item_type"].title())
        await interaction.response.send_message(
            f"⚔️ **{item_name}** equipped! ({slot_label} slot)"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
