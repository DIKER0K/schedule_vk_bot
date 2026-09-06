from vkbottle.bot import Message, MessageEvent
from vkbottle import Keyboard, Callback
from core.bot import bot

from keyboards.course import course_keyboard
from keyboards.group import group_keyboard
from keyboards.main import create_main_keyboard
from states.feedback_states import FeedbackStates
from states.reg_states import RegStates
from utils.api import api
from utils.teacher_requests import teacher_requests

@bot.on.message(state=FeedbackStates.WAIT_MESSAGE)
async def process_feedback(message: Message):

    if message.text.lower() in ("отмена", "назад"):
        await bot.state_dispenser.delete(message.peer_id)
        return await message.answer("❌ Отправка отменена.")

    text = message.text
    user_id = message.from_id

    await bot.state_dispenser.delete(message.peer_id)

    await message.answer("✅ Ваше сообщение отправлено администрации.")

    # получаем имя пользователя VK
    user_info = await bot.api.users.get(user_ids=user_id)
    user = user_info[0]

    username = f"{user.first_name} {user.last_name}"

    # получаем админов из базы
    users = api.get_users_by_platform(limit=1000)
    admins = [u for u in users if u.get("role") == "admin"]

    for admin in admins:
        try:
            await bot.api.messages.send(
                user_id=admin["user_id"],
                message=(
                    "💬 Новая обратная связь\n\n"
                    f"👤 Пользователь: {username}\n"
                    f"🆔 ID: {user_id}\n\n"
                    f"{text}"
                ),
                random_id=0
            )
        except:
            pass

@bot.on.message(state=RegStates.WAIT_TEACHER_FIO)
async def process_teacher_fio(message: Message):
    fio = message.text.strip()
    
    # Простая проверка: должно быть минимум 2 слова (Фамилия Имя)
    parts = fio.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Неверный формат. Введите полностью: Фамилия Имя Отчество.\n"
            "Пример: Иванов Иван Иванович"
        )
        return

    # Обновляем данные на бэкенде
    # Также ставим группу "Преподаватель", как было в ТГ
    api.update_user(message.from_id, {
        "teacher_fio": fio,
        "group_name": "Преподаватель"
    })

    await bot.state_dispenser.delete(message.peer_id)

    # Создаем клавиатуру (как в вашем commands.py)
    kb = create_main_keyboard(is_teacher=True, is_admin=False) # admin=False т.к. мы только что назначили учителя

    await message.answer(
        f"✅ Приятно познакомиться, {fio}!\n\n"
        "Теперь вы можете просматривать расписание и настраивать уведомления.",
        keyboard=kb.get_json()
    )

@bot.on.message(text="👨‍🏫 Я преподаватель")
async def teacher_request_start(message: Message, user):
    state = await bot.state_dispenser.get(message.peer_id)
    if state:
        return

    if user.get("role") in ["teacher", "admin"]:
        await message.answer("✅ У вас уже есть роль преподавателя.")
        return

    if teacher_requests.get(message.from_id):
        await message.answer("⏳ У вас уже есть заявка на рассмотрении.")
        return

    cooldown = teacher_requests.get_cooldown_remaining(message.from_id)
    if cooldown > 0:
        minutes = cooldown // 60
        seconds = cooldown % 60
        await message.answer(
            f"⏳ Вы недавно получили отказ. Попробуйте снова через {minutes} мин. {seconds} сек."
        )
        return

    await bot.state_dispenser.set(message.peer_id, RegStates.WAIT_TEACHER_REQUEST_FIO)
    await message.answer(
        "👨‍🏫 Заявка на роль преподавателя\n\n"
        "Введите ваше ФИО полностью (Фамилия Имя Отчество):\n"
        "Пример: Иванов Иван Иванович\n\n"
        "Для отмены напишите «отмена»."
    )

