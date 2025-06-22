"""
Frontend utilities for the AFI Tracker.

This module provides functions for generating reports and calculating member rating changes.
"""

import logging
from datetime import datetime
from typing import List, Tuple

import discord

from config import TIMEZONE

logger = logging.getLogger(__name__)

# Constants
MAX_REPORT_ENTRIES = 50


def get_member_delta(old_members: List[Tuple[str, int]], new_members: List[Tuple[str, int]]) -> List[
    Tuple[str, int, int]]:
    """
    Calculate the rating changes between two sets of member ratings.
    
    Args:
        old_members: List of (member_name, rating) tuples from the old rating
        new_members: List of (member_name, rating) tuples from the new rating
        
    Returns:
        List of (member_name, current_rating, delta) tuples, sorted by current rating
    """
    if not old_members or not new_members:
        logger.warning("Empty member list provided to get_member_delta")
        return []

    old_dict = dict(old_members)
    new_dict = dict(new_members)

    # Sort by new rating (descending)
    names = sorted(new_dict, key=lambda n: new_dict[n], reverse=True)

    table_entries = []
    for name in names:
        new_rating = new_dict.get(name, 0)
        old_rating = old_dict.get(name)

        if old_rating is not None:
            delta = new_rating - old_rating
        else:
            # New member
            delta = new_rating
            logger.info(f"New member detected: {name} with rating {new_rating}")

        if delta != 0:
            table_entries.append((name, new_rating, delta))

    # Add members who left the clan
    leavers = [(name, old_dict[name], -old_dict[name]) for name in old_dict if name not in new_dict]
    if leavers:
        logger.info(f"Members who left the clan: {', '.join(name for name, _, _ in leavers)}")

    table_entries.extend(leavers)
    return table_entries


def generate_report(
        old_time: datetime,
        old_total: int,
        old_members: List[Tuple[str, int]],
        new_total: int,
        new_members: List[Tuple[str, int]],
) -> discord.Embed:
    """
    Generate a Discord embed report comparing old and new clan ratings.
    
    Args:
        old_time: Timestamp of the old rating
        old_total: Total clan rating from the old rating
        old_members: List of (member_name, rating) tuples from the old rating
        new_total: Total clan rating from the new rating
        new_members: List of (member_name, rating) tuples from the new rating
        
    Returns:
        Discord embed containing the report
        
    Raises:
        ValueError: If the input data is invalid
    """
    if not old_members or not new_members:
        raise ValueError("Empty member list provided to generate_report")

    now = datetime.now(TIMEZONE)
    title = f"**{now:%H:%M %d.%m.%Y}**"

    # Get the 20th member's rating if available
    member_20_rating = None
    if len(new_members) >= 20:
        member_20_rating = new_members[19][1]
        logger.debug(f"20th member rating: {member_20_rating}")

    # Build description
    description_parts = [
        f"С {old_time} полк набрал {new_total - old_total} очков.",
        f"Всего у полка {new_total} очков."
    ]

    if member_20_rating is not None:
        description_parts.append(f"Конец топ-20 = {member_20_rating}.")

    description = "\n".join(description_parts)

    # Calculate member deltas and limit to MAX_REPORT_ENTRIES
    member_delta = get_member_delta(old_members, new_members)[:MAX_REPORT_ENTRIES]

    # Create fields for the embed
    if not member_delta:
        logger.info("No rating changes to report")
        embed = discord.Embed(
            title=title,
            description=description + "\n\nНет изменений в рейтинге участников."
        )
        return embed

    # Extract data for the three columns
    items_names = [str(x[0]) for x in member_delta]
    field_names = "```\n" + "\n".join(items_names) + "```"

    items_ratings = [str(x[1]) for x in member_delta]
    field_ratings = "```\n" + "\n".join(items_ratings) + "```"

    items_diffs = []
    for diff in [x[2] for x in member_delta]:
        if diff > 0:
            # Green background
            items_diffs.append(f"\u001b[2;32m+{diff}\u001b[0m")
        elif diff < 0:
            # Red background
            items_diffs.append(f"\u001b[2;31m{diff}\u001b[0m")
        else:
            items_diffs.append(f"{diff}")
    field_diffs = "```ansi\n" + "\n".join(items_diffs) + "```"

    # Create the embed
    embed = discord.Embed(
        title=title,
        description=description,
    )

    # Add fields with appropriate names
    embed.add_field(name=" ", inline=True, value=field_names)
    embed.add_field(name=" ", inline=True, value=field_ratings)
    embed.add_field(name=" ", inline=True, value=field_diffs)

    logger.info(f"Generated report with {len(member_delta)} entries")
    return embed
