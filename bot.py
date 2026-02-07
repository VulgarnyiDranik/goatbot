from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "8524916434:AAH2V0JbHb3pio9y0BO5HKsjQcSjpLql1q0"
ADMIN_ID = 8384055519  # твой Telegram ID

# состояния пользователей
# wait_data → ждём данные
# wait_admin → ждём админа
# dialog → диалог
user_state = {}

# кто сейчас ждёт ответ админа
admin_reply_target = {}

START_TEXT = (
    "🎉 Поздравляю! Ты успел купить билет в первую волну.\n\n"
    "В течение часа отправь данные в формате, указанном ниже, "
    "и жди ответ от организаторов!\n\n"
    "1. ФИО\n"
    "2. Телеграмм\n"
    "3. Кто тебя пригласил(необязательно)"
)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = "wait_data"
    await update.message.reply_text(START_TEXT)

# --- любое сообщение от пользователя ---
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id == ADMIN_ID:
        # админ пишет ответ пользователю
        if user_id in admin_reply_target:
            target_id = admin_reply_target.pop(user_id)
            await context.bot.send_message(target_id, text)
            await update.message.reply_text("✅ Сообщение отправлено пользователю")
        return

    # пользователь пишет данные или сообщение
    state = user_state.get(user_id)

    if state in ("wait_data", "dialog"):
        msg = (
            "📩 СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ\n\n"
            f"{text}\n\n"
            f"🆔 User ID: {user_id}"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✉️ Ответить", callback_data=f"reply_{user_id}")],
            [InlineKeyboardButton("🚫 Завершить", callback_data=f"close_{user_id}")]
        ])

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            reply_markup=keyboard
        )

        user_state[user_id] = "wait_admin"
        await update.message.reply_text("✅ Данные получены. Ожидайте ответ организатора.")

# --- кнопки админа ---
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if action == "reply":
        admin_reply_target[ADMIN_ID] = user_id
        user_state[user_id] = "dialog"
        await query.message.reply_text("✍️ Напишите сообщение пользователю:")

    elif action == "close":
        await context.bot.send_message(
            user_id,
            "✅ Диалог завершён. Спасибо!"
        )
        user_state[user_id] = "closed"
        await query.edit_message_reply_markup(reply_markup=None)

# --- запуск ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(admin_buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_message))


app.run_polling()

