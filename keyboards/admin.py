from vkbottle import Keyboard, Callback


def admin_keyboard():

    kb = Keyboard(inline=True)

    kb.add(Callback("👥 Пользователи", payload={"cmd": "admin_users"}))
    kb.add(Callback("📊 Статистика", payload={"cmd": "admin_stats"})).row()

    kb.add(Callback("📢 Рассылка", payload={"cmd": "admin_broadcast"})).row()

    kb.add(Callback("🔄 Обновить расписание", payload={"cmd": "admin_refresh"}))
    kb.add(Callback("🔔 Звонки", payload={"cmd": "admin_refresh_bell"})).row()

    kb.add(Callback("🎯 Преподаватель", payload={"cmd": "admin_set_teacher"}))
    kb.add(Callback("👑 Админ", payload={"cmd": "admin_set_admin"}))

    return kb
