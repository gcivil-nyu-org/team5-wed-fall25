// Create Item Form JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Character counter
    const descriptionField = document.querySelector('textarea[name="description"]');
    const charCount = document.getElementById('charCount');

    if (descriptionField && charCount) {
        // Update counter on page load
        charCount.textContent = descriptionField.value.length;
        updateCharCountColor(descriptionField.value.length);

        descriptionField.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length;
            updateCharCountColor(length);
        });
    }

    function updateCharCountColor(length) {
        if (length < 20) {
            charCount.classList.remove('success');
            charCount.classList.add('warning');
        } else {
            charCount.classList.remove('warning');
            charCount.classList.add('success');
        }
    }

    // Image preview functionality
    const imageInput = document.getElementById('id_images');
    const imagePreview = document.getElementById('imagePreview');
    const imageCountDiv = document.getElementById('imageCount');
    let selectedFiles = [];

    if (imageInput && imagePreview && imageCountDiv) {
        imageInput.addEventListener('change', function(e) {
            const files = Array.from(e.target.files);

            if (files.length < 1) {
                alert('Please select at least 1 image.');
                return;
            }
            if (files.length > 10) {
                alert('You can only upload a maximum of 10 images.');
                e.target.value = '';
                return;
            }

            selectedFiles = files;
            imageCountDiv.textContent = `${files.length} image(s) selected`;
            imageCountDiv.classList.add('success');
            imagePreview.innerHTML = '';

            files.forEach((file, index) => {
                if (!file.type.startsWith('image/')) {
                    alert(`${file.name} is not a valid image file.`);
                    return;
                }
                if (file.size > 5 * 1024 * 1024) {
                    alert(`${file.name} exceeds 5MB size limit.`);
                    return;
                }

                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewItem = document.createElement('div');
                    previewItem.className = 'image-preview-item';
                    previewItem.innerHTML = `
                        <img src="${e.target.result}" alt="Preview ${index + 1}">
                        <button type="button" class="remove-btn" data-index="${index}" title="Remove image">×</button>
                    `;
                    imagePreview.appendChild(previewItem);
                };
                reader.readAsDataURL(file);
            });
        });

        // Event delegation for remove buttons
        imagePreview.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-btn')) {
                const index = parseInt(e.target.getAttribute('data-index'));
                removeImage(index);
            }
        });
    }

    function removeImage(index) {
        selectedFiles.splice(index, 1);
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => dataTransfer.items.add(file));
        imageInput.files = dataTransfer.files;
        imageInput.dispatchEvent(new Event('change'));
    }

    // Form submission validation
    const itemForm = document.getElementById('itemForm');
    const submitBtn = document.getElementById('submitBtn');

    if (itemForm && submitBtn) {
        itemForm.addEventListener('submit', function(e) {
            const files = imageInput.files;
            if (files.length < 1) {
                e.preventDefault();
                alert('Please upload at least 1 image.');
                return false;
            }
            if (files.length > 10) {
                e.preventDefault();
                alert('You can only upload a maximum of 10 images.');
                return false;
            }
            submitBtn.disabled = true;
            submitBtn.textContent = 'Posting...';
        });
    }
});
