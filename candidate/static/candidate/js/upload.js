/**
 * Upload page — Drag & Drop, File Validation, Progress Animation
 */
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const selectedFile = document.getElementById('selectedFile');
    const fileName = document.getElementById('fileName');
    const removeBtn = document.getElementById('removeFile');
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const spinner = document.getElementById('spinner');
    const progressWrap = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    const ALLOWED = ['application/pdf',
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

    // ── Drag & Drop ──
    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, e => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, e => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', e => {
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) handleFile(fileInput.files[0]);
    });

    function handleFile(file) {
        if (!ALLOWED.includes(file.type)) {
            alert('Only PDF and DOCX files are accepted.');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            alert('File size must be under 10 MB.');
            return;
        }

        // Transfer to hidden input
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;

        fileName.textContent = file.name;
        selectedFile.classList.add('show');
        submitBtn.disabled = false;
    }

    removeBtn.addEventListener('click', e => {
        e.stopPropagation();
        fileInput.value = '';
        selectedFile.classList.remove('show');
        submitBtn.disabled = true;
    });

    // ── Form submit with progress ──
    form.addEventListener('submit', () => {
        submitBtn.disabled = true;
        submitText.textContent = 'Analyzing…';
        spinner.classList.add('show');
        progressWrap.classList.add('show');

        // Fake progress (real upload is synchronous form post)
        let pct = 0;
        const steps = [
            { to: 30, text: 'Uploading resume…' },
            { to: 55, text: 'Extracting text…' },
            { to: 70, text: 'Running NLP analysis…' },
            { to: 85, text: 'Calculating scores…' },
            { to: 95, text: 'Generating report…' },
        ];
        let idx = 0;

        const interval = setInterval(() => {
            if (idx < steps.length) {
                pct = steps[idx].to;
                progressFill.style.width = pct + '%';
                progressText.textContent = steps[idx].text;
                idx++;
            } else {
                clearInterval(interval);
            }
        }, 800);
    });
});
