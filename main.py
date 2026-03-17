from core.bot import bot
from middlewares.user import UserMiddleware
from scheduler.scheduler import start_scheduler
import logging

logging.basicConfig(level=logging.INFO)
print("BOT STARTING")

bot.labeler.message_view.register_middleware(UserMiddleware)

# регистрация handlers
import handlers.commands
import handlers.settings
import handlers.settings_callbacks
import handlers.teacher_panel
import handlers.teacher_callbacks
import handlers.admin_callbacks
import handlers.feedback
import handlers.onboarding
import handlers.text

start_scheduler()

bot.run_forever()
