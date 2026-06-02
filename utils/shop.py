GOLD_PER_CHECKIN = 10


def compute_gold_earned(equipped_items: list[dict]) -> int:
    bonus = sum(
        item["effect_value"]
        for item in equipped_items
        if item["effect_type"] == "gold_bonus"
    )
    return GOLD_PER_CHECKIN + bonus


def compute_streak_bonus(streak: int) -> int:
    if streak >= 100:
        return 20
    if streak >= 30:
        return 10
    if streak >= 7:
        return 5
    return 0
