// Edit Item JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Character counting for description field
  const descriptionField = document.querySelector('textarea[name="description"]');
  const charCount = document.getElementById('charCount');

  if (descriptionField && charCount) {
    charCount.textContent = descriptionField.value.length;
    charCount.style.color = descriptionField.value.length < 20 ? '#fca5a5' : '#6ee7b7';

    descriptionField.addEventListener('input', function() {
      charCount.textContent = this.value.length;
      charCount.style.color = this.value.length < 20 ? '#fca5a5' : '#6ee7b7';
    });
  }

  // Image upload handling
  const imageInput = document.getElementById('id_images');
  const imagePreview = document.getElementById('imagePreview');
  const imageCountDiv = document.getElementById('imageCount');
  const keepExistingCheckbox = document.getElementById('keep_existing_images');
  let selectedFiles = [];

  // Handle keep existing images checkbox
  if (keepExistingCheckbox) {
    keepExistingCheckbox.addEventListener('change', function() {
      if (this.checked) {
        imageInput.value = '';
        imagePreview.innerHTML = '';
        imageCountDiv.textContent = '';
        selectedFiles = [];
      }
    });
  }

  // Handle new image selection
  if (imageInput) {
    imageInput.addEventListener('change', function(e) {
      const files = Array.from(e.target.files);

      // Uncheck keep existing if new files selected
      if (files.length > 0 && keepExistingCheckbox) {
        keepExistingCheckbox.checked = false;
      }

      // Validate max 10 images
      if (files.length > 10) {
        alert('You can only upload a maximum of 10 images.');
        e.target.value = '';
        return;
      }

      selectedFiles = files;

      // Update image count display
      if (files.length > 0) {
        imageCountDiv.textContent = `${files.length} new image(s) selected`;
        imageCountDiv.style.color = '#6ee7b7';
      } else {
        imageCountDiv.textContent = '';
      }

      // Clear and rebuild preview
      imagePreview.innerHTML = '';

      files.forEach((file, index) => {
        // Validate file type
        if (!file.type.startsWith('image/')) {
          alert(`${file.name} is not a valid image file.`);
          return;
        }

        // Validate file size (5MB limit)
        if (file.size > 5 * 1024 * 1024) {
          alert(`${file.name} exceeds 5MB size limit.`);
          return;
        }

        // Create preview
        const reader = new FileReader();
        reader.onload = function(e) {
          const previewItem = document.createElement('div');
          previewItem.className = 'image-preview-item';
          previewItem.innerHTML = `
            <img src="${e.target.result}" alt="Preview ${index + 1}">
            <button type="button" class="remove-btn" onclick="removeImage(${index})" title="Remove image">×</button>
          `;
          imagePreview.appendChild(previewItem);
        };
        reader.readAsDataURL(file);
      });
    });
  }

  // Handle form submission
  const itemForm = document.getElementById('itemForm');
  const submitBtn = document.getElementById('submitBtn');

  if (itemForm && submitBtn) {
    itemForm.addEventListener('submit', function(e) {
      const files = imageInput.files;
      if (files.length > 10) {
        e.preventDefault();
        alert('You can only upload a maximum of 10 images.');
        return false;
      }
      submitBtn.disabled = true;
      submitBtn.textContent = 'Updating...';
    });
  }

  // Track removed current images
  let removedImages = [];

  // Make removeCurrentImage available globally
  window.removeCurrentImage = function(imageId) {
    const imageItem = document.querySelector(`.current-image-item[data-image-id="${imageId}"]`);

    if (!imageItem) return;

    if (imageItem.classList.contains('marked-for-removal')) {
      // Unmark for removal
      imageItem.classList.remove('marked-for-removal');
      removedImages = removedImages.filter(id => id !== imageId);
    } else {
      // Mark for removal
      imageItem.classList.add('marked-for-removal');
      removedImages.push(imageId);
    }

    // Update hidden input
    const removedImagesInput = document.getElementById('removed_images');
    if (removedImagesInput) {
      removedImagesInput.value = removedImages.join(',');
    }

    // Update message
    const messageDiv = document.getElementById('current-images-message');
    const countSpan = document.getElementById('removed-count');

    if (messageDiv && countSpan) {
      if (removedImages.length > 0) {
        countSpan.textContent = removedImages.length;
        messageDiv.style.display = 'block';
      } else {
        messageDiv.style.display = 'none';
      }
    }
  };

  // Make removeImage available globally for new image previews
  window.removeImage = function(index) {
    selectedFiles.splice(index, 1);
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(file => dataTransfer.items.add(file));
    imageInput.files = dataTransfer.files;
    imageInput.dispatchEvent(new Event('change'));
  };

  // Hide keep existing images checkbox since we handle individual removals
  if (keepExistingCheckbox && keepExistingCheckbox.parentElement) {
    keepExistingCheckbox.parentElement.style.display = 'none';
  }
});
