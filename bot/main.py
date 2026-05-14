import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

# Завантажуємо змінні з файлу .env
load_dotenv(dotenv_path='C:/Projects/vitayko/.env', override=True)

# Налаштування логування — щоб бачити що відбувається в терміналі
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота з .env файлу
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f'Привіт, {user.first_name}! 👋\n\n'
        f'Я VitayKo — сервіс персоналізованих музичних привітань 🎵\n\n'
        f'Незабаром тут буде кнопка для відкриття Mini App!'
    )

# Обробник команди /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🎵 VitayKo — як це працює:\n\n'
        '1. Відкрий Mini App\n'
        '2. Введи ім\'я та дату народження\n'
        '3. Отримай персональне музичне привітання!'
    )

# Головна функція — запуск бота
def main():
    # Створюємо додаток бота
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Реєструємо обробники команд
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    
    # Запускаємо бота
    logger.info('Бот запущено!')
    app.run_polling()

if __name__ == '__main__':
    main()