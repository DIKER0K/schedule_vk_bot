from vkbottle.bot import Message
from core.bot import bot

from keyboards.teacher import teacher_panel_keyboard


@bot.on.message(text="👨‍🏫 Панель преподавателя")
async def teacher_panel(message: Message, user):

    if user.get("role") not in ["teacher", "admin"]:
        await message.answer("❌ У вас нет доступа к панели преподавателя.")
        return

    kb = teacher_panel_keyboard(user)

    await message.answer(
        "👨‍🏫 Панель преподавателя\n\nВыберите действие:",
        keyboard=kb.get_json(),
    )
