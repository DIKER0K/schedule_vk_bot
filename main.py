from core.config import BOT_TOKEN
from vkbottle.bot import Bot

bot = Bot(BOT_TOKEN)


@bot.on.message()
async def handler(_) -> str:
    return "Hello, World!"


bot.run_forever()
