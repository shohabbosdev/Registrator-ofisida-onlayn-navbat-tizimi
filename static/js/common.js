function updateQueueData(url, containerId, isEmployee = false) {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Yangilashda xatolik:', data.error);
                return;
            }
            const container = document.querySelector(containerId);
            if (isEmployee) {
                container.querySelector('tbody').innerHTML = data.html;
            } else {
                container.innerHTML = data.html;
            }
        })
        .catch(error => console.error('Yangilashda xatolik:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('#queueContainer')) {
        updateQueueData('/get_queue_data', '#queueContainer');
        setInterval(() => updateQueueData('/get_queue_data', '#queueContainer'), 5000);
    }
    if (document.querySelector('#employeeQueueContainer')) {
        updateQueueData('/get_employee_queue_data', '#employeeQueueContainer', true);
        setInterval(() => updateQueueData('/get_employee_queue_data', '#employeeQueueContainer', true), 5000);
    }
});