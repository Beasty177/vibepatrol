# /home/beasty197/projects/vibepatrol/backend/models.py

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ────────────────────────────────────────────────
# ПОЛЬЗОВАТЕЛИ (из Telegram-бота)
# ────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)             # telegram_id
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    vibe_data = db.Column(db.JSON, default=dict)                # любые данные вайба
    country = db.Column(db.String(100))                         # страна юзера → для выбора языка анкеты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ────────────────────────────────────────────────
# СОБЫТИЯ / ВЕЧЕРИНКИ
# ────────────────────────────────────────────────
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    main_place = db.Column(db.String(200), nullable=False)
    zones = db.Column(db.JSON, default=list)
    vibe = db.Column(db.String(300))
    description = db.Column(db.Text)
    country = db.Column(db.String(100))                         # страна проведения → влияет на язык анкеты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ────────────────────────────────────────────────
# ЛОКАЦИИ / ПЛОЩАДКИ
# ────────────────────────────────────────────────
class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ────────────────────────────────────────────────
# ВОПРОСЫ АНКЕТЫ (с поддержкой переводов)
# ────────────────────────────────────────────────
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    
    # Текст вопроса на разных языках (ru — основной, остальные optional)
    text_ru = db.Column(db.String(500), nullable=False)
    text_en = db.Column(db.String(500))
    text_he = db.Column(db.String(500))
    
    type = db.Column(db.String(50), nullable=False)             # 'multiple_choice' / 'free_text'
    required = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Float, default=50.0)                  # вес в процентах (0–100)
    order = db.Column(db.Integer, default=0)    
    is_active = db.Column(db.Boolean, default=True)
    
    # Варианты ответа — список строк (для multiple_choice)
    options = db.Column(db.JSON, default=list)                  # ← это поле обязательно для вариантов
    
    # Если нужно фильтровать вопросы по стране/региону
    countries = db.Column(db.JSON, default=list)                # список кодов стран, напр. ['ru', 'il']


# ────────────────────────────────────────────────
# ВАРИАНТЫ ОТВЕТОВ (отдельная таблица — если захочешь переводить каждый вариант отдельно)
# Пока можно не использовать, если варианты хранятся в Question.options
# ────────────────────────────────────────────────
class AnswerOption(db.Model):
    __tablename__ = 'answer_options'                            # поменял имя таблицы, чтобы не путать с ответами пользователей
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    # Текст варианта на разных языках
    text_ru = db.Column(db.String(128), nullable=False)
    text_en = db.Column(db.String(128))
    text_he = db.Column(db.String(128))
    
    # Ключ для матчинга (чтобы сравнивать независимо от языка)
    match_key = db.Column(db.String(50), nullable=False)        # напр. 'beer', 'techno'


# ────────────────────────────────────────────────
# ОТВЕТЫ ПОЛЬЗОВАТЕЛЕЙ НА ВОПРОСЫ
# ────────────────────────────────────────────────
class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    # Ответ: для free_text — текст, для multiple_choice — match_key выбранного варианта
    answer_value = db.Column(db.String(256), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ────────────────────────────────────────────────
# АДМИНЫ 
# ────────────────────────────────────────────────
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='questionnaire')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)