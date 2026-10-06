document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('diseaseDropZone');
    const fileInput = document.getElementById('diseaseImageInput');
    const chooseButton = document.getElementById('chooseDiseaseImage');
    const previewBox = document.getElementById('diseasePreviewBox');
    const previewImage = document.getElementById('diseasePreviewImage');

    const renderPreview = (file) => {
        if (!file || !previewBox || !previewImage) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            previewImage.src = event.target.result;
            previewBox.classList.add('show');
        };
        reader.readAsDataURL(file);
    };

    if (chooseButton && fileInput) {
        chooseButton.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) renderPreview(fileInput.files[0]);
        });
    }

    if (dropZone && fileInput) {
        dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            dropZone.classList.add('dragging');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragging');
        });

        dropZone.addEventListener('drop', (event) => {
            event.preventDefault();
            dropZone.classList.remove('dragging');
            const files = event.dataTransfer.files;
            if (!files || !files.length) return;

            const dt = new DataTransfer();
            dt.items.add(files[0]);
            fileInput.files = dt.files;
            renderPreview(files[0]);
        });
    }
});
