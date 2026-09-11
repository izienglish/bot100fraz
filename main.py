import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Настройки ---
BOT_TOKEN = os.environ["BOT_TOKEN"]          # токен берём из переменной окружения, не хардкодим
CHANNEL_USERNAME = "@izi_en"                  # канал, на который проверяем подписку
PDF_PATH = os.path.join(os.path.dirname(__file__), "assets", "EasyPeasy_100Fraz.pdf")
PDF_FILENAME = "100_фраз_Easy-Peasy.pdf"

SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}


async def is_subscribed(bot, user_id: int) -> bool:
    """Проверяет через Bot API, состоит ли пользователь в канале.
    Боту обязательно нужно быть админом канала, иначе get_chat_member упадёт с ошибкой."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in SUBSCRIBED_STATUSES
    except Exception as e:
        logger.warning(f"Не удалось проверить подписку для {user_id}: {e}")
        return False


def subscribe_keyboard() -> InlineKeyboardMarkup:
    channel_url = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Подписаться на канал", url=channel_url)],
            [InlineKeyboardButton("✅ Я подписался, проверить", callback_data="check_subscription")],
        ]
    )


async def send_pdf(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    with open(PDF_PATH, "rb") as f:
        await context.bot.send_document(
            chat_id=chat_id,
            document=f,
            filename=PDF_FILENAME,
            caption=(
                "Вот твой файл «100 самых нужных фраз на Английском»! 🎉\n\n"
                "Сохрани его и повторяй фразы каждый день — так лучше всего запоминается 💪"
            ),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if await is_subscribed(context.bot, user.id):
        await send_pdf(update.effective_chat.id, context)
    else:
        await update.message.reply_text(
            "Привет! 👋\n\n"
            f"Чтобы получить файл «100 самых нужных фраз на Английском», сначала подпишись на канал {CHANNEL_USERNAME} "
            "— там ещё много полезного для изучения английского.\n\n"
            "После подписки нажми кнопку ниже 👇",
            reply_markup=subscribe_keyboard(),
        )


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if await is_subscribed(context.bot, user.id):
        await query.edit_message_text("Отлично, подписка подтверждена! ✅ Отправляю файл...")
        await send_pdf(query.message.chat_id, context)
    else:
        await query.answer(
            "Пока не вижу подписки 🙁 Подпишись на канал и попробуй ещё раз.",
            show_alert=True,
        )


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))

    logger.info("Бот запущен, жду сообщений...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
