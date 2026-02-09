// web/static/js/admin/admin_management.js

// ────────────────────────────────────────────────
// Аккордеон (раскрытие/скрытие блоков)
// ────────────────────────────────────────────────
function toggleAdminBlock(header) {
    const content = header.nextElementSibling;
    const isOpen = content.style.display !== 'block';

    content.style.display = isOpen ? 'block' : 'none';
    header.classList.toggle('active', isOpen);
}

// ────────────────────────────────────────────────
// Попап редактирования/добавления админа
// ────────────────────────────────────────────────
function openAdminPopup(mode, id = '', username = '', role = '') {
    const popup = document.getElementById('adminPopup');
    const titleEl = document.getElementById('popupTitle');
    const form = document.getElementById('adminForm');
    const deleteBtn = document.getElementById('deleteAdminBtn');
    const deleteConfirmation = document.getElementById('deleteConfirmation');
    const passwordHint = document.getElementById('passwordHint');  // подсказка у пароля

    if (!popup || !titleEl || !form) {
        console.error('Не найдены элементы попапа');
        return;
    }

    // Полный сброс состояния
    form.reset();
    document.getElementById('password').value = '';

    if (deleteConfirmation) deleteConfirmation.style.display = 'none';
    if (deleteBtn) deleteBtn.style.display = 'none';

    document.querySelectorAll('.form-group').forEach(el => {
        el.style.display = 'block';
    });
    const saveBtn = document.querySelector('.save-btn');
    if (saveBtn) saveBtn.style.display = 'inline-block';

    const actionInput = document.getElementById('action');
    const idInput = document.getElementById('admin_id');
    const usernameInput = document.getElementById('username');
    const roleSelect = document.getElementById('role');

    // Управляем видимостью подсказки к полю пароля
    if (passwordHint) {
        // Показываем только в режиме редактирования
        passwordHint.style.display = (mode === 'edit') ? 'inline' : 'none';
    }

    // Устанавливаем заголовок из data-атрибутов (переводы из шаблона)
    if (mode === 'add') {
        titleEl.textContent = titleEl.dataset.add || 'Добавить администратора';
        if (actionInput) actionInput.value = 'add_admin';
        if (idInput) idInput.value = '';
        if (usernameInput) usernameInput.value = '';
        if (roleSelect) roleSelect.value = 'questionnaire';
    } 
    else if (mode === 'edit') {
        titleEl.textContent = titleEl.dataset.edit || 'Редактировать администратора';
        if (actionInput) actionInput.value = 'edit_admin';
        if (idInput) idInput.value = id;
        if (usernameInput) usernameInput.value = username;
        if (roleSelect) roleSelect.value = role || 'questionnaire';

        if (deleteBtn) {
            deleteBtn.style.display = 'inline-block';
            deleteBtn.dataset.id = id;
            deleteBtn.dataset.username = username;
        }
    } 
    else {
        console.warn('Неизвестный режим:', mode);
        return;
    }

    popup.style.display = 'flex';
}

// ────────────────────────────────────────────────
// Инициализация кнопки удаления в попапе
// ────────────────────────────────────────────────
function initDeleteButton() {
    const deleteBtn = document.getElementById('deleteAdminBtn');
    if (!deleteBtn) return;

    deleteBtn.addEventListener('click', function () {
        const username = document.getElementById('username')?.value.trim() || '[логин]';
        
        const confirmUsernameEl = document.getElementById('confirmUsername');
        if (confirmUsernameEl) {
            confirmUsernameEl.textContent = username;
        }

        document.querySelectorAll('.form-group').forEach(el => el.style.display = 'none');
        const saveBtn = document.querySelector('.save-btn');
        if (saveBtn) saveBtn.style.display = 'none';
        deleteBtn.style.display = 'none';

        const deleteConfirmation = document.getElementById('deleteConfirmation');
        if (deleteConfirmation) deleteConfirmation.style.display = 'block';

        // Заголовок подтверждения тоже из data-атрибута
        const titleEl = document.getElementById('popupTitle');
        if (titleEl) titleEl.textContent = titleEl.dataset.delete || 'Удалить администратора?';
    });
}

