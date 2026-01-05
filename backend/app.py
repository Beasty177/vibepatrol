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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)