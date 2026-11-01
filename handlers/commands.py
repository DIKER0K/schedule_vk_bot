from datetime import datetime
from zoneinfo import ZoneInfo

from vkbottle.bot import Message, MessageEvent
from core.bot import bot

from keyboards.admin import admin_keyboard
from utils.api import APIError, api
from keyboards.main import create_main_keyboard
from keyboards.bells import bell_lessons_keyboard, BELL_LESSONS_CACHE

from core.config import TZ
from utils.fio_utils import fio_full_to_initials
from utils.schedule_utils import (
    date_for_day,
    get_current_day,
    get_tomorrow_day,
    format_schedule_error,
    format_schedule_for_day,
    format_teacher_schedule_error,
    format_teacher_schedule_for_day,
)
from utils.subscription import is_subscribed, get_subscribe_message


def _minutes_between(now: datetime, hhmm: str) -> int:
    """Сколько минут от now до HH:MM того же дня."""
    h, m = map(int, hhmm.split(":"))
    then = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return int(max(0, (then - now).total_seconds() // 60))

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

    # спрашиваем расписание ровно на ту дату, которая соответствует дню:
    # бэкенд выбирает версию приказа по дате, а не по «сейчас»
    date_str = date_for_day(day)

    try:
        sch = api.get_schedule(group, date=date_str, raise_on_error=True)
    except APIError as e:
        return format_schedule_error(group, day, e.detail)

    return format_schedule_for_day(group, sch or {}, day)


# =========================
# ПРЕПОДАВАТЕЛЬ
# =========================


def get_teacher_schedule(user, day):

    teacher_fio = user.get("teacher_fio")

    if not teacher_fio:
        return "❌ У вас не указано ФИО преподавателя"

    # как и для студентов: спрашиваем расписание ровно на дату этого дня,
    # иначе бэкенд отдаёт версию на «сегодня»
    date_str = date_for_day(day)

    try:
        sch = api.get_teacher_schedule(
            fio_full_to_initials(teacher_fio),
            date=date_str,
            raise_on_error=True,
        )
    except APIError as e:
        return format_teacher_schedule_error(teacher_fio, day, e.detail)

    return format_teacher_schedule_for_day(
        teacher_fio,
        sch or {},
        day,
    )


# =========================
# ОБЩИЙ ОБРАБОТЧИК
# =========================


async def send_schedule(message: Message, user, day):

    subscribed = await is_subscribed(message.ctx_api, message.from_id)
    if not subscribed:
        await message.answer(get_subscribe_message(), keyboard=get_menu(user))
        return

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


@bot.on.message(text="🔔 Когда звонок")
async def next_bell(message: Message, user):

    data = api.get_next_bell()

    if not data:
        await message.answer(
            "😔 Не удалось получить расписание звонков.\nПопробуйте чуть позже.",
            keyboard=get_menu(user),
        )
        return

    text = data.get("message")

    if not text:
        # Бэкенд старый или ответ неполный — собираем текст сами
        event = data.get("current_event") or {}
        nxt = data.get("next_bell") or {}
        lines = [f"🕒 Сейчас: {data.get('current_time', '?')}"]

        if event.get("start") and event.get("end"):
            lines.append(f"📍 Идёт: {event['start']}–{event['end']}")

        if nxt.get("time"):
            left = nxt.get("in_minutes")
            tail = f" (через {left} мин)" if left is not None else ""
            lines.append(f"🔔 Следующий звонок: {nxt['time']}{tail}")
        else:
            lines.append("🌙 Звонков больше нет")

        text = "\n".join(lines)

    kb = bell_lessons_keyboard(data, user_id=message.from_id)

    if kb is None:
        await message.answer(text, keyboard=get_menu(user))
        return

    # кнопки пар — прямо на сообщении со временем звонка.
    # Главное меню (обычная клавиатура) остаётся в поле ввода с прошлого
    # сообщения: VK не убирает её, пока бот не пришлёт новую.
    await message.answer(text, keyboard=kb.get_json())


@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload_contains={"cmd": "bell_pair_info"},
)
async def bell_pair_info(event: MessageEvent):
    """Клик по кнопке «Nп»: время пары и сколько до неё осталось."""
    number = (event.object.payload or {}).get("number")
    slot = BELL_LESSONS_CACHE.get((event.object.user_id, number))

    if not slot:
        await event.send_empty_answer()
        await event.send_message(
            "⌛ Данные устарели, спросите «Когда звонок» ещё раз"
        )
        return

    now = datetime.now(ZoneInfo(TZ))
    start, end = slot["start"], slot["end"]

    # тот же день, зона — как у now (иначе сравнение aware/naive падает)
    start_dt = datetime.strptime(f"{now:%Y-%m-%d} {start}", "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(TZ)
    )
    end_dt = datetime.strptime(f"{now:%Y-%m-%d} {end}", "%Y-%m-%d %H:%M").replace(
        tzinfo=ZoneInfo(TZ)
    )

    # ответ — отдельным сообщением, не всплывашкой
    await event.send_empty_answer()

    if now < start_dt:
        left = _minutes_between(now, start)
        head = f"⏰ {slot['label']}: {start}–{end} — начнётся через {left} мин."
    elif now <= end_dt:
        left = _minutes_between(now, end)
        head = f"⏰ {slot['label']}: {start}–{end} — идёт сейчас, до конца {left} мин."
    else:
        head = f"⏰ {slot['label']}: {start}–{end} — уже закончилась сегодня"

    # если пара из двух часов — показываем обе половинки и пересменок
    halves = slot.get("halves") or []
    lines = [head]
    if len(halves) == 2:
        h1, h2 = halves
        brk = slot.get("break_between_minutes")
        brk_text = (
            f"\n☕ между половинками пар перемена {brk} минут" if brk else ""
        )
        lines.append(
            f"🕐 1 половинка: {h1['start']}–{h1['end']}"
            f"\n🕐 2 половинка: {h2['start']}–{h2['end']}{brk_text}"
        )

    await event.send_message("\n".join(lines))


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
