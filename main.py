import asyncio
import logging

import discord
from discord.ext import commands

from config import DISCORD_TOKEN
from models import init_db
from report_cog import ClanRatingTracker

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")


async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    await bot.add_cog(ClanRatingTracker(bot))
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
