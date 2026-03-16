import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

from core.bot import bot
from utils.api import api
from utils.schedule_utils import get_current_day, format_schedule_for_day


scheduler = AsyncIOScheduler()


async def send_daily_schedule():

    now = datetime.now().strftime("%H:%M")

    users = api.get_schedule_users(now)

    if not users:
        return

    day = get_current_day()

    if not day:
        return

    for user in users:
        group = user.get("group_name")

        if not group:
            continue

        user_id = user["user_id"]

        schedule = api.get_schedule(group)

        text = format_schedule_for_day(group, schedule or {}, day)

        try:
            await bot.api.messages.send(
                peer_id=user_id,
                message=text,
                random_id=0,
            )

        except Exception as e:
            print("send schedule error:", e)


def start_scheduler():

    loop = asyncio.get_event_loop()

    scheduler.configure(event_loop=loop)

    scheduler.add_job(
        send_daily_schedule,
        "interval",
        minutes=1,
    )

    scheduler.start()
