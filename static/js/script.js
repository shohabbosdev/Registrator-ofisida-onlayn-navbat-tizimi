document.addEventListener('DOMContentLoaded', () => {
    // Real vaqt ko‘rsatkichi
    const updateClock = () => {
        const now = new Date();
        const days = ['Yakshanba', 'Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba'];
        const months = ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentyabr', 'Oktyabr', 'Noyabr', 'Dekabr'];
        const dayName = days[now.getDay()];
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const date = now.getDate();
        const month = months[now.getMonth()];
        document.getElementById('clock-display').textContent = `${dayName} ${hours}:${minutes} ${date} ${month}`;
    };
    setInterval(updateClock, 1000);
    updateClock();

    const updateQueueCount = () => {
        fetch('/get_queue_count')
            .then(response => response.json())
            .then(data => {
                const queueCountElement = document.getElementById('queue-count');
                if (queueCountElement) {
                    queueCountElement.textContent = data.count;
                }
            });
    };

    const updateQueueTable = () => {
        fetch('/employee')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newTableBody = doc.querySelector('#queue-table');
                const currentTableBody = document.querySelector('#queue-table');
                if (newTableBody && currentTableBody) {
                    currentTableBody.innerHTML = newTableBody.innerHTML;
                }
            });
    };

    const updateStatsTable = () => {
        fetch('/admin')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newStatsTable = doc.querySelector('#stats-table');
                const currentStatsTable = document.querySelector('#stats-table');
                const newEmployeeStatsTable = doc.querySelector('#employee-stats-table');
                const currentEmployeeStatsTable = document.querySelector('#employee-stats-table');
                if (newStatsTable && currentStatsTable) {
                    currentStatsTable.innerHTML = newStatsTable.innerHTML;
                }
                if (newEmployeeStatsTable && currentEmployeeStatsTable) {
                    currentEmployeeStatsTable.innerHTML = newEmployeeStatsTable.innerHTML;
                }
            });
    };

    // setInterval(() => {
    //     updateQueueCount();
    //     updateQueueTable();
    //     updateStatsTable();
    // }, 5000);
    updateQueueCount();
    updateQueueTable();
    updateStatsTable();

    const queueForm = document.getElementById('queue-form');
    if (queueForm) {
        queueForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(queueForm);
            fetch('/add_to_queue', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    const queueNumber = document.getElementById('queue-number');
                    const createdTime = document.getElementById('created-time');
                    queueNumber.textContent = formatQueueNumber(data.queue_number);
                    createdTime.textContent = new Date().toISOString().replace('T', ' ').split('.')[0];
                    const queueModal = new bootstrap.Modal(document.getElementById('queueModal'));
                    queueModal.show();
                }
            });
        });
    }

    const serveForm = document.getElementById('serve-form');
    if (serveForm) {
        serveForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const queueId = document.getElementById('queue-id').value;
            const formData = new FormData(serveForm);
            fetch(`/serve_queue/${queueId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelector(`tr[data-id="${queueId}"]`).remove();
                    closeServeModal();
                } else {
                    alert(data.error || 'Xatolik yuz berdi');
                }
            });
        });
    }

    const currentTheme = localStorage.getItem('theme') || 'light';
    document.body.classList.toggle('bg-dark', currentTheme === 'dark');
    document.body.classList.toggle('text-white', currentTheme === 'dark');
    updateThemeIcon(currentTheme);
});

function formatQueueNumber(number) {
    return `A${number.toString().padStart(3, '0')}`;
}

function selectService(serviceId) {
    document.getElementById('service_type_id').value = serviceId;
    document.getElementById('submit-btn').disabled = false;
    const buttons = document.querySelectorAll('.service-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
}

function closeModal() {
    const queueModal = bootstrap.Modal.getInstance(document.getElementById('queueModal'));
    queueModal.hide();
}

function openServeModal(queueId) {
    document.getElementById('queue-id').value = queueId;
    const serveModal = new bootstrap.Modal(document.getElementById('serve-modal'));
    serveModal.show();
}

function closeServeModal() {
    const serveModal = bootstrap.Modal.getInstance(document.getElementById('serve-modal'));
    serveModal.hide();
    document.getElementById('serve-form').reset();
}

function changeLanguage(lang) {
    fetch(`/set_language/${lang}`, {
        headers: {
            'Cache-Control': 'no-cache'
        }
    })
        .then(() => {
            window.location.reload(true);
        });
}

function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.body.classList.toggle('bg-dark', newTheme === 'dark');
    document.body.classList.toggle('text-white', newTheme === 'dark');
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

function refreshData() {
    fetch('/admin', {
        headers: {
            'Cache-Control': 'no-cache'
        }
    })
    .then(response => response.text())
    .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newStatsTable = doc.querySelector('#stats-table');
        const currentStatsTable = document.querySelector('#stats-table');
        const newEmployeeStatsTable = doc.querySelector('#employee-stats-table');
        const currentEmployeeStatsTable = document.querySelector('#employee-stats-table');
        if (newStatsTable && currentStatsTable) {
            currentStatsTable.innerHTML = newStatsTable.innerHTML;
        }
        if (newEmployeeStatsTable && currentEmployeeStatsTable) {
            currentEmployeeStatsTable.innerHTML = newEmployeeStatsTable.innerHTML;
        }
    });
}

function serveQueue() {
    const queueId = document.getElementById('queueId').value;
    const firstName = document.getElementById('first_name').value;
    const lastName = document.getElementById('last_name').value;
    const group = document.getElementById('group').value;
    fetch(`/serve_queue/${queueId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `first_name=${encodeURIComponent(firstName)}&last_name=${encodeURIComponent(lastName)}&group=${encodeURIComponent(group)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) throw new Error(data.error);
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('serveModal')).hide();
            location.reload();
        }
    })
    .catch(error => alert("Xatolik: " + error.message));
}

function requeue(queueId) {
    fetch(`/requeue/${queueId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fetch('/employee')
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newTableBody = doc.querySelector('#queue-table');
                    const currentTableBody = document.querySelector('#queue-table');
                    if (newTableBody && currentTableBody) {
                        currentTableBody.innerHTML = newTableBody.innerHTML;
                    }
                });
        } else {
            alert(data.error || 'Xatolik yuz berdi');
        }
    });
}