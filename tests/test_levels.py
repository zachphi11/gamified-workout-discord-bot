from datetime import date, timedelta
import pytest
from utils.levels import get_level
from utils.streak import compute_new_streak
from utils.hype import get_hype


class TestGetLevel:
    def test_zero_xp_is_level_1(self):
        assert get_level(0) == 1

    def test_below_first_threshold_is_level_1(self):
        assert get_level(99) == 1

    def test_exactly_first_threshold_is_level_2(self):
        assert get_level(100) == 2

    def test_max_threshold_is_level_10(self):
        assert get_level(12000) == 10

    def test_above_max_threshold_clamped_to_10(self):
        assert get_level(99999) == 10

    def test_mid_range_levels(self):
        assert get_level(250) == 3
        assert get_level(500) == 4
        assert get_level(1000) == 5


class TestComputeNewStreak:
    def setup_method(self):
        self.today = date(2024, 6, 15)

    def test_no_prior_checkin_starts_at_1(self):
        assert compute_new_streak(None, 0, self.today) == 1

    def test_yesterday_increments(self):
        yesterday = self.today - timedelta(days=1)
        assert compute_new_streak(yesterday, 5, self.today) == 6

    def test_two_days_ago_increments(self):
        two_days_ago = self.today - timedelta(days=2)
        assert compute_new_streak(two_days_ago, 5, self.today) == 6

    def test_three_days_ago_resets(self):
        three_days_ago = self.today - timedelta(days=3)
        assert compute_new_streak(three_days_ago, 5, self.today) == 1

    def test_large_gap_resets(self):
        old_date = self.today - timedelta(days=30)
        assert compute_new_streak(old_date, 10, self.today) == 1


class TestGetHype:
    def test_returns_dict(self):
        result = get_hype()
        assert isinstance(result, dict)

    def test_has_text_key(self):
        result = get_hype()
        assert "text" in result

    def test_text_is_nonempty_string(self):
        result = get_hype()
        assert isinstance(result["text"], str)
        assert len(result["text"]) > 0
