# bot/main.py
# Telegram бот VitayKo з підтримкою Mini App та Stars платежів

import logging
import os
import sys

# Додаємо корінь проєкту до шляху щоб імпортувати api модулі
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from telegram import (
    Update, WebAppInfo,
    InlineKeyboardButton, InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    PreCheckoutQueryHandler, filters, ContextTypes
)
from dotenv import load_dotenv

# Завантажуємо .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Імпортуємо функції бази даних
from api.database import save_user, update_greeting_status

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Змінні середовища
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBHOOK_URL', 'https://твій-домен.com')

# ===================================================
# КОМАНДА /start
# ===================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє /start і /start <greeting_id>.
    Якщо є параметр — відкриває Mini App одразу на привітанні.
    """
    user = update.effective_user

    # Зберігаємо користувача в БД
    save_user(
        tg_id=user.id,
        username=user.username or '',
        first_name=user.first_name or ''
    )

    # Перевіряємо чи є параметр після /start
    # Наприклад: /start abc123 — посилання на конкретне привітання
    start_param = context.args[0] if context.args else None

    if start_param:
        # Є ID привітання → відкриваємо Mini App одразу на привітанні
        webapp_url = f"{WEBAPP_URL}?start={start_param}"
        keyboard = [[
            InlineKeyboardButton(
                "🎵 Відкрити привітання",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]]
    else:
        # Немає параметра → відкриваємо демо сторінку
        keyboard = [[
            InlineKeyboardButton(
                "🎵 Відкрити VitayKo",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f'Привіт, {user.first_name}! 👋\n\n'
        f'🎵 *VitayKo* — персоналізовані музичні привітання\n\n'
        f'Натисни кнопку щоб відкрити додаток:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ===================================================
# КОМАНДА /help
# ===================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton(
            "🎵 Відкрити VitayKo",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        '🎵 *VitayKo* — як це працює:\n\n'
        '1️⃣ Натисни "Привітати" в додатку\n'
        '2️⃣ Введи ім\'я та оберіть привід\n'
        '3️⃣ Безкоштовно або за 49 ⭐ Stars\n'
        '4️⃣ Надішли другу персональну пісню!\n\n'
        '💡 Безкоштовно: шаблонна пісня\n'
        '⭐ За 49 Stars: унікальна пісня від AI',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ===================================================
# ВІДПРАВКА ІНВОЙСУ (запит оплати Stars)
# ===================================================
async def send_payment_invoice(
    bot, chat_id: int, greeting_id: str,
    recipient_name: str, occasion: str
):
    """
    Надсилає інвойс для оплати 49 Stars.
    Викликається з Flask API після того як
    користувач натиснув "Оплатити" в Mini App.
    """

    # Назва і опис для екрану оплати
    title = "🎵 Персональне привітання VitayKo"

    if recipient_name:
        description = (
            f"Унікальна пісня для {recipient_name} • "
            f"{occasion} • Створена AI спеціально для вас"
        )
    else:
        description = (
            f"Унікальна пісня • {occasion} • "
            f"Створена AI спеціально для вас"
        )

    # Ціна: 49 Stars
    # LabeledPrice — назва і ціна в найменших одиницях (XTR = Stars)
    prices = [LabeledPrice("Персональне привітання", 49)]

    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=greeting_id,   # ID привітання — повернеться після оплати
        currency="XTR",        # XTR = Telegram Stars
        prices=prices,
        # Для Stars не потрібен provider_token — передаємо порожній рядок
        provider_token=""
    )
    logger.info(f"💳 Інвойс надіслано для привітання {greeting_id}")

# ===================================================
# ОБРОБКА PRE-CHECKOUT (підтвердження перед оплатою)
# ===================================================
async def pre_checkout_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Telegram надсилає pre_checkout_query перед списанням Stars.
    Ми маємо відповісти протягом 10 секунд — ok=True або ok=False.
    """
    query = update.pre_checkout_query

    # Завжди підтверджуємо — можна додати перевірку тут
    await query.answer(ok=True)
    logger.info(f"✅ Pre-checkout підтверджено для {query.invoice_payload}")

# ===================================================
# ОБРОБКА SUCCESSFUL_PAYMENT (оплата пройшла)
# ===================================================
async def successful_payment_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Викликається коли Stars успішно списані.
    Тут запускаємо генерацію пісні.
    """
    payment = update.message.successful_payment
    greeting_id = payment.invoice_payload  # ID привітання з інвойсу
    stars_paid = payment.total_amount      # Скільки Stars списано
    user = update.effective_user

    logger.info(
        f"💰 Оплата отримана: {stars_paid} Stars "
        f"від {user.id} для привітання {greeting_id}"
    )

    # Повідомляємо користувача що генерація почалась
    await update.message.reply_text(
        f"✅ Оплата {stars_paid} ⭐ отримана!\n\n"
        f"🎵 Створюємо твою унікальну пісню...\n"
        f"Це займе ~30-60 секунд. Зачекай, будь ласка!"
    )

    # TODO: Запускаємо генерацію в фоні
    # Поки що — заглушка
    try:
        # Оновлюємо статус в БД
        update_greeting_status(greeting_id, 'generating')

        # TODO: Тут буде виклик generate_greeting() з generator.py
        # from api.generator import generate_greeting
        # audio_url = generate_greeting(greeting_id, ...)

        # Поки заглушка — симулюємо готовність
        update_greeting_status(greeting_id, 'done', '/static/demo.mp3')

        # Повідомляємо що готово
        webapp_url = f"{WEBAPP_URL}?start={greeting_id}"
        keyboard = [[
            InlineKeyboardButton(
                "🎵 Слухати пісню",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🎉 Твоя пісня готова!\n\n"
            f"Натисни кнопку щоб послухати і надіслати:",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"❌ Помилка генерації: {e}")
        update_greeting_status(greeting_id, 'error')
        await update.message.reply_text(
            "❌ Помилка при створенні пісні. "
            "Зверніться до підтримки — Stars будуть повернені."
        )

# ===================================================
# ЗАПУСК БОТА
# ===================================================
async def webapp_data_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Отримує дані від Mini App через tg.sendData().
    Надсилає інвойс на оплату Stars.
    """
    import json
    data_str = update.message.web_app_data.data
    
    try:
        data = json.loads(data_str)
    except Exception:
        return

    if data.get('action') == 'request_payment':
        greeting_id = data.get('greeting_id')
        recipient_name = data.get('recipient_name', '')
        occasion = data.get('occasion', 'привітання')

        # Надсилаємо інвойс
        await send_payment_invoice(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            greeting_id=greeting_id,
            recipient_name=recipient_name,
            occasion=occasion
        )
        logger.info(f"💳 Надіслано інвойс для {greeting_id}")
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Команди
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))

    # Обробники платежів — порядок важливий!
    app.add_handler(MessageHandler(
        filters.StatusUpdate.WEB_APP_DATA, webapp_data_handler
    ))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(
        filters.SUCCESSFUL_PAYMENT, successful_payment_handler
    ))

    logger.info('🤖 VitayKo бот запущено!')
    app.run_polling()

if __name__ == '__main__':
    main()