# /home/beasty197/projects/vibepatrol/backend/admin/routes.py

from flask import render_template, request, redirect, url_for, session, flash, g
from . import admin_bp
from models import Admin, db
import os
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

# Правильный импорт — без ".." (чтобы не было ошибки relative import)
from translations import custom_gettext

admin_logger = logging.getLogger('admin')
admin_logger.setLevel(logging.DEBUG)

admin_handler = RotatingFileHandler(
    '/home/beasty197/projects/vibepatrol/logs/admin.log',
    maxBytes=10*1024*1024,
    backupCount=5
)
admin_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
admin_logger.addHandler(admin_handler)

admin_logger.info("=== admin/routes.py успешно загружен ===")

# Декоратор защиты админки
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            admin_logger.warning("Неавторизованный доступ → редирект на login")
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    admin_logger.info(f"Зашли на /admin/login | IP: {request.remote_addr}")
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_logger.info(f"Попытка входа | Username: {username}")

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['is_admin'] = True
            session['admin_role'] = admin.role
            session.permanent = True
            admin_logger.info(f"Успешный вход админа | Роль: {admin.role}")
            flash(custom_gettext('Успешный вход!', 'common'), 'success')
            return redirect(url_for('admin.dashboard'))

        super_username = os.getenv('ADMIN_USERNAME', 'super')
        super_password = os.getenv('ADMIN_PASSWORD')

        if username == super_username and password == super_password:
            session['is_admin'] = True
            session['admin_role'] = 'super'
            session.permanent = True
            admin_logger.info("Успешный вход СУПЕР-админа")
            flash(custom_gettext('Успешный вход (супер-админ)!', 'dashboard'), 'success')
            return redirect(url_for('admin.dashboard'))

        admin_logger.warning(f"Неверный логин/пароль для {username}")
        error = custom_gettext('Неверный логин или пароль', 'common')

    return render_template('login.html', error=error)


@admin_bp.route('/', methods=['GET', 'POST'])
@admin_required
def dashboard():
    admin_logger.info(f"Зашли на dashboard | Метод: {request.method} | Роль: {session.get('admin_role')}")

    if request.method == 'POST':
        action = request.form.get('action')
        admin_logger.info(f"POST действие: {action}")

        if action == 'add_admin':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', 'questionnaire')

            if not username or not password:
                flash(custom_gettext('Логин и пароль обязательны!', 'dashboard'), 'error')
            elif Admin.query.filter_by(username=username).first():
                msg = custom_gettext('Админ с логином "{username}" уже существует', 'dashboard')
                flash(msg.format(username=username), 'error')
            else:
                try:
                    new_admin = Admin(username=username, role=role)
                    new_admin.set_password(password)
                    db.session.add(new_admin)
                    db.session.commit()
                    admin_logger.info(f"УСПЕШНО добавлен админ: {username} ({role})")
                    flash(custom_gettext('Администратор успешно добавлен', 'dashboard'), 'success')
                except Exception as e:
                    db.session.rollback()
                    admin_logger.error(f"Ошибка добавления админа {username}: {e}")
                    flash(custom_gettext('Ошибка при добавлении админа', 'dashboard'), 'error')

        elif action == 'edit_admin':
            admin_id = request.form.get('admin_id')
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', 'questionnaire')

            admin = Admin.query.get(admin_id)
            if not admin:
                flash(custom_gettext('Администратор не найден', 'dashboard'), 'error')
            else:
                try:
                    admin.username = username
                    admin.role = role
                    if password:
                        admin.set_password(password)
                    
                    db.session.commit()
                    admin_logger.info(f"УСПЕШНО обновлён админ ID {admin_id} → {username} ({role})")
                    flash(custom_gettext('Администратор успешно обновлён', 'dashboard'), 'success')
                except Exception as e:
                    db.session.rollback()
                    admin_logger.error(f"Ошибка обновления админа {admin_id}: {e}")
                    flash(custom_gettext('Ошибка при обновлении админа', 'dashboard'), 'error')

        elif action == 'delete_admin':
            admin_id = request.form.get('admin_id')

            if not admin_id:
                admin_logger.warning("Попытка удаления без admin_id")
                flash(custom_gettext('ID администратора не передан', 'dashboard'), 'error')
            else:
                admin = Admin.query.get(admin_id)
                if not admin:
                    admin_logger.warning(f"Админ с ID {admin_id} не найден")
                    flash(custom_gettext('Администратор не найден', 'dashboard'), 'error')
                else:
                    username = admin.username
                    try:
                        db.session.delete(admin)
                        db.session.commit()
                        admin_logger.info(f"Удалён админ ID {admin_id} ({username})")
                        flash(custom_gettext('Администратор успешно удалён', 'dashboard'), 'success')
                    except Exception as e:
                        db.session.rollback()
                        admin_logger.error(f"Ошибка при удалении админа ID {admin_id}: {str(e)}")
                        flash(custom_gettext('Ошибка при удалении администратора', 'dashboard'), 'error')

        return redirect(url_for('admin.dashboard'))

    # GET — показываем страницу
    admins = Admin.query.all()
    admin_logger.info(f"Отображаем {len(admins)} админов в таблице")

    return render_template(
        'dashboard.html',
        title=custom_gettext('Админ-панель VibePatrol', 'dashboard'),
        admins=admins,
        custom_gettext=custom_gettext
    )


@admin_bp.route('/questionnaire')
@admin_required
def questionnaire_list():
    admin_logger.info("Зашли на /admin/questionnaire")
    questions = []  # потом Question.query.all()
    return render_template('questionnaire_list.html', questions=questions)


@admin_bp.route('/logout')
def admin_logout():
    admin_logger.info(f"Админ {session.get('admin_role')} вышел из системы")
    session.pop('is_admin', None)
    session.pop('admin_role', None)
    session.modified = True
    flash(custom_gettext('Вы успешно вышли из админки', 'dashboard'), 'info')
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/debug-test')
def debug_test():
    return "<h1>VibePatrol Admin Blueprint ЖИВОЙ 🔥</h1><p>Всё работает, бро!</p>"