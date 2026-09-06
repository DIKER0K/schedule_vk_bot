import threading
from typing import Dict, Optional


class TeacherRequest:
    def __init__(self, user_id: int, fio: str, username: str = ""):
        self.user_id = user_id
        self.fio = fio
        self.username = username


class TeacherRequestStore:
    def __init__(self):
        self._requests: Dict[int, TeacherRequest] = {}
        self._lock = threading.Lock()

    def add(self, user_id: int, fio: str, username: str = "") -> TeacherRequest:
        with self._lock:
            req = TeacherRequest(user_id, fio, username)
            self._requests[user_id] = req
            return req

    def get(self, user_id: int) -> Optional[TeacherRequest]:
        with self._lock:
            return self._requests.get(user_id)

    def remove(self, user_id: int) -> Optional[TeacherRequest]:
        with self._lock:
            return self._requests.pop(user_id, None)

    def get_all(self) -> list:
        with self._lock:
            return list(self._requests.values())


teacher_requests = TeacherRequestStore()
