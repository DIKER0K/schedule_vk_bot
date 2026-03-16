import re
from vkbottle.bot import Message
from core.bot import bot
from states.user_states import UserStates
from utils.api import api
from keyboards.settings import settings_keyboard
from keyboards.course import course_keyboard


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
