from datetime import timezone, timedelta, time

import yaml


def load_config(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG_FILE = "config.yaml"
config = load_config(CONFIG_FILE)
CLAN_NAME: str = config["clan_name"]
DISCORD_TOKEN: str = config["discord_token"]
CHANNEL_ID: int = config["channel_id"]

DB_FILE = "clan_ratings.db"

TIMEZONE = timezone(timedelta(hours=3))
day_start = (17, 00)
day_end = (1, 0)
regular_report_times = [time(hour=x // 60, minute=x // 30 % 2 * 30, tzinfo=TIMEZONE) for x in
                        range(0, 24 * 60, 30)]
end_of_day_report_time = regular_report_times[2].replace(minute=5)
