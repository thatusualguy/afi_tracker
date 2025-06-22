# AFI Tracker

A Discord bot for tracking War Thunder clan ratings and reporting changes.

## Features

- Periodically fetches clan ratings from the War Thunder website
- Stores ratings in a SQLite database
- Generates reports on rating changes
- Sends reports to a Discord channel
- Provides both regular (hourly) and daily reports

## Project Structure

The project is organized into the following modules:

- `afi_tracker/` - Main package
    - `config/` - Configuration management
    - `database/` - Database models and operations
    - `scraping/` - Web scraping functionality
    - `utils/` - Utility functions for report generation
    - `bot/` - Discord bot functionality
- `main.py` - Entry point for the application
- `config.yaml` - Configuration file
- `requirements.txt` - Dependencies

## Installation

1. Clone the repository
   ```shell
   git clone https://github.com/thatusualguy/afi_tracker.git
   ```
2. Configure the bot by editing `config.yaml`

3. Launch deploy.sh script:
   ```shell
   .\afi_tracker\deploy.sh
   ```
   
    - Pulls latest version
    - Creates venv
    - Installs packages
    - Launch main.py in tmux

## Configuration

Edit the `config.yaml` file to configure the bot:

```yaml
# Discord configuration
clan_name: "Your Clan Name"
discord_token: "Your Discord Bot Token"
channel_id: 123456789012345678  # Discord channel ID

# Database configuration
db_file: "clan_ratings.db"

# Time configuration
timezone_offset: 3  # Hours from UTC
day_start: [ 17, 0 ]  # Hour, minute
day_end: [ 1, 0 ]  # Hour, minute
report_interval: 30  # Minutes between reports
end_of_day_hour: 1
end_of_day_minute: 5

# Scraper configuration
max_retries: 3
retry_delay: 5  # Seconds between retry attempts

# Report configuration
max_report_entries: 50
```

## Usage

Run the bot:

   ```shell
   .\afi_tracker\deploy.sh
   ```

The bot will:

1. Initialize the database if it doesn't exist
2. Connect to Discord
3. Start fetching clan ratings at the configured intervals
4. Send reports to the configured Discord channel