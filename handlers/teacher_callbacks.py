from vkbottle.bot import MessageEvent
from core.bot import bot

from utils.api import api
from utils.schedule_utils import get_current_day
from utils.fio_utils import fio_full_to_initials


@bot.on.raw_event(
    "message_event", dataclass=MessageEvent, payload={"cmd": "teacher_lessons"}
)
async def teacher_lessons(event: MessageEvent):

    user_id = event.object.user_id

    user = api.get_user(user_id) or {}

    teacher_fio = user.get("teacher_fio")

    if not teacher_fio:
        await event.send_message("❌ У вас не указано ФИО")
        return

    fio_key = fio_full_to_initials(teacher_fio)

    today = get_current_day()

    if not today:
        await event.send_message("🎉 Сегодня воскресенье — занятий нет.")
        return

    sch = api.get_teacher_schedule(fio_key) or {}

    schedule = sch.get("schedule", {})

    groups = set()

    for _, shift_data in schedule.items():
        day_lessons = shift_data.get(today, {})

        for _, info in day_lessons.items():
            group = info.get("group")

            if group:
                groups.add(group)

    if not groups:
        await event.send_message("Сегодня занятий нет.")
        return

    text = "📚 Ваши группы сегодня:\n\n"

    for g in sorted(groups):
        text += f"• {g}\n"

    await event.send_message(text)
