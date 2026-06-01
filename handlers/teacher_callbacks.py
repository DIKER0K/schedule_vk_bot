from vkbottle.bot import MessageEvent, Message
from core.bot import bot

from utils.api import api
from utils.schedule_utils import get_current_day, format_teacher_schedule_for_week
from utils.fio_utils import fio_full_to_initials
from keyboards.teacher import teacher_panel_keyboard
from states.teacher_states import TeacherStates


@bot.on.raw_event(
    "message_event", dataclass=MessageEvent, payload={"cmd": "teacher_lessons"}
)
async def teacher_lessons(event: MessageEvent):

    user_id = event.object.user_id

    user = api.get_users_by_platform(user_id) or {}

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


@bot.on.raw_event(
    "message_event", dataclass=MessageEvent, payload={"cmd": "teacher_other_schedule"}
)
async def teacher_other_schedule_init(event: MessageEvent):
    await bot.state_dispenser.set(event.object.user_id, TeacherStates.WAIT_OTHER_TEACHER_FIO)
    await event.send_message(
        "👤 Введите ФИО преподавателя в формате:\n"
        "Фамилия И.О. (например: Албаева И.В)\n\n"
        "Для отмены напишите 'отмена'."
    )


@bot.on.message(state=TeacherStates.WAIT_OTHER_TEACHER_FIO)
async def teacher_other_schedule_show(message: Message, user):
    if message.text.lower() in ("отмена", "назад", "cancel"):
        await bot.state_dispenser.delete(message.peer_id)
        kb = teacher_panel_keyboard(user)
        await message.answer("❌ Отменено.", keyboard=kb.get_json())
        return

    fio = message.text.strip()
    fio_key = fio[0].upper() + fio[1:] if fio else fio

    sch = api.get_teacher_schedule(fio_key)
    if not sch:
        await message.answer(f"❌ Расписание для '{fio_key}' не найдено.")
        return

    text = format_teacher_schedule_for_week(fio_key, sch)
    await bot.state_dispenser.delete(message.peer_id)

    kb = teacher_panel_keyboard(user)
    await message.answer(text, keyboard=kb.get_json())
