import threading
import time
from typing import Dict, List, Optional


COOLDOWN_SECONDS = 3600


class TeacherRequest:
    def __init__(self, user_id: int, fio: str, username: str = ""):
        self.user_id = user_id
        self.fio = fio
        self.username = username
        self.votes_for: Dict[int, str] = {}
        self.votes_against: Dict[int, str] = {}
        self.resolved = False

    def add_vote(self, admin_id: int, admin_name: str, vote_for: bool) -> None:
        if vote_for:
            self.votes_for[admin_id] = admin_name
            self.votes_against.pop(admin_id, None)
        else:
            self.votes_against[admin_id] = admin_name
            self.votes_for.pop(admin_id, None)

    def get_vote_text(self, total_admins: int) -> str:
        threshold = (total_admins + 1) // 2
        for_needed = max(0, threshold - len(self.votes_for))
        against_needed = max(0, threshold - len(self.votes_against))

        lines = []
        if self.votes_for:
            names = ", ".join(self.votes_for.values())
            lines.append(f"✅ Принять ({len(self.votes_for)}): {names}")
        else:
            lines.append(f"✅ Принять (0)")
        if self.votes_against:
            names = ", ".join(self.votes_against.values())
            lines.append(f"❌ Отклонить ({len(self.votes_against)}): {names}")
        else:
            lines.append(f"❌ Отклонить (0)")
        lines.append(f"\nГолосов: {len(self.votes_for) + len(self.votes_against)} из {total_admins}")
        lines.append(f"Нужно голосов: {for_needed} за / {against_needed} против")
        return "\n".join(lines)

    def is_approved(self, total_admins: int) -> bool:
        threshold = (total_admins + 1) // 2
        return len(self.votes_for) >= threshold

    def is_rejected(self, total_admins: int) -> bool:
        threshold = (total_admins + 1) // 2
        return len(self.votes_against) >= threshold


class TeacherRequestStore:
    def __init__(self):
        self._requests: Dict[int, TeacherRequest] = {}
        self._cooldowns: Dict[int, float] = {}
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

    def set_cooldown(self, user_id: int) -> None:
        with self._lock:
            self._cooldowns[user_id] = time.time()

    def get_cooldown_remaining(self, user_id: int) -> int:
        with self._lock:
            expire_at = self._cooldowns.get(user_id)
            if not expire_at:
                return 0
            remaining = int(expire_at + COOLDOWN_SECONDS - time.time())
            if remaining <= 0:
                del self._cooldowns[user_id]
                return 0
            return remaining

    def get_all(self) -> List[TeacherRequest]:
        with self._lock:
            return list(self._requests.values())


teacher_requests = TeacherRequestStore()
