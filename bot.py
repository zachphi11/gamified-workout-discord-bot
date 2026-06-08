import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from db.database import create_pool
from utils.scheduler import start_schedulers

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    bot.pool = await create_pool()
    start_schedulers(bot.pool, bot)
    await bot.tree.sync()
    print(f"Bot is ready — logged in as {bot.user} (ID: {bot.user.id})")


async def main():
    async with bot:
        await bot.load_extension("cogs.checkin")
        await bot.load_extension("cogs.stats")
        await bot.load_extension("cogs.leaderboard")
        await bot.load_extension("cogs.shop")
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
