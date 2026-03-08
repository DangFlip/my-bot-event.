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

# Состояния диалога
CHOOSING_EVENT, ASK_GUESTS, ASK_VENUE, ASK_BUDGET, ASK_PHONE, CONFIRM = range(6)

# Список мероприятий с эмодзи (для красоты)
EVENTS = [
    "🎂 День рождения", "💍 Свадьба", "💼 Корпоратив", "🎓 Выпускной",
    "🎉 Вечеринка", "🍻 Мальчишник", "👰 Девичник", "🥂 Юбилей",
    "💍 Предложение руки и сердца", "🎤 Концерт", "🤝 Тимбилдинг",
    "🖼️ Выставка", "👶 Гендерная вечеринка"
]

# Твой chat_id (замени на свой!)
ADMIN_CHAT_ID = 796306412  # <--- ВСТАВЬ СВОЙ ID СЮДА

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ Токен не задан! Укажите BOT_TOKEN в переменных окружения.")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- Обработчики --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приветствие и выбор мероприятия."""
    # Создаём клавиатуру с кнопками (по 2 в ряд)
    keyboard = []
    row = []
    for i, event in enumerate(EVENTS):
        row.append(InlineKeyboardButton(event, callback_data=event))
        if (i + 1) % 2 == 0 or i == len(EVENTS) - 1:
            keyboard.append(row)
            row = []
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🌟 *Добрый день!* 🌟\n\n"
        "Какого вида мероприятие вас интересует?",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return CHOOSING_EVENT

async def event_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняем выбранное мероприятие и переходим к вопросу о гостях."""
    query = update.callback_query
    await query.answer()
    chosen_event = query.data
    context.user_data['event'] = chosen_event

    await query.edit_message_text(
        f"✅ Вы выбрали: *{chosen_event}*\n\n"
        "👥 Сколько планируется гостей? (введите число)",
        parse_mode='Markdown'
    )
    return ASK_GUESTS

async def ask_guests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем количество гостей."""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text(
            "❌ Пожалуйста, введите **число** (например, 50).",
            parse_mode='Markdown'
        )
        return ASK_GUESTS
    context.user_data['guests'] = text

    await update.message.reply_text(
        "📍 Какая площадка у вас будет? (введите название или адрес)"
    )
    return ASK_VENUE

async def ask_venue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем площадку."""
    venue = update.message.text.strip()
    context.user_data['venue'] = venue

    await update.message.reply_text(
        "💰 Сколько планируете бюджет данного мероприятия? (введите сумму)"
    )
    return ASK_BUDGET

async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем бюджет."""
    budget = update.message.text.strip()
    # Можно добавить проверку на число, но оставим как есть
    context.user_data['budget'] = budget

    await update.message.reply_text(
        "📞 Укажите ваш номер телефона для связи (можно в любом формате):"
    )
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем номер телефона и переходим к подтверждению."""
    phone = update.message.text.strip()
    context.user_data['phone'] = phone

    # Формируем сводку для подтверждения
    summary = (
        "📋 *Проверьте введённые данные:*\n\n"
        f"🎉 *Мероприятие:* {context.user_data.get('event', '—')}\n"
        f"👥 *Гостей:* {context.user_data.get('guests', '—')}\n"
        f"📍 *Площадка:* {context.user_data.get('venue', '—')}\n"
        f"💰 *Бюджет:* {context.user_data.get('budget', '—')}\n"
        f"📞 *Телефон:* {context.user_data.get('phone', '—')}\n\n"
        "Всё верно?"
    )

    # Кнопки Да / Нет
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, отправить", callback_data="confirm_yes"),
            InlineKeyboardButton("🔄 Нет, заполнить заново", callback_data="confirm_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(summary, parse_mode='Markdown', reply_markup=reply_markup)
    return CONFIRM

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатываем ответ пользователя на подтверждение."""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_yes":
        # Отправляем данные админу
        user = update.effective_user
        username = user.username or "нет username"
        user_id = user.id

        admin_message = (
            "📬 *Новая заявка!*\n\n"
            f"👤 *Пользователь:* @{username} (ID: `{user_id}`)\n"
            f"🎉 *Мероприятие:* {context.user_data['event']}\n"
            f"👥 *Гостей:* {context.user_data['guests']}\n"
            f"📍 *Площадка:* {context.user_data['venue']}\n"
            f"💰 *Бюджет:* {context.user_data['budget']}\n"
            f"📞 *Телефон:* {context.user_data['phone']}"
        )

        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_message,
                parse_mode='Markdown'
            )
            logger.info(f"Заявка отправлена админу от пользователя {user_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение админу: {e}")
            await query.edit_message_text(
                "⚠️ Произошла ошибка при отправке заявки. Мы уже знаем и скоро исправим."
            )
            # Всё равно завершаем диалог, чтобы не зависло
            context.user_data.clear()
            return ConversationHandler.END

        # Благодарим пользователя
        await query.edit_message_text(
            "✅ *Спасибо за обращение!*\n\n"
            "Ваша заявка отправлена. Скоро с вами свяжутся.",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END

    else:  # confirm_no
        # Пользователь хочет начать заново
        await query.edit_message_text(
            "🔄 Давайте начнём сначала. Чтобы заполнить новую анкету, отправьте /start"
        )
        context.user_data.clear()
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога."""
    await update.message.reply_text(
        "❌ Диалог отменён. Если захотите заполнить анкету, нажмите /start"
    )
    context.user_data.clear()
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help."""
    await update.message.reply_text(
        "ℹ️ Этот бот помогает собрать заявку на мероприятие.\n"
        "Просто отправьте /start и следуйте инструкциям."
    )

# -------------------- Запуск --------------------

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Обработчик диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_EVENT: [CallbackQueryHandler(event_chosen)],
            ASK_GUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_guests)],
            ASK_VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_venue)],
            ASK_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_budget)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            CONFIRM: [CallbackQueryHandler(confirm_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))

    print("🚀 Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
