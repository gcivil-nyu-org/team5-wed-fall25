/**
 * Edit Profile JavaScript
 * Handles photo preview functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Photo preview handler
    const photoInput = document.getElementById('id_profile_photo');
    if (photoInput) {
        photoInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const preview = document.getElementById('photoPreview');
                if (preview) {
                    preview.src = URL.createObjectURL(file);
                    preview.style.display = 'block';
                }
            }
        });
    }
});
