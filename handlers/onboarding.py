from vkbottle.bot import Message
from core.bot import bot

from keyboards.course import course_keyboard
from keyboards.group import group_keyboard
from keyboards.main import create_main_keyboard
from utils.api import api


@bot.on.message()
async def onboarding_handler(message: Message, user):

    # если группа уже выбрана — onboarding пропускаем
    if user.get("group_name"):
        return

    text = message.text

    # выбор курса
    if text in ["1 курс", "2 курс", "3 курс", "4 курс"]:
        course = int(text[0])

        kb = group_keyboard(course)

        await message.answer("📚 Выберите вашу группу:", keyboard=kb.get_json())
        return

    # выбор группы
    groups = api.get_groups()

    if text in groups:
        api.update_user(message.from_id, {"group_name": text})

        # получаем роль пользователя
        is_admin = user.get("role") == "admin"
        is_teacher = user.get("role") in ["teacher", "admin"]

        kb = create_main_keyboard(is_teacher, is_admin)

        await message.answer(
            f"✅ Ваша группа: {text}\n\nИспользуйте меню ниже:", keyboard=kb.get_json()
        )

        return

    # первый экран
    kb = course_keyboard()

    await message.answer(
        "👋 Добро пожаловать в бот расписания!\n\n📚 Выберите ваш курс:",
        keyboard=kb.get_json(),
    )
