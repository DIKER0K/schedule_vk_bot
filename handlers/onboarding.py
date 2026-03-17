from vkbottle.bot import Message
from core.bot import bot

from keyboards.course import course_keyboard
from keyboards.group import group_keyboard
from keyboards.main import create_main_keyboard
from states.feedback_states import FeedbackStates
from states.reg_states import RegStates
from utils.api import api

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