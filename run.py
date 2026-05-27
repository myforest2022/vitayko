# run.py
# Головний файл для запуску всього проєкту

from api.database import init_db
from api.app import app

if __name__ == '__main__':
    # Створюємо таблиці в БД якщо їх немає
    init_db()
    
    # Запускаємо Flask сервер
    app.run(debug=True, host='0.0.0.0', port=5000)