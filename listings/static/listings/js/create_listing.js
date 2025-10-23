// Create Listing JavaScript
// Note: This file expects certain element IDs to be passed from the template

function initCreateListing(descriptionFieldId, availabilityStartId, availabilityEndId) {
  // Character counter for description
  const descriptionField = document.getElementById(descriptionFieldId);
  const charCount = document.getElementById('charCount');

  if (descriptionField && charCount) {
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
  let selectedFiles = [];

  if (imageInput) {
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

      if (imageCountDiv) {
        imageCountDiv.textContent = `${files.length} image(s) selected`;
        imageCountDiv.style.color = '#6ee7b7';
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

      const submitBtn = document.getElementById('submitBtn');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Posting...';
      }
    });
  }
}

function removeImage(index) {
  const imageInput = document.getElementById('id_images');
  if (!imageInput) return;

  // This is called from inline onclick, so we need to handle the global selectedFiles
  if (typeof selectedFiles !== 'undefined') {
    selectedFiles.splice(index, 1);
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(file => dataTransfer.items.add(file));
    imageInput.files = dataTransfer.files;
    imageInput.dispatchEvent(new Event('change'));
  }
}
