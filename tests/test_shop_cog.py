"""Discord interaction tests for cogs/shop.py."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from cogs.shop import ShopCog


def make_interaction(user_id="user1", display_name="Alice"):
    interaction = MagicMock()
    interaction.user.id = user_id
    interaction.user.display_name = display_name
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


def make_bot(pool=None):
    bot = MagicMock()
    bot.pool = pool or MagicMock()
    return bot


def make_item(
    id=1,
    name="Iron Ring",
    description="A ring",
    item_type="accessory",
    cost=50,
    level_required=1,
    effect_type="gold_bonus",
    effect_value=2,
):
    item = MagicMock()
    item.__getitem__ = lambda self, key: {
        "id": id,
        "name": name,
        "description": description,
        "item_type": item_type,
        "cost": cost,
        "level_required": level_required,
        "effect_type": effect_type,
        "effect_value": effect_value,
    }[key]
    item.get = lambda key, default=None: {
        "id": id,
        "name": name,
        "description": description,
        "item_type": item_type,
        "cost": cost,
        "level_required": level_required,
        "effect_type": effect_type,
        "effect_value": effect_value,
    }.get(key, default)
    return item


def make_user_row(gold=100, total_xp=0):
    row = MagicMock()
    row.__getitem__ = lambda self, key: {"gold": gold, "total_xp": total_xp}[key]
    return row


class TestBuyCommand:
    async def test_sufficient_gold_and_level_returns_success(self):
        bot = make_bot()
        cog = ShopCog(bot)
        interaction = make_interaction()
        item = make_item()
        user_row = make_user_row(gold=100, total_xp=0)

        with (
            patch("cogs.shop.queries.get_item_by_name", new=AsyncMock(return_value=item)),
            patch("cogs.shop.queries.get_user", new=AsyncMock(return_value=user_row)),
            patch("cogs.shop.queries.buy_item", new=AsyncMock(return_value=True)),
        ):
            await cog.buy.callback(cog, interaction, item_name="Iron Ring")

        interaction.response.send_message.assert_called_once()
        call_kwargs = interaction.response.send_message.call_args
        assert call_kwargs.kwargs.get("ephemeral") is not True

    async def test_insufficient_gold_returns_ephemeral_error(self):
        bot = make_bot()
        cog = ShopCog(bot)
        interaction = make_interaction()
        item = make_item(cost=200)
        user_row = make_user_row(gold=10, total_xp=0)

        with (
            patch("cogs.shop.queries.get_item_by_name", new=AsyncMock(return_value=item)),
            patch("cogs.shop.queries.get_user", new=AsyncMock(return_value=user_row)),
            patch("cogs.shop.queries.buy_item", new=AsyncMock()) as mock_buy,
        ):
            await cog.buy.callback(cog, interaction, item_name="Iron Ring")

        mock_buy.assert_not_called()
        call_kwargs = interaction.response.send_message.call_args
        assert call_kwargs.kwargs.get("ephemeral") is True

    async def test_below_level_requirement_returns_ephemeral_error(self):
        bot = make_bot()
        cog = ShopCog(bot)
        interaction = make_interaction()
        item = make_item(level_required=5, cost=50)
        user_row = make_user_row(gold=500, total_xp=0)  # level 1

        with (
            patch("cogs.shop.queries.get_item_by_name", new=AsyncMock(return_value=item)),
            patch("cogs.shop.queries.get_user", new=AsyncMock(return_value=user_row)),
            patch("cogs.shop.queries.buy_item", new=AsyncMock()) as mock_buy,
        ):
            await cog.buy.callback(cog, interaction, item_name="Iron Ring")

        mock_buy.assert_not_called()
        call_kwargs = interaction.response.send_message.call_args
        assert call_kwargs.kwargs.get("ephemeral") is True


class TestEquipCommand:
    def make_inv_item(self, name="Iron Ring", item_id=1, item_type="accessory", equipped=False):
        inv = MagicMock()
        inv.__getitem__ = lambda self, key: {
            "item_id": item_id,
            "name": name,
            "item_type": item_type,
            "equipped": equipped,
        }[key]
        return inv

    async def test_equip_owned_item_returns_confirmation(self):
        bot = make_bot()
        cog = ShopCog(bot)
        interaction = make_interaction()
        inv_item = self.make_inv_item()

        with (
            patch("cogs.shop.queries.get_inventory", new=AsyncMock(return_value=[inv_item])),
            patch("cogs.shop.queries.equip_item", new=AsyncMock()) as mock_equip,
        ):
            await cog.equip.callback(cog, interaction, item_name="Iron Ring")

        mock_equip.assert_called_once()
        interaction.response.send_message.assert_called_once()

    async def test_equip_when_slot_occupied_calls_equip_item(self):
        bot = make_bot()
        cog = ShopCog(bot)
        interaction = make_interaction()
        inv_item = self.make_inv_item(name="Iron Ring", item_id=1, item_type="accessory", equipped=False)

        with (
            patch("cogs.shop.queries.get_inventory", new=AsyncMock(return_value=[inv_item])),
            patch("cogs.shop.queries.equip_item", new=AsyncMock()) as mock_equip,
        ):
            await cog.equip.callback(cog, interaction, item_name="Iron Ring")

        # equip_item handles unequipping old slot occupant transactionally in queries layer
        mock_equip.assert_called_once_with(bot.pool, "user1", 1, "accessory")


class TestInventoryCommand:
    async def test_returns_embed_listing_owned_items(self):
        bot = make_bot()
        cog = ShopCog(bot)
        interaction = make_interaction()

        inv_item = MagicMock()
        inv_item.__getitem__ = lambda self, key: {
            "item_id": 1,
            "name": "Iron Ring",
            "item_type": "accessory",
            "equipped": True,
            "effect_type": "gold_bonus",
            "effect_value": 2,
            "description": "A sturdy ring",
        }[key]

        with patch("cogs.shop.queries.get_inventory", new=AsyncMock(return_value=[inv_item])):
            await cog.inventory.callback(cog, interaction)

        interaction.response.send_message.assert_called_once()
        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs.get("embed") or (call_kwargs.args[0] if call_kwargs.args else None)
        assert embed is not None
