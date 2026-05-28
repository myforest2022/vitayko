# start_ngrok.py
# Запускає ngrok і автоматично оновлює .env

from pyngrok import conf, ngrok
import re

NGROK_TOKEN = '3EMWevoVLhBALSQHBvywNVqH7s3_3AuVXnSbhLeNvQ6aYGBBM'

conf.get_default().auth_token = NGROK_TOKEN
url = ngrok.connect(5000)
public_url = url.public_url
print(f"🌐 Публічна адреса: {public_url}")

# Автоматично оновлюємо .env
with open('.env', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'WEBHOOK_URL=.*', f'WEBHOOK_URL={public_url}', content)

with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ .env оновлено!")
print("🤖 Тепер запусти бота: python bot/main.py")

# Тримаємо ngrok активним
input("Натисни Enter щоб зупинити ngrok...")