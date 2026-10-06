document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('imagesInput');
    const chooseBtn = document.getElementById('chooseFilesBtn');
    const dropZone = document.getElementById('dropZone');
    const previewGrid = document.getElementById('previewGrid');
    const description = document.querySelector('textarea[name="description"]');
    const charCount = document.getElementById('charCount');
    const priceInput = document.querySelector('.price-input');

    const updateCounter = () => {
        if (!description || !charCount) return;
        charCount.textContent = description.value.length;
    };

    if (description) {
        description.addEventListener('input', updateCounter);
        updateCounter();
    }

    if (priceInput) {
        priceInput.addEventListener('blur', () => {
            const raw = priceInput.value.replace(/[^0-9]/g, '');
            if (!raw) return;
            priceInput.value = `₹ ${Number(raw).toLocaleString('en-IN')}`;
        });
    }

    const renderFiles = (files) => {
        if (!previewGrid) return;
        previewGrid.innerHTML = '';
        Array.from(files).slice(0, 10).forEach((file) => {
            const reader = new FileReader();
            reader.onload = (event) => {
                const wrapper = document.createElement('div');
                wrapper.className = 'preview-item';
                wrapper.innerHTML = `<img src="${event.target.result}" alt="Preview">`;
                previewGrid.appendChild(wrapper);
            };
            reader.readAsDataURL(file);
        });
    };

    if (chooseBtn && input) {
        chooseBtn.addEventListener('click', () => input.click());
        input.addEventListener('change', () => renderFiles(input.files));
    }

    if (dropZone && input) {
        dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            dropZone.classList.add('dragging');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragging'));
        dropZone.addEventListener('drop', (event) => {
            event.preventDefault();
            dropZone.classList.remove('dragging');
            input.files = event.dataTransfer.files;
            renderFiles(input.files);
        });
    }
});