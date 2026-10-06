function initializeNearbyMap() {
    const nearbyHero = document.querySelector('.nearby-hero');
    const points = nearbyHero?.dataset.mapPoints ? JSON.parse(nearbyHero.dataset.mapPoints) : (window.NEARBY_POINTS || []);
    const location = {
        latitude: Number(nearbyHero?.dataset.userLat || window.NEARBY_LOCATION?.latitude || 18.5204),
        longitude: Number(nearbyHero?.dataset.userLon || window.NEARBY_LOCATION?.longitude || 73.8567)
    };
    const radius = Number(nearbyHero?.dataset.radius || window.NEARBY_RADIUS || 25);
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (window.nearbyMap) {
        window.nearbyMap.remove();
        window.nearbyMap = null;
    }
    let mapElement = document.getElementById('nearbyMap');
    if (!mapElement) {
        const mapPanel = document.querySelector('.nearby-map-panel');
        if (mapPanel) {
            mapPanel.innerHTML = '<div id="nearbyMap" class="nearby-map"></div>';
            mapElement = document.getElementById('nearbyMap');
        }
    }
    if (!mapElement || typeof L === 'undefined') return;
    const map = L.map(mapElement, { scrollWheelZoom: false }).setView([location.latitude, location.longitude], 7);
    window.nearbyMap = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    L.circle([location.latitude, location.longitude], {
        radius: radius * 1000,
        color: '#15803d',
        fillColor: '#22c55e',
        fillOpacity: 0.08,
        weight: 2
    }).addTo(map).bindPopup('Your location');

    if (!window.nearbyLocationWatcher) {
        let locationUpdateTimer;
        const saveLocation = (position) => {
            fetch('/api/location', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ latitude: position.coords.latitude, longitude: position.coords.longitude })
            }).catch(() => {});
        };

        if (navigator.geolocation && csrfToken) {
            window.nearbyLocationWatcher = navigator.geolocation.watchPosition((position) => {
                clearTimeout(locationUpdateTimer);
                locationUpdateTimer = setTimeout(() => saveLocation(position), 1000);
            }, () => {}, { enableHighAccuracy: true, maximumAge: 60000, timeout: 10000 });
        }
    }

    const markers = [];
    points.forEach((point) => {
        if (!point.lat || !point.lng) return;
        const marker = L.marker([point.lat, point.lng]).addTo(map);
        marker.bindPopup(`
            <div style="min-width:180px">
                <strong>${point.name}</strong><br>
                <span>${point.distance_label || `${point.distance_km} km`} away</span><br>
                <span>₹${Math.round(point.price).toLocaleString('en-IN')}</span>
            </div>
        `);
        markers.push(marker);
    });

    if (markers.length) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.25));
    }
}

async function refreshNearbyResults(form) {
    const button = form.querySelector('button[type="submit"]');
    const originalText = button?.textContent;
    if (button) {
        button.disabled = true;
        button.textContent = 'Loading...';
    }

    try {
        const query = new URLSearchParams(new FormData(form));
        const response = await fetch(`${form.action}?${query.toString()}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) throw new Error('Nearby results request failed');
        const documentText = await response.text();
        const parsedPage = new DOMParser().parseFromString(documentText, 'text/html');
        const currentHero = document.querySelector('.nearby-hero');
        const nextHero = parsedPage.querySelector('.nearby-hero');
        const currentLayout = document.querySelector('.nearby-layout');
        const currentList = document.querySelector('.nearby-list-grid');
        const currentPagination = document.querySelector('.pagination-wrap');
        if (!nextHero || !currentLayout || !currentList || !currentPagination) throw new Error('Nearby results markup missing');

        currentHero.dataset.mapPoints = nextHero.dataset.mapPoints;
        currentHero.dataset.userLat = nextHero.dataset.userLat;
        currentHero.dataset.userLon = nextHero.dataset.userLon;
        currentHero.dataset.radius = nextHero.dataset.radius;
        document.querySelector('.nearby-head h1').textContent = parsedPage.querySelector('.nearby-head h1').textContent;
        currentLayout.replaceWith(parsedPage.querySelector('.nearby-layout'));
        currentList.replaceWith(parsedPage.querySelector('.nearby-list-grid'));
        currentPagination.replaceWith(parsedPage.querySelector('.pagination-wrap'));
        document.querySelectorAll('.nearby-layout .reveal, .nearby-list-grid.reveal, .nearby-list-grid .reveal')
            .forEach((element) => element.classList.add('visible'));
        window.history.replaceState({}, '', `${form.action}?${query.toString()}`);
        initializeNearbyMap();
    } catch (error) {
        console.error(error);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = originalText;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeNearbyMap();
});

document.addEventListener('submit', (event) => {
    if (event.target.id !== 'nearby-filter-form') return;
    const filterForm = event.target;
    event.preventDefault();
    refreshNearbyResults(filterForm);
});