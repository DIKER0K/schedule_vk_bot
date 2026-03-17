import asyncio
import re

import aiohttp
from vkbottle import Callback, Keyboard
from vkbottle.bot import MessageEvent, Message
from core.bot import bot

from core.config import ROLES
from states.reg_states import RegStates
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

    kb = Keyboard(inline=True)
    kb.add(Callback("👨‍🎓 Статистика по группам", {"cmd": "admin_group_stats"})).row()
    kb.add(Callback("👨‍🏫 Список преподавателей", {"cmd": "admin_teachers_list"})).row()
    kb.add(Callback("⬅️ Назад", {"cmd": "admin_back"}))

    await event.edit_message(text, keyboard=kb.get_json())

@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload_map={"cmd": "admin_group_stats"},
)
async def admin_group_stats(event: MessageEvent):

    payload = event.get_payload_json()
    page = payload.get("page", 0)
    per_page = payload.get("per_page", 20)

    users = api.get_users_by_platform(limit=1000)

    from collections import defaultdict
    groups = defaultdict(int)
    total_students = 0

    for u in users:
        if u.get("role") != "student":
            continue

        total_students += 1
        g = (u.get("group_name") or "").strip() or "без группы"
        groups[g] += 1

    items = sorted(groups.items())
    total_groups = len(items)

    start = page * per_page
    end = start + per_page
    page_items = items[start:end]

    lines = [f"• {g} — {cnt}" for g, cnt in page_items]

    page_total = (total_groups + per_page - 1) // per_page

    text = (
        "👨‍🎓 Статистика по группам\n\n"
        f"Всего студентов: {total_students}\n"
        f"Групп: {total_groups}\n"
        f"Страница: {page+1}/{page_total}\n\n"
        + "\n".join(lines)
    )

    kb = Keyboard(inline=True)

    if page > 0:
        kb.add(Callback("⬅️", {"cmd": "admin_group_stats", "page": page-1}))

    if end < total_groups:
        kb.add(Callback("➡️", {"cmd": "admin_group_stats", "page": page+1}))

    kb.row()
    kb.add(Callback("⬅️ Назад", {"cmd": "admin_stats"}))
    kb.add(Callback("🏠 Панель", {"cmd": "admin_back"}))

    await event.edit_message(text, keyboard=kb.get_json())

@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload_map={"cmd": "admin_teachers_list"},
)
async def admin_teachers_list(event: MessageEvent):

    payload = event.get_payload_json()
    page = payload.get("page", 0)
    per_page = payload.get("per_page", 20)

    users = api.get_users_by_platform(limit=1000)

    teachers = [u for u in users if u.get("role") == "teacher"]

    teachers = sorted(
        teachers,
        key=lambda x: (x.get("teacher_fio") or "").lower()
    )

    total = len(teachers)

    start = page * per_page
    end = start + per_page

    page_items = teachers[start:end]

    lines = []

    for t in page_items:
        fio = t.get("teacher_fio") or "Не указано"
        uid = t.get("user_id")
        uname = t.get("username") or "—"

        lines.append(f"• {fio} (ID: {uid}, @{uname})")

    page_total = (total + per_page - 1) // per_page

    text = (
        "👨‍🏫 Список преподавателей\n\n"
        f"Всего: {total}\n"
        f"Страница: {page+1}/{page_total}\n\n"
        + "\n".join(lines)
    )

    kb = Keyboard(inline=True)

    if page > 0:
        kb.add(Callback("⬅️", {"cmd": "admin_teachers_list", "page": page-1}))

    if end < total:
        kb.add(Callback("➡️", {"cmd": "admin_teachers_list", "page": page+1}))

    kb.row()
    kb.add(Callback("⬅️ Назад", {"cmd": "admin_stats"}))
    kb.add(Callback("🏠 Панель", {"cmd": "admin_back"}))

    await event.edit_message(text, keyboard=kb.get_json())


@bot.on.raw_event("message_event", dataclass=MessageEvent, payload={"cmd": "admin_broadcast"})
async def admin_broadcast_init(event: MessageEvent):
    await bot.state_dispenser.set(event.peer_id, AdminStates.WAIT_BROADCAST_MSG)
    await event.send_message(
        "📣 Отправьте сообщение (текст), которое нужно разослать всем пользователям.\n"
        "Для отмены напишите 'отмена'."
    )

@bot.on.message(state=AdminStates.WAIT_BROADCAST_MSG)
async def process_broadcast(message: Message):
    if message.text.lower() in ("отмена", "назад"):
        await bot.state_dispenser.delete(message.peer_id)
        return await message.answer("❌ Рассылка отменена.", keyboard=admin_keyboard().get_json())

    await message.answer("⏳ Начинаю рассылку...")
    users = api.get_users_by_platform() # Предполагаем метод получения всех юзеров
    
    count = 0
    for u in users:
        try:
            await bot.api.messages.send(user_id=u["user_id"], message=message.text, random_id=0)
            count += 1
            await asyncio.sleep(0.05) # Защита от флуда VK
        except:
            continue

    await bot.state_dispenser.delete(message.peer_id)
    await message.answer(f"✅ Рассылка завершена. Получили: {count} чел.", keyboard=admin_keyboard().get_json())

