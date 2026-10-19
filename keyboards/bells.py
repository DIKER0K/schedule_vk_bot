"""Inline-кнопки пар под сообщением «Когда звонок».

Бэкенд /next-bell отдаёт lessons: список пар дня (номер, время, метка).
Кнопки начинаются с текущей (или следующей) пары — та, что уже прошла,
не показывается. Время пары хранится в кэше, чтобы клик по кнопке
не ходил в API повторно.
"""
from typing import Optional
import re

from vkbottle import Callback, Keyboard

from core.config import TZ
from datetime import datetime
from zoneinfo import ZoneInfo

# {(user_id, номер пары): {start, end, label}}
BELL_LESSONS_CACHE: dict = {}


def _now() -> datetime:
    return datetime.now(ZoneInfo(TZ))


def _pair_sort_key(number: str):
    """«0» в конец, остальное — числово."""
    try:
        return (1, int(number), "")
    except (TypeError, ValueError):
        return (0, 0, str(number))


def bell_lessons_keyboard(
    data: dict, user_id: Optional[int] = None, now: Optional[datetime] = None
) -> Optional[Keyboard]:
    """Собирает inline-клавиатуру пар из ответа /next-bell.

    Возвращает None, если пар нет (выходной) или бэкенд старый — тогда
    обработчик отправляет только текст.
    """
    lessons = data.get("lessons") or []
    if not lessons:
        return None

    if now is None:
        now = _now()
    now_seconds = now.hour * 3600 + now.minute * 60 + now.second

    # пары, которые уже закончились, в кнопки не попадают
    live = [l for l in lessons if _hhmm_to_sec(l.get("end", "23:59")) > now_seconds]
    if not live:
        return None

    # если сейчас перемена/пара — стартуем с текущей
    ev = data.get("current_event") or {}
    current_number = ev.get("lesson_number")
    if current_number:
        current_number = str(current_number).split(".")[0]
        idx = [i for i, l in enumerate(live) if l.get("number") == current_number]
        if idx:
            live = live[idx[0]:]

    kb = Keyboard(inline=True)

    # каждая кнопка — отдельной строкой, во всю ширину
    for l in live:
        number = l.get("number")
        # подпись кнопки: чистое имя пары без «(1-й час)» —
        # кнопка показывает пару целиком (обе половинки), так что
        # приписка про первый час вводит в заблуждение
        raw = (l.get("label") or f"{number} пара").strip()
        clean = re.sub(r"\s*\(\d+-й час\)\s*$", "", raw).strip()
        # классный час и прочие длинные специальные метки — короче
        if len(clean) > 20:
            m = re.search(r"«([^»]+)»", clean)
            if m and len(m.group(1)) <= 20:
                clean = m.group(1)
            else:
                clean = clean[:18].rstrip() + "…"
        title = clean.lower()
        if not title.startswith("когда"):
            title = f"когда {title}"
        payload = {"cmd": "bell_pair_info", "number": number}
        kb.add(Callback(title, payload=payload))
        kb.row()

    # кэш для обработчика кликов: время пары на сегодня
    if user_id is not None:
        for l in lessons:
            BELL_LESSONS_CACHE[(user_id, l.get("number"))] = {
                "start": l.get("start"),
                "end": l.get("end"),
                # в ответе по клику приписку часа тоже убираем
                "label": re.sub(r"\s*\(\d+-й час\)\s*$", "",
                                (l.get("label") or f"{l.get('number')} пара").strip()),
                "halves": l.get("halves") or [],
                "break_between_minutes": l.get("break_between_minutes"),
            }

    return kb


def _hhmm_to_sec(value: str) -> int:
    try:
        h, m = value.split(":")
        return int(h) * 3600 + int(m) * 60
    except (ValueError, AttributeError):
        return 0