from vkbottle import Keyboard, Text


def course_keyboard():

    kb = Keyboard(one_time=False)

    kb.add(Text("1 курс")).add(Text("2 курс")).row()
    kb.add(Text("3 курс")).add(Text("4 курс")).row()

    kb.add(Text("❌ Отмена"))

    return kb
