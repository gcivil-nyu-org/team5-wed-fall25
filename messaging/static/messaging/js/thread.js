// messaging/static/messaging/js/thread.js
// JavaScript for thread/chat page enhancements with AJAX polling

document.addEventListener('DOMContentLoaded', function() {
    // ===== Elements =====
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = document.getElementById('messageInput');
    const messageForm = document.getElementById('messageForm');

    if (!messagesContainer) return;

    // Get thread and user info from data attributes
    const threadId = messagesContainer.dataset.threadId;
    const currentUserId = parseInt(messagesContainer.dataset.currentUserId);

    // Track the last message ID we've seen
    let lastMessageId = 0;

    // Initialize lastMessageId from existing messages
    function initializeLastMessageId() {
        const messageRows = messagesContainer.querySelectorAll('.message-row[data-message-id]');
        if (messageRows.length > 0) {
            // Find the highest message ID
            messageRows.forEach(row => {
                const messageId = parseInt(row.dataset.messageId);
                if (messageId > lastMessageId) {
                    lastMessageId = messageId;
                }
            });
        }
    }

    initializeLastMessageId();

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

    // Check if user is near bottom of messages
    function isNearBottom() {
        if (!messagesContainer) return false;
        const threshold = 100;
        return messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold;
    }

    // Scroll to bottom on page load
    setTimeout(() => scrollToBottom(false), 100);

    // ===== Create Message HTML =====
    function createMessageHTML(message) {
        const isSent = message.is_current_user;
        const messageClass = isSent ? 'message-sent' : 'message-received';

        // Create avatar HTML
        let avatarHTML = '';
        if (message.profile_photo_url) {
            avatarHTML = `<img src="${message.profile_photo_url}" alt="${message.sender_name}" class="message-avatar-image">`;
        } else {
            const initials = message.sender_first_initial + message.sender_last_initial;
            avatarHTML = `<div class="message-avatar-placeholder">${initials}</div>`;
        }

        // Build message row HTML
        let html = `<div class="message-row ${messageClass}" data-message-id="${message.id}">`;

        // Avatar on left for received messages
        if (!isSent) {
            html += `<div class="message-avatar">${avatarHTML}</div>`;
        }

        // Message bubble
        html += `
            <div class="message-content">
                <div class="message-bubble">
                    <p class="message-text">${escapeHtml(message.body)}</p>
                    <div class="message-meta">
                        <span class="message-sender">${escapeHtml(message.sender_name)}</span>
                        <span class="message-separator">•</span>
                        <span class="message-time">${escapeHtml(message.created_at)}</span>
                    </div>
                </div>
            </div>
        `;

        // Avatar on right for sent messages
        if (isSent) {
            html += `<div class="message-avatar">${avatarHTML}</div>`;
        }

        html += `</div>`;

        return html;
    }

    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== Poll for New Messages =====
    function pollNewMessages() {
        // Only poll if page is visible
        if (document.hidden) return;

        const url = `/messages/thread/${threadId}/get-new-messages/?last_message_id=${lastMessageId}`;

        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.messages && data.messages.length > 0) {
                const shouldScroll = isNearBottom();

                // Append new messages to the container
                data.messages.forEach(message => {
                    const messageHTML = createMessageHTML(message);
                    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);

                    // Update last message ID
                    if (message.id > lastMessageId) {
                        lastMessageId = message.id;
                    }
                });

                // Scroll to bottom if user was near bottom
                if (shouldScroll) {
                    scrollToBottom(true);
                }
            }
        })
        .catch(error => {
            console.error('Error polling for new messages:', error);
        });
    }

    // Start polling every 2 seconds
    const pollInterval = setInterval(pollNewMessages, 2000);

    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        clearInterval(pollInterval);
    });

    // ===== Auto-expanding Textarea =====
    if (messageInput) {
        // Focus on input when page loads
        messageInput.focus();

        // Auto-expand textarea as user types
        function autoExpand() {
            this.style.height = 'auto';
            const maxHeight = 150;
            const newHeight = Math.min(this.scrollHeight, maxHeight);
            this.style.height = newHeight + 'px';
        }

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

                // Re-enable after a delay
                setTimeout(() => {
                    sendButton.disabled = false;
                }, 1000);
            }

            // After form submission completes, poll immediately for the new message
            setTimeout(() => {
                pollNewMessages();
            }, 500);
        });
    }
});
