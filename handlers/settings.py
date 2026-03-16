from vkbottle.bot import Message
from core.bot import bot

from keyboards.settings import settings_keyboard


@bot.on.message(text="⚙️ Настройки")
async def settings_handler(message: Message, user):

    enabled = user.get("schedule_enabled", False)
    sched_time = user.get("schedule_time", "08:00")

    text = (
        "⚙️ Настройки\n\n"
        f"📚 Группа: {user.get('group_name')}\n"
        f"🔔 Ежедневное расписание: {'включено' if enabled else 'выключено'}\n"
        f"⏰ Время отправки: {sched_time}"
    )

    kb = settings_keyboard(user)

    await message.answer(
        text,
        keyboard=kb.get_json(),
    )
