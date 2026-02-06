# /home/beasty197/projects/vibepatrol/backend/add_super_admin.py

from app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

# Настройки супер-админа (можно менять прямо здесь)
SUPER_USERNAME = "Super-Beasty"
SUPER_PASSWORD = "Grsns197Vibe"  # ← СЮДА ВСТАВЬ СВОЙ ПАРОЛЬ
SUPER_ROLE = "super"

with app.app_context():
    # Проверяем, есть ли уже супер-админ с таким username
    existing = Admin.query.filter_by(username=SUPER_USERNAME).first()

    if existing:
        print(f"Админ '{SUPER_USERNAME}' уже существует.")
        print("Обновляем пароль...")
        existing.set_password(SUPER_PASSWORD)
        db.session.commit()
        print("Пароль успешно обновлён!")
    else:
        print(f"Создаём нового супер-админа '{SUPER_USERNAME}'...")
        new_admin = Admin(
            username=SUPER_USERNAME,
            role=SUPER_ROLE
        )
        new_admin.set_password(SUPER_PASSWORD)
        db.session.add(new_admin)
        db.session.commit()
        print("Супер-админ успешно добавлен!")
        print(f"Логин: {SUPER_USERNAME}")
        print(f"Пароль: {SUPER_PASSWORD}")
        print(f"Роль: {SUPER_ROLE}")

    # Показываем всех админов для проверки
    print("\nТекущие админы в базе:")
    all_admins = Admin.query.all()
    if all_admins:
        for admin in all_admins:
            print(f" - {admin.username} | Роль: {admin.role}")
    else:
        print("Админов пока нет.")