@bot.on.message(state=RegStates.WAIT_TEACHER_REQUEST_FIO)
async def process_teacher_request_fio(message: Message, user):
    text = message.text.strip()

    if text.lower() in ("отмена", "cancel", "назад"):
        await bot.state_dispenser.delete(message.peer_id)
        kb = course_keyboard()
        await message.answer("❌ Заявка отменена.", keyboard=kb.get_json())
        return

    parts = text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Неверный формат. Введите полностью: Фамилия Имя Отчество.\n"
            "Пример: Иванов Иван Иванович"
        )
        return

    username = user.get("username") or str(message.from_id)
    first_name = user.get("first_name") or ""
    last_name = user.get("last_name") or ""
    display_name = f"{first_name} {last_name}".strip() or username

    teacher_requests.add(message.from_id, text, display_name)

    await bot.state_dispenser.delete(message.peer_id)

    from vkbottle import Keyboard, Callback
    kb = Keyboard(inline=True)
    kb.add(Callback("❌ Отменить заявку", {"cmd": "cancel_teacher_request", "uid": message.from_id}))

    await message.answer(
        "⏳ Заявка отправлена!\n\n"
        "Ожидайте подтверждения администраторов."
        keyboard=kb.get_json()
    )

    users = api.get_users_by_platform(limit=1000)
    admins = [u for u in users if u.get("role") == "admin"]
    total_admins = len(admins)

    req = teacher_requests.get(message.from_id)
    vote_text = req.get_vote_text(total_admins) if req else ""

    kb_admin = Keyboard(inline=True)
    kb_admin.add(Callback("✅ Принять", {"cmd": "vote_teacher", "uid": message.from_id, "vote": True}))
    kb_admin.add(Callback("❌ Отклонить", {"cmd": "vote_teacher", "uid": message.from_id, "vote": False})).row()

    profile_link = f"https://vk.com/{username}" if username and not username.startswith("id") else f"https://vk.com/id{message.from_id}"

    msg_text = (
        "📬 Новая заявка на роль преподавателя\n\n"
        f"👤 {display_name}\n"
        f"🆔 ID: {message.from_id}\n"
        f"🔗 {profile_link}\n"
        f"📝 ФИО: {text}\n\n"
        f"📊 Голосование ({total_admins} админов, нужно {((total_admins + 1) // 2)} голосов)\n"
        f"{vote_text}"
    )

    for admin in admins:
        try:
            await bot.api.messages.send(
                user_id=admin["user_id"],
                message=msg_text,
                random_id=0,
                keyboard=kb_admin.get_json()
            )
        except:
            pass

@bot.on.message()
async def onboarding_handler(message: Message, user):
    # 1. Проверяем, не находится ли пользователь уже в процессе ввода ФИО
    state = await bot.state_dispenser.get(message.peer_id)
    if state and state.state == RegStates.WAIT_TEACHER_FIO:
        return # Уходим, чтобы сообщение обработал process_teacher_fio

    # 2. ЕСЛИ РОЛЬ ИЗМЕНИЛАСЬ НА УЧИТЕЛЯ (даже в середине регистрации студента)
    if user.get("role") in ["teacher", "admin"] and not user.get("teacher_fio"):
        await bot.state_dispenser.set(message.from_id, RegStates.WAIT_TEACHER_FIO)
        await message.answer("👨‍🏫 Вам была назначена роль преподавателя!\n\nПожалуйста, введите ваше ФИО полностью (Фамилия Имя Отчество):")
        return # Это ВАЖНО: мы прерываем выполнение кода выбора курса

    # 3. Если регистрация уже завершена
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


@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload_map={"cmd": "cancel_teacher_request"},
)
async def cancel_teacher_request(event: MessageEvent):
    payload = event.get_payload_json()
    uid = payload.get("uid", event.object.user_id)

    req = teacher_requests.remove(uid)
    if not req:
        await event.show_snackbar("❌ У вас нет активных заявок.")
        return

    kb = course_keyboard()
    await event.edit_message("❌ Заявка отменена.", keyboard=kb.get_json())