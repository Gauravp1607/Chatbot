document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    document.querySelectorAll('.pay-order-btn').forEach((button) => {
        button.addEventListener('click', async () => {
            button.disabled = true;
            try {
                const response = await fetch(`/payment/create/${button.dataset.orderId}`, {
                    method: 'POST',
                    headers: { 'X-CSRF-Token': csrfToken }
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Unable to start payment.');
                const checkout = new Razorpay({
                    key: data.key_id,
                    amount: data.amount,
                    currency: data.currency,
                    name: 'LivestockAI',
                    description: `Product ₹${Number(data.base_amount).toLocaleString('en-IN')} + platform fee ₹${Number(data.buyer_commission).toLocaleString('en-IN')} = ₹${Number(data.buyer_payable).toLocaleString('en-IN')}`,
                    order_id: data.gateway_order_id,
                    handler: async (payment) => {
                        const verification = await fetch('/payment/verify', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                            body: JSON.stringify({ ...payment, order_id: button.dataset.orderId })
                        });
                        const verificationData = await verification.json();
                        if (!verification.ok || !verificationData.verified) throw new Error(verificationData.error || 'Payment verification failed.');
                        button.textContent = 'Payment successful';
                        button.classList.add('btn-success');
                        button.disabled = true;
                        window.setTimeout(() => window.location.reload(), 600);
                    }
                });
                checkout.open();
            } catch (error) {
                window.alert(error.message);
                button.disabled = false;
            }
        });
    });
});