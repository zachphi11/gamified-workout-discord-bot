from datetime import date


def compute_new_streak(last_checkin: date | None, current_streak: int, today: date) -> int:
    if last_checkin is None:
        return 1
    gap = (today - last_checkin).days
    if gap <= 2:
        return current_streak + 1
    return 1
