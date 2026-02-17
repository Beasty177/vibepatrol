# /home/beasty197/projects/vibepatrol/backend/admin/routes.py

from flask import render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.utils import secure_filename
from . import admin_bp
from models import Admin, db, Question, Location, Zone, MeetingSpot
import os
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import json  # для парсинга zones_json

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

# Папка для загрузки изображений локаций
UPLOAD_FOLDER = '/home/beasty197/projects/vibepatrol/web/static/images/locations'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    admin = Admin.query.get(session.get('admin_id'))  # точнее проверяем роль

    if request.method == 'POST':
        # Для AJAX (локации, вопросы и т.д.) action может приходить в JSON
        if request.is_json:
            action = request.json.get('action')
            data = request.json
        else:
            action = request.form.get('action')
            data = request.form.to_dict()

        admin_logger.info(f"POST действие: {action}")

        # Отладка — ВСЕ данные из формы при любом POST
        print("[DEBUG] ВСЕ ДАННЫЕ ИЗ ФОРМЫ:", data)
        admin_logger.info(f"[DEBUG] ВСЕ ДАННЫЕ ИЗ ФОРМЫ: {data}")

        # Добавление нового админа
        if action == 'add_admin':
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            role = data.get('role', 'questionnaire')

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
            admin_id = data.get('admin_id')
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            role = data.get('role', 'questionnaire')

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
            admin_id = data.get('admin_id')

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
                new_username = data.get('new_username', '').strip()
                old_password = data.get('old_password')
                new_password = data.get('new_password')
                new_password_confirm = data.get('new_password_confirm')

                if not admin.check_password(old_password):
                    flash(custom_gettext('Текущий пароль неверный', 'dashboard'), 'error')
                elif new_password and new_password != new_password_confirm:
                    flash(custom_gettext('Новые пароли не совпадают', 'dashboard'), 'error')
                elif new_username and new_username != admin.username:
                    if Admin.query.filter_by(username=new_username).first():
                        flash(custom_gettext('Этот логин уже занят', 'dashboard'), 'error')
                    else:
                        old_username = admin.username
                        admin.username = new_username
                        session['admin_username'] = new_username
                        admin_logger.info(f"[PROFILE] Логин изменён с {old_username} → {new_username}")

                if new_password:
                    admin.set_password(new_password)
                    admin_logger.info(f"[PROFILE] Пароль изменён для {admin.username}")

                try:
                    db.session.commit()
                    admin_logger.info(f"[PROFILE] Профиль успешно обновлён для {admin.username}")
                    flash(custom_gettext('Профиль успешно обновлён', 'dashboard'), 'success')
                except Exception as e:
                    db.session.rollback()
                    admin_logger.error(f"[PROFILE] Ошибка обновления профиля {current_username}: {str(e)}")
                    flash(custom_gettext('Ошибка при обновлении профиля', 'dashboard'), 'error')

        # Добавление вопроса в анкету
        elif action == 'add_question':
            text_ru = data.get('text_ru', '').strip()
            text_en = data.get('text_en', '').strip() or None
            text_he = data.get('text_he', '').strip() or None
            qtype = data.get('type', 'multiple_choice')
            required = 'required' in data
            weight = float(data.get('weight', 50))
            order = int(data.get('order', 0))

            options_raw = data.get('options', '').strip()
            options_list = [line.strip() for line in options_raw.split('\n') if line.strip()]

            print("[DEBUG] ADD_QUESTION — ПОЛНЫЕ ДАННЫЕ ФОРМЫ:", data)
            admin_logger.info(f"[DEBUG] ADD_QUESTION — ПОЛНЫЕ ДАННЫЕ ФОРМЫ: {data}")

            if not text_ru:
                flash(custom_gettext('Текст вопроса на русском обязателен', 'questionnaire'), 'error')
                return redirect(url_for('admin.dashboard'))

            try:
                max_order = db.session.query(db.func.max(Question.order)).scalar() or 0
                if order == 0:
                    order = max_order + 1

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

        # Редактирование вопроса
        elif action == 'edit_question':
            qid = data.get('question_id')
            question = Question.query.get(qid)

            if not question:
                flash(custom_gettext('Вопрос не найден', 'questionnaire'), 'error')
                return redirect(url_for('admin.dashboard'))

            old_order = question.order
            new_order = int(data.get('order', old_order))

            options_raw = data.get('options', '').strip()
            options_list = [line.strip() for line in options_raw.split('\n') if line.strip()]

            try:
                if new_order != old_order:
                    db.session.query(Question).filter(Question.order > old_order).update(
                        {Question.order: Question.order - 1},
                        synchronize_session=False
                    )
                    db.session.query(Question).filter(Question.order >= new_order).update(
                        {Question.order: Question.order + 1},
                        synchronize_session=False
                    )

                question.text_ru = data.get('text_ru', question.text_ru)
                question.text_en = data.get('text_en', question.text_en)
                question.text_he = data.get('text_he', question.text_he)
                question.type = data.get('type', question.type)
                question.required = 'required' in data
                question.weight = float(data.get('weight', question.weight))
                question.order = new_order
                question.options = options_list

                db.session.commit()

                questions = Question.query.order_by(Question.order).all()
                for i, q in enumerate(questions, 1):
                    q.order = i
                db.session.commit()

                admin_logger.info(f"[QUESTION] Обновлён вопрос ID {qid}: {question.text_ru} (ru), order={new_order}")
                flash(custom_gettext('Вопрос успешно обновлён', 'questionnaire'), 'success')
            except Exception as e:
                db.session.rollback()
                admin_logger.error(f"[QUESTION] Ошибка обновления вопроса ID {qid}: {str(e)}")
                flash(custom_gettext('Ошибка при обновлении вопроса', 'questionnaire'), 'error')

        # Удаление вопроса
        elif action == 'delete_question':
            qid = data.get('question_id')

            if not qid:
                flash(custom_gettext('ID вопроса не передан', 'questionnaire'), 'error')
            else:
                question = Question.query.get(qid)
                if not question:
                    flash(custom_gettext('Вопрос не найден', 'questionnaire'), 'error')
                else:
                    try:
                        db.session.delete(question)
                        db.session.commit()

                        questions = Question.query.order_by(Question.order).all()
                        for i, q in enumerate(questions, 1):
                            q.order = i
                        db.session.commit()

                        admin_logger.info(f"[QUESTION] Удалён вопрос ID {qid}: {question.text_ru}")
                        flash(custom_gettext('Вопрос успешно удалён', 'questionnaire'), 'success')
                    except Exception as e:
                        db.session.rollback()
                        admin_logger.error(f"[QUESTION] Ошибка удаления вопроса ID {qid}: {str(e)}")
                        flash(custom_gettext('Ошибка при удалении вопроса', 'questionnaire'), 'error')

        # ────────────────────────────────────────────────
        # ДОБАВЛЕНИЕ ЛОКАЦИИ (AJAX + multipart для фото)
        # ────────────────────────────────────────────────
        elif action == 'add_location':
            if session.get('admin_role') != 'super':
                return jsonify({'success': False, 'error': 'Доступ только для super'}), 403

            try:
                new_loc = Location(
                    name=request.form.get('name', '').strip(),
                    city=request.form.get('city') or None,
                    country=request.form.get('country') or None,
                    type=request.form.get('type', 'club'),
                    address=request.form.get('address') or None,
                    coordinates=request.form.get('coordinates') or None,
                    contact_info=request.form.get('contact_info') or None,
                    additional_info=request.form.get('additional_info') or None,
                    description=request.form.get('description') or None
                )
                db.session.add(new_loc)
                db.session.flush()

                # Обработка фото
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(file_path)
                        new_loc.image_url = f'/static/images/locations/{filename}'

                # Зоны и споты — теперь берём из zones_json
                zones_json = request.form.get('zones_json', '[]')
                admin_logger.info(f"[ZONES] Получено zones_json при add: {zones_json}")
                print(f"[DEBUG] zones_json при add: {zones_json}")
                try:
                    zones_data = json.loads(zones_json)
                except Exception as e:
                    admin_logger.error(f"[ZONES] Ошибка парсинга zones_json при add: {str(e)}")
                    print(f"[ERROR] zones_json парсинг при add: {str(e)}")
                    zones_data = []

                for z_data in zones_data:
                    zone = Zone(
                        name=z_data.get('name', '').strip(),
                        description=z_data.get('description') or None,
                        location_id=new_loc.id
                    )
                    db.session.add(zone)
                    db.session.flush()

                    spots_data = z_data.get('spots', [])
                    for s_data in spots_data:
                        spot = MeetingSpot(
                            name=s_data.get('name', '').strip(),
                            description=s_data.get('description') or None,
                            zone_id=zone.id
                        )
                        db.session.add(spot)

                db.session.commit()
                admin_logger.info(f"Добавлена локация '{new_loc.name}' (ID {new_loc.id}), зон: {len(zones_data)}")
                return jsonify({'success': True, 'location_id': new_loc.id})

            except Exception as e:
                db.session.rollback()
                admin_logger.error(f"Ошибка добавления локации: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # ────────────────────────────────────────────────
        # РЕДАКТИРОВАНИЕ ЛОКАЦИИ (AJAX + multipart для фото)
        # ────────────────────────────────────────────────
        elif action == 'edit_location':
            if session.get('admin_role') != 'super':
                return jsonify({'success': False, 'error': 'Доступ только для super'}), 403

            loc_id = request.form.get('location_id')
            if not loc_id:
                return jsonify({'success': False, 'error': 'ID локации не передан'}), 400

            loc = Location.query.get(loc_id)
            if not loc:
                return jsonify({'success': False, 'error': 'Локация не найдена'}), 404

            try:
                loc.name = request.form.get('name', loc.name).strip()
                loc.city = request.form.get('city', loc.city) or None
                loc.country = request.form.get('country', loc.country) or None
                loc.type = request.form.get('type', loc.type) or 'club'
                loc.address = request.form.get('address', loc.address) or None
                loc.coordinates = request.form.get('coordinates', loc.coordinates) or None
                loc.contact_info = request.form.get('contact_info', loc.contact_info) or None
                loc.additional_info = request.form.get('additional_info', loc.additional_info) or None
                loc.description = request.form.get('description') or None

                # Обработка фото
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename and allowed_file(file.filename):
                        # Удаляем старую фотку, если была
                        if loc.image_url:
                            old_path = os.path.join('/home/beasty197/projects/vibepatrol/web/static', loc.image_url.lstrip('/'))
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(file_path)
                        loc.image_url = f'/static/images/locations/{filename}'

                # Флаг удаления фото
                if request.form.get('delete_image') == '1':
                    if loc.image_url:
                        old_path = os.path.join('/home/beasty197/projects/vibepatrol/web/static', loc.image_url.lstrip('/'))
                        if os.path.exists(old_path):
                            os.remove(old_path)
                        loc.image_url = None

                # Зоны и споты — удаляем старые и добавляем новые
                for zone in loc.zones:
                    db.session.delete(zone)

                zones_json = request.form.get('zones_json', '[]')
                admin_logger.info(f"[ZONES] Получено zones_json при edit: {zones_json}")
                print(f"[DEBUG] zones_json при edit: {zones_json}")
                try:
                    zones_data = json.loads(zones_json)
                except Exception as e:
                    admin_logger.error(f"[ZONES] Ошибка парсинга zones_json при edit: {str(e)}")
                    print(f"[ERROR] zones_json парсинг при edit: {str(e)}")
                    zones_data = []

                for z_data in zones_data:
                    zone = Zone(
                        name=z_data.get('name', '').strip(),
                        description=z_data.get('description') or None,
                        location_id=loc.id
                    )
                    db.session.add(zone)
                    db.session.flush()

                    spots_data = z_data.get('spots', [])
                    for s_data in spots_data:
                        spot = MeetingSpot(
                            name=s_data.get('name', '').strip(),
                            description=s_data.get('description') or None,
                            zone_id=zone.id
                        )
                        db.session.add(spot)

                db.session.commit()
                admin_logger.info(f"Обновлена локация ID {loc_id} ('{loc.name}'), зон: {len(zones_data)}")
                return jsonify({'success': True})

            except Exception as e:
                db.session.rollback()
                admin_logger.error(f"Ошибка редактирования локации ID {loc_id}: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # ────────────────────────────────────────────────
        # УДАЛЕНИЕ ЛОКАЦИИ (AJAX)
        # ────────────────────────────────────────────────
        elif action == 'delete_location':
            if session.get('admin_role') != 'super':
                return jsonify({'success': False, 'error': 'Доступ только для super'}), 403

            loc_id = data.get('id') or data.get('location_id')
            if not loc_id:
                return jsonify({'success': False, 'error': 'ID не передан'}), 400

            loc = Location.query.get(loc_id)
            if not loc:
                return jsonify({'success': False, 'error': 'Локация не найдена'}), 404

            try:
                # Удаляем фотку, если была
                if loc.image_url:
                    old_path = os.path.join('/home/beasty197/projects/vibepatrol/web/static', loc.image_url.lstrip('/'))
                    if os.path.exists(old_path):
                        os.remove(old_path)

                db.session.delete(loc)  # каскад удалит зоны и споты
                db.session.commit()
                admin_logger.info(f"Удалена локация ID {loc_id} ({loc.name})")
                return jsonify({'success': True})
            except Exception as e:
                db.session.rollback()
                admin_logger.error(f"Ошибка удаления локации {loc_id}: {str(e)}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # Для обычных форм — редирект после POST
        return redirect(url_for('admin.dashboard'))

    # GET — отображаем дашборд
    admins = Admin.query.all()
    questions = Question.query.order_by(Question.order).all()

    max_order = db.session.query(db.func.max(Question.order)).scalar() or 0
    max_order_for_new = max_order + 1

    locations = []
    if session.get('admin_role') == 'super':
        locations = Location.query.order_by(Location.name).all()
        admin_logger.info(f"Загружено {len(locations)} локаций для super")

    print("[DEBUG] === GET DASHBOARD ===")
    print("[DEBUG] Количество вопросов в базе:", len(questions))
    print("[DEBUG] Максимальный order в базе:", max_order)
    print("[DEBUG] Локаций загружено:", len(locations))

    admin_logger.info(f"Отображаем {len(admins)} админов, {len(questions)} вопросов, {len(locations)} локаций")

    return render_template(
        'dashboard.html',
        title=custom_gettext('Админ-панель VibePatrol', 'dashboard'),
        admins=admins,
        questions=questions,
        locations=locations,
        max_order=max_order_for_new,
        custom_gettext=custom_gettext
    )


# ──────────────────────────────────────────────────────────────────────────────
# НОВЫЙ РОУТ — ПОЛУЧЕНИЕ ЗОН И СПТОВ ДЛЯ EDIT
# ──────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/get_location_zones/<int:loc_id>', methods=['GET'])
@admin_required
def get_location_zones(loc_id):
    if session.get('admin_role') != 'super':
        return jsonify({'success': False, 'error': 'Доступ только для super'}), 403

    loc = Location.query.get(loc_id)
    if not loc:
        return jsonify({'success': False, 'error': 'Локация не найдена'}), 404

    zones = []
    for zone in loc.zones:
        zones.append({
            'name': zone.name,
            'description': zone.description,
            'spots': [{'name': spot.name, 'description': spot.description} for spot in zone.spots]
        })

    admin_logger.info(f"[ZONES] Отправляем зоны для локации {loc_id}: {len(zones)} зон")
    print(f"[DEBUG] get_location_zones: {len(zones)} зон для {loc_id}")
    return jsonify({'success': True, 'zones': zones})


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