from vkbottle import BaseStateGroup


class AdminStates(BaseStateGroup):
    WAIT_BROADCAST = "wait_broadcast"
    WAIT_TEACHER_ID = "wait_teacher_id"
    WAIT_BROADCAST_MSG = "wait_broadcast_msg"
    WAIT_BELL_JSON = "wait_bell_json"
    WAIT_SCHEDULE_DOCX = "wait_schedule_docx"
