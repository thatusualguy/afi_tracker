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
