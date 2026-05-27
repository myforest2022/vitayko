# api/database.py
# Цей файл відповідає за роботу з базою даних SQLite

import sqlite3  # Вбудований модуль Python — не потрібно встановлювати
import os
import uuid     # Для генерації унікальних ID
from datetime import datetime

# Шлях до файлу бази даних
# os.path.dirname(__file__) — папка де знаходиться цей файл (api/)
# '..' — на рівень вище (vitayko/)
# 'db/vitayko.db' — файл бази даних
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'vitayko.db')

def get_connection():
    """
    Створює підключення до бази даних.
    check_same_thread=False потрібно для Flask щоб 
    різні запити могли використовувати одне підключення.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Дозволяє звертатись до колонок по імені
    return conn

def init_db():
    """
    Створює таблиці якщо вони ще не існують.
    Викликається один раз при запуску Flask.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблиця замовлень
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS greetings (
            id TEXT PRIMARY KEY,        -- Унікальний ID (наприклад: abc123)
            creator_tg_id INTEGER,      -- Telegram ID замовника
            recipient_name TEXT,        -- Ім'я отримувача (може бути порожнім)
            occasion TEXT NOT NULL,     -- Привід (день народження, річниця...)
            is_paid INTEGER DEFAULT 0,  -- 0 = безкоштовно, 1 = платно
            style TEXT,                 -- Стиль музики (тільки для платних)
            language TEXT DEFAULT 'uk', -- Мова пісні
            details TEXT,               -- Деталі про людину
            status TEXT DEFAULT 'pending', -- pending/generating/done/error
            audio_url TEXT,             -- Посилання на MP3 файл
            created_at TEXT,            -- Дата створення
            stars_paid INTEGER DEFAULT 0 -- Скільки Stars сплачено
        )
    ''')
    
    # Таблиця користувачів (для підрахунку безкоштовних генерацій)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,  -- Telegram ID користувача
            username TEXT,              -- @username
            first_name TEXT,            -- Ім'я
            free_used INTEGER DEFAULT 0, -- Скільки безкоштовних використано
            created_at TEXT             -- Дата першого використання
        )
    ''')
    
    conn.commit()
    conn.close()
    print('✅ База даних ініціалізована')

def create_greeting(creator_tg_id, recipient_name, occasion, is_paid, 
                    style=None, language='uk', details=None):
    """
    Створює новий запис привітання і повертає унікальний ID.
    Цей ID стане частиною посилання: t.me/VitayKoBot?start=abc123
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Генеруємо короткий унікальний ID (8 символів)
    greeting_id = str(uuid.uuid4())[:8]
    
    cursor.execute('''
        INSERT INTO greetings 
        (id, creator_tg_id, recipient_name, occasion, is_paid, 
         style, language, details, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    ''', (greeting_id, creator_tg_id, recipient_name, occasion, 
          is_paid, style, language, details, 
          datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return greeting_id

def get_greeting(greeting_id):
    """
    Повертає дані привітання за ID.
    Використовується коли отримувач відкриває посилання.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM greetings WHERE id = ?', (greeting_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)  # Перетворюємо в словник
    return None

def update_greeting_status(greeting_id, status, audio_url=None):
    """
    Оновлює статус привітання після генерації.
    status: 'generating' → 'done' або 'error'
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if audio_url:
        cursor.execute(
            'UPDATE greetings SET status=?, audio_url=? WHERE id=?',
            (status, audio_url, greeting_id)
        )
    else:
        cursor.execute(
            'UPDATE greetings SET status=? WHERE id=?',
            (status, greeting_id)
        )
    
    conn.commit()
    conn.close()

def save_user(tg_id, username, first_name):
    """
    Зберігає або оновлює дані користувача.
    INSERT OR IGNORE — якщо користувач вже є, нічого не робимо.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (tg_id, username, first_name, created_at)
        VALUES (?, ?, ?, ?)
    ''', (tg_id, username, first_name, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()