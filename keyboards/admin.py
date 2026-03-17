from vkbottle import Keyboard, Callback


def admin_keyboard():

    kb = Keyboard(inline=True)

    kb.add(Callback("👥 Пользователи", payload={"cmd": "admin_users"})).row()

    kb.add(Callback("📊 Статистика", payload={"cmd": "admin_stats"})).row()

    kb.add(Callback("📢 Рассылка", payload={"cmd": "admin_broadcast"})).row()

    kb.add(Callback("🔄 Обновить расписание", payload={"cmd": "admin_refresh"})).row()

    kb.add(Callback("🔔 Обновить расписание звонков", payload={"cmd": "admin_refresh_bell"})).row()

    kb.add(Callback("🎯 Назначить преподавателя", payload={"cmd": "admin_set_teacher"}))

    return kb
