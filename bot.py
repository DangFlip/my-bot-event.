import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

CHOOSING_EVENT, ASK_GUESTS, ASK_VENUE, ASK_BUDGET = range(4)

EVENTS = [
    "День рождения", "Свадьба", "Корпоратив", "Выпускной", "Вечеринка",
    "Мальчишник", "Девичнник", "Юбилей", "Предложение руки и сердца",
    "Концерт", "Тимбилдинг", "Выставка", "Гендерная вечеринка"
]

ADMIN_CHAT_ID = 796306412 

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("Токен не задан! Укажите BOT_TOKEN в переменных окружения.")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- Обработчики --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога: приветствие и выбор мероприятия."""
    # Создаём клавиатуру с кнопками мероприятий (по 2 в ряд)
    keyboard = []
    row = []
    for i, event in enumerate(EVENTS):
        row.append(InlineKeyboardButton(event, callback_data=event))
        if (i + 1) % 2 == 0 or i == len(EVENTS) - 1:
            keyboard.append(row)
            row = []
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Добрый день! Какого вида мероприятие вас интересует?",
        reply_markup=reply_markup
    )
    return CHOOSING_EVENT

async def event_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пользователь выбрал мероприятие через кнопку."""
    query = update.callback_query
    await query.answer()
    chosen_event = query.data
    context.user_data['event'] = chosen_event 

    await query.edit_message_text(
        f"Вы выбрали: {chosen_event}\n\nСколько планируется гостей? (введите число)"
    )
    return ASK_GUESTS

async def ask_guests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем количество гостей."""
    text = update.message.text
 
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите число (количество гостей).")
        return ASK_GUESTS  
    context.user_data['guests'] = text

    await update.message.reply_text("Какая площадка у вас будет? (введите название)")
    return ASK_VENUE

async def ask_venue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем название площадки."""
    venue = update.message.text
    context.user_data['venue'] = venue

    await update.message.reply_text("Сколько планируете бюджет данного мероприятия? (введите число)")
    return ASK_BUDGET

async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем бюджет и завершаем опрос."""
    budget = update.message.text
  
    context.user_data['budget'] = budget


    user_id = update.effective_user.id
    username = update.effective_user.username or "нет username"
    event = context.user_data.get('event', 'не указано')
    guests = context.user_data.get('guests', 'не указано')
    venue = context.user_data.get('venue', 'не указано')
    budget_val = context.user_data.get('budget', 'не указано')

 
    admin_message = (
        f"📋 Новая заявка от пользователя @{username} (ID: {user_id})\n\n"
        f"🎉 Мероприятие: {event}\n"
        f"👥 Гостей: {guests}\n"
        f"📍 Площадка: {venue}\n"
        f"💰 Бюджет: {budget_val}"
    )

    try:
        
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        logger.info(f"Сообщение админу отправлено для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение админу: {e}")
      

    await update.message.reply_text("Спасибо за обращение, с вами свяжутся!")

 
    context.user_data.clear()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога."""
    await update.message.reply_text("Диалог отменён. Для начала напишите /start")
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help."""
    await update.message.reply_text("Для начала анкеты напишите /start")

# -------------------- Запуск --------------------

def main() -> None:
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()

    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_EVENT: [CallbackQueryHandler(event_chosen)],
            ASK_GUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_guests)],
            ASK_VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_venue)],
            ASK_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_budget)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))

    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
