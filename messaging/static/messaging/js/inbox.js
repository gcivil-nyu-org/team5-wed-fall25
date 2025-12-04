// messaging/static/messaging/js/inbox.js
// WebSocket client for real-time inbox updates

document.addEventListener('DOMContentLoaded', function() {
    const conversationsGrid = document.querySelector('.conversations-grid');

    if (!conversationsGrid) return;

    // ===== WebSocket Connection =====
    let socket;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_DELAY = 30000; // 30 seconds

    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/messages/inbox/`;

        socket = new WebSocket(wsUrl);

        socket.onopen = function(e) {
            console.log('Inbox WebSocket connected');
            reconnectAttempts = 0;
        };

        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);

            if (data.type === 'inbox_update') {
                console.log('Inbox update received:', data.thread);
                updateOrAddConversation(data.thread);
            }
        };

        socket.onclose = function(e) {
            console.log('Inbox WebSocket closed, reconnecting...');
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
            reconnectAttempts++;
            setTimeout(connectWebSocket, delay);
        };

        socket.onerror = function(e) {
            console.error('Inbox WebSocket error:', e);
        };
    }

    // Initialize WebSocket connection
    connectWebSocket();

    // ===== Update or Add Conversation =====
    function updateOrAddConversation(threadData) {
        const existingCard = document.querySelector(`[data-thread-id="${threadData.id}"]`);

        if (existingCard) {
            // Update existing conversation card
            updateConversationCard(existingCard, threadData);
            // Move to top of grid
            conversationsGrid.insertBefore(existingCard, conversationsGrid.firstChild);
        } else {
            // Create new conversation card
            const newCard = createConversationCard(threadData);
            conversationsGrid.insertBefore(newCard, conversationsGrid.firstChild);

            // Add slide-in animation
            newCard.style.animation = 'slideInFromTop 0.3s ease-out';
        }
    }

    // ===== Update Existing Card =====
    function updateConversationCard(card, threadData) {
        // Update last message text (in .preview-text)
        const previewText = card.querySelector('.preview-text');
        if (previewText && threadData.last_message) {
            const senderSpan = previewText.querySelector('.preview-sender');
            if (senderSpan) {
                senderSpan.textContent = threadData.last_message.sender_name + ':';
            } else {
                // If no sender span exists, create it
                previewText.innerHTML = `<span class="preview-sender">${escapeHtml(threadData.last_message.sender_name)}:</span> ${escapeHtml(truncateText(threadData.last_message.body, 80))}`;
            }
            // Update just the text after the sender
            const textNode = previewText.childNodes[previewText.childNodes.length - 1];
            if (textNode && textNode.nodeType === Node.TEXT_NODE) {
                textNode.textContent = ' ' + truncateText(threadData.last_message.body, 80);
            }
        }

        // Update timestamp (in .preview-time - update text node after SVG)
        const previewTime = card.querySelector('.preview-time');
        if (previewTime && threadData.last_message) {
            // Find the text node (after the SVG icon)
            const textNode = Array.from(previewTime.childNodes).find(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
            if (textNode) {
                textNode.textContent = ' ' + threadData.last_message.created_at;
            }
        }

        // Update unread badge (in .avatar-badge)
        const avatarBadge = card.querySelector('.avatar-badge');
        if (threadData.unread_count > 0) {
            if (!avatarBadge) {
                // Add unread badge
                const badge = document.createElement('div');
                badge.className = 'avatar-badge';
                badge.textContent = threadData.unread_count;
                const avatarLink = card.querySelector('.conversation-avatar');
                if (avatarLink) {
                    avatarLink.appendChild(badge);
                }
            } else {
                // Update existing badge
                avatarBadge.textContent = threadData.unread_count;
            }
            // Add unread class to card
            card.classList.add('conversation-unread');
        } else {
            // Remove unread badge if count is 0
            if (avatarBadge) {
                avatarBadge.remove();
            }
            card.classList.remove('conversation-unread');
        }

        // Add subtle highlight animation
        card.style.animation = 'highlightCard 0.5s ease-out';
        setTimeout(() => {
            card.style.animation = '';
        }, 500);
    }

    // ===== Create New Conversation Card =====
    function createConversationCard(threadData) {
        const card = document.createElement('div');
        card.className = 'conversation-card';
        card.setAttribute('data-thread-id', threadData.id);

        // Avatar HTML
        let avatarHTML = '';
        if (threadData.other_user.profile_photo_url) {
            avatarHTML = `<img src="${escapeHtml(threadData.other_user.profile_photo_url)}"
                               alt="${escapeHtml(threadData.other_user.name)}"
                               class="conversation-avatar-img">`;
        } else {
            const initials = threadData.other_user.first_initial + threadData.other_user.last_initial;
            avatarHTML = `<div class="conversation-avatar-placeholder">${initials}</div>`;
        }

        // Build card HTML
        card.innerHTML = `
            <div class="conversation-avatar">
                ${avatarHTML}
            </div>
            <div class="conversation-info">
                <div class="conversation-header">
                    <h3 class="conversation-name">${escapeHtml(threadData.other_user.name)}</h3>
                    <span class="conversation-time">${escapeHtml(threadData.updated_at)}</span>
                </div>
                <p class="conversation-listing">
                    ${threadData.related_object.type === 'listing' ? '🏠' : '🛍️'}
                    ${escapeHtml(threadData.related_object.title)}
                </p>
                ${threadData.last_message ? `
                    <p class="last-message">${escapeHtml(truncateText(threadData.last_message.body, 80))}</p>
                ` : ''}
                ${threadData.unread_count > 0 ? `
                    <span class="unread-badge">${threadData.unread_count}</span>
                ` : ''}
            </div>
            <a href="/messages/thread/${threadData.id}/" class="conversation-link">
                <span>Open</span>
                <svg class="conversation-arrow" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
            </a>
        `;

        return card;
    }

    // ===== Helper Functions =====
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
});
