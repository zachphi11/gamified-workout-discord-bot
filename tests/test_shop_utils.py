from utils.shop import GOLD_PER_CHECKIN, compute_gold_earned, compute_streak_bonus


class TestComputeGoldEarned:
    def test_empty_list_returns_base_rate(self):
        assert compute_gold_earned([]) == 10

    def test_single_gold_bonus_item_adds_effect_value(self):
        item = {"effect_type": "gold_bonus", "effect_value": 2}
        assert compute_gold_earned([item]) == 12

    def test_multiple_gold_bonus_items_stack_additively(self):
        items = [
            {"effect_type": "gold_bonus", "effect_value": 2},
            {"effect_type": "gold_bonus", "effect_value": 5},
        ]
        assert compute_gold_earned(items) == 17

    def test_non_gold_effect_type_ignored(self):
        item = {"effect_type": "raid_damage", "effect_value": 10}
        assert compute_gold_earned([item]) == 10

    def test_mixed_effect_types_only_sums_gold_bonus(self):
        items = [
            {"effect_type": "gold_bonus", "effect_value": 4},
            {"effect_type": "raid_defense", "effect_value": 20},
            {"effect_type": "gold_bonus", "effect_value": 1},
        ]
        assert compute_gold_earned(items) == 15


class TestComputeStreakBonus:
    def test_no_streak_returns_zero(self):
        assert compute_streak_bonus(0) == 0

    def test_below_seven_returns_zero(self):
        assert compute_streak_bonus(6) == 0

    def test_exactly_seven_returns_five(self):
        assert compute_streak_bonus(7) == 5

    def test_between_seven_and_thirty_returns_five(self):
        assert compute_streak_bonus(29) == 5

    def test_exactly_thirty_returns_ten(self):
        assert compute_streak_bonus(30) == 10

    def test_between_thirty_and_hundred_returns_ten(self):
        assert compute_streak_bonus(99) == 10

    def test_exactly_hundred_returns_twenty(self):
        assert compute_streak_bonus(100) == 20

    def test_above_hundred_returns_twenty(self):
        assert compute_streak_bonus(365) == 20
