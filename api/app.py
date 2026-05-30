# api/app.py
# Головний Flask додаток — сервер який обробляє запити від Mini App

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Завантажуємо .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Імпортуємо функції бази даних
from api.database import init_db, get_greeting, create_greeting

# Шляхи до папок проєкту
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # папка vitayko/
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Створюємо Flask додаток
app = Flask(__name__, 
            static_folder=STATIC_DIR,
            static_url_path='/static')
app.config['JSON_AS_ASCII'] = False

# Дозволяємо запити з будь-якого домену (потрібно для Mini App)
CORS(app)

# ===================================================
# МАРШРУТ: Головна сторінка → index.html
# ===================================================
@app.route('/')
def index():
    """
    Повертає index.html для будь-якого запиту на головну.
    Mini App завжди відкривається через цей маршрут.
    """
    return send_from_directory(FRONTEND_DIR, 'index.html')

# ===================================================
# МАРШРУТ: Отримати дані привітання
# GET /api/greeting/<id>
# ===================================================
@app.route('/api/greeting/<greeting_id>', methods=['GET'])
def get_greeting_api(greeting_id):
    """
    Mini App викликає цей маршрут щоб отримати дані привітання.
    Наприклад: GET /api/greeting/abc123
    """
    greeting = get_greeting(greeting_id)
    
    if not greeting:
        # 404 — привітання не знайдено
        return jsonify({'error': 'Привітання не знайдено'}), 404
    
    # Повертаємо тільки потрібні поля (не всі — для безпеки)
    return jsonify({
        'id': greeting['id'],
        'recipient_name': greeting['recipient_name'],
        'occasion': greeting['occasion'],
        'status': greeting['status'],
        'audio_url': greeting['audio_url'],
        'is_paid': greeting['is_paid']
    })

# ===================================================
# МАРШРУТ: Створити привітання
# POST /api/greeting/create
# ===================================================
@app.route('/api/greeting/create', methods=['POST'])
def create_greeting_api():
    """
    Mini App надсилає дані форми сюди.
    Flask зберігає в БД і повертає унікальний ID.
    """
    data = request.get_json()
    
    # Перевіряємо обов'язкові поля
    if not data or 'occasion' not in data:
        return jsonify({'error': 'Вкажіть привід'}), 400
    
    # Створюємо запис в базі даних
    greeting_id = create_greeting(
        creator_tg_id=data.get('creator_tg_id'),
        recipient_name=data.get('recipient_name', ''),  # Може бути порожнім
        occasion=data['occasion'],
        is_paid=data.get('is_paid', 0),
        style=data.get('style'),
        language=data.get('language', 'uk'),
        details=data.get('details', '')
    )
    
    # Повертаємо ID — Mini App побудує посилання з нього
    return jsonify({
        'success': True,
        'greeting_id': greeting_id,
        'share_url': f"https://t.me/VitayKoBot?start={greeting_id}"
    })

# ===================================================
# МАРШРУТ: Перевірка що сервер працює
# GET /api/health
# ===================================================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'VitayKo API'})

# ===================================================
# ЗАПУСК СЕРВЕРА
# ===================================================
# ===================================================
# МАРШРУТ: Запит оплати — бот надсилає інвойс
# POST /api/payment/request
# ===================================================
@app.route('/api/payment/request', methods=['POST'])
def request_payment():
    """
    Mini App викликає цей маршрут.
    Flask просить бота надіслати інвойс користувачу.
    """
    import asyncio
    from telegram import Bot, LabeledPrice

    data = request.get_json()
    greeting_id = data.get('greeting_id')
    tg_user_id = data.get('tg_user_id')
    recipient_name = data.get('recipient_name', '')
    occasion = data.get('occasion', 'привітання')

    if not greeting_id or not tg_user_id:
        return jsonify({'error': 'Відсутні дані'}), 400

    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    async def send_invoice():
        bot = Bot(token=BOT_TOKEN)
        if recipient_name:
            description = f"Унікальна пісня для {recipient_name} • {occasion}"
        else:
            description = f"Унікальна пісня • {occasion}"

        await bot.send_invoice(
            chat_id=tg_user_id,
            title="🎵 Персональне привітання VitayKo",
            description=description,
            payload=greeting_id,
            currency="XTR",
            prices=[LabeledPrice("Персональне привітання", 49)],
            provider_token=""
        )

    asyncio.run(send_invoice())
    return jsonify({'success': True})
if __name__ == '__main__':
    # Ініціалізуємо базу даних при першому запуску
    init_db()
    
    print('🚀 VitayKo API запущено на http://localhost:5000')
    
    # debug=True — автоматично перезапускає при змінах в коді
    app.run(debug=True, host='0.0.0.0', port=5000)