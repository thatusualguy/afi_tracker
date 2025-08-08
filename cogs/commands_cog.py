"""
Discord bot cog for slash commands.

This module defines the SlashCommands cog, which handles user-invoked slash commands
like /today that provide on-demand information without affecting the automated tracking system.
"""

import logging
import os
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from config import CLAN_NAME, TIMEZONE, day_start, DB_FILE
from models import get_rating_at_time
from scraper import get_ratings
from utils import get_member_delta, generate_report

logger = logging.getLogger(__name__)


class SlashCommands(commands.Cog):
    """
    Discord cog for handling slash commands.

    This cog provides user-invoked commands that fetch and display information
    on-demand without affecting the automated tracking system.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initialize the SlashCommands cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        logger.info("Initializing SlashCommands cog")

    def cog_unload(self):
        """
        Clean up when the cog is unloaded.
        """
        logger.info("Unloading SlashCommands cog")

    @app_commands.command(name="сегодня", description="Изменение рейтинга с начала дня на текущий момент")
    async def today_command(self, interaction: discord.Interaction):
        """
        Slash command to show rating changes from start of day to current moment.
        This command fetches current ratings without storing them in the database.

        Args:
            interaction: Discord interaction context
        """
        logger.info(f"Today command invoked by {interaction.user}")

        try:
            # Defer the response since this might take a while
            await interaction.response.defer()

            # Get start of day time
            now = datetime.now(TIMEZONE)
            start_of_day = now.replace(hour=day_start[0] + 1, minute=day_start[1], second=0, microsecond=0)
            if now.hour < 2:
                start_of_day = start_of_day - timedelta(days=1)

            # Get rating from start of day from database
            old_timestamp, old_total, old_members = get_rating_at_time(start_of_day)

            if old_total is None or old_members is None or old_timestamp is None:
                await interaction.followup.send("Нет данных о рейтинге на начало дня.")
                return

            # Fetch current ratings without storing them
            logger.info(f"Fetching current ratings for clan {CLAN_NAME} (not storing)")
            new_rating, new_members = get_ratings(CLAN_NAME)

            # Calculate member changes
            member_delta = get_member_delta(old_members, new_members)
            if not member_delta:
                await interaction.followup.send("Нет изменений в рейтинге с начала дня.")
                return

            # Generate and send the report
            try:
                report_embed = generate_report(old_timestamp, old_total, old_members, new_rating, new_members)
                await interaction.followup.send(embed=report_embed)
                logger.info(f"Sent today report with {len(member_delta)} entries")
            except Exception as e:
                logger.error(f"Failed to generate or send today report: {e}")
                await interaction.followup.send(f"Ошибка при создании отчета: {e}")

        except Exception as e:
            logger.error(f"Error in today_command: {e}")
            await interaction.followup.send(f"Произошла ошибка при получении рейтинга: {e}")

    @app_commands.command(name="сравнить", description="Сравнить текущий рейтинг с указанной датой и временем")
    async def compare_command(
            self,
            interaction: discord.Interaction,
            compare_date: str,
            compare_time: str = "02:00"
    ):
        """
        Slash command to compare current ratings with ratings at a specified date and time.
        
        Args:
            interaction: Discord interaction context
            compare_date: Date in DD.MM.YYYY format
            compare_time: Time in HH:MM format (optional, defaults to 02:00)
        """
        logger.info(f"Compare command invoked by {interaction.user} for date {compare_date} time {compare_time}")

        if compare_date.count('.') < 3:
            compare_date += '.' + str(datetime.now().year)

        try:
            # Defer the response since this might take a while
            await interaction.response.defer()

            # Parse and validate date
            try:
                day, month, year = map(int, compare_date.split('.'))
                hour, minute = map(int, compare_time.split(':'))

                # Create target datetime with timezone
                target_datetime = datetime(year, month, day, hour, minute, tzinfo=TIMEZONE)

                # Check if target date is in the future
                now = datetime.now(TIMEZONE)
                if target_datetime > now:
                    await interaction.followup.send("Нельзя сравнивать с будущей датой.")
                    return

            except ValueError as e:
                await interaction.followup.send(
                    "Неверный формат даты или времени. Используйте формат ДД.ММ.ГГГГ для даты и ЧЧ:ММ для времени."
                )
                logger.warning(f"Invalid date/time format from {interaction.user}: {compare_date} {compare_time}")
                return

            # Get historical rating from database
            old_timestamp, old_total, old_members = get_rating_at_time(target_datetime)

            if old_total is None or old_members is None or old_timestamp is None:
                await interaction.followup.send(f"Нет данных о рейтинге на {compare_date} {compare_time}.")
                return

            # Fetch current ratings without storing them
            logger.info(f"Fetching current ratings for clan {CLAN_NAME} (not storing)")
            new_rating, new_members = get_ratings(CLAN_NAME)

            # Calculate member changes
            member_delta = get_member_delta(old_members, new_members)
            if not member_delta:
                await interaction.followup.send(f"Нет изменений в рейтинге с {compare_date} {compare_time}.")
                return

            # Generate and send the report
            try:
                report_embed = generate_report(old_timestamp, old_total, old_members, new_rating, new_members)
                await interaction.followup.send(embed=report_embed)
                logger.info(f"Sent compare report with {len(member_delta)} entries for {compare_date} {compare_time}")
            except Exception as e:
                logger.error(f"Failed to generate or send compare report: {e}")
                await interaction.followup.send(f"Ошибка при создании отчета: {e}")

        except Exception as e:
            logger.error(f"Error in compare_command: {e}")
            await interaction.followup.send(f"Произошла ошибка при сравнении рейтинга: {e}")

    @app_commands.command(name="database", description="Send the database file to chat")
    async def database_command(self, interaction: discord.Interaction):
        """
        Slash command to send the database file to the Discord channel.
        
        Args:
            interaction: Discord interaction context
        """
        logger.info(f"Database command invoked by {interaction.user}")

        try:
            # Defer the response since file upload might take a while
            await interaction.response.defer()

            # Check if database file exists
            if not os.path.exists(DB_FILE):
                await interaction.followup.send("Database file not found.")
                logger.warning(f"Database file not found at {DB_FILE}")
                return

            # Get file size for logging
            file_size = os.path.getsize(DB_FILE)
            logger.info(f"Sending database file: {DB_FILE} (size: {file_size} bytes)")

            # Create Discord file object and send it
            with open(DB_FILE, 'rb') as f:
                discord_file = discord.File(f, filename=os.path.basename(DB_FILE))
                await interaction.followup.send(
                    content=f"Database file: {os.path.basename(DB_FILE)}",
                    file=discord_file
                )

            logger.info(f"Successfully sent database file to {interaction.user}")

        except Exception as e:
            logger.error(f"Error in database_command: {e}")
            await interaction.followup.send(f"Error sending database file: {e}")
