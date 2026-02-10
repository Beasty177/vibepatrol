// web/static/js/admin/admin_management.js

// ────────────────────────────────────────────────
// АККОРДЕОН — раскрытие/скрытие блоков
// ────────────────────────────────────────────────
function toggleAdminBlock(header) {
    const content = header.nextElementSibling;
    const isOpen = content.style.display !== 'block';

    content.style.display = isOpen ? 'block' : 'none';
    header.classList.toggle('active', isOpen);
}

// ────────────────────────────────────────────────
// ПОПАП АДМИНОВ
// ────────────────────────────────────────────────
function openAdminPopup(mode, id = '', username = '', role = '') {
    const popup = document.getElementById('adminPopup');
    const titleEl = document.getElementById('popupTitle');
    const form = document.getElementById('adminForm');
    const deleteBtn = document.getElementById('deleteAdminBtn');
    const deleteConfirmation = document.getElementById('deleteConfirmation');
    const passwordHint = document.getElementById('passwordHint');

    if (!popup || !titleEl || !form) {
        console.error('Не найдены элементы попапа админов');
        return;
    }

    form.reset();
    document.getElementById('password').value = '';

    if (deleteConfirmation) deleteConfirmation.style.display = 'none';
    if (deleteBtn) deleteBtn.style.display = 'none';

    document.querySelectorAll('.form-group').forEach(el => el.style.display = 'block');
    const saveBtn = document.querySelector('.save-btn');
    if (saveBtn) saveBtn.style.display = 'inline-block';

    const actionInput = document.getElementById('action');
    const idInput = document.getElementById('admin_id');
    const usernameInput = document.getElementById('username');
    const roleSelect = document.getElementById('role');

    if (passwordHint) {
        passwordHint.style.display = (mode === 'edit') ? 'inline' : 'none';
    }

    if (mode === 'add') {
        titleEl.textContent = titleEl.dataset.add || 'Добавить администратора';
        actionInput.value = 'add_admin';
        idInput.value = '';
        usernameInput.value = '';
        roleSelect.value = 'questionnaire';
    } else if (mode === 'edit') {
        titleEl.textContent = titleEl.dataset.edit || 'Редактировать администратора';
        actionInput.value = 'edit_admin';
        idInput.value = id;
        usernameInput.value = username;
        roleSelect.value = role || 'questionnaire';

        if (deleteBtn) {
            deleteBtn.style.display = 'inline-block';
            deleteBtn.dataset.id = id;
            deleteBtn.dataset.username = username;
        }
    } else {
        console.warn('Неизвестный режим для попапа админов:', mode);
        return;
    }

    popup.style.display = 'flex';
}

// ────────────────────────────────────────────────
// ИНИЦИАЛИЗАЦИЯ КНОПКИ УДАЛЕНИЯ АДМИНА
// ────────────────────────────────────────────────
function initDeleteButton() {
    const deleteBtn = document.getElementById('deleteAdminBtn');
    if (!deleteBtn) return;

    deleteBtn.addEventListener('click', function () {
        const username = document.getElementById('username')?.value.trim() || '[логин]';
        
        const confirmUsernameEl = document.getElementById('confirmUsername');
        if (confirmUsernameEl) confirmUsernameEl.textContent = username;

        document.querySelectorAll('.form-group').forEach(el => el.style.display = 'none');
        const saveBtn = document.querySelector('.save-btn');
        if (saveBtn) saveBtn.style.display = 'none';
        deleteBtn.style.display = 'none';

        const deleteConfirmation = document.getElementById('deleteConfirmation');
        if (deleteConfirmation) deleteConfirmation.style.display = 'block';

        const titleEl = document.getElementById('popupTitle');
        if (titleEl) titleEl.textContent = titleEl.dataset.delete || 'Удалить администратора?';
    });
}

// ────────────────────────────────────────────────
// ОТМЕНА УДАЛЕНИЯ АДМИНА
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
// ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ АДМИНА
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
// ЗАКРЫТИЕ ПОПАПА АДМИНОВ
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
// ПОПАП ПРОФИЛЯ ТЕКУЩЕГО АДМИНА
// ────────────────────────────────────────────────
function openProfilePopup() {
    const popup = document.getElementById('profilePopup');
    if (popup) popup.style.display = 'flex';
    else console.error('[PROFILE] Попап #profilePopup не найден');
}

function closeProfilePopup() {
    const popup = document.getElementById('profilePopup');
    if (popup) popup.style.display = 'none';
    
    const form = document.getElementById('profileForm');
    if (form) form.reset();
}

// ────────────────────────────────────────────────
// УПРАВЛЕНИЕ ПЕРЕВОДОМ В ПОПАПЕ ВОПРОСА
// ────────────────────────────────────────────────
function toggleLanguageField(lang) {
    document.querySelectorAll('.lang-field').forEach(field => {
        field.style.display = 'none';
    });

    if (lang) {
        const field = document.getElementById(lang + 'Field');
        if (field) field.style.display = 'block';
    }
}

// ────────────────────────────────────────────────
// СИНХРОНИЗАЦИЯ ПОЛЗУНКА И ЧИСЛА ДЛЯ ВЕСА ВОПРОСА
// ────────────────────────────────────────────────
function syncWeightInputs() {
    const slider = document.getElementById('weightSlider');
    const number = document.getElementById('question_weight');

    if (!slider || !number) {
        console.warn("[DEBUG] Элементы слайдера или числа не найдены");
        return;
    }

    slider.removeEventListener('input', updateNumber);
    number.removeEventListener('input', updateSlider);

    function updateNumber() {
        number.value = slider.value;
    }
    slider.addEventListener('input', updateNumber);

    function updateSlider() {
        let val = parseInt(number.value);
        if (isNaN(val)) val = 50;
        val = Math.max(0, Math.min(100, val));
        slider.value = val;
        number.value = val;
    }
    number.addEventListener('input', updateSlider);

    number.value = slider.value;
}

