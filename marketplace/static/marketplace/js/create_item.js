// create item JavaScript

  // Character counter
  const descriptionField = document.getElementById('{{ form.description.id_for_label }}');
  const charCount = document.getElementById('charCount');

  descriptionField.addEventListener('input', function() {
    charCount.textContent = this.value.length;
    charCount.style.color = this.value.length < 20 ? '#fca5a5' : '#6ee7b7';
  });

  // Image preview
  const imageInput = document.getElementById('id_images');
  const imagePreview = document.getElementById('imagePreview');
  const imageCountDiv = document.getElementById('imageCount');
  let selectedFiles = [];

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
    imageCountDiv.style.color = '#6ee7b7';
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
    document.getElementById('submitBtn').disabled = true;
    document.getElementById('submitBtn').textContent = 'Posting...';
  });
