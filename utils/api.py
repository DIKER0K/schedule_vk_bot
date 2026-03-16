from typing import Any, Dict, List, Optional
from requests.adapters import HTTPAdapter, Retry
import requests
from ..core.config import API_URL, PLATFORM

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))


def _request(method: str, path: str, **kwargs):
    try:
        url = f"{API_URL}{path}"
        r = session.request(method, url, timeout=30, **kwargs)

        if r.status_code == 200:
            return r.json()

        print(f"[WARN] {method} {path} → {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[API ERROR] {method} {path}", e)

    return None


def api_get_user(user_id: int):
    return _request("GET", f"/users/{PLATFORM}/{user_id}")


def api_create_user(user_id: int, role="student", username=""):
    payload = {
        "user_id": user_id,
        "platform": PLATFORM,
        "role": role,
        "username": username,
    }

    return _request("POST", "/users/", json=payload)


def api_update_user(user_id: int, data: dict):
    return _request("PUT", f"/users/{PLATFORM}/{user_id}", json=data)


def api_delete_user(user_id: int):
    return _request("DELETE", f"/users/{PLATFORM}/{user_id}")


def api_get_users(skip=0, limit=100):
    return _request("GET", "/users/", params={"skip": skip, "limit": limit}) or []


def api_get_users_page_peek(skip=0, limit=10):
    rows = api_get_users(skip, limit + 1)
    return rows[:limit], len(rows) > limit


def api_get_all_groups() -> List[str]:
    arr = _request("GET", "/schedule/")
    if not arr:
        return []

    groups: List[str] = []

    for item in arr:
        if isinstance(item, dict) and "group_name" in item:
            groups.append(item["group_name"])
        elif isinstance(item, str):
            groups.append(item)

    import re

    def key_fn(g: str):
        m = re.match(r"(\d+)", g)
        course = int(m.group(1)) if m else 0
        m2 = re.match(r"\d+\s*([А-Яа-яA-Za-z]*)", g)
        suf = m2.group(1) if m2 else g
        return (course, suf)

    return sorted(list(dict.fromkeys(groups)), key=key_fn)


def api_get_schedule(group_name: str) -> Optional[Dict[str, Any]]:
    return _request("GET", f"/schedule/{group_name}")


def api_get_teacher_schedule(fio_key: str) -> Optional[Dict[str, Any]]:
    return _request("GET", f"/schedule/teacher/{fio_key}")


def api_upload_schedule(docx_bytes: bytes, json_bytes: bytes | None = None):
    files = {
        "schedule_file": (
            "schedule.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    }

    if json_bytes:
        files["shifts_file"] = ("group_shifts.json", json_bytes, "application/json")

    return _request("POST", "/schedule/upload", files=files)


def check_api_connection():
    print(f"🔍 Проверка API-доступности: {API_URL}")

    data = _request("GET", "/users/?limit=1")

    if data is not None:
        print("✅ API доступно, соединение установлено!")
    else:
        print("❌ Не удалось подключиться к API.")


def api_upload_bell_schedule(json_bytes: bytes):
    files = {
        "file": ("bell_schedule.json", json_bytes, "application/json"),
    }

    return _request("POST", "/bell_schedule/bell/upload", files=files)
