import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from zoneinfo import ZoneInfo

from core.bot import bot
from core.config import TZ
from utils.api import api
from utils.fio_utils import fio_full_to_initials
from utils.schedule_utils import get_current_day, format_schedule_for_day, format_teacher_schedule_for_day
from utils.subscription import is_subscribed


scheduler = AsyncIOScheduler()


async def send_daily_schedule():

    now = datetime.now(ZoneInfo(TZ)).strftime("%H:%M")

    users = api.get_schedule_users(now)

    if not users:
        return

    day = get_current_day()

    if not day:
        return

    for user in users:
        user_id = user["user_id"]

        subscribed = await is_subscribed(bot.api, user_id)
        if not subscribed:
            continue

        teacher_fio = user.get("teacher_fio")
        if teacher_fio:
            schedule = api.get_teacher_schedule(fio_full_to_initials(teacher_fio))
            if not schedule:
                continue
            text = format_teacher_schedule_for_day(teacher_fio, schedule, day)
        else:
            group = user.get("group_name")
            if not group:
                continue
            schedule = api.get_schedule(group)
            if not schedule:
                continue
            text = format_schedule_for_day(group, schedule, day)

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
