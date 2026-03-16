import re
from vkbottle.bot import Message
from core.bot import bot
from states.user_states import UserStates
from utils.api import api
from keyboards.settings import settings_keyboard
from keyboards.course import course_keyboard
from utils.fio_utils import is_valid_full_fio, normalize_full_fio


@bot.on.message(payload={"cmd": "change_group"})
async def change_group(message: Message, user):

    # сбрасываем группу
    api.update_user(message.from_id, {"group_name": None})

    user["group_name"] = None

    kb = course_keyboard()

    await message.answer(
        "📚 Выберите новый курс:",
        keyboard=kb.get_json(),
    )


@bot.on.message(payload={"cmd": "enable_schedule"})
async def enable_schedule(message: Message, user):

    api.update_user(message.from_id, {"schedule_enabled": True})

    user["schedule_enabled"] = True

    kb = settings_keyboard(user)

    await message.answer(
        "🔔 Ежедневное расписание включено",
        keyboard=kb.get_json(),
    )


@bot.on.message(payload={"cmd": "disable_schedule"})
async def disable_schedule(message: Message, user):

    api.update_user(message.from_id, {"schedule_enabled": False})

    user["schedule_enabled"] = False

    kb = settings_keyboard(user)

    await message.answer(
        "🔕 Ежедневное расписание отключено",
        keyboard=kb.get_json(),
    )


@bot.on.message(payload={"cmd": "change_time"})
async def change_time(message: Message):

    await bot.state_dispenser.set(message.peer_id, UserStates.WAIT_TIME)

    await message.answer(
        "⏰ Введите новое время отправки расписания.\n\nФормат: HH:MM\nПример: 08:30"
    )


TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


# обработка ввода времени
@bot.on.message(state=UserStates.WAIT_TIME)
async def process_time(message: Message, user):

    text = message.text.strip()

    if not TIME_PATTERN.match(text):
        await message.answer(
            "❌ Неверный формат времени.\nВведите в формате HH:MM\nНапример: 08:30"
        )
        return

    api.update_user(message.from_id, {"schedule_time": text})
    user["schedule_time"] = text

    await bot.state_dispenser.delete(message.peer_id)

    kb = settings_keyboard(user)

    await message.answer(
        f"✅ Время отправки изменено на {text}",
        keyboard=kb.get_json(),
    )


@bot.on.message(payload={"cmd": "teacher_settings"})
async def teacher_settings(message: Message, user):

    teacher_fio = user.get("teacher_fio") or "Не указано"

    text = (
        "👨‍🏫 Настройки преподавателя\n\n"
        f"Текущее ФИО: {teacher_fio}\n\n"
        "Введите новое ФИО полностью.\n"
        "Пример:\n"
        "Иванов Иван Иванович"
    )

    await bot.state_dispenser.set(message.peer_id, UserStates.WAIT_TEACHER_FIO)

    await message.answer(text)


@bot.on.message(state=UserStates.WAIT_TEACHER_FIO)
async def process_teacher_fio(message: Message, user):

    fio_raw = message.text.strip()

    fio = normalize_full_fio(fio_raw)

    if not is_valid_full_fio(fio):
        await message.answer(
            "❌ Неверный формат ФИО.\n\n"
            "Введите полностью:\n"
            "Фамилия Имя Отчество\n\n"
            "Пример:\n"
            "Иванов Иван Иванович"
        )
        return

    if message.text.lower() in ["отмена", "cancel"]:
        await bot.state_dispenser.delete(message.peer_id)
        await message.answer("❌ Изменение ФИО отменено")
        return

    api.update_user(message.from_id, {"teacher_fio": fio})

    user["teacher_fio"] = fio

    await bot.state_dispenser.delete(message.peer_id)

    kb = settings_keyboard(user)

    await message.answer(
        f"✅ ФИО обновлено:\n{fio}",
        keyboard=kb.get_json(),
    )
