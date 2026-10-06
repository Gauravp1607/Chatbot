document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chatForm');
    const thread = document.getElementById('chatThread');
    const input = form?.querySelector('[name="question"]');
    const imageInput = document.getElementById('chatImage');
    const uploadImageButton = document.getElementById('uploadImageButton');
    const voiceInputButton = document.getElementById('voiceInputButton');
    const voiceInputLabel = document.getElementById('voiceInputLabel');
    const voiceInputStatus = document.getElementById('voiceInputStatus');
    const welcome = document.getElementById('welcomeScreen');
    const savedChats = document.getElementById('savedChats');
    const savedChatData = document.getElementById('savedChatData');
    let history = [];
    try { history = JSON.parse(savedChatData?.textContent || '[]'); } catch (_) { history = []; }
    const scroll = () => { thread.scrollTop = thread.scrollHeight; };
    const escapeHtml = (value) => String(value || '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
    const markdown = (value) => escapeHtml(value)
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\n[-*]\s+([^\n]+)/g, '<br>• $1')
        .replace(/\n/g, '<br>');
    const speechText = (value) => String(value || '')
        .replace(/```[\s\S]*?```/g, ' ')
        .replace(/<[^>]*>/g, ' ')
        .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
        .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
        .replace(/^\s{0,3}#{1,6}\s*/gm, '')
        .replace(/^\s*[-*+]\s+/gm, '')
        .replace(/^\s*\d+\.\s+/gm, '')
        .replace(/[\\*_~`{}[\]|]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    let activeSpeechButton = null;
    const detectLanguage = (value) => {
        const text = String(value || '').toLowerCase();
        const marathiLatinWords = ['paryant', 'dakhva', 'malak', 'manjar', 'ahe', 'aani', 'madhye', 'tumhi', 'nahi'];
        const hindiLatinWords = ['tak', 'dikhao', 'maalik', 'billi', 'hai', 'aur', 'mein', 'mujhe', 'nahin'];
        const marathiLatinScore = marathiLatinWords.filter((word) => new RegExp(`\\b${word}\\b`).test(text)).length;
        const hindiLatinScore = hindiLatinWords.filter((word) => new RegExp(`\\b${word}\\b`).test(text)).length;
        if (!/[\u0900-\u097f]/.test(text)) return marathiLatinScore > hindiLatinScore ? 'mr-IN' : hindiLatinScore ? 'hi-IN' : 'en-US';
        const marathiWords = ['आहे', 'आणि', 'मध्ये', 'मला', 'तुम्ही', 'नाही', 'करू', 'कृपया', 'शेतकरी', 'जनावर'];
        const hindiWords = ['है', 'और', 'में', 'मुझे', 'आप', 'नहीं', 'करें', 'कृपया', 'किसान', 'जानवर'];
        const marathiScore = marathiWords.filter((word) => text.includes(word)).length;
        const hindiScore = hindiWords.filter((word) => text.includes(word)).length;
        return hindiScore > marathiScore ? 'hi-IN' : 'mr-IN';
    };
    let activeSpeechAudio = null;
    const stopSpeech = () => {
        window.speechSynthesis?.cancel();
        activeSpeechAudio?.pause();
        activeSpeechAudio = null;
        if (activeSpeechButton) {
            activeSpeechButton.textContent = '🔊 Listen';
            activeSpeechButton = null;
        }
    };
    const findVoice = (language) => {
        const voices = window.speechSynthesis.getVoices();
        const prefix = language.split('-')[0].toLowerCase();
        return voices.find((voice) => voice.lang.toLowerCase() === language.toLowerCase() && voice.localService)
            || voices.find((voice) => voice.lang.toLowerCase() === language.toLowerCase())
            || voices.find((voice) => voice.lang.toLowerCase().startsWith(prefix) && voice.localService)
            || voices.find((voice) => voice.lang.toLowerCase().startsWith(prefix))
            || (language === 'mr-IN' && voices.find((voice) => voice.lang.toLowerCase() === 'en-in' && voice.localService));
    };
    const speakResponse = (text, button) => {
        if (!window.speechSynthesis) return;
        if (activeSpeechButton === button) { stopSpeech(); return; }
        stopSpeech();
        const spoken = speechText(text);
        if (!spoken) return;
        const language = detectLanguage(text);
        if (language === 'mr-IN') {
            activeSpeechButton = button;
            button.textContent = '⏸ Stop';
            fetch('/api/ai/speak', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': form.querySelector('[name="csrf_token"]').value }, body: JSON.stringify({ text: spoken, language: 'mr' }) })
                .then((response) => { if (!response.ok) throw new Error('Marathi voice service is temporarily unavailable.'); return response.blob(); })
                .then((blob) => { if (activeSpeechButton !== button) return; activeSpeechAudio = new Audio(URL.createObjectURL(blob)); activeSpeechAudio.onended = () => stopSpeech(); activeSpeechAudio.onerror = () => { button.textContent = '🔊 Marathi audio error'; activeSpeechButton = null; }; return activeSpeechAudio.play(); })
                .catch(() => { if (activeSpeechButton === button) { button.textContent = '🔊 Tap to play Marathi'; activeSpeechButton = null; } });
            return;
        }
        const utterance = new SpeechSynthesisUtterance(spoken);
        utterance.lang = language; utterance.rate = 1; utterance.pitch = 1; utterance.volume = 1;
        activeSpeechButton = button;
        button.textContent = '⏸ Stop';
        let started = false;
        const speak = () => {
            if (activeSpeechButton !== button || started) return;
            started = true;
            const voice = findVoice(language);
            if (voice) utterance.voice = voice;
            utterance.onend = utterance.onerror = () => {
                if (activeSpeechButton === button) { button.textContent = '🔊 Listen'; activeSpeechButton = null; }
            };
            window.speechSynthesis.speak(utterance);
        };
        if (window.speechSynthesis.getVoices().length) speak();
        else {
            window.speechSynthesis.addEventListener('voiceschanged', speak, { once: true });
            window.setTimeout(speak, 700);
        }
    };
    const bubble = (text, role) => {
        const row = document.createElement('div');
        row.className = `chat-message ${role}-message`;
        if (role === 'ai') { const avatar = document.createElement('span'); avatar.className = 'ai-avatar'; avatar.textContent = '✦'; row.append(avatar); }
        const message = document.createElement('div'); message.className = `chat-bubble ${role}`; message.innerHTML = markdown(text);
        if (role === 'ai') {
            const content = document.createElement('div'); content.className = 'ai-response-content';
            const speakButton = document.createElement('button'); speakButton.type = 'button'; speakButton.className = 'voice-output-btn'; speakButton.setAttribute('aria-label', 'Read response aloud'); speakButton.title = 'Read response aloud'; speakButton.textContent = '🔊 Listen';
            speakButton.addEventListener('click', () => speakResponse(text, speakButton));
            content.append(message, speakButton); row.append(content);
        } else row.append(message);
        if (role === 'user') { const avatar = document.createElement('span'); avatar.className = 'user-avatar'; avatar.textContent = 'You'; row.append(avatar); }
        return row;
    };
    const cards = (items) => {
        const grid = document.createElement('div'); grid.className = 'animal-result-grid';
        items.forEach((item) => {
            const card = document.createElement('a'); card.className = 'animal-result-card'; card.href = item.detail_url || `/animal/${encodeURIComponent(item.animal_id)}`;
            const title = document.createElement('strong'); title.textContent = `${item.animal_type || 'Animal'}${item.breed ? ` · ${item.breed}` : ''}`;
            const price = document.createElement('span'); price.textContent = `₹${Number(item.price || 0).toLocaleString('en-IN')}`;
            const details = document.createElement('small'); details.textContent = [item.health_status, item.city, item.state].filter(Boolean).join(' · ');
            const link = document.createElement('em'); link.textContent = 'View details →';
            card.append(title, price, details, link);
            grid.append(card);
        });
        return grid;
    };
    const clearThread = () => {
        thread.querySelectorAll('.chat-message, .animal-result-grid').forEach((node) => node.remove());
        if (welcome) welcome.hidden = false;
        scroll();
    };
    const showSavedChats = () => {
        if (!savedChats) return;
        savedChats.replaceChildren();
        if (!history.length) {
            const empty = document.createElement('p'); empty.className = 'saved-chat-empty'; empty.textContent = 'No saved chats yet.';
            savedChats.append(empty);
        } else {
            [...history].reverse().forEach((item) => {
                const button = document.createElement('button'); button.type = 'button'; button.className = 'saved-chat-item'; button.textContent = item.question;
                button.addEventListener('click', () => {
                    clearThread();
                    if (welcome) welcome.hidden = true;
                    thread.insertBefore(bubble(item.question, 'user'), form);
                    thread.insertBefore(bubble(item.response, 'ai'), form);
                    savedChats.hidden = true;
                    scroll();
                });
                savedChats.append(button);
            });
        }
        savedChats.hidden = !savedChats.hidden;
    };
    document.querySelectorAll('.suggestion-btn').forEach((button) => button.addEventListener('click', () => { input.value = button.textContent.trim(); input.focus(); }));
    document.getElementById('newChat')?.addEventListener('click', () => { clearThread(); input?.focus(); });
    document.getElementById('historyToggle')?.addEventListener('click', showSavedChats);
    uploadImageButton?.addEventListener('click', () => imageInput?.click());
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
        voiceInputButton.disabled = true;
        voiceInputButton.title = 'Voice input is not supported in this browser.';
        voiceInputStatus.textContent = 'Voice input is not supported in this browser.';
    } else {
        const recognition = new Recognition();
        let listening = false;
        recognition.lang = 'mr-IN';
        recognition.interimResults = true; recognition.continuous = false;
        recognition.onstart = () => { listening = true; voiceInputButton.classList.add('is-listening'); voiceInputLabel.textContent = 'Listening...'; voiceInputStatus.textContent = ''; };
        recognition.onresult = (event) => {
            const transcript = Array.from(event.results).map((result) => result[0].transcript).join('');
            input.value = transcript.trim();
            input.dispatchEvent(new Event('input', { bubbles: true }));
        };
        recognition.onerror = (event) => {
            listening = false; voiceInputButton.classList.remove('is-listening'); voiceInputLabel.textContent = 'Speak';
            const status = {
                'not-allowed': 'Microphone permission is required for voice input.',
                'service-not-allowed': 'Microphone permission is required for voice input.',
                'audio-capture': 'No microphone was found. Check your microphone connection.',
                'network': 'Voice input could not connect to the speech service.',
                'no-speech': 'No speech was detected. Please try again.'
            }[event.error] || 'Voice input could not start. Please try again.';
            voiceInputStatus.textContent = status;
            if (event.error === 'not-allowed' || event.error === 'service-not-allowed') alert(status);
        };
        recognition.onnomatch = () => { voiceInputStatus.textContent = 'No speech was detected. Please try again.'; };
        recognition.onend = () => { listening = false; voiceInputButton.classList.remove('is-listening'); voiceInputLabel.textContent = 'Speak'; };
        voiceInputButton.addEventListener('click', () => {
            if (listening) {
                recognition.stop();
                return;
            }
            voiceInputStatus.textContent = 'Starting microphone...';
            try { recognition.start(); } catch (error) {
                listening = false;
                voiceInputStatus.textContent = error.name === 'InvalidStateError' ? 'Voice input is already active.' : 'Voice input could not start. Please try again.';
            }
        });
    }
    
    // Enhanced image preview functionality
    imageInput?.addEventListener('change', () => {
        const file = imageInput.files?.[0];
        const previewContainer = document.getElementById('imagePreviewContainer');
        const previewImg = document.getElementById('imagePreviewImg');
        
        if (file) {
            uploadImageButton.querySelector('span').textContent = file.name;
            uploadImageButton.title = `Selected ${file.name}`;
            
            // Display image preview
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                previewContainer.hidden = false;
                scroll();
            };
            reader.readAsDataURL(file);
        } else {
            previewContainer.hidden = true;
        }
    });
    
    // Remove image button functionality
    document.getElementById('removeImageButton')?.addEventListener('click', (e) => {
        e.preventDefault();
        imageInput.value = '';
        document.getElementById('imagePreviewContainer').hidden = true;
        uploadImageButton.querySelector('span').textContent = 'Add files';
        uploadImageButton.title = 'Add an image file for analysis';
        input?.focus();
    });
    
    input?.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
    form?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const question = input.value.trim();
        const selectedImage = imageInput?.files?.[0];
        if ((!question && !selectedImage) || form.dataset.busy) return;

        form.dataset.busy = 'true';
        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        welcome && (welcome.hidden = true);

        const finalQuestion = question || (selectedImage ? 'Analyze this image.' : '');
        thread.insertBefore(bubble(finalQuestion, 'user'), form); input.value = ''; const thinking = bubble('AI is thinking…', 'ai'); thinking.classList.add('thinking'); thread.insertBefore(thinking, form); scroll();
        try {
            let response;
            if (selectedImage) {
                const formData = new FormData();
                formData.append('message', finalQuestion);
                formData.append('image', selectedImage);
                formData.append('csrf_token', form.querySelector('[name="csrf_token"]').value);
                response = await fetch(form.dataset.endpoint, { method: 'POST', headers: { 'X-CSRF-Token': form.querySelector('[name="csrf_token"]').value }, body: formData });
            } else {
                response = await fetch(form.dataset.endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': form.querySelector('[name="csrf_token"]').value }, body: JSON.stringify({ message: finalQuestion }) });
            }
            const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Unable to get an answer.');
            thinking.replaceWith(bubble(data.message, 'ai'));
            if (data.data?.type === 'animal_results' && Array.isArray(data.data.items) && data.data.items.length) {
                thread.insertBefore(cards(data.data.items), form);
            }
            if (selectedImage) {
                imageInput.value = '';
                document.getElementById('imagePreviewContainer').hidden = true;
                uploadImageButton.querySelector('span').textContent = 'Add files';
                uploadImageButton.title = 'Add an image file for analysis';
            }
            history.push({ question: finalQuestion, response: data.message });
        } catch (error) { thinking.replaceWith(bubble(error.message || 'Please try again.', 'ai')); }
        finally { delete form.dataset.busy; button.disabled = false; input.focus(); scroll(); }
    });
    scroll();
});
