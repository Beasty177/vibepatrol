// web/static/js/admin/admin_management.js

function toggleAdminBlock(header) {
    const content = header.nextElementSibling;
    const isOpen = content.style.display !== 'block';

    content.style.display = isOpen ? 'block' : 'none';
    header.classList.toggle('active', isOpen);
}

function openAdminPopup(mode, id = '', username = '', role = '') {
    const popup = document.getElementById('adminPopup');
    const title = document.getElementById('popupTitle');
    const form = document.getElementById('adminForm');
    const deleteBtn = document.getElementById('deleteAdminBtn');
    const deleteConfirmation = document.getElementById('deleteConfirmation');

    if (!popup || !title || !form) {
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

    if (mode === 'add') {
        title.textContent = 'Добавить администратора';
        if (actionInput) actionInput.value = 'add_admin';
        if (idInput) idInput.value = '';
        if (usernameInput) usernameInput.value = '';
        if (roleSelect) roleSelect.value = 'questionnaire';
    } 
    else if (mode === 'edit') {
        title.textContent = 'Редактировать администратора';
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

        document.getElementById('popupTitle').textContent = 'Удалить администратора?';
    });
}

function cancelDelete() {
    const deleteConfirmation = document.getElementById('deleteConfirmation');
    if (deleteConfirmation) deleteConfirmation.style.display = 'none';

    document.querySelectorAll('.form-group').forEach(el => el.style.display = 'block');
    const saveBtn = document.querySelector('.save-btn');
    if (saveBtn) saveBtn.style.display = 'inline-block';
    const deleteBtn = document.getElementById('deleteAdminBtn');
    if (deleteBtn) deleteBtn.style.display = 'inline-block';

    document.getElementById('popupTitle').textContent = 'Редактировать администратора';
}

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

    document.getElementById('popupTitle').textContent = 'Добавить администратора';
}

// Инициализация
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