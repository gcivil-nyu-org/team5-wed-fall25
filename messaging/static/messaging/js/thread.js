// messaging/static/messaging/js/thread.js
// JavaScript for thread/chat page enhancements

document.addEventListener('DOMContentLoaded', function() {
    // ===== Elements =====
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = document.getElementById('messageInput');
    const messageForm = document.getElementById('messageForm');

    // ===== Auto-scroll to Latest Message =====
    function scrollToBottom(smooth = true) {
        if (messagesContainer) {
            const scrollOptions = {
                top: messagesContainer.scrollHeight,
                behavior: smooth ? 'smooth' : 'auto'
            };
            messagesContainer.scrollTo(scrollOptions);
        }
    }

    // Scroll to bottom on page load (after a small delay to ensure content is rendered)
    if (messagesContainer) {
        setTimeout(() => scrollToBottom(false), 100);
    }

    // ===== Auto-expanding Textarea =====
    if (messageInput) {
        // Focus on input when page loads
        messageInput.focus();

        // Auto-expand textarea as user types
        function autoExpand() {
            // Reset height to auto to get the correct scrollHeight
            this.style.height = 'auto';

            // Calculate new height (with max limit)
            const maxHeight = 150; // matches CSS max-height
            const newHeight = Math.min(this.scrollHeight, maxHeight);

            // Set new height
            this.style.height = newHeight + 'px';
        }

        // Listen for input events
        messageInput.addEventListener('input', autoExpand);

        // Listen for Enter key (send on Enter, new line on Shift+Enter)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                messageForm.submit();
            }
        });
    }

    // ===== Form Submit Handler =====
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            // Disable send button temporarily to prevent double-sending
            const sendButton = messageForm.querySelector('.send-button');
            if (sendButton) {
                sendButton.disabled = true;

                // Re-enable after form submission
                setTimeout(() => {
                    sendButton.disabled = false;
                }, 1000);
            }
        });
    }

    // ===== Scroll to Bottom on New Message (if near bottom) =====
    // This is useful if messages are loaded dynamically via AJAX in the future
    const observer = new MutationObserver(function(mutations) {
        if (messagesContainer) {
            const isNearBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 100;

            if (isNearBottom) {
                scrollToBottom(true);
            }
        }
    });

    // Observe messages container for new messages
    if (messagesContainer) {
        observer.observe(messagesContainer, {
            childList: true,
            subtree: true
        });
    }
});
