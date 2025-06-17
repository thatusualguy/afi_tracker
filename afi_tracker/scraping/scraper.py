"""
Web scraping functionality for the AFI Tracker.

This module handles fetching clan ratings from the War Thunder website.
"""

import logging
import time
from typing import Tuple, List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class ScraperError(Exception):
    """Exception raised for errors in the scraper."""
    pass


def get_ratings(clan_name: str, retries: int = MAX_RETRIES) -> tuple[int, list[tuple[str, int]]] | None:
    """
    Fetch clan ratings from the War Thunder website.
    
    Args:
        clan_name: The name of the clan to fetch ratings for
        retries: Number of retry attempts for failed requests
        
    Returns:
        Tuple of (total_rating, members) where members is a list of (member_name, rating) tuples
        
    Raises:
        ScraperError: If the ratings cannot be fetched after all retries
    """
    url = f"https://warthunder.com/en/community/claninfo/{quote(clan_name)}"
    headers = {"User-Agent": USER_AGENT}
    
    logger.info(f"Fetching ratings for clan: {clan_name}")
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            return _parse_ratings(response.text)
            
        except RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to fetch ratings after {retries} attempts")
                raise ScraperError(f"Failed to fetch ratings: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ScraperError(f"Error processing ratings: {e}") from e
    return None


def _parse_ratings(html_content: str) -> Tuple[int, List[Tuple[str, int]]]:
    """
    Parse clan ratings from HTML content.
    
    Args:
        html_content: HTML content from the War Thunder clan info page
        
    Returns:
        Tuple of (total_rating, members) where members is a list of (member_name, rating) tuples
        
    Raises:
        ScraperError: If the HTML cannot be parsed or required elements are not found
    """
    try:
        soup = BeautifulSoup(html_content, "lxml")
        
        # Extract total rating
        total_rating_tags = soup.select("div.squadrons-counter__value")
        if not total_rating_tags:
            raise ScraperError("Total rating element not found")
        
        total_rating_tag = total_rating_tags[0]
        try:
            total_rating: int = int(total_rating_tag.text.strip())
        except ValueError as e:
            raise ScraperError(f"Invalid total rating value: {total_rating_tag.text.strip()}") from e
        
        # Extract member ratings
        members = soup.select("div.squadrons-members__grid-item")
        if not members or len(members) < 7:
            raise ScraperError("Member elements not found or insufficient data")
        
        try:
            names = [member.text.strip() for member in members[7::6]]
            ratings = [int(member.text.strip()) for member in members[8::6]]
        except (ValueError, IndexError) as e:
            raise ScraperError(f"Error extracting member data: {e}") from e
        
        if len(names) != len(ratings):
            raise ScraperError(f"Mismatch between names ({len(names)}) and ratings ({len(ratings)})")
        
        result = list(zip(names, ratings))
        result.sort(key=lambda member: member[1], reverse=True)
        
        logger.info(f"Successfully parsed ratings: total={total_rating}, members={len(result)}")
        return total_rating, result
        
    except Exception as e:
        if not isinstance(e, ScraperError):
            logger.error(f"Error parsing HTML: {e}")
            raise ScraperError(f"Error parsing HTML: {e}") from e
        raise