from vkbottle import Keyboard, Callback


def teacher_panel_keyboard(user):

    kb = Keyboard(inline=True)

    kb.add(Callback("📚 Мои занятия", payload={"cmd": "teacher_lessons"})).row()

    kb.add(Callback("👥 Мои группы", payload={"cmd": "teacher_groups"})).row()

    return kb
