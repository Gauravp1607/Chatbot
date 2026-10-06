document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const chatThread = document.getElementById('chatThread');

    const scrollToLatest = () => {
        if (chatThread) chatThread.scrollTop = chatThread.scrollHeight;
    };

    scrollToLatest();

    document.querySelectorAll('.suggestion-btn').forEach((button) => {
        button.addEventListener('click', () => {
            const input = document.querySelector('.chat-input-bar input[name="question"]');
            if (input) {
                input.value = button.textContent.trim();
                input.focus();
            }
        });
    });

    if (chatForm && chatThread) {
        chatForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const input = chatForm.querySelector('input[name="question"]');
            const submitButton = chatForm.querySelector('button[type="submit"]');
            const question = input?.value.trim();
            if (!question) return;
            const formData = new FormData(chatForm);
            formData.set('question', question);

            submitButton.disabled = true;
            const userBubble = document.createElement('div');
            userBubble.className = 'chat-bubble user';
            userBubble.textContent = question;
            chatThread.insertBefore(userBubble, chatForm);
            input.value = '';
            scrollToLatest();

            try {
                const response = await fetch(chatForm.action || window.location.pathname, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRF-Token': chatForm.querySelector('input[name="csrf_token"]')?.value || ''
                    },
                    body: new URLSearchParams(formData)
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Unable to get an answer.');
                const aiBubble = document.createElement('div');
                aiBubble.className = 'chat-bubble ai';
                aiBubble.textContent = data.answer;
                chatThread.insertBefore(aiBubble, chatForm);
                scrollToLatest();
            } catch (error) {
                userBubble.remove();
                input.value = question;
                window.alert(error.message);
            } finally {
                submitButton.disabled = false;
                input.focus();
            }
        });
    }
});
