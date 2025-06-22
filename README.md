# AFI Tracker

A Discord bot for tracking War Thunder clan ratings and reporting changes.

Built with the **[discord.py](https://github.com/Rapptz/discord.py)** library for Discord integration and *
*[BeautifulSoup](https://github.com/wention/BeautifulSoup4)** for parsing webpage.

## Features

- Periodically fetches clan ratings from the War Thunder website
- Stores ratings in an SQLite database
- Generates reports on rating changes
- Sends reports to a Discord channel
- Provides both regular (hourly) and daily reports
- Interactive slash commands for on-demand information

## Available Commands

The bot provides the following slash commands:

- `/сегодня` - Shows rating changes from the start of the day to the current moment
    - Displays member rating changes without affecting the automated tracking
    - Provides real-time comparison with the beginning of the day

## Project Structure

The project is organized with the following files and directories:

- `main.py` - Entry point for the application
- `config.py` - Configuration management
- `config.yaml` - Configuration file
- `models.py` - Database models and operations
- `scraper.py` - Web scraping functionality for War Thunder ratings
- `utils.py` - Utility functions for report generation
- `cogs/` - Discord bot cogs (modular components)
    - `commands_cog.py` - Slash commands handling
    - `report_cog.py` - Automated reporting functionality
- `deploy.sh` - Deployment script
- `clan_ratings.db` - SQLite database (created automatically)
- `afi_tracker.log` - Application logs

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
    - Launches main.py in tmux

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
