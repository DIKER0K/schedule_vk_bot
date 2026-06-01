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
                user_ids=user_id, fields=["domain,first_name,last_name"]
            )

            username = ""
            first_name = ""
            last_name = ""

            if vk_user:
                vk_user = vk_user[0]
                first_name = getattr(vk_user, 'first_name', '') or ''
                last_name = getattr(vk_user, 'last_name', '') or ''
                username = vk_user.domain or f"{first_name} {last_name}"

            user = api.create_user(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            logger.info(f"✅ Пользователь создан: {user}")

        # Дозаполняем first_name, last_name, если пустые
        if not user.get("first_name") or not user.get("last_name"):
            try:
                vk_user = await message.ctx_api.users.get(
                    user_ids=user_id, fields=["domain,first_name,last_name"]
                )
                if vk_user:
                    vk_user = vk_user[0]
                    first_name = getattr(vk_user, 'first_name', '') or ''
                    last_name = getattr(vk_user, 'last_name', '') or ''
                    domain = getattr(vk_user, 'domain', '') or ''
                    api.update_user(user_id, {
                        "first_name": first_name,
                        "last_name": last_name,
                        "username": domain or f"{first_name} {last_name}",
                    })
                    user["first_name"] = first_name
                    user["last_name"] = last_name
                    user["username"] = domain or f"{first_name} {last_name}"
            except Exception as e:
                logger.warning(f"Failed to update user data for {user_id}: {e}")

        # ВАЖНО
        self.send({"user": user})
