import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Получаем токен из переменной окружения
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    print("ОШИБКА: токен не задан!")
    exit(1)

# Функция-обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Привет":
        await update.message.reply_text("Здравствуй мой дорогой друг!")
    else:
        await update.message.reply_text("Я понимаю только 'Привет'.")

# Запуск бота
if __name__ == "__main__":
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    # Запускаем polling (этот метод сам создаёт цикл событий и блокирует выполнение)
    application.run_polling()