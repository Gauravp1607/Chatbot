document.addEventListener('DOMContentLoaded', () => {
    const adminMenu = document.querySelector('.admin-menu');
    adminMenu?.addEventListener('click', (event) => {
        const link = event.target.closest('a[href^="#"]');
        if (!link) return;

        const target = document.getElementById(link.hash.slice(1));
        if (!target) return;

        event.preventDefault();
        target.classList.add('visible');
        target.querySelectorAll('.reveal').forEach((element) => element.classList.add('visible'));
        adminMenu.querySelectorAll('a').forEach((item) => item.classList.toggle('active', item === link));
        window.history.pushState(null, '', link.hash);
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    const categoryCanvas = document.getElementById('statusChart');
    const usersCanvas = document.getElementById('salesChart');
    const sellers = window.ADMIN_SELLERS || [];
    const categoryData = window.ADMIN_CATEGORY_CHART || { labels: [], values: [] };
    const statusData = window.ADMIN_STATUS_CHART || { labels: [], values: [] };
    const userGrowth = window.ADMIN_USER_GROWTH || { labels: [], values: [] };

    if (usersCanvas && window.Chart) {
        new Chart(usersCanvas, {
            type: 'line',
            data: {
                labels: userGrowth.labels,
                datasets: [{
                    label: 'Users',
                    data: userGrowth.values,
                    borderColor: '#15803d',
                    backgroundColor: 'rgba(34, 197, 94, 0.12)',
                    fill: true,
                    tension: 0.35
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    if (categoryCanvas && window.Chart) {
        new Chart(categoryCanvas, {
            type: 'doughnut',
            data: {
                labels: categoryData.labels,
                datasets: [{
                    data: categoryData.values,
                    backgroundColor: ['#15803d', '#22c55e', '#86efac', '#a7f3d0', '#dcfce7', '#bbf7d0']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    const map = document.getElementById('adminMap');
    if (map && window.L) {
        const leafletMap = L.map('adminMap').setView([22.9707, 72.4857], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(leafletMap);

        sellers.forEach((seller) => {
            if (!seller.latitude || !seller.longitude) return;
            L.marker([seller.latitude, seller.longitude]).addTo(leafletMap)
                .bindPopup(`<strong>${seller.seller_name}</strong><br>Rating: ${seller.rating}`);
        });
    }
});
