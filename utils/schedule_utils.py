from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from core.config import DAYS_RU, TZ

DAY_PREP_CASE = {
    "Понедельник": "в понедельник",
    "Вторник": "во вторник",
    "Среда": "в среду",
    "Четверг": "в четверг",
    "Пятница": "в пятницу",
    "Суббота": "в субботу",
    "Воскресенье": "в воскресенье",
}

# Пометки вместо номера кабинета в приказе о распределении
CLASSROOM_NOTES = {
    "ПП": "практика",
    "ДО": "дистанционно",
}


def lesson_sort_key(num: str):
    return [int(x) for x in num.split(".")]


def in_day_ru(day: str) -> str:
    """Возвращает 'в понедельник/во вторник/в среду/...' (с маленькой буквы)."""
    return DAY_PREP_CASE.get(day, f"в {day.lower()}")


def format_lesson_number(num: str):
    parts = num.split(".")
    base = parts[0]
    half = None
    subgroup = None

    if len(parts) >= 2:
        half = parts[1]
    if len(parts) == 3:
        subgroup = parts[2]
    return base, half, subgroup


def get_current_day() -> Optional[str]:
    today = datetime.now(ZoneInfo(TZ)).weekday()
    if today == 6:
        return None
    return DAYS_RU[today]


def get_tomorrow_day() -> Optional[str]:
    tomorrow_date = datetime.now(ZoneInfo(TZ)) + timedelta(days=1)
    wd = tomorrow_date.weekday()
    if wd == 6:
        return None
    return DAYS_RU[wd]


def date_for_day(day: str, now: Optional[datetime] = None) -> str:
    """Дата ближайшего дня `day` в формате YYYY-MM-DD (сегодня, если совпал).

    Бот обязан спрашивать расписание на конкретную дату: бэкенд выбирает версию
    расписания по дате, и без параметра отдаёт «сегодня», даже если человек
    нажал «📅 ПТ».
    """
    now = now or datetime.now(ZoneInfo(TZ))
    if day not in DAYS_RU:
        return ""
    delta = (DAYS_RU.index(day) - now.weekday()) % 7
    return (now.date() + timedelta(days=delta)).isoformat()


def today_date() -> str:
    """Сегодняшняя дата в формате YYYY-MM-DD (по часовому поясу школы)."""
    return datetime.now(ZoneInfo(TZ)).date().isoformat()


def _as_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _classroom_note_text(note) -> str:
    """«ПП» → «практика», «ДО» → «дистанционно», неизвестное — как есть."""
    text = str(note or "").strip()
    if not text:
        return ""
    return CLASSROOM_NOTES.get(text.upper(), text.lower())


def _lesson_place(info: Dict[str, Any]) -> str:
    """Место пары для строки преподавателя: «117 каб.» или «практика».

    Бэкенд отдаёт либо номер кабинета, либо пометку «ПП» / «ДО» (у группы нет
    кабинета на этот период). Раньше бот печатал «ПП каб.».
    """
    room = str(info.get("classroom") or "").strip()
    if room:
        return f"{room} каб."
    return _classroom_note_text(info.get("classroom_note"))


def schedule_header_lines(schedule_doc: Dict[str, Any]) -> List[str]:
    """Строки шапки: корпус и кабинет на период, затем смена (если не первая).

    Бэкенд отдаёт эти поля у версии расписания; у старого бэкенда их нет,
    тогда шапка пустая и вид расписания не меняется.
    """
    doc = schedule_doc or {}

    def value(key):
        """Поле версии: сначала сверху, затем внутри блока schedule."""
        if doc.get(key) not in (None, ""):
            return doc.get(key)
        return (doc.get("schedule") or {}).get(key)

    shift = _as_int(value("shift"))
    if shift is None:
        shift = _as_int((doc.get("shift_info") or {}).get("shift"))

    building = _as_int(value("building"))
    classroom = str(value("classroom") or "").strip()
    note = _classroom_note_text(value("classroom_note"))

    place = ""
    if building:
        place = f"{building} корпус"
    if classroom:
        room = f"каб. {classroom}"
        place = f"{place}, {room}" if place else room
    elif note:
        place = f"{place}, {note}" if place else note

    lines: List[str] = []
    if place:
        lines.append(f"📍 {place}")
    if shift and shift > 1:
        # первая смена — обычное состояние, про неё не пишем
        lines.append(f"    {shift} смена")
    return lines


