from vkbottle.dispatch.middlewares import BaseMiddleware
from vkbottle.bot import Message
from utils.api import api


class UserMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        message: Message = self.event
        user_id = message.from_id

        user = api.get_user(user_id)

        if not user:
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

        # ВАЖНО
        self.send({"user": user})