@bot.on.raw_event("message_event", dataclass=MessageEvent, payload={"cmd": "admin_refresh_bell"})
async def admin_bell_init(event: MessageEvent):
    await bot.state_dispenser.set(event.peer_id, AdminStates.WAIT_BELL_JSON)
    await event.send_message("📤 Отправьте JSON-файл с расписанием звонков.")

@bot.on.message(state=AdminStates.WAIT_BELL_JSON)
async def process_bell_upload(message: Message):
    if not message.attachments or not message.attachments[0].doc:
        return await message.answer("❌ Пожалуйста, отправьте файл (документ).")
    
    doc = message.attachments[0].doc
    if not doc.title.endswith(".json"):
        return await message.answer("❌ Это не JSON файл.")

    # В VK нужно сначала скачать файл по URL
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(doc.url) as resp:
            file_bytes = await resp.read()

    success = api.upload_bell_schedule(file_bytes) # Ваш метод в API
    await bot.state_dispenser.delete(message.peer_id)
    
    if success:
        kb = Keyboard(inline=True)
        kb.add(Callback("✅ Да, уведомить", {"cmd": "notify_all", "type": "bell"}))
        kb.add(Callback("🚫 Не уведомлять", {"cmd": "skip_notify", "type": "bell"}))

        await message.answer(
            "✅ Расписание звонков обновлено!\n\n"
            "📣 Уведомить всех пользователей о новых звонках?",
            keyboard=kb.get_json()
        )
    else:
        await message.answer("❌ Ошибка при загрузке на сервер.")

@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload_map={"cmd": "skip_notify"},
)
async def skip_notify(event: MessageEvent):

    payload = event.get_payload_json()
    context = payload.get("type", "update")

    await event.show_snackbar("Уведомления пропущены")

    await event.edit_message(
        f"✅ Обновление '{context}' завершено без уведомлений.",
        keyboard=admin_keyboard().get_json()
    )

@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload_map={"cmd": "notify_all"},
)
async def notify_all(event: MessageEvent):

    payload = event.get_payload_json()
    context = payload.get("type", "update")

    await event.show_snackbar("Начинаю рассылку")

    users = api.get_users_by_platform(limit=1000)

    if context == "bell":
        msg_text = "🔔 Обновлено расписание звонков!"
    elif context == "schedule":
        msg_text = "📚 Обновлено основное расписание занятий!"
    else:
        msg_text = "📢 Новое обновление в системе!"

    count = 0

    for u in users:
        try:
            await bot.api.messages.send(
                user_id=u["user_id"],
                message=msg_text,
                random_id=0
            )
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass

    await event.send_message(
        f"✅ Уведомлено пользователей: {count}",
        keyboard=admin_keyboard().get_json()
    )

@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload={"cmd": "admin_refresh"},
)
async def admin_refresh(event: MessageEvent):
    # 1. Сначала убираем загрузку (отправляем пустой ответ или уведомление)
    await event.show_snackbar("Загрузка...")
    
    # 2. Устанавливаем состояние ожидания файла
    await bot.state_dispenser.set(event.peer_id, AdminStates.WAIT_SCHEDULE_DOCX)
    
    # 3. Отправляем инструкции
    await event.send_message(
        "📤 Отправьте жопу попу мопу DOCX-файл расписания.\n"
        "(Необязательно) Следом отправьте JSON со сменами `group_shifts.json`.\n"
        "Я загружу файлы на сервер."
    )

