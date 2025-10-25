// listings/static/listings/js/message_modal.js
// JavaScript for contact seller message modal functionality

/**
 * Show the message modal
 */
function showMessageForm() {
    const modal = document.getElementById('messageModal');
    if (modal) {
        modal.classList.add('active');
        // Focus on textarea for better UX
        const textarea = modal.querySelector('textarea');
        if (textarea) {
            setTimeout(() => textarea.focus(), 100);
        }
    }
}

/**
 * Hide the message modal
 */
function hideMessageForm() {
    const modal = document.getElementById('messageModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Initialize modal event listeners when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('messageModal');

    if (modal) {
        // Close modal when clicking outside (on the overlay)
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                hideMessageForm();
            }
        });

        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                hideMessageForm();
            }
        });
    }
});
