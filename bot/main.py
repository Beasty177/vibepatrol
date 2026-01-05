from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import hashlib
import hmac
import urllib.parse
import time
from dotenv import load_dotenv

# Читаем .env из корня проекта
load_dotenv(dotenv_path="/home/beasty197/projects/vibepatrol/.env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Берём из .env, по умолчанию https (у тебя уже Certbot стоит)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://vibepatrol.me/login/telegram")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден в .env!")

def make_auth_url(user):
    data = {
        "id": str(user.id),
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "auth_date": str(int(time.time())),
    }
    # Убираем пустые поля — иначе хеш не совпадёт с backend
    data = {k: v for k, v in data.items() if v}
    
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    data["hash"] = hash_value

    query = urllib.parse.urlencode(data)
    return f"{WEBHOOK_URL}?{query}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    auth_url = make_auth_url(user)

    keyboard = [[InlineKeyboardButton("🔥 Войти на vibepatrol.me", url=auth_url)]]

    await update.message.reply_html(
        f"<b>Привет, {user.first_name or 'бро'}! 👋</b>\n\n"
        "Нажми кнопку ниже — и сразу окажешься на сайте:\n"
        "• Твои ближайшие вечеринки по вайбу\n"
        "• Анкета (музыка • танцы • напитки)\n"
        "• Матчи с людьми на тех же тусовках 🔥",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

if __name__ == "__main__":
    print("Бот VibePatrol запускается...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Бот VibePatrol запущен! Готов ловить вайб на вечеринках 🚀")
    app.run_polling(drop_pending_updates=True)