// static/js/stability.js
document.addEventListener('DOMContentLoaded', function() {
    const controlTypeSelect = document.getElementById('control-type');
    const imageUploadArea = document.querySelector('.image-upload-area');
    const controlStrength = document.querySelector('.control-strength');
    
    if (controlTypeSelect) {
        controlTypeSelect.addEventListener('change', function() {
            const showImageUpload = ['sketch', 'structure'].includes(this.value);
            imageUploadArea.style.display = showImageUpload ? 'block' : 'none';
            controlStrength.style.display = showImageUpload ? 'block' : 'none';
        });
    }

    const fileInput = document.getElementById('stability-file-input');
    const previewDiv = document.getElementById('stability-image-preview');
    
    if (fileInput && previewDiv) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewDiv.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; max-height: 300px;">`;
                };
                reader.readAsDataURL(file);
            } else {
                previewDiv.innerHTML = '';
            }
        });
    }
});

// Helper function to display generated images
function displayGeneratedImage(response) {
    const resultsDiv = document.getElementById('stability-results');
    if (response.type.startsWith('image/')) {
        const blob = new Blob([response], { type: response.type });
        const imageUrl = URL.createObjectURL(blob);
        resultsDiv.innerHTML = `<img src="${imageUrl}" alt="Generated image" style="max-width: 100%;">`;
    } else {
        resultsDiv.innerHTML = '<div class="error">Error generating image</div>';
    }
}