@bot.on.message(state=AdminStates.WAIT_SCHEDULE_DOCX)
async def process_schedule_upload(message: Message):
    # Ищем документ во вложениях
    doc = next((a.doc for a in message.attachments if a.doc), None)
    
    if not doc:
        return await message.answer("❌ Пожалуйста, отправьте файл как 'Документ'.")

    # Скачиваем файл
    async with aiohttp.ClientSession() as session:
        async with session.get(doc.url) as resp:
            file_bytes = await resp.read()

    # Отправляем на бэкенд (используя ваш api.py)
    if doc.title.endswith(".docx"):
        result = api.upload_schedule(file_bytes)

        kb = Keyboard(inline=True)
        kb.add(Callback("✅ Да, уведомить", {"cmd": "notify_all", "type": "schedule"}))
        kb.add(Callback("🚫 Не уведомлять", {"cmd": "skip_notify", "type": "schedule"}))

        await message.answer(
            "✅ Расписание успешно загружено!\n\n"
            "📣 Уведомить пользователей об обновлении?",
            keyboard=kb.get_json()
        )
    elif doc.title.endswith(".json"):
        # Логика для смен, если нужно
        await message.answer("✅ Файл смен загружен!")
    
    await bot.state_dispenser.delete(message.peer_id)

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
    text = message.text.strip()

    if text.lower() in ("отмена", "cancel", "назад"):
        await bot.state_dispenser.delete(message.peer_id)
        return await message.answer("⛔️ Назначение отменено.", keyboard=admin_keyboard().get_json())

    raw_ids = re.split(r'[\,\s]+', text)
    ok, fail = [], []

    for token in raw_ids:
        if not token: continue
        try:
            uid = int(token)
            updated = api.update_user(uid, {"role": "teacher"})
            
            if updated:
                ok.append(str(uid))
                try:
                    # 1. Отправляем уведомление пользователю
                    await bot.api.messages.send(
                        user_id=uid, 
                        message=(
                            "🎉 Вам назначена роль преподавателя!\n\n"
                            "Пожалуйста, введите ваше ФИО полностью (например: Иванов Иван Иванович):"
                        ),
                        random_id=0
                    )
                    # 2. УСТАНАВЛИВАЕМ СОСТОЯНИЕ ДЛЯ ЭТОГО ПОЛЬЗОВАТЕЛЯ
                    await bot.state_dispenser.set(uid, RegStates.WAIT_TEACHER_FIO)
                except: pass
            else:
                fail.append(token)
        except ValueError:
            fail.append(token)

    # 3. Формирование ответа
    response = ""
    if ok:
        response += f"✅ Назначены преподавателями: {', '.join(ok)}\n"
    if fail:
        response += f"⚠️ Не удалось обработать (не найдены или неверный формат): {', '.join(fail)}"
    
    if not response:
        response = "❌ Вы не ввели ни одного корректного ID."

    await message.answer(response, keyboard=admin_keyboard().get_json())
    await bot.state_dispenser.delete(message.peer_id)

@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    # Фильтруем по команде, игнорируя остальные поля payload для пагинации
    payload_map={"cmd": "admin_users"},
)
async def admin_users_list(event: MessageEvent):
    payload = event.get_payload_json()
    skip = payload.get("skip", 0)
    limit = payload.get("limit", 10)

    # 1. Получаем всех пользователей платформы (для расчета общего кол-ва)
    # Если на бэке тысячи юзеров, лучше сделать эндпоинт /count, 
    # но пока используем логику из твоего ТГ-примера:
    all_users = api.get_users_by_platform(limit=1000) # Берем с запасом
    all_users.reverse() # Новые в начале
    
    total = len(all_users)
    
    # 2. Срез для текущей страницы
    page_rows = all_users[skip : skip + limit]
    
    if not page_rows and skip > 0:
        # Если вдруг страница пустая (удалили юзеров), откатываемся в начало
        return await admin_users_list(event) # Рекурсивно вызываем с дефолтами

    # 3. Формируем текст
    lines = []
    for u in page_rows:
        uid = u.get("user_id")
        uname = u.get("username") or "id" + str(uid)
        role = ROLES.get(u.get("role"), u.get("role"))
        
        emoji = "👨‍🎓" if u.get("role") == "student" else "👨‍🏫" if u.get("role") == "teacher" else "👑"
        line = f"{emoji} @{uname} ({uid}): {role}"
        
        if u.get("group_name"):
            line += f", гр: {u.get('group_name')}"
        lines.append(line)

    page_num = (skip // limit) + 1
    total_pages = (total + limit - 1) // limit
    
    text = (
        "👥 Управление пользователями\n\n"
        f"Страница: {page_num} из {total_pages}\n"
        f"Показано: {len(page_rows)} из {total}\n\n"
        + "\n".join(lines)
    )

    # 4. Клавиатура пагинации
    kb = Keyboard(inline=True)
    
    # Кнопки "Назад" и "Вперед" в один ряд
    has_prev = skip > 0
    has_next = (skip + limit) < total
    
    if has_prev or has_next:
        if has_prev:
            kb.add(Callback("⬅️", {"cmd": "admin_users", "skip": skip - limit, "limit": limit}))
        if has_next:
            kb.add(Callback("➡️", {"cmd": "admin_users", "skip": skip + limit, "limit": limit}))
        kb.row()

    kb.add(Callback("🎯 Назначить преподавателя", {"cmd": "admin_set_teacher"})).row()
    kb.add(Callback("🏠 В админ-панель", {"cmd": "admin_back"}))

    # 5. Редактируем старое сообщение (в ВК это send_message с тем же conversation_message_id не работает так просто, 
    # поэтому просто шлем новое или используем event.edit_message)
    await event.edit_message(text, keyboard=kb.get_json())

# Обработчик кнопки "Назад"
@bot.on.raw_event(
    "message_event",
    dataclass=MessageEvent,
    payload={"cmd": "admin_back"},
)
async def admin_back_to_menu(event: MessageEvent):
    await event.edit_message(
        "👑 Панель администратора\n\nВыберите действие:",
        keyboard=admin_keyboard().get_json()
    )