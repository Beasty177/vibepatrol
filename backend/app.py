from flask import Flask, request, jsonify, render_template, redirect, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import hashlib
import hmac
import datetime

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-key-2025')

# HTTPS уже стоит — безопасные куки
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # с большой N!
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_DOMAIN'] = None  # работает на текущем домене

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    vibe_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

def check_telegram_auth(data):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return True  # тестовый режим
    data = data.copy()
    try:
        received_hash = data.pop('hash')
        auth_date = int(data['auth_date'])
        if abs(datetime.datetime.now().timestamp() - auth_date) > 86400:
            print("Auth failed: old auth_date")
            return False
        # Убираем пустые поля — иначе хеш не совпадёт
        clean_data = {k: v for k, v in data.items() if v}
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(clean_data.items()))
        secret_key = hashlib.sha256(token.encode()).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash != received_hash:
            print(f"Hash mismatch: calculated {calculated_hash}, received {received_hash}")
            return False
        return True
    except Exception as e:
        print("Telegram auth error:", e)
        return False

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

# КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: редирект сразу на главную, а не на /me
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
        resp = make_response(redirect('/'))  # Явно для куков
        return resp
    else:
        return "Ошибка авторизации — данные неверны или устарели", 401

@app.route('/me')
def profile():
    if 'user_id' not in session:
        return redirect('/')
    user = User.query.get(session['user_id'])
    try:
        return render_template('profile.html', user=user)
    except:
        return f"<h1>Привет, {user.first_name or 'братан'}!</h1><p>Анкета по вайбу в разработке... 🔥</p><a href='/'>На главную</a> | <a href='/full-logout'>Выйти</a>"

@app.route('/login')
def login_page():
    return redirect('/')

@app.route('/save-vibe', methods=['POST'])
def save_vibe():
    if 'user_id' not in session:
        return "unauthorized", 401
    user = User.query.get(session['user_id'])
    user.vibe_data = request.get_json() or {}
    db.session.commit()
    return jsonify({"status": "saved"})

@app.route('/logout')
def logout():
    return redirect('/')

@app.route('/full-logout')
def full_logout():
    session.clear()
    response = make_response(redirect('/'))
    response.set_cookie('session', '', expires=0, path='/', secure=True, httponly=True, samesite='None')
    return response

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


# ------------------ АДМИНКА ------------------
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')  # в .env 

# Простая проверка админа (в будущем → отдельная таблица/роль)
def is_admin():
    return session.get('is_admin', False)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect('/admin')
        else:
            return render_template_string("""
                <h2 style="color:red">Неверный пароль, бро 😈</h2>
                <form method="post">
                    <input type="password" name="password" placeholder="Пароль" required>
                    <button type="submit">Войти</button>
                </form>
            """, password_error=True)

    if not is_admin():
        return render_template_string("""
            <!DOCTYPE html>
            <html lang="ru">
            <head><meta charset="utf-8"><title>Admin Login</title>
            <style>body{background:#1a1a2e;color:#e0e0ff;font-family:sans-serif;text-align:center;padding:100px 20px;}
            input,button{padding:14px;font-size:1.2rem;margin:12px;border-radius:8px;border:1px solid #5a4a8a;background:#2a2a40;color:white;}
            button{background:#7c3aed;cursor:pointer;}
            button:hover{background:#6d28d9;}</style>
            </head>
            <body>
            <h1>VibePatrol Admin</h1>
            <form method="post">
                <input type="password" name="password" placeholder="Пароль..." required autocomplete="off">
                <br><button type="submit">Войти</button>
            </form>
            </body></html>
        """)

    # Если админ → отдаём страницу
    return app.send_static_file('admin.html')  # лежит в /web/admin.html


@app.route('/api/admin/users')
def api_admin_users():
    if not is_admin():
        return jsonify({"error": "access denied"}), 403

    users = User.query.order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "name": u.first_name or "—",
            "username": u.username or "—",
            "tg_id": str(u.id),  # telegram id = наш pk
            "reg_date": u.created_at.strftime("%Y-%m-%d %H:%M"),
            "photo": f"https://t.me/i/userpic/320/{u.username}.jpg" if u.username else None,
            "tags": ", ".join(u.vibe_data.get("tags", [])) if u.vibe_data else "—"
        })
    return jsonify(result)


@app.route('/api/admin/events')
def api_admin_events():
    if not is_admin():
        return jsonify({"error": "access denied"}), 403

    # Пока заглушка — потом сделаем модель Event
    fake_events = [
        {"date": "2026-01-15", "title": "Techno Eclipse", "place": "Pulse Club, Москва", "vibe": "Техно, Коктейли, Лазеры", "participants": 42},
        {"date": "2026-01-22", "title": "Hip-Hop Takeover", "place": "Vibe Bar, СПб", "vibe": "Рэп, Пиво, Баттлы", "participants": 78},
        {"date": "2026-02-01", "title": "Deep House & Wine", "place": "Loft 77, Екат", "vibe": "Хаус, Вино, Чилл", "participants": 31},
    ]
    return jsonify(fake_events)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)