from datetime import datetime, timedelta, timezone, time

from discord.ext import commands, tasks

from config import CHANNEL_ID, CLAN_NAME
from frontend import diff_ratings
from models import insert_rating, get_last_rating, get_rating_at_time
from scraper import get_ratings


class ClanRatingTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hourly_report.start()
        self.daily_report.start()

    def cog_unload(self):
        self.hourly_report.cancel()
        self.daily_report.cancel()

    async def _send_report(self, timestamp, last_total, last_members):
        channel = self.bot.get_channel(CHANNEL_ID)
        # try:
        total_rating, members = get_ratings(CLAN_NAME)
        now = datetime.now(timezone(timedelta(hours=3))).replace(microsecond=0)
        if last_total is None:
            insert_rating(now, total_rating, members)
            await channel.send(f"Initial clan rating data stored.")
            return
        change_msg = diff_ratings(timestamp, last_total, last_members, total_rating, members)[0:2000]
        print(change_msg)
        if change_msg:
            insert_rating(now, total_rating, members)
            await channel.send(change_msg)
        # except Exception as e:
        #     logging.error(f"Error in check_ratings: {e}")

    @tasks.loop(time=list(
        [time(hour=(17 + x // 2 )%24, minute=00 + 30 * (x % 2), tzinfo=timezone(timedelta(hours=3))) for x in
         range((25 - 17) * 2)]))
    async def hourly_report(self):
        timestamp, last_total, last_members = get_last_rating()
        await self._send_report(timestamp, last_total, last_members)

    @tasks.loop(time=time(hour=1, minute=5, tzinfo=timezone(timedelta(hours=3))))
    # @tasks.loop(minutes=1)
    async def daily_report(self):
        timestamp, last_total, last_members = get_rating_at_time(datetime.now(timezone(timedelta(hours=3))) - timedelta(hours=2))
        await self._send_report(timestamp, last_total, last_members)

    @hourly_report.before_loop
    async def before_check_ratings(self):
        await self.bot.wait_until_ready()

    @daily_report.before_loop
    async def before_daily_report(self):
        await self.bot.wait_until_ready()
