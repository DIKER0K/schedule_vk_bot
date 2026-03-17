from typing import Any, Dict, List, Tuple
import requests
from requests.adapters import HTTPAdapter, Retry

from core.config import API_URL, PLATFORM


class APIClient:
    def __init__(self):
        self.base_url = API_URL
        self.platform = PLATFORM

        self.session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def request(self, method: str, path: str, **kwargs):
        try:
            url = f"{self.base_url}{path}"
            r = self.session.request(method, url, timeout=30, **kwargs)

            if r.status_code == 200:
                return r.json()

            print(f"[WARN] {method} {path} → {r.status_code}: {r.text[:200]}")

        except Exception as e:
            print(f"[API ERROR] {method} {path}", e)

        return None

    # USERS

    def get_users_by_platform(self, skip=0, limit=100):

        return (
            self.request(
                "GET",
                f"/users/platform/{self.platform}",
                params={"skip": skip, "limit": limit},
            )
            or []
        )
    
    def get_user_by_platform(self, user_id: int):
        """Получить пользователя по platform + user_id"""
        return self.request("GET", f"/users/{self.platform}/{user_id}")

    def get_group_users(self, group_name: str):
        return (
            self.request(
                "GET",
                f"/users/group/{self.platform}/{group_name}",
            )
            or []
        )

    def create_user(self, user_id: int, role="student", username=""):
        payload = {
            "user_id": user_id,
            "platform": self.platform,
            "role": role,
            "username": username,
        }
        return self.request("POST", "/users/", json=payload)

    def update_user(self, user_id: int, data: dict):
        return self.request("PUT", f"/users/{self.platform}/{user_id}", json=data)

    def delete_user(self, user_id: int):
        return self.request("DELETE", f"/users/{self.platform}/{user_id}")

    def get_users(self, skip=0, limit=100):
        return (
            self.request("GET", "/users/", params={"skip": skip, "limit": limit}) or []
        )

    def get_users_page_peek(
        self, skip=0, limit=10
    ) -> Tuple[List[Dict[str, Any]], bool]:
        rows = self.get_users(skip, limit + 1)
        return rows[:limit], len(rows) > limit

    def get_schedule_users(self, time: str):
        return (
            self.request(
                "GET",
                f"/users/schedule/send/{self.platform}/{time}",
            )
            or []
        )

    def get_stats(self):

        return (
            self.request(
                "GET",
                f"/users/stats/{self.platform}",
            )
            or {}
        )

    # SCHEDULE

    def get_groups(self) -> List[str]:
        arr = self.request("GET", "/schedule/")
        if not arr:
            return []

        groups = []
        for item in arr:
            if isinstance(item, dict) and "group_name" in item:
                groups.append(item["group_name"])
            elif isinstance(item, str):
                groups.append(item)

        return sorted(set(groups))

    def get_schedule(self, group_name: str):
        return self.request("GET", f"/schedule/{group_name}")

    def get_teacher_schedule(self, fio_key: str):
        return self.request("GET", f"/schedule/teacher/{fio_key}")

    def upload_schedule(self, docx_bytes: bytes, json_bytes: bytes | None = None):
        files = {
            "schedule_file": (
                "schedule.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        }

        if json_bytes:
            files["shifts_file"] = ("group_shifts.json", json_bytes, "application/json")

        return self.request("POST", "/schedule/upload", files=files)

    def upload_bell_schedule(self, json_bytes: bytes):
        files = {
            "file": ("bell_schedule.json", json_bytes, "application/json"),
        }

        return self.request("POST", "/bell_schedule/bell/upload", files=files)


api = APIClient()
