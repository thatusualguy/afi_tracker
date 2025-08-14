"""
Discord bot cog for tracking clan ratings and sending reports.

This module defines the ClanRatingTracker cog, which periodically fetches
clan ratings and sends reports to a Discord channel.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from discord.ext import commands, tasks

from config import CHANNEL_ID, CLAN_NAME, TIMEZONE, day_start, regular_report_times, end_of_day_report_time
from models import get_last_rating, get_rating_at_time, insert_rating
from scraper import get_ratings
from utils import get_member_delta, generate_report

logger = logging.getLogger(__name__)


class ClanRatingTracker(commands.Cog):
    """
    Discord cog for tracking clan ratings and sending reports.

    This cog periodically fetches clan ratings and sends reports to a Discord channel.
    It provides two types of reports:
    1. Hourly reports comparing to the last rating
    2. Daily reports comparing to the rating at the start of the day
    """

    def __init__(self, bot: commands.Bot):
        """
        Initialize the ClanRatingTracker cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        logger.info("Initializing ClanRatingTracker cog")
        self.hourly_report.start()
        self.daily_report.start()

    def cog_unload(self):
        """
        Clean up when the cog is unloaded.
        """
        logger.info("Unloading ClanRatingTracker cog")
        self.hourly_report.cancel()
        self.daily_report.cancel()

    async def _send_report(self, old_time: Optional[datetime], old_total: Optional[int],
                           old_members: Optional[List[Tuple[str, int]]], silence = False):
        """
        Fetch new ratings and send a report comparing to old ratings.

        Args:
            old_time: Timestamp of the old rating
            old_total: Total clan rating from the old rating
            old_members: List of (member_name, rating) tuples from the old rating
        """
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            logger.error(f"Channel with ID {CHANNEL_ID} not found")
            return

        try:
            logger.info(f"Fetching new ratings for clan {CLAN_NAME}")
            new_rating, new_members = get_ratings(CLAN_NAME)

            # Store the new rating in the database
            try:
                insert_rating(new_rating, new_members)
                logger.info(f"Stored new rating: {new_rating} with {len(new_members)} members")
            except Exception as e:
                logger.error(f"Failed to store rating in database: {e}")
                await channel.send(f"Ошибка при сохранении рейтинга: {e}")
                return

            # If this is the first rating (no old data), acknowledge
            if old_total is None or old_members is None or old_time is None:
                logger.info("No previous rating data available")
                await channel.send("Чистый запуск. Данные сохранены.")
                return

            # Calculate member changes
            member_delta = get_member_delta(old_members, new_members)
            if not member_delta:
                logger.info("No rating changes to report")
                return

            # Generate and send the report
            if silence:
                return
            try:
                report_embed = generate_report(old_time, old_total, old_members, new_rating, new_members)
                await channel.send(embed=report_embed)
                logger.info(f"Sent report with {len(member_delta)} entries")
            except Exception as e:
                logger.error(f"Failed to generate or send report: {e}")
                await channel.send(f"Ошибка при создании отчета: {e}")

        except Exception as e:
            logger.error(f"Error in _send_report: {e}")
            await channel.send(f"Произошла ошибка при получении рейтинга: {e}")

    @tasks.loop(time=regular_report_times)
    async def hourly_report(self):
        """
        Task that runs at regular intervals to fetch and report rating changes.
        """
        logger.info("Running hourly report")
        try:
            timestamp, last_total, last_members = get_last_rating()
            await self._send_report(timestamp, last_total, last_members, silence=True)
        except Exception as e:
            logger.error(f"Error in hourly_report: {e}")

    @tasks.loop(time=end_of_day_report_time)
    async def daily_report(self):
        """
        Task that runs at the end of the day to report daily rating changes.
        """
        logger.info("Running daily report")
        try:
            now = datetime.now(TIMEZONE)
            start_of_day = now.replace(hour=day_start[0] + 1, minute=day_start[1], second=0, microsecond=0)
            if now.hour < 2:
                start_of_day = start_of_day - timedelta(days=1)
            old_timestamp, old_total, old_members = get_rating_at_time(start_of_day)
            await self._send_report(old_timestamp, old_total, old_members)
        except Exception as e:
            logger.error(f"Error in daily_report: {e}")

    @hourly_report.before_loop
    async def before_hourly_report(self):
        """
        Wait for the bot to be ready before starting the hourly report loop.
        """
        logger.info("Waiting for bot to be ready before starting hourly report")
        await self.bot.wait_until_ready()

    @daily_report.before_loop
    async def before_daily_report(self):
        """
        Wait for the bot to be ready before starting the daily report loop.
        """
        logger.info("Waiting for bot to be ready before starting daily report")
        await self.bot.wait_until_ready()
