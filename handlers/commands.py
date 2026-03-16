from vkbottle.bot import Message
from core.bot import bot

from keyboards.admin import admin_keyboard
from utils.api import api
from keyboards.main import create_main_keyboard

from utils.fio_utils import fio_full_to_initials
from utils.schedule_utils import (
    get_current_day,
    get_tomorrow_day,
    format_schedule_for_day,
    format_teacher_schedule_for_day,
)

DAY_MAP = {
    "📅 ПН": "Понедельник",
    "📅 ВТ": "Вторник",
    "📅 СР": "Среда",
    "📅 ЧТ": "Четверг",
    "📅 ПТ": "Пятница",
    "📅 СБ": "Суббота",
}


def get_menu(user):
    is_admin = user.get("role") == "admin"
    is_teacher = user.get("role") in ["teacher", "admin"]
    return create_main_keyboard(is_teacher, is_admin).get_json()


# =========================
# СТУДЕНТ
# =========================


def get_student_schedule(user, day):

    group = user.get("group_name")

    if not group:
        return "❌ Сначала выберите группу"

    sch = api.get_schedule(group)

    return format_schedule_for_day(group, sch or {}, day)


# =========================
# ПРЕПОДАВАТЕЛЬ
# =========================


def get_teacher_schedule(user, day):

    teacher_fio = user.get("teacher_fio")

    if not teacher_fio:
        return "❌ У вас не указано ФИО преподавателя"

    sch = api.get_teacher_schedule(fio_full_to_initials(teacher_fio))

    return format_teacher_schedule_for_day(
        teacher_fio,
        sch or {},
        day,
    )


# =========================
# ОБЩИЙ ОБРАБОТЧИК
# =========================


async def send_schedule(message: Message, user, day):

    is_teacher = user.get("role") in ["teacher", "admin"]

    if is_teacher:
        text = get_teacher_schedule(user, day)
    else:
        text = get_student_schedule(user, day)

    await message.answer(text, keyboard=get_menu(user))


# =========================
# СЕГОДНЯ
# =========================


@bot.on.message(text="📅 Сегодня")
async def today_schedule(message: Message, user):

    today = get_current_day()

    if not today:
        tomorrow = get_tomorrow_day()

        if tomorrow:
            await send_schedule(message, user, tomorrow)
            return

        await message.answer(
            "🎉 Сегодня воскресенье — выходной!",
            keyboard=get_menu(user),
        )
        return

    await send_schedule(message, user, today)


@bot.on.message(text="👑 Админ панель")
async def admin_panel(message: Message, user):

    if user.get("role") != "admin":
        await message.answer("❌ У вас нет прав администратора.")
        return

    await message.answer(
        "👑 Панель администратора\n\nВыберите действие:",
        keyboard=admin_keyboard().get_json(),
    )


# =========================
# ДНИ НЕДЕЛИ
# =========================


@bot.on.message(text=list(DAY_MAP.keys()))
async def weekday_schedule(message: Message, user):

    day = DAY_MAP.get(message.text)

    await send_schedule(message, user, day)
