# /home/beasty197/projects/vibepatrol/backend/admin/routes.py

from flask import render_template, request, redirect, url_for, session, flash
from . import admin_bp
from models import Admin
import os
import logging
from logging.handlers import RotatingFileHandler

admin_logger = logging.getLogger('admin')
admin_logger.setLevel(logging.DEBUG)

admin_handler = RotatingFileHandler(
    '/home/beasty197/projects/vibepatrol/logs/admin.log',
    maxBytes=10*1024*1024,
    backupCount=5
)
admin_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
admin_logger.addHandler(admin_handler)

admin_logger.info("=== routes.py успешно загружен ===")

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    admin_logger.info(f"Зашли на /admin/login | IP: {request.remote_addr}")
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_logger.info(f"Попытка входа | Username: {username}")

        # Проверяем обычных админов из БД
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['is_admin'] = True
            session['admin_role'] = admin.role
            session.permanent = True
            admin_logger.info(f"Успешный вход админа | Роль: {admin.role}")
            flash('Успешный вход!', 'success')
            return redirect(url_for('admin.dashboard'))

        # Проверяем супер-админа из .env
        super_username = os.getenv('ADMIN_USERNAME', 'super')
        super_password = os.getenv('ADMIN_PASSWORD')

        if username == super_username and password == super_password:
            session['is_admin'] = True
            session['admin_role'] = 'super'
            session.permanent = True
            admin_logger.info("Успешный вход СУПЕР-админа")
            flash('Успешный вход (супер-админ)!', 'success')
            return redirect(url_for('admin.dashboard'))

        admin_logger.warning(f"Неверный логин/пароль для {username}")
        error = "Неверный логин или пароль"

    admin_logger.debug("Рендерим шаблон 'login.html'")
    return render_template('login.html', error=error)  # ← без 'admin/'

@admin_bp.route('/')
def dashboard():
    admin_logger.info("Зашли на dashboard")
    if not session.get('is_admin'):
        admin_logger.warning("Неавторизованный доступ → редирект на login")
        return redirect(url_for('admin.admin_login'))
    admin_logger.debug("Админ авторизован, рендерим 'dashboard.html'")
    return render_template('dashboard.html', title="Админ-панель VibePatrol")

@admin_bp.route('/questionnaire')
def questionnaire_list():
    admin_logger.info("Зашли на /admin/questionnaire")
    if not session.get('is_admin'):
        admin_logger.warning("Неавторизованный доступ → редирект")
        return redirect(url_for('admin.admin_login'))
    questions = []  # скоро Question.query.all()
    admin_logger.debug(f"Вопросов в списке: {len(questions)}")
    return render_template('questionnaire_list.html', questions=questions)

@admin_bp.route('/logout')
def admin_logout():
    admin_logger.info("Админ вышел из системы")
    session.pop('is_admin', None)
    session.modified = True
    flash('Вы вышли из админки', 'info')
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/debug-test')
def debug_test():
    admin_logger.info("Зашли на /debug-test")
    return "<h1>Тестовый роут /admin/debug-test работает!</h1><p>Blueprint живой 🔥</p>"