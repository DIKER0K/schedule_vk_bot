from vkbottle.bot import Message
from core.bot import bot
from states.feedback_states import FeedbackStates


@bot.on.message(text="💬 Обратная связь")
async def feedback_start(message: Message):

    await bot.state_dispenser.set(
        message.peer_id,
        FeedbackStates.WAIT_MESSAGE
    )

    await message.answer(
        "💬 Напишите сообщение для администрации.\n\n"
        "Опишите проблему или вопрос.\n"
        "Для отмены напишите 'отмена'."
    )