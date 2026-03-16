from vkbottle.bot import Message
from core.bot import bot

from keyboards.main import create_main_keyboard


@bot.on.message()
async def fallback(message: Message, user):

    # если пользователь ещё не прошёл onboarding
    if not user.get("group_name"):
        return

    is_admin = user.get("role") == "admin"
    is_teacher = user.get("role") in ["teacher", "admin"]

    kb = create_main_keyboard(is_teacher, is_admin)

    await message.answer(
        "❓ Я не понял команду.\nПопробуйте использовать меню.",
        keyboard=kb.get_json(),
    )
