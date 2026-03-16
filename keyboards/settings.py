from vkbottle import Keyboard, Text


def settings_keyboard(user):

    enabled = bool(user.get("schedule_enabled", False))

    kb = Keyboard(inline=True)

    kb.add(Text("🔄 Сменить группу", payload={"cmd": "change_group"})).row()

    if enabled:
        kb.add(
            Text(
                "🔕 Отключить ежедневное расписание",
                payload={"cmd": "disable_schedule"},
            )
        )
    else:
        kb.add(
            Text(
                "🔔 Включить ежедневное расписание",
                payload={"cmd": "enable_schedule"},
            )
        )

    kb.row()

    kb.add(
        Text(
            "⏰ Изменить время отправки",
            payload={"cmd": "change_time"},
        )
    )

    if user.get("role") in ["teacher", "admin"]:
        kb.row()
        kb.add(
            Text(
                "👨‍🏫 Настройки преподавателя",
                payload={"cmd": "teacher_settings"},
            )
        )

    return kb
