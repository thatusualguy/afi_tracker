"""
Discord bot cog for slash commands.

This module defines the SlashCommands cog, which handles user-invoked slash commands
like /today that provide on-demand information without affecting the automated tracking system.
"""

import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from afi_tracker.config import CLAN_NAME, TIMEZONE, day_start
from afi_tracker.database import get_rating_at_time
from afi_tracker.scraping import get_ratings
from afi_tracker.utils import get_member_delta, generate_report

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
            start_of_day = now.replace(hour=day_start[0], minute=day_start[1], second=0, microsecond=0)

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