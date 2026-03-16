from vkbottle import BaseStateGroup


class AdminStates(BaseStateGroup):
    WAIT_BROADCAST = "wait_broadcast"
    WAIT_TEACHER_ID = "wait_teacher_id"
