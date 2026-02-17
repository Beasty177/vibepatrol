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
    vibe_data = db.Column(db.JSON, default=dict)                # любые данные вайба (ответы на вопросы)
    country = db.Column(db.String(100))                         # страна юзера → для выбора языка анкеты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ────────────────────────────────────────────────
# СОБЫТИЯ / ВЕЧЕРИНКИ (будущие планы, пока заготовка)
# ────────────────────────────────────────────────
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    main_place = db.Column(db.String(200), nullable=False)
    zones = db.Column(db.JSON, default=list)                    # пока JSON, потом перейдём на связь
    vibe = db.Column(db.String(300))
    description = db.Column(db.Text)
    country = db.Column(db.String(100))                         # страна проведения → влияет на язык
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ────────────────────────────────────────────────
# ЛОКАЦИИ / ПЛОЩАДКИ (клубы, бары, фестивали и т.д.)
# ────────────────────────────────────────────────
class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    coordinates = db.Column(db.String(255))                     # ссылка: https://maps.google.com/?q=lat,long
    country = db.Column(db.String(100))
    type = db.Column(db.String(50), default='club')             # club, bar, cafe, festival
    contact_info = db.Column(db.Text)                           # телефон, инста, сайт...
    additional_info = db.Column(db.Text)                        # дресс-код, особенности входа и т.д.
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Связь с зонами (одна локация → много зон)
    zones = db.relationship('Zone', back_populates='location', cascade="all, delete-orphan", lazy=True)


# ────────────────────────────────────────────────
# ЗОНЫ ВНУТРИ ЛОКАЦИИ (основной зал, чилаут, сцена, VIP и т.п.)
# ────────────────────────────────────────────────
class Zone(db.Model):
    __tablename__ = 'zones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)            # напр. "Основной зал", "Чилаут зона"
    description = db.Column(db.Text)                            # описание зоны
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Обратная связь с локацией
    location = db.relationship('Location', back_populates='zones')

    # Связь с местами встречи внутри зоны (одна зона → много спотов)
    spots = db.relationship('MeetingSpot', back_populates='zone', cascade="all, delete-orphan", lazy=True)


# ────────────────────────────────────────────────
# МЕСТА ВСТРЕЧИ ВНУТРИ ЗОНЫ (красный диван, стол у окна, беседка и т.п.)
# ────────────────────────────────────────────────
class MeetingSpot(db.Model):
    __tablename__ = 'meeting_spots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)            # напр. "Красный диван у бара"
    description = db.Column(db.Text)                            # детали: "возле окна, 2 места"
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Обратная связь с зоной
    zone = db.relationship('Zone', back_populates='spots')


# ────────────────────────────────────────────────
# ВОПРОСЫ АНКЕТЫ (с поддержкой переводов)
# ────────────────────────────────────────────────
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    
    # Текст вопроса на разных языках (ru — основной)
    text_ru = db.Column(db.String(500), nullable=False)
    text_en = db.Column(db.String(500))
    text_he = db.Column(db.String(500))
    
    type = db.Column(db.String(50), nullable=False)             # 'multiple_choice' / 'free_text'
    required = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Float, default=50.0)                  # вес в процентах (0–100)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Варианты ответа — список строк (для multiple_choice)
    options = db.Column(db.JSON, default=list)
    
    # Фильтр по странам (если вопрос актуален только для определённых регионов)
    countries = db.Column(db.JSON, default=list)                # ['ru', 'il', 'ua'] и т.д.


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
# АДМИНЫ (управление панелью)
# ────────────────────────────────────────────────
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='questionnaire')    # super, full, questionnaire, location...
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))  # кто создал этого админа

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)