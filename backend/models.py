# /home/beasty197/projects/vibepatrol/backend/models.py

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()  # ← db создаётся здесь

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    vibe_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    main_place = db.Column(db.String(200), nullable=False)
    zones = db.Column(db.JSON, default=list)
    vibe = db.Column(db.String(300))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50))  # text, select, radio, checkbox
    options = db.Column(db.JSON)  # список вариантов
    required = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Float, default=1.0)
    order = db.Column(db.Integer, default=0)

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='questionnaire')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)