// ────────────────────────────────────────────────
// Отмена удаления — возвращаем форму в режим редактирования
// ────────────────────────────────────────────────
function cancelDelete() {
    const deleteConfirmation = document.getElementById('deleteConfirmation');
    if (deleteConfirmation) deleteConfirmation.style.display = 'none';

    document.querySelectorAll('.form-group').forEach(el => el.style.display = 'block');
    const saveBtn = document.querySelector('.save-btn');
    if (saveBtn) saveBtn.style.display = 'inline-block';
    const deleteBtn = document.getElementById('deleteAdminBtn');
    if (deleteBtn) deleteBtn.style.display = 'inline-block';

    const titleEl = document.getElementById('popupTitle');
    if (titleEl) titleEl.textContent = titleEl.dataset.edit || 'Редактировать администратора';
}

// ────────────────────────────────────────────────
// Подтверждение удаления
// ────────────────────────────────────────────────
function confirmDelete() {
    console.log("[DEBUG] confirmDelete() запущен");

    const actionInput = document.getElementById('action');
    if (actionInput) {
        actionInput.value = 'delete_admin';
        console.log("[DEBUG] action →", actionInput.value);
    } else {
        console.error("[ERROR] Не найден input#action");
    }

    const form = document.getElementById('adminForm');
    if (form) {
        console.log("[DEBUG] Форма найдена, отправляем...");
        try {
            form.submit();
            console.log("[DEBUG] form.submit() вызван");
        } catch (err) {
            console.error("[ERROR] Ошибка при submit:", err);
        }
    } else {
        console.error("[ERROR] Форма с id='adminForm' не найдена!");
    }
}

// ────────────────────────────────────────────────
// Закрытие основного попапа админов
// ────────────────────────────────────────────────
function closeAdminPopup() {
    const popup = document.getElementById('adminPopup');
    if (popup) popup.style.display = 'none';

    const deleteConfirmation = document.getElementById('deleteConfirmation');
    if (deleteConfirmation) deleteConfirmation.style.display = 'none';

    document.querySelectorAll('.form-group').forEach(el => el.style.display = 'block');
    const saveBtn = document.querySelector('.save-btn');
    if (saveBtn) saveBtn.style.display = 'inline-block';
    const deleteBtn = document.getElementById('deleteAdminBtn');
    if (deleteBtn) deleteBtn.style.display = 'none';

    const titleEl = document.getElementById('popupTitle');
    if (titleEl) titleEl.textContent = titleEl.dataset.add || 'Добавить администратора';
}

// ────────────────────────────────────────────────
// Попап профиля текущего админа (смена логина/пароля)
// ────────────────────────────────────────────────
function openProfilePopup() {
    const popup = document.getElementById('profilePopup');
    if (popup) {
        popup.style.display = 'flex';
    } else {
        console.error('[PROFILE] Попап #profilePopup не найден');
    }
}

function closeProfilePopup() {
    const popup = document.getElementById('profilePopup');
    if (popup) {
        popup.style.display = 'none';
    }
    
    const form = document.getElementById('profileForm');
    if (form) {
        form.reset();
    }
}

// ────────────────────────────────────────────────
// Инициализация при загрузке страницы
// ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    console.log("[DEBUG] Скрипт admin_management.js загружен");

    initDeleteButton();

    document.addEventListener('click', function (e) {
        const target = e.target;

        if (target.classList.contains('add-btn')) {
            openAdminPopup('add');
        }
        else if (target.classList.contains('edit-btn')) {
            openAdminPopup(
                'edit',
                target.dataset.id,
                target.dataset.username,
                target.dataset.role
            );
        }
    });
});