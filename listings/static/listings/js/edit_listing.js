// Edit Listing JavaScript

function initEditListing(descriptionFieldId, availabilityStartId, availabilityEndId, initialCharCount) {
  // Character counter for description
  const descriptionField = document.getElementById(descriptionFieldId);
  const charCount = document.getElementById('charCount');

  if (descriptionField && charCount) {
    // Update initial count
    charCount.textContent = initialCharCount || descriptionField.value.length;
    if (descriptionField.value.length < 20) {
      charCount.style.color = '#fca5a5';
    } else {
      charCount.style.color = '#6ee7b7';
    }

    descriptionField.addEventListener('input', function() {
      charCount.textContent = this.value.length;
      charCount.style.color = this.value.length < 20 ? '#fca5a5' : '#6ee7b7';
    });
  }

  // Set minimum date for date inputs (today)
  const today = new Date().toISOString().split('T')[0];
  const startField = document.getElementById(availabilityStartId);
  const endField = document.getElementById(availabilityEndId);

  if (startField) startField.setAttribute('min', today);
  if (endField) endField.setAttribute('min', today);

  // Image preview functionality
  const imageInput = document.getElementById('id_images');
  const imagePreview = document.getElementById('imagePreview');
  const imageCountDiv = document.getElementById('imageCount');
  const keepExistingCheckbox = document.getElementById('keep_existing_images');
  let selectedFiles = [];

  // Handle keep existing checkbox
  if (keepExistingCheckbox) {
    keepExistingCheckbox.addEventListener('change', function() {
      if (this.checked) {
        if (imageInput) imageInput.value = '';
        if (imagePreview) imagePreview.innerHTML = '';
        if (imageCountDiv) imageCountDiv.textContent = '';
        selectedFiles = [];
      }
    });
  }

  if (imageInput) {
    imageInput.addEventListener('change', function(e) {
      const files = Array.from(e.target.files);

      if (files.length > 0 && keepExistingCheckbox) {
        keepExistingCheckbox.checked = false;
      }

      if (files.length > 10) {
        alert('You can only upload a maximum of 10 images.');
        e.target.value = '';
        return;
      }

      selectedFiles = files;

      if (imageCountDiv) {
        if (files.length > 0) {
          imageCountDiv.textContent = `${files.length} new image(s) selected`;
          imageCountDiv.style.color = '#6ee7b7';
        } else {
          imageCountDiv.textContent = '';
        }
      }

      if (imagePreview) {
        imagePreview.innerHTML = '';
      }

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
            <button type="button" class="remove-btn" onclick="removeImage(${index})" title="Remove image">×</button>
          `;
          if (imagePreview) {
            imagePreview.appendChild(previewItem);
          }
        };
        reader.readAsDataURL(file);
      });
    });
  }

  // Form submission
  const listingForm = document.getElementById('listingForm');
  if (listingForm) {
    listingForm.addEventListener('submit', function(e) {
      if (imageInput && imageInput.files.length > 10) {
        e.preventDefault();
        alert('You can only upload a maximum of 10 images.');
        return false;
      }

      const submitBtn = document.getElementById('submitBtn');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Updating...';
      }
    });
  }
}

function removeImage(index) {
  const imageInput = document.getElementById('id_images');
  if (!imageInput) return;

  if (typeof selectedFiles !== 'undefined') {
    selectedFiles.splice(index, 1);
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(file => dataTransfer.items.add(file));
    imageInput.files = dataTransfer.files;
    imageInput.dispatchEvent(new Event('change'));
  }
}
