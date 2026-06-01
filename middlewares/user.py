from vkbottle.dispatch.middlewares import BaseMiddleware
from vkbottle.bot import Message
from utils.api import api
import logging

logger = logging.getLogger(__name__)

class UserMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        logger.info(f"📩 Middleware pre() вызван для user_id={self.event.from_id}, text='{self.event.text}'")
        message: Message = self.event
        user_id = message.from_id

        user = api.get_user_by_platform(user_id)
        logger.info(f"🔍 Пользователь в БД: {'найден' if user else 'не найден'}")

        if not user:
            logger.info(f"➕ Создаём нового пользователя {user_id}")
            vk_user = await message.ctx_api.users.get(
                user_ids=user_id, fields=["domain"]
            )

            username = ""

            if vk_user:
                vk_user = vk_user[0]

                if vk_user.domain:
                    username = vk_user.domain
                else:
                    username = f"{vk_user.first_name} {vk_user.last_name}"

            user = api.create_user(
                user_id=user_id,
                username=username,
            )
            logger.info(f"✅ Пользователь создан: {user}")

        # Дозаполняем username, если пустой
        if not user.get("username"):
            try:
                vk_user = await message.ctx_api.users.get(
                    user_ids=user_id, fields=["domain"]
                )
                if vk_user:
                    vk_user = vk_user[0]
                    username = vk_user.domain or f"{vk_user.first_name} {vk_user.last_name}"
                    api.update_user(user_id, {"username": username})
                    user["username"] = username
            except Exception as e:
                logger.warning(f"Failed to update username for {user_id}: {e}")

        # ВАЖНО
        self.send({"user": user})
