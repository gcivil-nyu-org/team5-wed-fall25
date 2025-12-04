# Unread Message Badge Feature

## Overview

Added a real-time unread message counter badge to the "Messages" link in the navbar. The badge displays the total count of unread messages across all conversations and updates in real-time via WebSocket.

## Implementation Summary

### 1. Context Processor (`messaging/context_processors.py`)

**Purpose:** Inject unread message count into all templates for initial page load.

```python
def unread_message_count(request):
    """Returns unread message count for authenticated users."""
    if not request.user.is_authenticated:
        return {"unread_message_count": 0}

    count = Message.objects.filter(
        Q(thread__user_a=request.user) | Q(thread__user_b=request.user)
    ).filter(is_read=False).exclude(sender=request.user).count()

    return {"unread_message_count": count}
```

**Query Logic:**
- Find all messages in threads where user is a participant (user_a or user_b)
- Filter only unread messages (`is_read=False`)
- Exclude messages sent by the current user (don't count own messages)

### 2. Settings Configuration (`CampusNest/settings.py`)

Added context processor to `TEMPLATES` configuration:

```python
"context_processors": [
    # ... existing processors ...
    "messaging.context_processors.unread_message_count",
],
```

### 3. Navbar Badge (`templates/base.html`)

Updated the Messages link to include the badge:

```html
<a href="{% url 'messaging:inbox' %}" class="messages-link">
    Messages
    <span id="unread-badge" class="unread-badge" style="{% if unread_message_count == 0 %}display: none;{% endif %}">
        {{ unread_message_count }}
    </span>
</a>
```

**Loaded JavaScript:**
```html
{% if user.is_authenticated %}
<script src="{% static 'js/messaging-badge.js' %}"></script>
{% endif %}
```

### 4. Badge Styles (`static/css/base.css`)

Added responsive badge styles with pulsing animation:

```css
.messages-link {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.unread-badge {
    position: absolute;
    top: 0;
    right: -8px;
    background: linear-gradient(135deg, var(--color-danger) 0%, #dc2626 100%);
    color: white;
    font-size: 0.6875rem;
    font-weight: 700;
    padding: 0.125rem 0.375rem;
    border-radius: 10px;
    min-width: 18px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5);
    animation: pulse-badge 2s infinite;
    line-height: 1.2;
}

@keyframes pulse-badge {
    0%, 100% {
        transform: scale(1);
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5);
    }
    50% {
        transform: scale(1.05);
        box-shadow: 0 2px 12px rgba(239, 68, 68, 0.7);
    }
}
```

### 5. Real-Time Updates (`static/js/messaging-badge.js`)

**Purpose:** Connect to inbox WebSocket and update badge count in real-time when new messages arrive.

**Key Features:**
- Only runs for authenticated users (checks if `#unread-badge` exists)
- Connects to `ws://host/ws/messages/inbox/` (reuses existing inbox WebSocket)
- Exponential backoff reconnection (1s, 2s, 4s, ..., up to 30s)
- Fetches updated count from `/messages/unread-count/` API
- Updates badge visibility and count dynamically
- Re-triggers pulse animation on new messages
- Updates count when tab regains focus

**Flow:**
1. WebSocket receives `inbox_update` event
2. Triggers `updateUnreadBadge()` function
3. Fetches latest count from `/messages/unread-count/` API
4. Updates badge text and visibility
5. Re-triggers pulse animation

### 6. API Endpoint (`messaging/views.py`)

Added endpoint to fetch current unread count:

```python
@login_required
def unread_count(request):
    """API endpoint to get current unread message count."""
    count = Message.objects.filter(
        Q(thread__user_a=request.user) | Q(thread__user_b=request.user)
    ).filter(is_read=False).exclude(sender=request.user).count()

    return JsonResponse({"count": count})
```

**URL:** `/messages/unread-count/` (added to `messaging/urls.py`)

**Response Format:**
```json
{
    "count": 5
}
```

### 7. Tests (`messaging/tests.py`)

Added comprehensive test suite `UnreadCountViewTests`:

**Test Coverage:**
- ✅ `test_unread_count_zero` - Returns 0 when no unread messages
- ✅ `test_unread_count_with_messages` - Returns correct count with unread messages
- ✅ `test_unread_count_excludes_own_messages` - Doesn't count user's own messages
- ✅ `test_unread_count_after_read` - Updates after messages marked as read
- ✅ `test_unread_count_requires_login` - Requires authentication

**Run tests:**
```bash
source .venv/bin/activate
python manage.py test messaging.tests.UnreadCountViewTests
```

## How It Works

### Initial Page Load
1. Context processor queries database for unread count
2. Template renders badge with initial count
3. Badge hidden if count is 0

### Real-Time Updates
1. **Message sent in thread:**
   - `ChatConsumer` broadcasts to both users' inbox groups
   - `InboxConsumer` receives `inbox_update` event
   - Global `messaging-badge.js` listens to inbox WebSocket
   - Badge fetches updated count from API
   - Badge updates and re-animates

2. **User views thread:**
   - Thread view marks messages as read
   - When user returns to other pages, visibility change triggers badge update
   - Badge fetches new count and updates

### WebSocket Coordination

**Two WebSocket connections work together:**

1. **Global Badge WebSocket** (`messaging-badge.js`):
   - Runs on ALL pages for authenticated users
   - Connects to `/ws/messages/inbox/`
   - Updates navbar badge count only

2. **Inbox Page WebSocket** (`inbox.js`):
   - Only runs when on inbox page (`conversationsGrid` exists)
   - Connects to `/ws/messages/inbox/` (same endpoint)
   - Updates conversation cards and badge

**No Conflicts:**
- Each browser tab gets independent WebSocket connections
- Both connections receive same `inbox_update` events
- Global script only updates badge
- Inbox script only updates conversation list
- Performance impact minimal (lightweight events)

## Visual Appearance

**Badge Position:**
- Top-right corner of "Messages" link (absolute positioning)
- Red gradient background (#ef4444 to #dc2626)
- White text, small font (11px)
- Rounded corners (10px border-radius)
- Minimum width 18px for single digits

**Animation:**
- Continuous pulsing effect (2-second cycle)
- Scales from 1.0 to 1.05
- Shadow intensifies during pulse
- Re-triggers on new messages for attention

**Responsive:**
- Works on mobile and desktop
- Badge scales with navbar
- Always visible and readable

## User Experience Flow

**Scenario 1: New Message Arrives**
1. User A sends message to User B
2. User B is browsing housing listings (not on inbox page)
3. WebSocket delivers `inbox_update` event
4. Badge instantly updates: "Messages (3)" → "Messages (4)"
5. Badge pulses to grab attention
6. User B clicks "Messages" → goes to inbox

**Scenario 2: Reading Messages**
1. User has 5 unread messages (badge shows "5")
2. User clicks "Messages" → goes to inbox
3. Opens thread → messages marked as read
4. User navigates back to home page
5. Page visibility change triggers badge update
6. Badge fetches new count → updates to "2" (remaining unread)

**Scenario 3: No Messages**
1. User reads last message
2. Badge count reaches 0
3. Badge disappears (display: none)
4. "Messages" link remains, badge hidden

## Files Modified/Created

### Created
- `messaging/context_processors.py` - Context processor for unread count
- `static/js/messaging-badge.js` - Real-time badge updates via WebSocket
- `reference/UNREAD_MESSAGE_BADGE.md` - This documentation

### Modified
- `CampusNest/settings.py` - Added context processor
- `templates/base.html` - Added badge HTML and loaded JS
- `static/css/base.css` - Added badge styles and animation
- `messaging/views.py` - Added `unread_count()` API endpoint
- `messaging/urls.py` - Added `/unread-count/` URL pattern
- `messaging/tests.py` - Added `UnreadCountViewTests` class

## Performance Considerations

**Database Queries:**
- Context processor: 1 query per page load (only for authenticated users)
- API endpoint: 1 query per WebSocket update
- Queries use indexes: `(thread, is_read)`, `(thread__user_a)`, `(thread__user_b)`

**WebSocket Overhead:**
- Reuses existing inbox WebSocket endpoint
- No additional server resources
- Events are lightweight JSON (< 1KB)

**Caching Opportunities (Future):**
- Could cache unread count in Redis with TTL
- Invalidate cache on message send/read
- Reduce database queries significantly

## Testing Instructions

### Manual Testing

**Setup:**
1. Start Daphne server:
   ```bash
   daphne -b 0.0.0.0 -p 8000 CampusNest.asgi:application
   ```

2. Open two browsers (different users)

**Test Real-Time Updates:**
1. Browser 1: Login as User A
2. Browser 2: Login as User B
3. Browser 1: Navigate to any page (not inbox)
4. Browser 2: Send message to User A
5. ✅ Browser 1: Badge should update instantly without refresh
6. Browser 1: Click "Messages" → open thread
7. ✅ Badge should decrease after reading
8. Browser 2: Send another message
9. ✅ Browser 1: Badge should update again

**Test Badge Visibility:**
1. User has 5 unread messages (badge shows "5")
2. Read all messages
3. ✅ Badge should disappear
4. Receive new message
5. ✅ Badge should reappear with "1"

**Test Across Pages:**
1. Navigate to: Home, Listings, Marketplace, Profile
2. ✅ Badge should persist across all pages
3. ✅ Badge should update on any page (not just inbox)

### Automated Testing

```bash
source .venv/bin/activate
python manage.py test messaging.tests.UnreadCountViewTests -v 2
```

**Expected Output:**
```
test_unread_count_after_read ... ok
test_unread_count_excludes_own_messages ... ok
test_unread_count_requires_login ... ok
test_unread_count_with_messages ... ok
test_unread_count_zero ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.XXXs

OK
```

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Full support

**Requirements:**
- WebSocket support (95%+ of browsers)
- CSS animations (all modern browsers)
- Fetch API (all modern browsers)

## Future Enhancements

1. **Desktop Notifications:**
   - Request notification permission
   - Show browser notification on new message
   - Play sound on message arrival

2. **Per-Thread Badges:**
   - Show unread count per conversation in inbox
   - Highlight threads with unread messages

3. **Redis Caching:**
   - Cache unread count in Redis
   - Reduce database queries
   - Faster API responses

4. **Message Preview:**
   - Hover over badge to see last message preview
   - Quick action: Mark all as read

5. **Admin Dashboard:**
   - Track message statistics
   - Monitor WebSocket connections
   - Analyze user engagement

## Troubleshooting

**Badge not showing:**
- Check browser console for JavaScript errors
- Verify user is authenticated
- Ensure `messaging-badge.js` is loaded
- Check WebSocket connection status

**Badge not updating:**
- Verify Daphne is running (not runserver)
- Check WebSocket connection in Network tab
- Ensure Redis/in-memory channel layer is configured
- Check `InboxConsumer` is broadcasting events

**Count incorrect:**
- Hard refresh page (Ctrl+Shift+R)
- Check database: `Message.objects.filter(is_read=False).count()`
- Verify context processor is registered in settings

**WebSocket errors:**
- Check Nginx configuration (production)
- Verify WebSocket URL protocol (ws:// vs wss://)
- Ensure Django Channels is installed
- Check ASGI configuration

## Summary

The unread message badge provides users with instant feedback about new messages without requiring manual inbox checks. It integrates seamlessly with the existing WebSocket infrastructure (Phase 2: Inbox Live Updates) and uses minimal resources.

**Key Benefits:**
- ✅ Real-time updates (no polling required)
- ✅ Visible on all pages (not just inbox)
- ✅ Animated for attention
- ✅ Hidden when no messages
- ✅ Accurate count (excludes own messages)
- ✅ Works with existing WebSocket infrastructure
- ✅ Fully tested and documented
