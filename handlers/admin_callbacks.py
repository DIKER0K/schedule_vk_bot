from vkbottle.bot import MessageEvent, Message
from core.bot import bot

from utils.api import api
from keyboards.admin import admin_keyboard
from states.admin_states import AdminStates


@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload={"cmd": "admin_stats"},
)
async def admin_stats(event: MessageEvent):

    stats = api.get_stats()

    text = (
        "📊 Статистика\n\n"
        f"👥 Пользователей: {stats.get('total', 0)}\n"
        f"👨‍🎓 Студентов: {stats.get('students', 0)}\n"
        f"👨‍🏫 Преподавателей: {stats.get('teachers', 0)}\n"
        f"👑 Администраторов: {stats.get('admins', 0)}\n"
        f"📚 Групп: {stats.get('groups', 0)}\n"
        f"🔔 Подписок: {stats.get('subscriptions', 0)}"
    )

    await event.send_message(
        text,
        keyboard=admin_keyboard().get_json(),
    )


@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload={"cmd": "admin_broadcast"},
)
async def admin_broadcast(event: MessageEvent):

    await bot.state_dispenser.set(
        event.object.user_id,
        AdminStates.WAIT_BROADCAST,
    )

    await event.send_message(
        "📢 Отправьте сообщение для рассылки всем пользователям.\n\n"
        "Для отмены напишите: отмена"
    )


@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload={"cmd": "admin_broadcast"},
)
async def admin_broadcast(event: MessageEvent):

    await bot.state_dispenser.set(
        event.object.user_id,
        AdminStates.WAIT_BROADCAST,
    )

    await event.send_message(
        "📢 Отправьте сообщение для рассылки всем пользователям.\n\n"
        "Для отмены напишите: отмена"
    )


@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload={"cmd": "admin_set_teacher"},
)
async def admin_set_teacher(event: MessageEvent):

    await bot.state_dispenser.set(
        event.object.user_id,
        AdminStates.WAIT_TEACHER_ID,
    )

    await event.send_message(
        "🎯 Введите ID пользователя, которого нужно назначить преподавателем."
    )


@bot.on.message(state=AdminStates.WAIT_TEACHER_ID)
async def process_teacher_set(message: Message):

    try:
        uid = int(message.text)

    except:
        await message.answer("❌ Неверный ID")
        return

    updated = api.update_user(uid, {"role": "teacher"})

    if updated:
        await message.answer(f"✅ Пользователь {uid} назначен преподавателем")

    else:
        await message.answer("❌ Пользователь не найден")

    await bot.state_dispenser.delete(message.peer_id)
