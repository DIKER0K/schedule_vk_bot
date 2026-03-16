from vkbottle import Keyboard, Text
from utils.api import api


def group_keyboard(course: int):

    groups = api.get_groups()

    # фильтр групп по курсу
    course_groups = [g for g in groups if g.startswith(str(course))]

    kb = Keyboard(one_time=False)

    for i in range(0, len(course_groups), 2):
        for group in course_groups[i : i + 2]:
            kb.add(Text(group))

        kb.row()

    kb.add(Text("⬅️ Назад")).row()
    kb.add(Text("❌ Отмена"))

    return kb
