from flask import Flask, request, jsonify, redirect, session, make_response, send_from_directory, render_template
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

load_dotenv()

app = Flask(__name__)

# Конфиг
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-key-2025-vibe')

# Сессии: HTTPS-only, SameSite=None для Telegram Mini Apps и админки
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.permanent_session_lifetime = timedelta(hours=12)  # админ сессия живёт 12 часов

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Настройка логирования в отдельный файл
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'vibepatrol.log')

logging.basicConfig(level=logging.DEBUG)
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)  # 10MB + 5 бэкапов
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# ── Модели ───────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    vibe_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


# ── Telegram Auth Check ─────────────────────────────────────────────────
def check_telegram_auth(data):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return True  # dev mode без проверки

    data = data.copy()
    try:
        received_hash = data.pop('hash')
        auth_date = int(data['auth_date'])
        if abs(datetime.datetime.now().timestamp() - auth_date) > 86400:
            print("Auth failed: old auth_date")
            return False

        clean_data = {k: v for k, v in data.items() if v}
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(clean_data.items()))
        secret_key = hashlib.sha256(token.encode()).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if calculated_hash != received_hash:
            print(f"Hash mismatch: calc {calculated_hash}, recv {received_hash}")
            return False
        return True
    except Exception as e:
        print("Telegram auth error:", e)
        return False


# ── Роуты ────────────────────────────────────────────────────────────────
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


@app.route('/login/telegram', methods=['GET', 'POST'])
def telegram_login():
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args.to_dict()

    if not data or 'id' not in data:
        return "Bad request", 400

    if check_telegram_auth(data):
        user_id = int(data['id'])
        user = User.query.get(user_id)
        if not user:
            user = User(
                id=user_id,
                username=data.get('username'),
                first_name=data.get('first_name')
            )
            db.session.add(user)
            db.session.commit()

        session['user_id'] = user_id
        session.permanent = True
        return make_response(redirect('/'))
    else:
        return "Ошибка авторизации — данные неверны или устарели", 401


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
        "first_name": user.first_name or "братан",
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

    # Debug лог в файл logs/vibepatrol.log
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


# ── АДМИНКА ──────────────────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')  # меняй в .env!

def is_admin():
    return session.get('is_admin', False)


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            session.permanent = True
            session.modified = True
            return redirect('/admin', code=302)
        else:
            return redirect('/admin')

    return send_from_directory(
        '/home/beasty197/projects/vibepatrol/web',
        'admin.html'
    )


@app.route('/admin-logout')
def admin_logout():
    session.pop('is_admin', None)
    session.modified = True
    return redirect('/admin')


@app.route('/api/admin/users')
def api_admin_users():
    if not is_admin():
        return jsonify({"error": "access denied"}), 403

    users = User.query.order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        vibe = u.vibe_data or {}
        result.append({
            "name": u.first_name or "—",
            "username": u.username or "—",
            "tg_id": str(u.id),
            "reg_date": u.created_at.strftime("%Y-%m-%d %H:%M"),
            "photo": f"https://t.me/i/userpic/320/{u.username}.jpg" if u.username else None,
            "tags": ", ".join(vibe.get("tags", [])) if isinstance(vibe, dict) else "—",
            "vibe_data": vibe
        })
    return jsonify(result)


@app.route('/api/admin/events')
def api_admin_events():
    if not is_admin():
        return jsonify({"error": "access denied"}), 403

    # Пока заглушка
    fake_events = [
        {"date": "2026-01-15", "title": "Techno Eclipse", "place": "Pulse Club, Москва", "vibe": "Техно, Коктейли, Лазеры", "participants": 42},
        {"date": "2026-01-22", "title": "Hip-Hop Takeover", "place": "Vibe Bar, СПб", "vibe": "Рэп, Пиво, Баттлы", "participants": 78},
        {"date": "2026-02-01", "title": "Deep House & Wine", "place": "Loft 77, Екат", "vibe": "Хаус, Вино, Чилл", "participants": 31},
    ]
    return jsonify(fake_events)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)