// static/js/messaging-badge.js
// Global WebSocket for real-time unread message badge updates

document.addEventListener('DOMContentLoaded', function() {
    // Only run if user is authenticated (check if unread-badge exists)
    const badge = document.getElementById('unread-badge');
    if (!badge) return;

    let socket;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_DELAY = 30000; // 30 seconds

    function connectInboxWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/messages/inbox/`;

        socket = new WebSocket(wsUrl);

        socket.onopen = function(e) {
            console.log('[Badge] Inbox WebSocket connected');
            reconnectAttempts = 0;
        };

        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);

            if (data.type === 'inbox_update') {
                console.log('[Badge] Inbox update received:', data.thread);
                updateUnreadBadge();
            }
        };

        socket.onclose = function(e) {
            console.log('[Badge] Inbox WebSocket closed, reconnecting...');
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
            reconnectAttempts++;
            setTimeout(connectInboxWebSocket, delay);
        };

        socket.onerror = function(e) {
            console.error('[Badge] Inbox WebSocket error:', e);
        };
    }

    function updateUnreadBadge() {
        // Fetch updated unread count from backend
        fetch('/messages/unread-count/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            const count = data.count;
            const badge = document.getElementById('unread-badge');

            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline-block';

                // Add pulse animation
                badge.style.animation = 'none';
                setTimeout(() => {
                    badge.style.animation = 'pulse-badge 2s infinite';
                }, 10);
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('[Badge] Error fetching unread count:', error);
        });
    }

    // Initialize WebSocket connection
    connectInboxWebSocket();

    // Also update badge when returning to inbox page (marks as read)
    // Listen for page visibility changes
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            updateUnreadBadge();
        }
    });
});