// ────────────────────────────────────────────────
// УДАЛЕНИЕ ВОПРОСА
// ────────────────────────────────────────────────
function deleteQuestion(questionId, questionText) {
    const confirmation = document.getElementById('deleteQuestionConfirmation');
    const confirmText = document.getElementById('confirmQuestionText');
    
    if (confirmation && confirmText) {
        confirmText.textContent = questionText;
        confirmation.style.display = 'block';
        document.getElementById('deleteQuestionBtn').style.display = 'none';
    }

    document.getElementById('question_id').dataset.deleteId = questionId;
}

function cancelDeleteQuestion() {
    document.getElementById('deleteQuestionConfirmation').style.display = 'none';
    document.getElementById('deleteQuestionBtn').style.display = 'inline-block';
}

function confirmDeleteQuestion() {
    const questionId = document.getElementById('question_id').dataset.deleteId;
    if (!questionId) return;

    const actionInput = document.getElementById('question_action');
    actionInput.value = 'delete_question';

    const form = document.getElementById('questionForm');
    if (form) form.submit();
}

// ────────────────────────────────────────────────
// ПОПАП УПРАВЛЕНИЯ ВОПРОСАМИ АНКЕТЫ
// ────────────────────────────────────────────────
function openQuestionPopup(mode, id = '', text_ru = '', type = '', required = false, weight = 50, order = 0, text_en = '', text_he = '', options = '[]') {
    const popup = document.getElementById('questionPopup');
    const title = document.getElementById('questionPopupTitle');
    const form = document.getElementById('questionForm');
    const optionsGroup = document.getElementById('optionsGroup');
    const deleteBtn = document.getElementById('deleteQuestionBtn');

    if (!popup || !title || !form) {
        console.error('Не найдены элементы попапа вопроса');
        return;
    }

    form.reset();

    const actionInput = document.getElementById('question_action');
    const idInput = document.getElementById('question_id');
    const textRuInput = document.getElementById('text_ru');
    const textEnInput = document.getElementById('text_en');
    const textHeInput = document.getElementById('text_he');
    const typeSelect = document.getElementById('question_type');
    const requiredCheckbox = document.getElementById('question_required');
    const weightInput = document.getElementById('question_weight');
    const weightSlider = document.getElementById('weightSlider');
    const orderInput = document.getElementById('question_order');
    const optionsTextarea = document.getElementById('question_options');

    if (mode === 'add') {
        title.textContent = 'Добавить вопрос';
        actionInput.value = 'add_question';
        idInput.value = '';
        textRuInput.value = '';
        textEnInput.value = '';
        textHeInput.value = '';
        typeSelect.value = 'multiple_choice';
        requiredCheckbox.checked = false;
        weightInput.value = '50';
        weightSlider.value = '50';
        orderInput.value = '0';
        optionsTextarea.value = '';
        if (optionsGroup) optionsGroup.style.display = 'block';
        if (deleteBtn) deleteBtn.style.display = 'none';

        document.querySelectorAll('.lang-field').forEach(field => field.style.display = 'none');
    } else if (mode === 'edit') {
        title.textContent = 'Редактировать вопрос';
        actionInput.value = 'edit_question';
        idInput.value = id;
        textRuInput.value = text_ru || '';
        textEnInput.value = text_en || '';
        textHeInput.value = text_he || '';
        typeSelect.value = type;
        requiredCheckbox.checked = required === 'True' || required === true;
        weightInput.value = weight || '50';
        weightSlider.value = weight || '50';
        orderInput.value = order;

        // Заполняем варианты
        let optionsArray = [];
        console.log("[DEBUG] Полученные options:", options); // отладка

        try {
            if (options && options.trim() !== '' && options.trim() !== '[]') {
                optionsArray = JSON.parse(options);
            }
        } catch (e) {
            console.warn("[ERROR] Не удалось распарсить options:", options, e);
        }

        console.log("[DEBUG] Вставляем в textarea:", optionsArray);
        optionsTextarea.value = optionsArray.join('\n');

        if (optionsGroup) optionsGroup.style.display = (type === 'multiple_choice') ? 'block' : 'none';

        if (text_en) document.getElementById('enField').style.display = 'block';
        if (text_he) document.getElementById('heField').style.display = 'block';

        if (deleteBtn) {
            deleteBtn.style.display = 'inline-block';
            deleteBtn.onclick = () => deleteQuestion(id, text_ru);
        }
    }

    syncWeightInputs();

    popup.style.display = 'flex';
}

function closeQuestionPopup() {
    document.getElementById('questionPopup').style.display = 'none';
}

// ────────────────────────────────────────────────
// ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
// ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    console.log("[DEBUG] Скрипт admin_management.js загружен");

    initDeleteButton();

    document.addEventListener('click', function (e) {
        const target = e.target;

        if (target.classList.contains('add-admin-btn')) {
            openAdminPopup('add');
        }

        if (target.classList.contains('add-question-btn')) {
            openQuestionPopup('add');
        }

        if (target.classList.contains('edit-btn')) {
            openAdminPopup(
                'edit',
                target.dataset.id,
                target.dataset.username,
                target.dataset.role
            );
        }
    });
});