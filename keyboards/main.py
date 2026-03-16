from vkbottle import Keyboard, Text


def create_main_keyboard(is_teacher: bool, is_admin: bool):

    kb = Keyboard(one_time=False)

    # первая строка
    kb.add(Text("📅 Сегодня"))
    kb.add(Text("⚙️ Настройки"))
    kb.row()

    # дни недели
    kb.add(Text("📅 ПН"))
    kb.add(Text("📅 ВТ"))
    kb.add(Text("📅 СР"))
    kb.row()

    kb.add(Text("📅 ЧТ"))
    kb.add(Text("📅 ПТ"))
    kb.add(Text("📅 СБ"))
    kb.row()

    # обратная связь
    if not is_admin:
        kb.add(Text("💬 Обратная связь")).row()

    # панель преподавателя
    if is_teacher:
        kb.add(Text("👨‍🏫 Панель преподавателя")).row()

    # админ панель
    if is_admin:
        kb.add(Text("👑 Админ панель")).row()

    return kb
