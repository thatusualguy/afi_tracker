from datetime import datetime

from discord.ext import commands, tasks

from config import CHANNEL_ID, CLAN_NAME, TIMEZONE, day_start, regular_report_times, end_of_day_report_time
from frontend import get_member_delta, generate_report
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

    async def _send_report(self, old_time, old_total, old_members):
        channel = self.bot.get_channel(CHANNEL_ID)

        new_rating, new_members = get_ratings(CLAN_NAME)

        insert_rating(new_rating, new_members)

        # if DB is clear
        if old_total is None:
            await channel.send(f"Чистый запуск. Данные сохранены.")
            return

        member_delta = get_member_delta(old_members, new_members)
        if len(member_delta) == 0:
            return

        report_embed = generate_report(old_time, old_total, old_members, new_rating, new_members)
        await channel.send(embed=report_embed)

    @tasks.loop(time=regular_report_times)
    async def hourly_report(self):
        timestamp, last_total, last_members = get_last_rating()
        await self._send_report(timestamp, last_total, last_members)

    @tasks.loop(time=end_of_day_report_time)
    async def daily_report(self):
        now = datetime.now(TIMEZONE)
        start_of_day = now.replace(hour=day_start[0], minute=day_start[1], second=0, microsecond=0)
        old_timestamp, old_total, old_members = get_rating_at_time(start_of_day)
        await self._send_report(old_timestamp, old_total, old_members)

    @hourly_report.before_loop
    async def before_check_ratings(self):
        await self.bot.wait_until_ready()

    @daily_report.before_loop
    async def before_daily_report(self):
        await self.bot.wait_until_ready()
