# Messaging App Integration Documentation

**Date:** October 25, 2025
**Branch:** `messaging`
**Integration Status:** ✅ Complete - All 200 tests passing

## Overview

Integrated a Django messaging app into CampusNest that enables users to message each other about housing listings. The messaging system creates conversation threads tied to specific listings, allowing prospective renters to contact listing owners directly.

---

## Changes Made

### 1. Added Messaging App to Django Settings

**File:** `CampusNest/settings.py`

**Change (Line 61):**
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "CampusNest",
    "accounts",
    "profiles",
    "listings",
    "marketplace",
    "messaging",  # ← Added
]
```

**Reason:** Django needs apps registered in INSTALLED_APPS to recognize models, templates, and URLs.

---

### 2. Fixed Admin Search Fields for Custom User Model

**File:** `messaging/admin.py`

**Changes (Lines 9 & 16):**

**Before:**
```python
search_fields = ("listing__title", "user_a__username", "user_b__username")
# ...
search_fields = ("sender__username", "body")
```

**After:**
```python
search_fields = ("listing__title", "user_a__email", "user_b__email")
# ...
search_fields = ("sender__email", "body")
```

**Reason:** CampusNest uses a custom User model where `email` is the USERNAME_FIELD (not `username`). Searching by `username` would fail in the admin interface.

---

### 3. Fixed Template Tags Directory Structure

**File Structure Change:**

**Before:**
```
messaging/
├── templates/
│   └── templatetags/        # ❌ Wrong location
│       ├── __init__.py
│       └── messaging_extras.py
```

**After:**
```
messaging/
├── templatetags/            # ✅ Correct location
│   ├── __init__.py
│   └── messaging_extras.py
```

**Command used:**
```bash
mkdir -p messaging/templatetags
mv messaging/templates/templatetags/* messaging/templatetags/
rmdir messaging/templates/templatetags
```

**Reason:** Django looks for template tags in `<app>/templatetags/`, not `<app>/templates/templatetags/`. The incorrect location would cause template tag loading errors.

---

### 4. Integrated Messaging URLs into Main Project

**File:** `CampusNest/urls.py`

**Change (Line 12):**
```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("profiles.urls")),
    path("accounts/", include("accounts.urls")),
    path("listings/", include("listings.urls")),
    path("marketplace/", include("marketplace.urls")),
    path("messages/", include("messaging.urls")),  # ← Added
]
```

**Routes Added:**
- `/messages/inbox/` - View all conversations
- `/messages/thread/<id>/` - View specific conversation thread
- `/messages/start/` - Start new conversation (POST only)
- `/messages/send/<id>/` - Send message to existing thread (POST only)

**Reason:** URL routing required for messaging views to be accessible.

---

### 5. Applied Database Migrations

**Commands:**
```bash
python manage.py makemigrations messaging  # No new migrations needed
python manage.py migrate messaging         # Applied existing migrations
```

**Tables Created:**
- `messaging_thread` - Conversation threads between two users about a listing
- `messaging_message` - Individual messages within threads

**Constraints:**
- Unique thread per listing-user pair
- Prevents self-messaging (user_a ≠ user_b)
- Indexed for performance on queries

**Reason:** Creates database tables for Thread and Message models.

---

### 6. Added Navigation Links

**File:** `templates/base.html`

**Change (Lines 31-34):**
```html
<a href="{% url 'view_profile' %}">My Profile</a>
<a href="{% url 'public_listings' %}">Browse Listings</a>  <!-- ← Added -->
<a href="{% url 'my_listings' %}">My Listings</a>
<a href="{% url 'my_items' %}">My Items</a>
<a href="{% url 'messaging:inbox' %}">Messages</a>  <!-- ← Added -->
```

**Reason:** Users need easy access to browse listings and check messages.

---

### 7. Created Public Listings Browse Feature

**File:** `listings/views.py`

**Added Function (Lines 182-186):**
```python
@login_required
def public_listings(request):
    """Display all active listings from other users"""
    listings = Listing.objects.filter(is_active=True).exclude(user=request.user).select_related('user').prefetch_related('images').order_by("-created_at")
    return render(request, "listings/public_listings.html", {"listings": listings})
```

**File:** `listings/urls.py`

**Added Route (Line 14):**
```python
path("browse/", views.public_listings, name="public_listings"),
```

**File Created:** `listings/templates/listings/public_listings.html`

**Purpose:** Shows all active housing listings from other users (excludes own listings).

**Reason:** Users need a way to discover listings before they can message about them.

---

### 8. Updated View Listing for Owner/Non-Owner Access

**File:** `listings/views.py`

**Modified Function (Lines 169-182):**

**Before:**
```python
@login_required
def view_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    return render(request, "listings/view_listing.html", {"listing": listing})
```

**After:**
```python
@login_required
def view_listing(request, listing_id):
    """View listing details. Shows different options based on ownership."""
    listing = get_object_or_404(Listing, id=listing_id)
    is_owner = listing.user == request.user

    # Only owners can view inactive listings
    if not listing.is_active and not is_owner:
        return get_object_or_404(Listing, id=listing_id, user=request.user)

    return render(request, "listings/view_listing.html", {
        "listing": listing,
        "is_owner": is_owner
    })
```

**Key Changes:**
- Removed `user=request.user` constraint - allows non-owners to view
- Added `is_owner` flag to context
- Inactive listings still restricted to owners only

**Reason:** Non-owners need to view listing details to decide if they want to contact the seller.

---

### 9. Added "Contact Seller" Feature to Listing Details

**File:** `listings/templates/listings/view_listing.html`

**Modified Section (Lines 98-157):**

**Action Buttons - Owner View:**
```html
{% if is_owner %}
<a href="{% url 'edit_listing' listing.id %}" class="btn-edit">Edit Listing</a>
<a href="{% url 'delete_listing' listing.id %}" class="btn-delete">Delete Listing</a>
<a href="{% url 'my_listings' %}" class="btn-back">Back to My Listings</a>
```

**Action Buttons - Non-Owner View:**
```html
{% else %}
<button onclick="showMessageForm()" class="btn-edit" style="background: #0d6efd;">
  Contact Seller
</button>
<a href="{% url 'public_listings' %}" class="btn-back">Back to Browse</a>
{% endif %}
```

**Added Modal (Lines 122-157):**
```html
<!-- Message Form Modal (for non-owners) -->
{% if not is_owner %}
<div id="messageModal" style="display:none; ...">
  <div style="...">
    <h3>Send Message to {{ listing.user.first_name|default:listing.user.username }}</h3>
    <form method="post" action="{% url 'messaging:start_thread' %}">
      {% csrf_token %}
      <input type="hidden" name="listing_id" value="{{ listing.id }}">
      <input type="hidden" name="recipient_id" value="{{ listing.user.id }}">
      <textarea name="body" rows="4" required placeholder="Hi, I'm interested in your listing..."></textarea>
      <button type="submit">Send Message</button>
      <button type="button" onclick="hideMessageForm()">Cancel</button>
    </form>
  </div>
</div>

<script>
function showMessageForm() {
  document.getElementById('messageModal').style.display = 'flex';
}
function hideMessageForm() {
  document.getElementById('messageModal').style.display = 'none';
}
// Close modal when clicking outside
document.getElementById('messageModal').addEventListener('click', function(e) {
  if (e.target === this) {
    hideMessageForm();
  }
});
</script>
{% endif %}
```

**Reason:** Provides the core integration point - non-owners can initiate conversations about listings.

---

### 10. Updated Tests for New Behavior

**File:** `listings/tests.py`

**Modified Test (Lines 1044-1058):**

**Before:**
```python
def test_view_listing_requires_ownership(self):
    """Test that only owner can view listing"""
    self.client.force_login(self.other_user)
    response = self.client.get(reverse("view_listing", args=[self.listing.id]))
    self.assertEqual(response.status_code, 404)
```

**After:**
```python
def test_view_listing_non_owner_can_view_active(self):
    """Test that non-owners can view active listings"""
    self.client.force_login(self.other_user)
    response = self.client.get(reverse("view_listing", args=[self.listing.id]))
    self.assertEqual(response.status_code, 200)
    self.assertFalse(response.context["is_owner"])
    self.assertEqual(response.context["listing"], self.listing)

def test_view_listing_non_owner_cannot_view_inactive(self):
    """Test that non-owners cannot view inactive listings"""
    self.listing.is_active = False
    self.listing.save()
    self.client.force_login(self.other_user)
    response = self.client.get(reverse("view_listing", args=[self.listing.id]))
    self.assertEqual(response.status_code, 404)
```

**Reason:** Old test expected 404 for non-owners, but new behavior allows viewing active listings. Updated to test the correct behavior.

---

## How the Messaging System Works

### User Flow

1. **Browse Listings**
   - User navigates to "Browse Listings" in navbar
   - Sees all active listings from other users
   - Click "View Details" on any listing

2. **View Listing Details**
   - If user owns the listing: sees Edit/Delete buttons
   - If user doesn't own: sees "Contact Seller" button

3. **Start Conversation**
   - Click "Contact Seller"
   - Modal appears with message form
   - Enter message and click "Send Message"
   - Form POSTs to `/messages/start/`

4. **Backend Thread Creation** (`messaging/views.py:start_thread`)
   - Validates listing_id and recipient_id
   - Prevents self-messaging
   - Creates or retrieves Thread (unique per listing-user pair)
   - Creates first Message in thread
   - Redirects to thread view

5. **View Messages**
   - Navigate to "Messages" in navbar
   - See inbox with all conversations
   - Shows: other user, listing title, last message, unread count
   - Sorted by most recent activity

6. **Continue Conversation**
   - Click "Open" on any thread
   - View all messages in chronological order
   - Messages auto-marked as read when viewing
   - Send reply via form at bottom
   - Form POSTs to `/messages/thread/<id>/`

### Data Model

**Thread Model:**
```python
class Thread(models.Model):
    listing = ForeignKey(Listing)        # Which listing is being discussed
    user_a = ForeignKey(User)            # First participant (lower ID)
    user_b = ForeignKey(User)            # Second participant (higher ID)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    # Constraints:
    # - Unique (listing, user_a, user_b)
    # - user_a != user_b
```

**Message Model:**
```python
class Message(models.Model):
    thread = ForeignKey(Thread)
    sender = ForeignKey(User)
    body = TextField(max_length=2000)
    created_at = DateTimeField()
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True)
```

**Key Design Decisions:**
- User IDs canonicalized (lower ID always user_a) to prevent duplicate threads
- Threads tied to listings - conversation context always clear
- Unread tracking per message for notification counts
- Ordering preserved via created_at timestamps

---

## Testing

### Run All Tests
```bash
python manage.py test
```

**Expected Result:** All 200 tests pass

### Test Specific Messaging Features
```bash
# Test listing views with new behavior
python manage.py test listings.tests.ViewListingViewTests

# Test public listings
python manage.py test listings.tests.ViewListingViewTests.test_view_listing_non_owner_can_view_active
python manage.py test listings.tests.ViewListingViewTests.test_view_listing_non_owner_cannot_view_inactive
```

### Manual Testing Checklist

1. ✅ Create two test users (both with .edu emails)
2. ✅ User A creates a housing listing
3. ✅ User B browses public listings
4. ✅ User B views User A's listing
5. ✅ User B clicks "Contact Seller" and sends message
6. ✅ User A checks "Messages" inbox - sees new message
7. ✅ User A opens thread and replies
8. ✅ User B sees reply in inbox (with unread count)
9. ✅ User B opens thread - messages marked as read
10. ✅ Verify User B cannot view User A's inactive listings

---

## Rollback Instructions

If you need to revert this integration:

### 1. Remove Messaging App
```bash
# Edit CampusNest/settings.py
# Remove "messaging" from INSTALLED_APPS (line 61)
```

### 2. Remove URL Routes
```bash
# Edit CampusNest/urls.py
# Remove line 12: path("messages/", include("messaging.urls")),
```

### 3. Revert Navigation Links
```bash
# Edit templates/base.html
# Remove lines 31 and 34:
# - <a href="{% url 'public_listings' %}">Browse Listings</a>
# - <a href="{% url 'messaging:inbox' %}">Messages</a>
```

### 4. Revert Listings Views
```bash
# Edit listings/views.py
# Revert view_listing to original (lines 169-182):

@login_required
def view_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    return render(request, "listings/view_listing.html", {"listing": listing})

# Remove public_listings function (lines 182-186)
```

### 5. Revert Listings URLs
```bash
# Edit listings/urls.py
# Remove line 14: path("browse/", views.public_listings, name="public_listings"),
```

### 6. Revert Listing Template
```bash
# Edit listings/templates/listings/view_listing.html
# Replace lines 98-157 with original action buttons (owner-only view)
```

### 7. Delete Created Files
```bash
rm listings/templates/listings/public_listings.html
```

### 8. Revert Tests
```bash
# Edit listings/tests.py
# Replace lines 1044-1058 with original test:

def test_view_listing_requires_ownership(self):
    """Test that only owner can view listing"""
    self.client.force_login(self.other_user)
    response = self.client.get(reverse("view_listing", args=[self.listing.id]))
    self.assertEqual(response.status_code, 404)
```

### 9. Remove Database Tables (Optional)
```bash
# If you want to remove messaging tables completely
python manage.py migrate messaging zero
rm -rf messaging/migrations/
```

### 10. Run Tests to Verify Rollback
```bash
python manage.py test
# Should have 199 tests (one fewer than with integration)
```

---

## Files Modified Summary

### Core Integration (Required)
1. `CampusNest/settings.py` - Added messaging to INSTALLED_APPS
2. `CampusNest/urls.py` - Added messaging URL routes
3. `messaging/admin.py` - Fixed search fields for custom User model
4. `messaging/templatetags/` - Moved to correct location (from templates/templatetags/)
5. Database migrations applied (no new files)

### Enhanced Integration (For Usability)
6. `listings/views.py` - Added public_listings view, updated view_listing
7. `listings/urls.py` - Added browse route
8. `listings/templates/listings/view_listing.html` - Added contact seller modal
9. `listings/templates/listings/public_listings.html` - Created new template
10. `templates/base.html` - Added navigation links
11. `listings/tests.py` - Updated tests for new behavior

---

## Known Issues & Limitations

### None Currently

All tests passing, no known bugs at time of integration.

### Future Enhancements (Not Implemented)

1. **Unread message count badge** in navbar (would require context processor)
2. **Email notifications** when new message received
3. **Message deletion** or thread archiving
4. **Bulk messaging** for admins
5. **Message search** functionality
6. **Real-time updates** via WebSockets/Channels
7. **Image attachments** in messages
8. **Read receipts** showing when other party viewed message

---

## Troubleshooting

### Issue: "No module named 'messaging'"
**Solution:** Verify messaging is in INSTALLED_APPS in settings.py

### Issue: Template tag 'messaging_extras' not found
**Solution:** Check templatetags directory is at `messaging/templatetags/` (not in templates/)

### Issue: 404 on /messages/inbox/
**Solution:** Verify messaging URLs included in main urls.py

### Issue: RelatedObjectDoesNotExist: User has no profile
**Solution:** Messaging doesn't require profiles - this is unrelated to messaging integration

### Issue: Tests failing after integration
**Solution:** Run `python manage.py test listings.tests.ViewListingViewTests.test_view_listing_non_owner_can_view_active` to verify new behavior

### Issue: Cannot create thread (500 error)
**Solution:** Check that:
- Both users have valid .edu emails
- Listing exists and is active
- Not trying to message own listing

---

## Security Considerations

### Implemented Protections

1. **@login_required** on all messaging views - no anonymous access
2. **CSRF protection** on all forms
3. **Thread participant validation** - users can only view their own threads
4. **Listing access control** - non-owners can only view active listings
5. **Self-messaging prevention** - constraint in database model
6. **Message length limits** - max 2000 characters

### Not Implemented (Consider for Production)

1. **Rate limiting** - prevent spam messaging
2. **Content filtering** - block inappropriate content
3. **User blocking** - allow users to block others
4. **Report abuse** - flag inappropriate messages for review

---

## CI/CD Impact

### Travis CI

**Current Pipeline:**
1. black check
2. flake8
3. tests with coverage
4. coveralls
5. deploy to AWS (develop branch only)

**Impact:** None - integration follows existing code style and all tests pass.

### Coverage

Test count increased from 199 to 200 tests (added new test for non-owner listing access).

---

## Git Commit Message (Recommended)

```
feat: Integrate messaging app for listing inquiries

- Add messaging app to INSTALLED_APPS
- Fix admin search fields to use email instead of username
- Move templatetags to correct directory structure
- Add messaging URL routes at /messages/
- Create public listings browse view
- Update view_listing to support non-owner access
- Add "Contact Seller" modal on listing detail pages
- Add navigation links for Browse Listings and Messages
- Update tests to reflect new non-owner viewing behavior

All 200 tests passing. Enables users to message each other about
housing listings through threaded conversations.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Support

For issues or questions:
1. Check this documentation first
2. Review git history: `git log --all --grep="messaging"`
3. Check specific commits on this branch: `git log messaging`
4. Review the original messaging app code in `messaging/` directory

---

**Last Updated:** October 25, 2025
**Maintained By:** CampusNest Development Team
**Integration Completed By:** Claude Code
