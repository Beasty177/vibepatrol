# /home/beasty197/projects/vibepatrol/backend/admin/routes.py

from flask import render_template, request, redirect, url_for, session, flash, g
from . import admin_bp
from models import Admin, db, Question
import os
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from datetime import datetime

# Импорт функции перевода
from translations import custom_gettext

# Настройка логгера для админки
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

# Декоратор для защиты роутов админки
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            admin_logger.warning("Неавторизованный доступ → редирект на login")
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Декоратор для ролей, которые могут работать с анкетой
def questionnaire_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('admin_role')
        if role not in ['super', 'full', 'questionnaire']:
            admin_logger.warning(f"Доступ к анкете запрещён для роли: {role}")
            flash(custom_gettext('У вас нет прав для управления анкетой', 'dashboard'), 'error')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ──────────────────────────────────────────────────────────────────────────────
# LOGIN ROUTE
# ──────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    lang = request.args.get('lang') or session.get('lang', 'ru')
    g.current_lang = lang

    admin_logger.info(f"Зашли на /admin/login | IP: {request.remote_addr} | Lang: {lang}")
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_logger.info(f"Попытка входа | Username: {username}")

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['is_admin'] = True
            session['admin_role'] = admin.role
            session['admin_username'] = admin.username
            session.permanent = True
            admin_logger.info(f"Успешный вход админа | Роль: {admin.role}")
            flash(custom_gettext('Успешный вход!', 'common'), 'success')
            return redirect(url_for('admin.dashboard'))

        super_username = os.getenv('ADMIN_USERNAME', 'super')
        super_password = os.getenv('ADMIN_PASSWORD')

        if username == super_username and password == super_password:
            session['is_admin'] = True
            session['admin_role'] = 'super'
            session['admin_username'] = super_username
            session.permanent = True
            admin_logger.info("Успешный вход СУПЕР-админа")
            flash(custom_gettext('Успешный вход (супер-админ)!', 'dashboard'), 'success')
            return redirect(url_for('admin.dashboard'))

        admin_logger.warning(f"Неверный логин/пароль для {username}")
        error = custom_gettext('Неверный логин или пароль', 'common')

    return render_template(
        'login.html',
        error=error,
        custom_gettext=custom_gettext
    )


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD (главная админ-панель)
# ──────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/', methods=['GET', 'POST'])
@admin_required
def dashboard():
    admin_logger.info(f"Зашли на dashboard | Метод: {request.method} | Роль: {session.get('admin_role')}")

    if request.method == 'POST':
        action = request.form.get('action')
        admin_logger.info(f"POST действие: {action}")

        # Отладка — ВСЕ данные из формы при любом POST
        form_data = dict(request.form)
        print("[DEBUG] ВСЕ ДАННЫЕ ИЗ ФОРМЫ:", form_data)
        admin_logger.info(f"[DEBUG] ВСЕ ДАННЫЕ ИЗ ФОРМЫ: {form_data}")

        # Добавление нового админа
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

        # Редактирование существующего админа
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

        # Удаление админа
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

        # Смена логина и/или пароля текущего админа (из попапа профиля)
        elif action == 'update_profile':
            current_username = session.get('admin_username')
            admin_logger.info(f"[PROFILE] Попытка обновления профиля текущего юзера: {current_username}")

            admin = None
            if current_username:
                admin = Admin.query.filter_by(username=current_username).first()

            if not admin:
                admin_logger.warning(f"[PROFILE] Админ не найден по сессии: {current_username}")
                flash(custom_gettext('Сессия недействительна, войдите заново', 'dashboard'), 'error')
            else:
                new_username = request.form.get('new_username', '').strip()
                old_password = request.form.get('old_password')
                new_password = request.form.get('new_password')
                new_password_confirm = request.form.get('new_password_confirm')

                # Проверка текущего пароля
                if not admin.check_password(old_password):
                    flash(custom_gettext('Текущий пароль неверный', 'dashboard'), 'error')
                # Проверка совпадения новых паролей
                elif new_password and new_password != new_password_confirm:
                    flash(custom_gettext('Новые пароли не совпадают', 'dashboard'), 'error')
                # Проверка уникальности нового логина
                elif new_username and new_username != admin.username:
                    if Admin.query.filter_by(username=new_username).first():
                        flash(custom_gettext('Этот логин уже занят', 'dashboard'), 'error')
                    else:
                        old_username = admin.username
                        admin.username = new_username
                        session['admin_username'] = new_username
                        admin_logger.info(f"[PROFILE] Логин изменён с {old_username} → {new_username}")
                # Если логин не меняется — всё равно идём дальше

                # Смена пароля, если указан
                if new_password:
                    admin.set_password(new_password)
                    admin_logger.info(f"[PROFILE] Пароль изменён для {admin.username}")

                # Финальный коммит
                try:
                    db.session.commit()
                    admin_logger.info(f"[PROFILE] Профиль успешно обновлён для {admin.username}")
                    flash(custom_gettext('Профиль успешно обновлён', 'dashboard'), 'success')
                except Exception as e:
                    db.session.rollback()
                    admin_logger.error(f"[PROFILE] Ошибка обновления профиля {current_username}: {str(e)}")
                    flash(custom_gettext('Ошибка при обновлении профиля', 'dashboard'), 'error')

        # ────────────────────────────────────────────────
        # Добавление вопроса в анкету
        # ────────────────────────────────────────────────
        elif action == 'add_question':
            text_ru = request.form.get('text_ru', '').strip()
            text_en = request.form.get('text_en', '').strip() or None
            text_he = request.form.get('text_he', '').strip() or None
            qtype = request.form.get('type', 'multiple_choice')
            required = 'required' in request.form
            weight = float(request.form.get('weight', 50))
            order = int(request.form.get('order', 0))

            options_raw = request.form.get('options', '').strip()
            options_list = [line.strip() for line in options_raw.split('\n') if line.strip()]

            # Отладка — всё, что пришло в форму
            print("[DEBUG] ADD_QUESTION — ПОЛНЫЕ ДАННЫЕ ФОРМЫ:", dict(request.form))
            admin_logger.info(f"[DEBUG] ADD_QUESTION — ПОЛНЫЕ ДАННЫЕ ФОРМЫ: {dict(request.form)}")

            print("[DEBUG] ADD_QUESTION — СЫРЫЕ ВАРИАНТЫ:", repr(options_raw))
            admin_logger.info(f"[DEBUG] ADD_QUESTION — СЫРЫЕ ВАРИАНТЫ: {repr(options_raw)}")

            print("[DEBUG] ADD_QUESTION — РАСПАРСЕННЫЕ ВАРИАНТЫ:", options_list)
            admin_logger.info(f"[DEBUG] ADD_QUESTION — РАСПАРСЕННЫЕ ВАРИАНТЫ: {options_list}")

            if not text_ru:
                flash(custom_gettext('Текст вопроса на русском обязателен', 'questionnaire'), 'error')
                return redirect(url_for('admin.dashboard'))

            try:
                max_order = db.session.query(db.func.max(Question.order)).scalar() or 0

                # Если order = 0 — ставим max + 1
                if order == 0:
                    order = max_order + 1

                # Сдвигаем все вопросы с order >= order на +1
                db.session.query(Question).filter(Question.order >= order).update(
                    {Question.order: Question.order + 1},
                    synchronize_session=False
                )

                new_question = Question(
                    text_ru=text_ru,
                    text_en=text_en,
                    text_he=text_he,
                    type=qtype,
                    required=required,
                    weight=weight,
                    order=order,
                    options=options_list,
                    is_active=True,
                    countries=[]
                )
                db.session.add(new_question)
                db.session.commit()

                # Нормализация — пересчитываем все order в 1,2,3...
                questions = Question.query.order_by(Question.order).all()
                for i, q in enumerate(questions, 1):
                    q.order = i
                db.session.commit()

                admin_logger.info(f"[QUESTION] Добавлен вопрос: {text_ru} (ru), order={order}, вариантов: {len(options_list)}")
                flash(custom_gettext('Вопрос успешно добавлен', 'questionnaire'), 'success')
            except Exception as e:
                db.session.rollback()
                admin_logger.error(f"[QUESTION] Ошибка добавления вопроса: {str(e)}")
                flash(custom_gettext('Ошибка при добавлении вопроса', 'questionnaire'), 'error')

        # ────────────────────────────────────────────────
        # Редактирование вопроса в анкете
        # ────────────────────────────────────────────────
        elif action == 'edit_question':
            qid = request.form.get('question_id')
            question = Question.query.get(qid)

            if not question:
                flash(custom_gettext('Вопрос не найден', 'questionnaire'), 'error')
                return redirect(url_for('admin.dashboard'))

            old_order = question.order
            new_order = int(request.form.get('order', old_order))

            options_raw = request.form.get('options', '').strip()
            options_list = [line.strip() for line in options_raw.split('\n') if line.strip()]

            print("[DEBUG] EDIT_QUESTION — ПОЛНЫЕ ДАННЫЕ ФОРМЫ:", dict(request.form))
            admin_logger.info(f"[DEBUG] EDIT_QUESTION — ПОЛНЫЕ ДАННЫЕ ФОРМЫ: {dict(request.form)}")

            print("[DEBUG] EDIT_QUESTION — СЫРЫЕ ВАРИАНТЫ:", repr(options_raw))
            admin_logger.info(f"[DEBUG] EDIT_QUESTION — СЫРЫЕ ВАРИАНТЫ: {repr(options_raw)}")

            print("[DEBUG] EDIT_QUESTION — РАСПАРСЕННЫЕ ВАРИАНТЫ:", options_list)
            admin_logger.info(f"[DEBUG] EDIT_QUESTION — РАСПАРСЕННЫЕ ВАРИАНТЫ: {options_list}")

            try:
                if new_order != old_order:
                    # Сдвигаем вопросы после старого порядка назад
                    db.session.query(Question).filter(Question.order > old_order).update(
                        {Question.order: Question.order - 1},
                        synchronize_session=False
                    )
                    # Сдвигаем вопросы после нового порядка вперёд
                    db.session.query(Question).filter(Question.order >= new_order).update(
                        {Question.order: Question.order + 1},
                        synchronize_session=False
                    )

                question.text_ru = request.form.get('text_ru', question.text_ru)
                question.text_en = request.form.get('text_en', question.text_en)
                question.text_he = request.form.get('text_he', question.text_he)
                question.type = request.form.get('type', question.type)
                question.required = 'required' in request.form
                question.weight = float(request.form.get('weight', question.weight))
                question.order = new_order
                question.options = options_list

                db.session.commit()

                # Финальная нормализация всех номеров в 1,2,3...
                questions = Question.query.order_by(Question.order).all()
                for i, q in enumerate(questions, 1):
                    q.order = i
                db.session.commit()

                admin_logger.info(f"[QUESTION] Обновлён вопрос ID {qid}: {question.text_ru} (ru), order={new_order}, вариантов: {len(options_list)}")
                flash(custom_gettext('Вопрос успешно обновлён', 'questionnaire'), 'success')
            except Exception as e:
                db.session.rollback()
                admin_logger.error(f"[QUESTION] Ошибка обновления вопроса ID {qid}: {str(e)}")
                flash(custom_gettext('Ошибка при обновлении вопроса', 'questionnaire'), 'error')

        # После любого POST — редирект
        return redirect(url_for('admin.dashboard'))

    # GET — отображаем главную страницу
    admins = Admin.query.all()
    questions = Question.query.order_by(Question.order).all()

    # Вычисляем максимальный order и следующий для нового вопроса
    max_order = db.session.query(db.func.max(Question.order)).scalar() or 0
    max_order_for_new = max_order + 1

    # Отладка в терминал — чтобы видеть, что реально считается
    print("[DEBUG] === GET DASHBOARD ===")
    print("[DEBUG] Количество вопросов в базе:", len(questions))
    print("[DEBUG] Максимальный order в базе:", max_order)
    print("[DEBUG] Следующий номер для нового вопроса:", max_order_for_new)

    admin_logger.info(f"Отображаем {len(admins)} админов и {len(questions)} вопросов в таблице")

    return render_template(
        'dashboard.html',
        title=custom_gettext('Админ-панель VibePatrol', 'dashboard'),
        admins=admins,
        questions=questions,
        custom_gettext=custom_gettext,
        max_order=max_order_for_new  # ← передаём в шаблон
    )


# ──────────────────────────────────────────────────────────────────────────────
# ДРУГИЕ РОУТЫ
# ──────────────────────────────────────────────────────────────────────────────

@admin_bp.route('/questionnaire')
@admin_required
@questionnaire_required
def questionnaire_list():
    admin_logger.info("Зашли на /admin/questionnaire")
    questions = Question.query.order_by(Question.order).all()
    return render_template('questionnaire_list.html', questions=questions)


@admin_bp.route('/logout')
def admin_logout():
    admin_logger.info(f"Админ {session.get('admin_role')} вышел из системы")
    session.pop('is_admin', None)
    session.pop('admin_role', None)
    session.pop('admin_username', None)
    session.modified = True
    flash(custom_gettext('Вы успешно вышли из админки', 'dashboard'), 'info')
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/debug-test')
def debug_test():
    return "<h1>VibePatrol Admin Blueprint ЖИВОЙ 🔥</h1><p>Всё работает, бро!</p>"