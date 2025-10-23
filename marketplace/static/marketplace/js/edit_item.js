// edit item JavaScript

  const descriptionField = document.getElementById('{{ form.description.id_for_label }}');
  const charCount = document.getElementById('charCount');

  charCount.textContent = descriptionField.value.length;
  charCount.style.color = descriptionField.value.length < 20 ? '#fca5a5' : '#6ee7b7';

  descriptionField.addEventListener('input', function() {
    charCount.textContent = this.value.length;
    charCount.style.color = this.value.length < 20 ? '#fca5a5' : '#6ee7b7';
  });

  const imageInput = document.getElementById('id_images');
  const imagePreview = document.getElementById('imagePreview');
  const imageCountDiv = document.getElementById('imageCount');
  const keepExistingCheckbox = document.getElementById('keep_existing_images');
  let selectedFiles = [];

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
    if (files.length > 0) {
      imageCountDiv.textContent = `${files.length} new image(s) selected`;
      imageCountDiv.style.color = '#6ee7b7';
    } else {
      imageCountDiv.textContent = '';
    }
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
          <button type="button" class="remove-btn" onclick="removeImage(${index})" title="Remove image">×</button>
        `;
        imagePreview.appendChild(previewItem);
      };
      reader.readAsDataURL(file);
    });
  });

  function removeImage(index) {
    selectedFiles.splice(index, 1);
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(file => dataTransfer.items.add(file));
    imageInput.files = dataTransfer.files;
    imageInput.dispatchEvent(new Event('change'));
  }

  document.getElementById('itemForm').addEventListener('submit', function(e) {
    const files = imageInput.files;
    if (files.length > 10) {
      e.preventDefault();
      alert('You can only upload a maximum of 10 images.');
      return false;
    }
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').textContent = 'Updating...';
  });

  // Track removed images
  let removedImages = [];

  function removeCurrentImage(imageId) {
    const imageItem = document.querySelector(`.current-image-item[data-image-id="${imageId}"]`);

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
    document.getElementById('removed_images').value = removedImages.join(',');

    // Update message
    const messageDiv = document.getElementById('current-images-message');
    const countSpan = document.getElementById('removed-count');

    if (removedImages.length > 0) {
        countSpan.textContent = removedImages.length;
        messageDiv.style.display = 'block';
    } else {
        messageDiv.style.display = 'none';
    }
  }

  // Clear the "keep existing images" checkbox behavior since we now handle individual removals
  if (keepExistingCheckbox) {
    keepExistingCheckbox.parentElement.style.display = 'none';
  }