def format_schedule_error(group_name: str, day: str, detail: str = "") -> str:
    """Что показать вместо расписания, когда бэкенд ответил ошибкой.

    «Ещё не опубликовано» — не сбой, а нормальная ситуация конца недели,
    поэтому отвечаем спокойным текстом без слова «ошибка». Про выходной
    показываем текст бэкенда как есть.
    """
    text = (detail or "").strip()
    low = text.lower()

    if "не опубликован" in low:
        return (
            f"📅 Расписание на {day} ({group_name}) ещё не опубликовано.\n"
            "Обычно его выкладывают в конце недели."
        )

    if any(word in low for word in ("выходн", "праздн", "не учебн", "каникул")):
        return text or f"📅 {day} — выходной"

    if "не найдена" in low or "не найден" in low:
        return "❌ Расписание для вашей группы не найдено"

    return "😔 Не удалось получить расписание.\nПопробуйте чуть позже."


def format_teacher_schedule_error(teacher_fio: str, day: str, detail: str = "") -> str:
    """То же для расписания преподавателя: 404 «не опубликовано», выходной и т.п."""
    text = (detail or "").strip()
    low = text.lower()

    if "не опубликован" in low:
        return (
            f"📅 Расписание для {teacher_fio} на {day} ещё не опубликовано.\n"
            "Обычно его выкладывают в конце недели."
        )

    if any(word in low for word in ("выходн", "праздн", "не учебн", "каникул")):
        return text or f"📅 {day} — выходной"

    if "не найден" in low:
        return f"❌ Преподаватель {teacher_fio} не найден в расписании"

    return f"😔 Не удалось получить расписание для {teacher_fio}.\nПопробуйте чуть позже."


def format_schedule_for_day(
    group_name: str, schedule_doc: Dict[str, Any], day: str
) -> str:
    if not schedule_doc:
        return "❌ Расписание для вашей группы не найдено"
    schedule = schedule_doc.get("schedule", {})
    zero_lesson = (schedule.get("zero_lesson") or {}).get(day, {})
    day_lessons = (schedule.get("days") or {}).get(day, {})
    if not zero_lesson and not day_lessons:
        return f"📅 {in_day_ru(day).capitalize()} пар нет"
    result = f"📚 Расписание на {day} ({group_name}):"
    header_lines = schedule_header_lines(schedule_doc)
    if header_lines:
        result += "\n" + "\n".join(header_lines)
    result += "\n\n"
    note = (schedule_doc.get("note") or "").strip()
    if note:
        # Приказ администрации дня: например, «все студенты учатся во 2 корпусе»
        result = f"📍 {note}\n\n" + result
    lessons_today: List[str] = []
    # Нулевая пара
    if zero_lesson:
        subject = zero_lesson.get("subject", "")
        classroom = zero_lesson.get("classroom", "")
        teacher = zero_lesson.get("teacher", "")
        time_str = zero_lesson.get("time")
        if subject:
            lesson_text = f"0. {subject}"
            if classroom:
                lesson_text += f" {classroom} каб."
            if teacher:
                lesson_text += f" ({teacher})"
            if time_str:
                lesson_text += f"\n 🕒 {time_str}"
            lessons_today.append(lesson_text)

    # Основные пары
    for lesson_num, lesson_info in sorted(
        (day_lessons or {}).items(), key=lambda x: lesson_sort_key(x[0])
    ):
        subject = lesson_info.get("subject", "")
        classroom = lesson_info.get("classroom", "")
        teacher = lesson_info.get("teacher", "")
        time_str = lesson_info.get("time")

        if not subject:
            continue

        base, half, subgroup = format_lesson_number(lesson_num)

        if half == "2":
            if subgroup:
                lesson_text = f"   [2/2] ({subgroup} гр) "
            else:
                lesson_text = "   [2/2] "
        else:
            lesson_text = f"{base}. "
            if half == "1":
                lesson_text += "[1/2] "

        lesson_text += subject

        if classroom:
            lesson_text += f" {classroom} каб"

        if teacher:
            lesson_text += f" ({teacher})"

        if time_str:
            lesson_text += f"\n 🕒 {time_str}"

        lessons_today.append(lesson_text)

    if not lessons_today:
        return f"📅 {in_day_ru(day).capitalize()} пар нет"
    result += "\n".join(lessons_today)
    return result


