"""
Configuration management for the AFI Tracker.

This module handles loading configuration from YAML files and environment variables,
and provides access to configuration values throughout the application.
"""

import logging
import os
from datetime import timezone, timedelta, time
from typing import Dict, Any, Tuple, List

import yaml

logger = logging.getLogger(__name__)

# Default configuration file path
CONFIG_FILE = "config.yaml"


def load_config(filename: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        filename: Path to the YAML configuration file
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the configuration file contains invalid YAML
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {filename}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {filename}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise


# Load configuration
try:
    config = load_config(CONFIG_FILE)
except (FileNotFoundError, yaml.YAMLError):
    logger.warning("Using default configuration")
    config = {}

# Configuration values with defaults and environment variable overrides
CLAN_NAME: str = os.environ.get("AFI_CLAN_NAME") or config.get("clan_name", "Anthems For Insubordinates")
DISCORD_TOKEN: str = os.environ.get("AFI_DISCORD_TOKEN") or config.get("discord_token", "")
CHANNEL_ID: int = int(os.environ.get("AFI_CHANNEL_ID") or config.get("channel_id", 0))

# Database configuration
DB_FILE: str = os.environ.get("AFI_DB_FILE") or config.get("db_file", "clan_ratings.db")

# Time configuration
TIMEZONE_OFFSET: int = int(os.environ.get("AFI_TIMEZONE_OFFSET") or config.get("timezone_offset", 3))
TIMEZONE = timezone(timedelta(hours=TIMEZONE_OFFSET))

# Day start and end times (hour, minute)
day_start: Tuple[int, int] = tuple(config.get("day_start", (17, 0)))
day_end: Tuple[int, int] = tuple(config.get("day_end", (1, 0)))


# Report times
def _generate_report_times() -> List[time]:
    """Generate a list of times for regular reports throughout the day."""
    interval_minutes = int(os.environ.get("AFI_REPORT_INTERVAL") or config.get("report_interval", 30))
    return [
        time(hour=x // 60, minute=x % 60, tzinfo=TIMEZONE)
        for x in range(0, 24 * 60, interval_minutes)
    ]


regular_report_times: List[time] = _generate_report_times()
end_of_day_report_time: time = time(
    hour=int(os.environ.get("AFI_END_OF_DAY_HOUR") or config.get("end_of_day_hour", 1)),
    minute=int(os.environ.get("AFI_END_OF_DAY_MINUTE") or config.get("end_of_day_minute", 5)),
    tzinfo=TIMEZONE
)

# Validate configuration
if not DISCORD_TOKEN:
    logger.warning("Discord token not set. Bot will not be able to connect to Discord.")

if CHANNEL_ID == 0:
    logger.warning("Channel ID not set. Bot will not be able to send messages.")

if not os.path.exists(os.path.dirname(DB_FILE)) and os.path.dirname(DB_FILE):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    logger.info(f"Created directory for database file: {os.path.dirname(DB_FILE)}")
