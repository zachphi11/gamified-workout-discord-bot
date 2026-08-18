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
        "text": "Can’t wait for you to wrap those veiny forearms around my neck as the light drains from my eyes!",
        "gif_url": "https://klipy.com/gifs/yumeko-anime"},
    {
        "text": "He’s still following you, don’t let your guard down just yet.",
        "gif_url": "https://klipy.com/gifs/kto-kounotoritoken-7",
    },
    {"text": "Pain is temporary. Suffering is eternal."},
    {"text": "Another check-in? You're becoming unstoppable. 🔥"},
    {"text": "The gym doesn't care what day it is. Neither do you. That's power."},
    {"text": "I want to crawl inside your ribcage and pay rent."},
    {
        "text": "I’d recognize your breathing anywhere.",
        "gif_url": "https://klipy.com/gifs/elmo-stare",
    },
]


def get_hype() -> dict:
    return random.choice(HYPE_ENTRIES)
