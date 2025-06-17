"""
AFI Tracker - Discord bot for tracking War Thunder clan ratings.

This is the main entry point for the application.
"""

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler

import discord
from discord.ext import commands

from afi_tracker.config import DISCORD_TOKEN
from afi_tracker.database import init_db
from afi_tracker.bot import ClanRatingTracker


def setup_logging():
    """
    Set up logging configuration.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        'afi_tracker.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


async def main():
    """
    Main entry point for the application.
    """
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting AFI Tracker")
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # Set up Discord bot
    intents = discord.Intents.default()
    intents.message_content = True  # Enable message content intent if needed
    
    bot = commands.Bot(command_prefix="/", intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user}")
    
    # Add cogs
    try:
        await bot.add_cog(ClanRatingTracker(bot))
    except Exception as e:
        logger.error(f"Failed to add cog: {e}")
        return
    
    # Start the bot
    try:
        if not DISCORD_TOKEN:
            logger.error("Discord token not set. Please set it in config.yaml or environment variable.")
            return
        
        logger.info("Connecting to Discord...")
        await bot.start(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Unhandled exception: {e}")