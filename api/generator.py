# api/generator.py
# Цей файл генерує текст пісні через Claude
# і музику через ElevenLabs

import anthropic
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# API ключі з .env
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Папка для збереження MP3 файлів
AUDIO_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)  # Створює папку якщо не існує

# ===================================================
# КРОК 1: Генерація тексту пісні через Claude
# ===================================================
def generate_lyrics(recipient_name, occasion, style, language, details):
    """
    Генерує текст пісні через Claude API.
    Повертає текст пісні як рядок.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Формуємо звертання залежно від наявності імені
    if recipient_name:
        address = f"людину на ім'я {recipient_name}"
    else:
        address = "людину (без конкретного імені, текст має бути універсальним)"

    # Деталі про людину
    details_text = f"\nДодаткові деталі: {details}" if details else ""

    # Мова пісні
    lang_text = "українською мовою" if language == 'uk' else "англійською мовою"

    # Промпт для Claude
    prompt = f"""Напиши текст пісні-привітання для {address}.
Привід: {occasion}
Стиль музики: {style}
Мова: {lang_text}{details_text}

Вимоги до тексту:
- 2 куплети і приспів
- Загальна довжина: 100-150 слів
- Теплий, щирий тон
- Без кліше типу "бажаю щастя і здоров'я"
- Тільки текст пісні, без заголовків та пояснень
- Якщо є ім'я — використай його в тексті 1-2 рази"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Найшвидша і найдешевша модель
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    lyrics = message.content[0].text.strip()
    print(f"✅ Текст пісні згенеровано ({len(lyrics)} символів)")
    return lyrics

# ===================================================
# КРОК 2: Генерація музики через ElevenLabs
# ===================================================
def generate_music(lyrics, style, language):
    """
    ЗАГЛУШКА — повертає тестовий MP3.
    Замінимо на реальний ElevenLabs після підключення Starter плану.
    """
    print("🎵 [ЗАГЛУШКА] Музика не генерується — використовуємо тестовий файл")
    
    # Повертаємо шлях до шаблонного MP3
    # Поклади будь-який MP3 файл у папку static/ з назвою demo.mp3
    return "/static/demo.mp3"

# ===================================================
# ГОЛОВНА ФУНКЦІЯ: Генерує і текст і музику
# ===================================================
def generate_greeting(greeting_id, recipient_name, occasion,
                      style, language, details):
    """
    Повний цикл генерації:
    1. Claude генерує текст
    2. ElevenLabs генерує музику
    3. Повертає URL аудіо файлу
    """
    print(f"🚀 Починаємо генерацію для привітання {greeting_id}")

    # Крок 1: Текст
    lyrics = generate_lyrics(
        recipient_name=recipient_name,
        occasion=occasion,
        style=style,
        language=language,
        details=details
    )

    # Крок 2: Музика
    audio_url = generate_music(
        lyrics=lyrics,
        style=style,
        language=language
    )

    print(f"🎉 Генерація завершена! Аудіо: {audio_url}")
    return audio_url, lyrics