(function () {
    const modal = document.getElementById('attendance-modal');
    const modalBackdrop = document.getElementById('attendance-modal-backdrop');

    // The script is included by base.html; most pages do not have this modal.
    if (!modal || !modalBackdrop) return;

    const cells = document.querySelectorAll('[data-attendance-cell]');
    if (!cells.length) return;

    const statusSelect = document.getElementById('attendance-modal-status');
    const reasonSelect = document.getElementById('attendance-modal-reason');
    const reasonField = document.getElementById('attendance-modal-reason-field');
    const error = document.getElementById('attendance-modal-error');
    const saveButton = document.getElementById('attendance-modal-save');
    const closeButtons = modal.querySelectorAll('[data-attendance-modal-close]');
    let activeCell = null;
    let previouslyFocusedElement = null;

    function setModalStatus(status) {
        statusSelect.value = status;
        reasonField.hidden = status !== 'absent';
        error.hidden = true;
        error.textContent = 'Выберите причину прогула.';

        if (status === 'absent') {
            reasonSelect.value = (activeCell?.dataset.reasonId || '').trim();
        } else {
            reasonSelect.value = '';
        }
    }

    function openModal(cell) {
        activeCell = cell;
        previouslyFocusedElement = document.activeElement;

        const row = cell.closest('tr');
        const playerName = row?.querySelector('.attendance-player__name');
        const date = cell.querySelector('.attendance-status__date');

        document.getElementById('attendance-modal-player').textContent =
            playerName ? playerName.textContent.trim() : 'Игрок';
        document.getElementById('attendance-modal-date').textContent =
            date ? date.textContent.trim() : '';

        // For an empty cell, make the common action (“Был”) the default.
        // Existing marks remain selected so opening an absence does not
        // silently turn it into attendance if the user simply saves.
        const storedStatus = (cell.dataset.status || 'none').trim();
        const initialStatus = storedStatus === 'none' ? 'present' : storedStatus;
        setModalStatus(initialStatus);

        modal.classList.add('attendance-modal--visible');
        modalBackdrop.classList.add('attendance-modal-backdrop--visible');
        document.body.classList.add('modal-open');
        statusSelect.focus();
    }

    function closeModal() {
        modal.classList.remove('attendance-modal--visible');
        modalBackdrop.classList.remove('attendance-modal-backdrop--visible');
        document.body.classList.remove('modal-open');
        activeCell = null;
        error.hidden = true;

        if (previouslyFocusedElement && typeof previouslyFocusedElement.focus === 'function') {
            previouslyFocusedElement.focus();
        }
        previouslyFocusedElement = null;
    }

    function renderCell(cell, data) {
        cell.dataset.status = data.status || 'none';
        cell.dataset.reasonId = data.reason_id ?? '';
        cell.dataset.reasonName = data.reason_name || '';
        cell.dataset.isValid = String(Boolean(data.is_valid));

        cell.classList.remove(
            'attendance-status-button--present',
            'attendance-status-button--valid-absence',
            'attendance-status-button--absent',
            'attendance-status-button--empty'
        );

        if (data.status === 'present') {
            cell.classList.add('attendance-status-button--present');
        } else if (data.status === 'absent' && data.is_valid) {
            cell.classList.add('attendance-status-button--valid-absence');
        } else if (data.status === 'absent') {
            cell.classList.add('attendance-status-button--absent');
        } else {
            cell.classList.add('attendance-status-button--empty');
        }

        const icon = cell.querySelector('.attendance-status__icon');
        const reason = cell.querySelector('.attendance-status__reason');
        if (icon) {
            icon.textContent = data.status === 'present'
                ? '✓'
                : data.status === 'absent' ? '×' : '—';
        }
        if (reason) {
            reason.textContent = data.status === 'absent' ? (data.reason_name || '') : '';
        }

        cell.title = data.status === 'present'
            ? 'Был'
            : data.status === 'absent'
                ? (data.reason_name ? `Прогул: ${data.reason_name}` : 'Прогул без причины')
                : 'Нет отметки';
    }

    async function saveAttendance() {
        if (!activeCell) return;

        const selectedStatus = statusSelect.value;
        const reasonId = reasonSelect.value;

        if (selectedStatus === 'absent' && !reasonId) {
            error.textContent = 'Выберите причину прогула.';
            error.hidden = false;
            reasonSelect.focus();
            return;
        }

        saveButton.disabled = true;
        try {
            const data = await window.apiRequest('/trainings/attendance', {
                method: 'POST',
                body: JSON.stringify({
                    player_id: Number(activeCell.dataset.playerId),
                    training_id: Number(activeCell.dataset.trainingId),
                    status: selectedStatus,
                    reason_id: selectedStatus === 'absent' ? Number(reasonId) : null
                })
            });

            if (!data) return;
            renderCell(activeCell, data);
            closeModal();
            window.showToast('Отметка сохранена');
        } catch (requestError) {
            error.textContent = requestError.message || 'Не удалось сохранить отметку.';
            error.hidden = false;
        } finally {
            saveButton.disabled = false;
        }
    }

    cells.forEach((cell) => cell.addEventListener('click', () => openModal(cell)));
    statusSelect.addEventListener('change', () => setModalStatus(statusSelect.value));
    saveButton.addEventListener('click', saveAttendance);
    modalBackdrop.addEventListener('click', closeModal);
    closeButtons.forEach((button) => button.addEventListener('click', closeModal));

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.classList.contains('attendance-modal--visible')) {
            closeModal();
        }
    });
})();
