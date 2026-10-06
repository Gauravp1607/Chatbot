document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    const resources = {
        users: { body: 'admin-users-body', columns: (item) => `<td>${item.full_name}<br><small>${item.email}</small></td><td>${item.role}</td><td>${item.status}</td><td><button class="btn btn-view" data-action="suspend-user" data-id="${item.user_id}">${item.status === 'Suspended' ? 'Activate' : 'Suspend'}</button></td>` },
        sellers: { body: 'admin-sellers-body', columns: (item) => `<td>${item.shop_name}<br><small>${item.city || ''}</small></td><td>${item.rating || '0'}</td><td>${item.verified ? 'Yes' : 'No'}</td><td><button class="btn btn-view" data-action="verify-seller" data-id="${item.seller_id}">${item.verified ? 'Unverify' : 'Verify'}</button></td>` },
        animals: { body: 'admin-animals-body', columns: (item) => `<td>${item.animal_type} ${item.breed}</td><td>Rs. ${Number(item.price).toLocaleString('en-IN')}</td><td>${item.availability}</td><td><button class="btn btn-view" data-action="remove-animal" data-id="${item.animal_id}">Delete</button></td>` },
        reports: { body: 'admin-reports-body', columns: (item) => `<td>${item.reason}</td><td>${item.status}</td><td>${item.created_at}</td><td><button class="btn btn-view" data-action="resolve-report" data-id="${item.report_id}">Resolve</button></td>` }
    };

    async function load(resource) {
        const response = await fetch(`/admin/api/${resource}`);
        if (!response.ok) return;
        const items = await response.json();
        const config = resources[resource];
        document.getElementById(config.body).innerHTML = items.map((item) => `<tr>${config.columns(item)}</tr>`).join('') || '<tr><td colspan="4">No records found.</td></tr>';
    }

    async function mutate(url, method, body) {
        const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }, body: JSON.stringify(body) });
        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            window.alert(result.error || 'The action could not be completed.');
        }
    }

    Object.keys(resources).forEach(load);
    document.querySelectorAll('.admin-refresh').forEach((button) => button.addEventListener('click', () => load(button.dataset.resource)));
    document.addEventListener('click', async (event) => {
        const button = event.target.closest('[data-action]');
        if (!button) return;
        const id = button.dataset.id;
        if (button.dataset.action === 'suspend-user') {
            const status = button.closest('tr').children[2].textContent.trim() === 'Suspended' ? 'Active' : 'Suspended';
            await mutate(`/admin/api/users/${id}`, 'PATCH', { status });
            load('users');
        } else if (button.dataset.action === 'verify-seller') {
            await mutate(`/admin/api/sellers/${id}`, 'PATCH', { verified: button.textContent.trim() === 'Verify' });
            load('sellers');
        } else if (button.dataset.action === 'remove-animal' && window.confirm('Delete this listing?')) {
            await mutate(`/admin/api/animals/${id}`, 'DELETE', {});
            load('animals');
        } else if (button.dataset.action === 'resolve-report') {
            await mutate(`/admin/api/reports/${id}`, 'PATCH', { status: 'Resolved', admin_action: 'Resolved from admin dashboard' });
            load('reports');
        }
    });
});
