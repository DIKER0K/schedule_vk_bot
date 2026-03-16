from vkbottle.bot import Message
from core.bot import bot

from utils.api import api
from utils.schedule_utils import (
    get_current_day,
    format_schedule_for_day,
    get_tomorrow_day,
)
from keyboards.main import create_main_keyboard


def get_menu(user):
    is_admin = user.get("role") == "admin"
    is_teacher = user.get("role") in ["teacher", "admin"]
    return create_main_keyboard(is_teacher, is_admin).get_json()


def get_group(user):
    return user.get("group_name")


# @bot.on.message()
# async def debug(message: Message):
#     print("MESSAGE:", message.text)


@bot.on.message(text="📅 Сегодня")
async def today_schedule(message: Message, user):

    group = get_group(user)

    if not group:
        await message.answer("❌ Сначала выберите группу")
        return

    today = get_current_day()

    # если воскресенье
    if not today:
        tomorrow = get_tomorrow_day()

        if tomorrow:
            sch = api.get_schedule(group)

            text = format_schedule_for_day(group, sch or {}, tomorrow)

            await message.answer(
                f"📅 Сегодня воскресенье! Завтра ({tomorrow}):\n\n{text}",
                keyboard=get_menu(user),
            )
            return

        await message.answer(
            "🎉 Сегодня воскресенье — выходной!",
            keyboard=get_menu(user),
        )
        return

    sch = api.get_schedule(group)

    text = format_schedule_for_day(group, sch or {}, today)

    await message.answer(text, keyboard=get_menu(user))


DAY_MAP = {
    "📅 ПН": "Понедельник",
    "📅 ВТ": "Вторник",
    "📅 СР": "Среда",
    "📅 ЧТ": "Четверг",
    "📅 ПТ": "Пятница",
    "📅 СБ": "Суббота",
}


@bot.on.message(text=list(DAY_MAP.keys()))
async def weekday_schedule(message: Message, user):

    group = get_group(user)

    if not group:
        await message.answer("❌ Сначала выберите группу")
        return

    day = DAY_MAP.get(message.text)

    sch = api.get_schedule(group)

    text = format_schedule_for_day(group, sch or {}, day)

    await message.answer(text, keyboard=get_menu(user))
