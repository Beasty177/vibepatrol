// web/static/js/admin/admin_management.js

// ────────────────────────────────────────────────
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// ────────────────────────────────────────────────
let zoneCounter = 0;
let spotCounter = 0;

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
// УДАЛЕНИЕ АДМИНА
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

function confirmDelete() {
    console.log("[DEBUG] confirmDelete() запущен");

    const actionInput = document.getElementById('action');
    if (actionInput) actionInput.value = 'delete_admin';

    const form = document.getElementById('adminForm');
    if (form) form.submit();
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
// ПОПАП ПРОФИЛЯ
// ────────────────────────────────────────────────
function openProfilePopup() {
    const popup = document.getElementById('profilePopup');
    if (popup) popup.style.display = 'flex';
}

function closeProfilePopup() {
    const popup = document.getElementById('profilePopup');
    if (popup) popup.style.display = 'none';
    
    const form = document.getElementById('profileForm');
    if (form) form.reset();
}

// ────────────────────────────────────────────────
// ВОПРОСЫ АНКЕТЫ
// ────────────────────────────────────────────────
function toggleLanguageField(lang) {
    document.querySelectorAll('.lang-field').forEach(field => field.style.display = 'none');
    if (lang) {
        const field = document.getElementById(lang + 'Field');
        if (field) field.style.display = 'block';
    }
}

function syncWeightInputs() {
    const slider = document.getElementById('weightSlider');
    const number = document.getElementById('question_weight');

    if (!slider || !number) return;

    slider.addEventListener('input', () => number.value = slider.value);
    number.addEventListener('input', () => {
        let val = parseInt(number.value) || 50;
        val = Math.max(0, Math.min(100, val));
        slider.value = val;
        number.value = val;
    });

    number.value = slider.value;
}

function getMaxOrder() {
    const maxOrderInput = document.getElementById('max_order');
    return maxOrderInput ? parseInt(maxOrderInput.value) || 20 : 20;
}

function changeOrder(delta) {
    const orderInput = document.getElementById('question_order');
    if (!orderInput) return;

    let current = parseInt(orderInput.value) || 0;
    let newVal = current + delta;
    const maxOrder = getMaxOrder();
    newVal = Math.max(1, Math.min(maxOrder, newVal));
    orderInput.value = newVal;
}

function deleteQuestion(questionId, questionText) {
    const overlay = document.getElementById('deleteQuestionOverlay');
    const confirmText = document.getElementById('confirmQuestionText');
    
    if (overlay && confirmText) {
        confirmText.textContent = questionText;
        overlay.style.display = 'flex';
        document.getElementById('question_id').dataset.deleteId = questionId;
    }
}

function cancelDeleteQuestion() {
    const overlay = document.getElementById('deleteQuestionOverlay');
    if (overlay) overlay.style.display = 'none';
}

function confirmDeleteQuestion() {
    const questionId = document.getElementById('question_id').dataset.deleteId;
    if (!questionId) return;

    const actionInput = document.getElementById('question_action');
    if (actionInput) actionInput.value = 'delete_question';

    const form = document.getElementById('questionForm');
    if (form) form.submit();
}

function openQuestionPopup(mode, id = '', text_ru = '', type = '', required = false, weight = 50, order = 0, text_en = '', text_he = '', options = '[]') {
    const popup = document.getElementById('questionPopup');
    const title = document.getElementById('questionPopupTitle');
    const form = document.getElementById('questionForm');

    if (!popup || !title || !form) return;

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
    const optionsGroup = document.getElementById('optionsGroup');
    const deleteBtn = document.getElementById('deleteQuestionBtn');

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
        orderInput.value = getMaxOrder();
        optionsTextarea.value = '';
        if (optionsGroup) optionsGroup.style.display = 'block';
        if (deleteBtn) deleteBtn.style.display = 'none';
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

        let optionsArray = [];
        try {
            if (options && options.trim() !== '' && options.trim() !== '[]') {
                optionsArray = JSON.parse(options);
            }
        } catch (e) {
            console.warn("[ERROR] Не удалось распарсить options:", options, e);
        }
        optionsTextarea.value = optionsArray.join('\n');

        if (optionsGroup) optionsGroup.style.display = (type === 'multiple_choice') ? 'block' : 'none';
        if (deleteBtn) {
            deleteBtn.style.display = 'inline-block';
            deleteBtn.onclick = () => deleteQuestion(id, text_ru);
        }
    }

    syncWeightInputs();
    popup.style.display = 'flex';
}

