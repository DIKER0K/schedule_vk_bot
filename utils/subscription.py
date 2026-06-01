import logging
from core.config import GROUP_ID, GROUP_LINK

logger = logging.getLogger(__name__)


async def is_subscribed(api, user_id: int) -> bool:
    if not GROUP_ID:
        return True

    try:
        result = await api.groups.is_member(group_id=GROUP_ID, user_id=user_id)
        return bool(result)
    except Exception as e:
        logger.error(f"Subscription check error for user {user_id}: {e}")
        return True


def get_subscribe_message() -> str:
    return (
        "🔒 Для доступа к расписанию нужно быть подписанным на наше сообщество!\n\n"
        f"📢 Подпишись: {GROUP_LINK}\n\n"
        "После подписки нажми любую кнопку снова"
    )
