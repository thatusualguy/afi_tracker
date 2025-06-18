# Cogs Module
"""
Discord bot cogs for the AFI Tracker.
"""

from .report_cog import ClanRatingTracker
from .commands_cog import SlashCommands

__all__ = ["ClanRatingTracker", "SlashCommands"]
