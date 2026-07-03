// SuperfastSync - Upload functionality with drag-and-drop

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    // Click to upload
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });

    // Drag and drop events
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // Delete buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-btn')) {
            const filename = e.target.getAttribute('data-filename');
            deleteFile(filename, e.target);
        }
    });

    function handleFiles(files) {
        if (files.length === 0) return;

        // Clear previous status
        uploadStatus.innerHTML = '';

        // Upload each file
        Array.from(files).forEach(file => {
            uploadFile(file);
        });
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Create progress element
        const progressDiv = document.createElement('div');
        progressDiv.className = 'upload-progress';
        progressDiv.innerHTML = `
            <p>Uploading: ${file.name} (${formatFileSize(file.size)})</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
        `;
        uploadStatus.appendChild(progressDiv);

        const progressFill = progressDiv.querySelector('.progress-fill');

        // Create XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
            }
        });

        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                progressDiv.className = 'upload-complete';
                progressDiv.innerHTML = `
                    <p>✓ ${file.name} uploaded successfully!</p>
                    <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                        Speed: ${response.speed_mbps} Mbps |
                        Duration: ${response.duration.toFixed(2)}s
                    </p>
                `;

                // Reload page after a short delay to show the new file
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                const error = JSON.parse(xhr.responseText);
                progressDiv.className = 'upload-error';
                progressDiv.innerHTML = `
                    <p>✗ Failed to upload ${file.name}</p>
                    <p style="font-size: 0.875rem;">${error.error || 'Unknown error'}</p>
                `;
            }
        });

        xhr.addEventListener('error', function() {
            progressDiv.className = 'upload-error';
            progressDiv.innerHTML = `
                <p>✗ Network error uploading ${file.name}</p>
            `;
        });

        xhr.open('POST', '/upload', true);
        xhr.send(formData);
    }

    function deleteFile(filename, button) {
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
            return;
        }

        button.disabled = true;
        button.textContent = 'Deleting...';

        fetch(`/delete/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the file card from the DOM
                const fileCard = button.closest('.file-card');
                fileCard.style.opacity = '0';
                setTimeout(() => {
                    fileCard.remove();

                    // Check if there are no more files
                    const filesGrid = document.querySelector('.files-grid');
                    if (filesGrid && filesGrid.children.length === 0) {
                        window.location.reload();
                    }
                }, 300);
            } else {
                alert(`Failed to delete file: ${data.error}`);
                button.disabled = false;
                button.textContent = 'Delete';
            }
        })
        .catch(error => {
            alert(`Error deleting file: ${error}`);
            button.disabled = false;
            button.textContent = 'Delete';
        });
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
});