function closeQuestionPopup() {
    const popup = document.getElementById('questionPopup');
    if (popup) popup.style.display = 'none';
}

// ────────────────────────────────────────────────
// ПОПАП ЛОКАЦИЙ — ПОЛНЫЙ И РАБОЧИЙ БЛОК
// ────────────────────────────────────────────────

function openLocationPopup(mode = 'add', id = '', name = '', city = '', country = '', type = 'club', address = '', coordinates = '', contact_info = '', additional_info = '', description = '', image_url = '') {
    const popup = document.getElementById('locationPopup');
    if (!popup) {
        console.error('[LOCATIONS] #locationPopup не найден');
        return;
    }

    const form = document.getElementById('locationForm');
    const actionInput = document.getElementById('location_action');
    const idInput = document.getElementById('location_id');
    const deleteBtn = document.getElementById('deleteLocationBtn');
    const previewImg = document.getElementById('previewImg');
    const noImageText = document.getElementById('noImageText');
    const removeImageBtn = document.getElementById('removeImageBtn');
    const deleteImageFlag = document.getElementById('delete_image');

    // Сбрасываем форму, фотку и зоны
    if (form) form.reset();
    if (previewImg) {
        previewImg.src = '';
        previewImg.style.display = 'none';
    }
    if (noImageText) noImageText.style.display = 'block';
    if (removeImageBtn) removeImageBtn.style.display = 'none';
    if (deleteImageFlag) deleteImageFlag.value = '0';

    const zonesContainer = document.getElementById('zonesContainer');
    if (zonesContainer) {
        zonesContainer.innerHTML = '<h6>Зоны</h6>';
    }

    zoneCounter = 0;
    spotCounter = 0;

    if (mode === 'add') {
        actionInput.value = 'add_location';
        idInput.value = '';
        deleteBtn.style.display = 'none';
    } else if (mode === 'edit') {
        actionInput.value = 'edit_location';
        idInput.value = id;

        document.getElementById('name').value = name || '';
        document.getElementById('city').value = city || '';
        document.getElementById('country').value = country || '';
        document.getElementById('type').value = type || 'club';
        document.getElementById('address').value = address || '';
        document.getElementById('coordinates').value = coordinates || '';
        document.getElementById('contact_info').value = contact_info || '';
        document.getElementById('additional_info').value = additional_info || '';
        document.getElementById('description').value = description || '';

        // Подгрузка зон и спотов при edit (AJAX)
        if (id) {
            fetch(`/admin/get_location_zones/${id}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.zones) {
                        data.zones.forEach((zone, zIndex) => {
                            zoneCounter = zIndex + 1;
                            const zoneBlock = document.createElement('div');
                            zoneBlock.className = 'zone-block mb-3 border p-3 rounded';
                            zoneBlock.dataset.zoneId = zoneCounter;

                            zoneBlock.innerHTML = `
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <h6 class="mb-0">Зона ${zoneCounter}</h6>
                                    <button type="button" class="btn btn-sm btn-danger remove-zone">×</button>
                                </div>
                                <div class="form-group">
                                    <label>Название зоны</label>
                                    <input type="text" class="form-control zone-name" name="zones[${zoneCounter}][name]" value="${zone.name || ''}" required>
                                </div>
                                <div class="form-group">
                                    <label>Описание зоны (опционально)</label>
                                    <textarea class="form-control zone-desc" name="zones[${zoneCounter}][description]" rows="2">${zone.description || ''}</textarea>
                                </div>
                                <div class="spots-container mt-3">
                                    <h6>Места для встречи</h6>
                                </div>
                                <button type="button" class="btn add-btn-base mt-2 add-spot-btn">
                                    + Добавить место
                                </button>
                            `;

                            zonesContainer.appendChild(zoneBlock);

                            // Добавляем споты
                            if (zone.spots) {
                                zone.spots.forEach((spot, sIndex) => {
                                    spotCounter = sIndex + 1;
                                    const spotsContainer = zoneBlock.querySelector('.spots-container');
                                    const spotBlock = document.createElement('div');
                                    spotBlock.className = 'spot-block mb-2 border-left pl-3';
                                    spotBlock.dataset.spotId = spotCounter;

                                    spotBlock.innerHTML = `
                                        <div class="d-flex justify-content-between align-items-center mb-1">
                                            <small class="text-muted">Место ${spotCounter}</small>
                                            <button type="button" class="btn btn-sm btn-outline-danger remove-spot">×</button>
                                        </div>
                                        <div class="form-group mb-1">
                                            <input type="text" class="form-control spot-name" 
                                                   name="zones[${zoneCounter}][spots][${spotCounter}][name]" 
                                                   value="${spot.name || ''}" 
                                                   placeholder="Название (например: красный диван)" required>
                                        </div>
                                        <div class="form-group mb-0">
                                            <textarea class="form-control spot-desc" rows="2"
                                                      name="zones[${zoneCounter}][spots][${spotCounter}][description]"
                                                      placeholder="Описание (опционально)">${spot.description || ''}</textarea>
                                        </div>
                                    `;

                                    spotsContainer.appendChild(spotBlock);
                                });
                            }
                        });
                    }
                })
                .catch(err => console.error('Ошибка загрузки зон:', err));
        }

        if (image_url && image_url !== 'None' && image_url.trim() !== '') {
            previewImg.src = image_url;
            previewImg.style.display = 'block';
            noImageText.style.display = 'none';
            removeImageBtn.style.display = 'block';
        } else {
            previewImg.style.display = 'none';
            noImageText.style.display = 'block';
            removeImageBtn.style.display = 'none';
        }

        deleteBtn.style.display = 'block';
        deleteBtn.onclick = () => deleteLocation(id, name);
    }

    popup.style.display = 'flex';
}

function closeLocationPopup() {
    const popup = document.getElementById('locationPopup');
    if (popup) popup.style.display = 'none';
    
    const form = document.getElementById('locationForm');
    if (form) form.reset();
    
    const zonesContainer = document.getElementById('zonesContainer');
    if (zonesContainer) zonesContainer.innerHTML = '<h6>Зоны</h6>';
    
    zoneCounter = 0;
    spotCounter = 0;
}

// Добавление зоны
function addZone() {
    zoneCounter++;

    const zonesContainer = document.getElementById('zonesContainer');
    if (!zonesContainer) return;

    const zoneBlock = document.createElement('div');
    zoneBlock.className = 'zone-block mb-3 border p-3 rounded';
    zoneBlock.dataset.zoneId = zoneCounter;

    zoneBlock.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">Зона ${zoneCounter}</h6>
            <button type="button" class="btn btn-sm btn-danger remove-zone">×</button>
        </div>
        <div class="form-group">
            <label>Название зоны</label>
            <input type="text" class="form-control zone-name" name="zones[${zoneCounter}][name]" required>
        </div>
        <div class="form-group">
            <label>Описание зоны (опционально)</label>
            <textarea class="form-control zone-desc" name="zones[${zoneCounter}][description]" rows="2"></textarea>
        </div>
        <div class="spots-container mt-3">
            <h6>Места для встречи</h6>
        </div>
        <button type="button" class="btn add-btn-base mt-2 add-spot-btn">
            + Добавить место
        </button>
    `;

    zonesContainer.appendChild(zoneBlock);
}

// Добавление спота в зону
function addSpot(zoneBlock) {
    spotCounter++;

    const zoneIndex = zoneBlock.dataset.zoneId;
    const spotsContainer = zoneBlock.querySelector('.spots-container');

    const spotBlock = document.createElement('div');
    spotBlock.className = 'spot-block mb-2 border-left pl-3';
    spotBlock.dataset.spotId = spotCounter;

    spotBlock.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1">
            <small class="text-muted">Место ${spotCounter}</small>
            <button type="button" class="btn btn-sm btn-outline-danger remove-spot">×</button>
        </div>
        <div class="form-group mb-1">
            <input type="text" class="form-control spot-name" 
                   name="zones[${zoneIndex}][spots][${spotCounter}][name]" 
                   placeholder="Название (например: красный диван)" required>
        </div>
        <div class="form-group mb-0">
            <textarea class="form-control spot-desc" rows="2"
                      name="zones[${zoneIndex}][spots][${spotCounter}][description]"
                      placeholder="Описание (опционально)"></textarea>
        </div>
    `;

    spotsContainer.appendChild(spotBlock);
}

// Сохранение локации (с поддержкой файла и удаления фото)
function saveLocation() {
    const form = document.getElementById('locationForm');
    if (!form) return;

    const formData = new FormData(form);
    formData.append('action', document.getElementById('location_action').value);

    // Собираем зоны и споты
    const zones = [];
    document.querySelectorAll('.zone-block').forEach(zoneEl => {
        const zone = {
            name: zoneEl.querySelector('.zone-name')?.value.trim() || '',
            description: zoneEl.querySelector('.zone-desc')?.value.trim() || '',
            spots: []
        };

        if (!zone.name) return;

        zoneEl.querySelectorAll('.spot-block').forEach(spotEl => {
            const spot = {
                name: spotEl.querySelector('.spot-name')?.value.trim() || '',
                description: spotEl.querySelector('.spot-desc')?.value.trim() || ''
            };
            if (spot.name) zone.spots.push(spot);
        });

        if (zone.name) zones.push(zone);
    });

    formData.append('zones_json', JSON.stringify(zones));

    console.log('[LOCATIONS] Отправляем форму с файлом и зонами:', zones);

    fetch('/admin/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('Сервер вернул ' + response.status);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            closeLocationPopup();
            location.reload();
        } else {
            alert('Ошибка: ' + (data.error || 'неизвестно'));
        }
    })
    .catch(err => {
        console.error('[LOCATIONS] Ошибка:', err);
        alert('Ошибка связи с сервером: ' + err.message);
    });
}

// Удаление локации (AJAX)
function deleteLocation(id, name) {
    if (!confirm('Вы уверены, что хотите удалить локацию "' + name + '"?')) return;

    fetch('/admin/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'delete_location', id: id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Ошибка удаления: ' + (data.error || 'неизвестно'));
        }
    })
    .catch(err => alert('Ошибка связи: ' + err));
}

// ────────────────────────────────────────────────
// ИНИЦИАЛИЗАЦИЯ СОБЫТИЙ
// ────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    console.log("[DEBUG] admin_management.js загружен — " + new Date().toLocaleTimeString());

    initDeleteButton();

    // События для админов и вопросов
    document.addEventListener('click', function (e) {
        const target = e.target;

        if (target.classList.contains('add-admin-btn')) {
            openAdminPopup('add');
        }
        if (target.classList.contains('edit-btn') && target.dataset.id) {
            openAdminPopup('edit', target.dataset.id, target.dataset.username, target.dataset.role);
        }
        if (target.classList.contains('add-question-btn')) {
            openQuestionPopup('add');
        }
    });

    // События для локаций
    const addZoneBtn = document.getElementById('addZoneBtn');
    if (addZoneBtn) {
        addZoneBtn.addEventListener('click', addZone);
    }

    // Делегирование для динамических кнопок
    document.addEventListener('click', function (e) {
        const target = e.target;

        if (target.classList.contains('add-spot-btn')) {
            const zoneBlock = target.closest('.zone-block');
            if (zoneBlock) addSpot(zoneBlock);
        }

        if (target.classList.contains('remove-zone')) {
            const zoneBlock = target.closest('.zone-block');
            if (zoneBlock) zoneBlock.remove();
        }

        if (target.classList.contains('remove-spot')) {
            const spotBlock = target.closest('.spot-block');
            if (spotBlock) spotBlock.remove();
        }

        if (target.id === 'saveLocationBtn') {
            saveLocation();
        }
    });

    // Предпросмотр и проверка файла (2 МБ, только картинки)
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
            if (!allowedTypes.includes(file.type)) {
                alert('Только изображения (jpg, png, gif)');
                this.value = '';
                return;
            }
            if (file.size > 2 * 1024 * 1024) {
                alert('Максимальный размер 2 МБ');
                this.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = function (e) {
                document.getElementById('previewImg').src = e.target.result;
                document.getElementById('previewImg').style.display = 'block';
                document.getElementById('noImageText').style.display = 'none';
                document.getElementById('removeImageBtn').style.display = 'block';
                document.getElementById('delete_image').value = '0';
            };
            reader.readAsDataURL(file);
        });
    }

    // Кнопка удаления текущей фотки
    const removeImageBtn = document.getElementById('removeImageBtn');
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function () {
            document.getElementById('image').value = '';
            document.getElementById('previewImg').style.display = 'none';
            document.getElementById('noImageText').style.display = 'block';
            this.style.display = 'none';
            document.getElementById('delete_image').value = '1'; // флаг для бэкенда
        });
    }
});