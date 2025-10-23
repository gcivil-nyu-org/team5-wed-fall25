// profile form JavaScript

    document.getElementById('id_profile_photo').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const preview = document.getElementById('photoPreview');
            preview.src = URL.createObjectURL(file);
            preview.style.display = 'block';
        }
    });
