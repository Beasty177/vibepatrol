from flask import Flask, request, jsonify, redirect, session, make_response, url_for, render_template, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import hashlib
import hmac
import datetime
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

# Импортируем модели, чтобы Pylance не ругался и всё работало
from models import db, User, Admin

load_dotenv()

app = Flask(__name__)

# ── Логи — сразу после создания app ────────────────────────────────────────────────
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'vibepatrol.log')

logging.basicConfig(level=logging.DEBUG)
handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,
    backupCount=5
)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

app.logger.info("=== ЛОГГЕР УСПЕШНО ЗАПУЩЕН ===")
app.logger.debug("Тест debug-сообщения сразу после инициализации")

# Конфиг
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-key-2025-vibe')

# Сессии
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.permanent_session_lifetime = timedelta(hours=12)

# ── Подключение переводов из отдельного файла ────────────────────────────────────────
from translations import custom_gettext

# Делаем функцию доступной во всех шаблонах
app.jinja_env.globals['custom_gettext'] = custom_gettext

# Сохраняем текущий язык в g (для custom_gettext)
@app.before_request
def set_current_lang():
    g.current_lang = session.get('lang', 'ru')

# db и migrate — инициализация после создания app
db.init_app(app)
migrate = Migrate(app, db)

# Специальный логгер для языка
language_logger = logging.getLogger('vibepatrol.language')
language_logger.setLevel(logging.DEBUG)

if not language_logger.handlers:
    lang_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5
    )
    lang_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    lang_handler.setFormatter(lang_formatter)
    language_logger.addHandler(lang_handler)

# ── Декоратор админки ────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

# ── Blueprint админки ────────────────────────────────────────────
from admin import admin_bp
app.register_blueprint(admin_bp, url_prefix='/admin')

# ── Telegram Auth Check ──────────────────────────────────────────
def check_telegram_auth(data):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return True  # dev mode

    data = data.copy()
    try:
        received_hash = data.pop('hash')
        auth_date = int(data['auth_date'])
        if abs(datetime.datetime.now().timestamp() - auth_date) > 86400:
            app.logger.warning("Auth failed: old auth_date")
            return False

        clean_data = {k: v for k, v in data.items() if v}
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(clean_data.items()))
        secret_key = hashlib.sha256(token.encode()).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != received_hash:
            app.logger.warning(f"Hash mismatch: calc {calculated_hash}, recv {received_hash}")
            return False
        return True
    except Exception as e:
        app.logger.error(f"Telegram auth error: {e}")
        return False

# ── Роуты ────────────────────────────────────────────────────────
@app.route('/')
def hello():
    return "VibePatrol backend живой, бро! 🔥"

@app.route('/api/user/<int:telegram_id>', methods=['GET', 'POST'])
def user_api(telegram_id):
    user = User.query.get(telegram_id)
    if request.method == 'GET':
        if not user:
            return jsonify({"error": "not found"}), 404
        return jsonify({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "vibe_data": user.vibe_data
        })

    data = request.get_json() or {}
    if not user:
        user = User(id=telegram_id)
        db.session.add(user)

    user.username = data.get('username', user.username)
    user.first_name = data.get('first_name', user.first_name)
    user.vibe_data = data.get('vibe_data', user.vibe_data)
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route('/api/user/current')
def current_user():
    if 'user_id' not in session:
        return jsonify({}), 200

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({}), 200

    return jsonify({
        "id": user.id,
        "first_name": user.first_name or "бро",
        "username": user.username or "безымянный",
        "profile_picture_url": f"https://t.me/i/userpic/320/{user.username}.jpg" if user.username else "https://via.placeholder.com/100"
    }), 200

@app.route('/save-vibe', methods=['POST'])
def save_vibe():
    if 'user_id' not in session:
        return jsonify({"error": "unauthorized"}), 401

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"error": "user not found"}), 404

    data = request.get_json() or {}
    user.vibe_data = data
    db.session.commit()
    app.logger.info(f"Vibe saved for user {user.id}: {data}")
    return jsonify({"status": "saved", "vibe_data": user.vibe_data})

@app.route('/me')
def profile():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    user = User.query.filter_by(id=user_id).first()

    if not user:
        session.clear()
        return redirect('/')

    app.logger.info(f"Debug /me: User ID {user_id}, Fresh Vibe Data: {user.vibe_data}")

    try:
        return render_template('profile.html', user=user)
    except Exception as e:
        app.logger.error(f"Render error in /me: {str(e)}")
        return f"Ошибка рендеринга шаблона: {str(e)}", 500

@app.route('/logout')
def logout():
    return redirect('/')

@app.route('/full-logout')
def full_logout():
    session.clear()
    resp = make_response(redirect('/'))
    resp.set_cookie('session', '', expires=0, path='/', secure=True, httponly=True, samesite='None')
    return resp

# ── Переключение языка ───────────────────────────────────────────
@app.route('/set_language/<lang>')
def set_language(lang):
    next_param = request.args.get('next')
    referrer = request.referrer or 'нет'
    current_lang = session.get('lang', 'не установлен')

    language_logger.info(
        f"ЗАШЛИ В set_language | lang={lang} | next={next_param} | "
        f"referrer={referrer} | текущий_язык_в_сессии={current_lang}"
    )

    if lang in ['ru', 'en', 'he']:
        session['lang'] = lang
        session.modified = True
        language_logger.info(f"Язык изменён → session['lang'] = {lang}")
    else:
        language_logger.warning(f"Недопустимый язык: {lang}")

    new_lang = session.get('lang', 'не установлен')
    language_logger.debug(f"После обработки: session['lang'] = {new_lang}")

    if next_param and next_param.startswith('/'):
        language_logger.info(f"РЕДИРЕКТ по next → {next_param}")
        return redirect(next_param)
    
    fallback = url_for('admin.admin_login')
    language_logger.info(f"next отсутствует/некорректный → редирект на {fallback}")
    return redirect(fallback)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)


# Инфа для запуска виртуального окружения, что бы незабыть
# source /home/beasty197/projects/vibepatrol/.venv/bin/activate