import random

HYPE_ENTRIES = [
    {"text": "BEAST MODE ACTIVATED. You showed up. That's everything. 💪"},
    {"text": "Another day, another W. The gains are coming for you."},
    {"text": "Consistency is a superpower. You've got it. Keep stacking."},
    {"text": "The iron doesn't care about your excuses. You didn't either. Let's go!"},
    {"text": "You just out-worked your future competition. Feel that."},
    {"text": "Rest day? Never heard of it. You're built different."},
    {"text": "Progress > perfection. You showed up. That's all that matters."},
    {"text": "Your future self is sending gratitude from the future. Keep going."},
    {
        "text": "SWEAT. GRIND. REPEAT. You know the drill.",
        "gif_url": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    },
    {
        "text": "No days off. Okay maybe rest days. But NOT today.",
        "gif_url": "https://media.giphy.com/media/3o7TKUM3IgJBX2as9O/giphy.gif",
    },
    {"text": "Pain is temporary. Glory is forever. You're writing your story."},
    {"text": "Another check-in? You're becoming unstoppable. 🔥"},
    {"text": "The gym doesn't care what day it is. Neither do you. That's power."},
    {"text": "Champions are made when nobody's watching. You're watching."},
    {
        "text": "LFG!!!!! The gains don't stop!",
        "gif_url": "https://media.giphy.com/media/xT9IgG50Lg7russFcA/giphy.gif",
    },
]


def get_hype() -> dict:
    return random.choice(HYPE_ENTRIES)