def format_teacher_schedule_for_day(
    teacher_full_fio: str, schedule_doc: Dict[str, Any], day: str
) -> str:
    if not teacher_full_fio:
        return "❌ Не указано ФИО преподавателя"

    if not schedule_doc or "schedule" not in schedule_doc:
        return f"📭 Расписание для {teacher_full_fio} не найдено"

    schedule = schedule_doc.get("schedule", {})
    first_shift = []
    second_shift = []

    for shift_name, shift_dict in schedule.items():
        day_dict = shift_dict.get(day, {})

        for num, info in sorted(day_dict.items(), key=lambda x: lesson_sort_key(x[0])):
            subject = info.get("subject", "")
            group = info.get("group", "")
            time_str = info.get("time")

            base, half, subgroup = format_lesson_number(num)

            if half == "2":
                if subgroup:
                    line = f"   [2/2] ({subgroup} гр) {subject}"
                else:
                    line = f"   [2/2] {subject}"
            else:
                line = f"{base}. "
                if half == "1":
                    line += "[1/2] "
                line += subject

            if group:
                line += f" — {group}"

            place = _lesson_place(info)
            if place:
                line += f" ({place})"

            if time_str:
                line += f"\n 🕒 {time_str}"

            # Параллельные группы (одна пара у нескольких групп сразу)
            for p in info.get("parallels") or []:
                p_subj = (p.get("subject") or "").strip()
                p_group = (p.get("group") or "").strip()
                alt = f"   ⚡ ещё: {p_group}"
                if p_subj and p_subj.lower() != (subject or "").strip().lower():
                    alt += f" — {p_subj}"
                p_place = _lesson_place(p)
                if p_place:
                    alt += f" ({p_place})"
                line += "\n" + alt

            if shift_name == "first_shift":
                first_shift.append(line)
            else:
                second_shift.append(line)

    if not first_shift and not second_shift:
        return f"📅 {in_day_ru(day).capitalize()} пар нет"

    result = f"👨‍🏫 Расписание преподавателя\n{teacher_full_fio}\n\n📅 {day}\n\n"

    # если есть только первая смена
    if first_shift and not second_shift:
        result += "\n".join(first_shift)
        return result

    # если есть обе смены
    if first_shift:
        result += "1️⃣ Первая смена:\n" + "\n".join(first_shift)

    if second_shift:
        result += "\n\n2️⃣ Вторая смена:\n" + "\n".join(second_shift)

    return result


def _format_shift_lessons(schedule: Dict, day: str, shift_name: str) -> list:
    shift_dict = schedule.get(shift_name, {})
    day_dict = shift_dict.get(day, {})
    lessons = []
    for num, info in sorted(day_dict.items(), key=lambda x: lesson_sort_key(x[0])):
        subject = info.get("subject", "")
        group = info.get("group", "")
        time_str = info.get("time")
        base, half, subgroup = format_lesson_number(num)
        if half == "2":
            line = f"   [2/2] ({subgroup} гр) {subject}" if subgroup else f"   [2/2] {subject}"
        else:
            line = f"{base}. "
            if half == "1":
                line += "[1/2] "
            line += subject
        if group:
            line += f" — {group}"
        place = _lesson_place(info)
        if place:
            line += f" ({place})"
        if time_str:
            line += f"\n 🕒 {time_str}"

        # Параллельные группы: в это же время у преподавателя пара с кем-то ещё.
        # Без этого бот показывал одну группу из нескольких.
        parallels = info.get("parallels") or []
        if parallels:
            line += "\n ⚡ Параллельно у вас ещё:"
            for p in parallels:
                p_subj = (p.get("subject") or "").strip()
                p_group = (p.get("group") or "").strip()
                alt = f"      • {p_group}"
                # предмет может совпадать (лекция на поток) — тогда не дублируем
                if p_subj and p_subj.lower() != (subject or "").strip().lower():
                    alt += f" — {p_subj}"
                p_place = _lesson_place(p)
                if p_place:
                    alt += f" ({p_place})"
                line += "\n" + alt

        lessons.append(line)
    return lessons


def format_teacher_schedule_for_week(
    teacher_full_fio: str, schedule_doc: Dict[str, Any]
) -> str:
    if not teacher_full_fio:
        return "❌ Не указано ФИО преподавателя"
    if not schedule_doc or "schedule" not in schedule_doc:
        return f"📭 Расписание для {teacher_full_fio} не найдено"

    schedule = schedule_doc.get("schedule", {})
    result = f"👨‍🏫 Расписание преподавателя\n{teacher_full_fio}\n\n"

    has_any = False
    for day in DAYS_RU:
        first = _format_shift_lessons(schedule, day, "first_shift")
        second = _format_shift_lessons(schedule, day, "second_shift")
        if not first and not second:
            continue
        has_any = True
        result += f"📅 {day}\n"
        if first:
            result += "1️⃣ Первая смена:\n" + "\n".join(first) + "\n"
        if second:
            result += "2️⃣ Вторая смена:\n" + "\n".join(second) + "\n"
        result += "\n"

    if not has_any:
        return f"📭 Расписание для {teacher_full_fio} не найдено"

    return result.strip()
