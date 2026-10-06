document.addEventListener('DOMContentLoaded', () => {
    const salesCanvas = document.getElementById('salesChart');
    const statusCanvas = document.getElementById('statusChart');
    const salesData = window.SELLER_SALES_DATA || { labels: [], values: [] };
    const statusData = window.SELLER_STATUS_DATA || { labels: [], values: [] };

    if (salesCanvas && window.Chart) {
        new Chart(salesCanvas, {
            type: 'line',
            data: {
                labels: salesData.labels,
                datasets: [{
                    label: 'Revenue',
                    data: salesData.values,
                    borderColor: '#15803d',
                    backgroundColor: 'rgba(34, 197, 94, 0.12)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    if (statusCanvas && window.Chart) {
        new Chart(statusCanvas, {
            type: 'doughnut',
                data: {
                labels: statusData.labels,
                datasets: [{
                    data: statusData.values,
                    backgroundColor: ['#15803d', '#22c55e', '#86efac', '#d1fae5']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
});
