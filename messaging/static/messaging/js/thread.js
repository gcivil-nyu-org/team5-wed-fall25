// messaging/static/messaging/js/thread.js
// JavaScript for thread/chat page with WebSocket real-time messaging

document.addEventListener('DOMContentLoaded', function() {
    // ===== Elements =====
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = document.getElementById('messageInput');
    const messageForm = document.getElementById('messageForm');

    if (!messagesContainer) return;

    // Get thread and user info from data attributes
    const threadId = messagesContainer.dataset.threadId;
    const currentUserId = parseInt(messagesContainer.dataset.currentUserId);

    // ===== WebSocket Connection =====
    let socket;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_DELAY = 30000; // 30 seconds

    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/messages/thread/${threadId}/`;

        socket = new WebSocket(wsUrl);

        socket.onopen = function(e) {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
        };

        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);

            if (data.type === 'chat_message') {
                console.log('WebSocket received message:', {
                    id: data.message.id,
                    sender_id: data.message.sender_id,
                    is_current_user: data.message.is_current_user,
                    current_user_id: currentUserId
                });

                const shouldScroll = isNearBottom();
                const messageHTML = createMessageHTML(data.message);
                messagesContainer.insertAdjacentHTML('beforeend', messageHTML);

                if (shouldScroll) {
                    scrollToBottom(true);
                }
            } else if (data.type === 'typing_indicator') {
                handleTypingIndicator(data);
            }
        };

        socket.onclose = function(e) {
            console.log('WebSocket closed, reconnecting...');
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
            reconnectAttempts++;
            setTimeout(connectWebSocket, delay);
        };

        socket.onerror = function(e) {
            console.error('WebSocket error:', e);
        };
    }

    // Initialize WebSocket connection
    connectWebSocket();

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

    // ===== Typing Indicator Handler (for Phase 3) =====
    function handleTypingIndicator(data) {
        // Placeholder for Phase 3 implementation
        // Will show "User is typing..." indicator
    }

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
                // Trigger submit event (not direct submission) so our handler can intercept
                messageForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
        });
    }

    // ===== Form Submit Handler =====
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const body = messageInput.value.trim();
            if (!body || !socket || socket.readyState !== WebSocket.OPEN) return;

            // Send message via WebSocket
            socket.send(JSON.stringify({
                'type': 'chat_message',
                'body': body
            }));

            // Clear input and reset height
            messageInput.value = '';
            messageInput.style.height = 'auto';

            // Disable send button temporarily to prevent double-sending
            const sendButton = messageForm.querySelector('.send-button');
            if (sendButton) {
                sendButton.disabled = true;
                setTimeout(() => {
                    sendButton.disabled = false;
                }, 1000);
            }
        });
    }
});
