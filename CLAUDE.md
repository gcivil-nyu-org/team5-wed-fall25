# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CampusNest is a Django-based platform for NYC university students to find roommates, housing listings, and buy/sell marketplace items. The application uses a custom User model requiring `.edu` email addresses and includes email verification workflows.

## Development Setup

### Environment Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Configure environment variables (see .env section below)
# Create .env file with required variables

# Database migrations
python manage.py migrate

# Optional: Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Required Environment Variables (.env)
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Gmail App Password required

# AWS S3 Configuration (required for production)
USE_S3=True  # Set to False for local development
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_STORAGE_BUCKET_NAME=campusnest-media
AWS_S3_REGION_NAME=us-east-1
```

**Note:**
- Email functionality requires Gmail App Password (not regular password). If not configured, Django falls back to console email backend for development.
- S3 is required for production to persist media files across deployments. Set `USE_S3=False` for local development to use local media storage.
- See `.env.example` for complete list of environment variables.

## Testing & CI/CD

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test profiles
python manage.py test listings
python manage.py test marketplace
python manage.py test messaging

# Run specific test class
python manage.py test accounts.tests.UserModelTests

# Run specific test method
python manage.py test accounts.tests.UserModelTests.test_create_user

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generates htmlcov/ directory
```

### Code Quality Checks
```bash
# Format check (does NOT modify files)
black --check .

# Format code (modifies files)
black .

# Linting
flake8 .
```

### CI/CD Pipeline
- **Travis CI** runs on `develop` branch only
- **Pipeline steps:** black check → flake8 → tests with coverage → coveralls → deploy to AWS
- **Deployment:** Auto-deploys to AWS Elastic Beanstalk on successful `develop` branch builds
- **Coverage:** Reports to Coveralls (see badge in README.md)

## Architecture Overview

### Custom Authentication System
- **Custom User Model:** `accounts.User` (extends `AbstractUser`)
- **USERNAME_FIELD:** `email` (not username)
- **Email Validation:** Enforces strict `.edu` domain validation (pattern: `^[\w\.-]+@[\w-]+\.edu$`)
- **Email Verification:** Required before login via token-based verification
- **AUTH_USER_MODEL:** `accounts.User` (defined in settings.py)

### App Structure & Responsibilities

**accounts/** - Authentication & User Management
- Custom User model with `.edu` email requirement
- Registration with email verification
- Login/logout, password reset flows
- Email verification token generation and validation

**profiles/** - User Profiles & Roommate Matching
- One-to-one relationship with User
- Lifestyle preferences (eating, smoking, drinking, pets, cleanliness, sharing)
- Housing preferences (budget, location, move-in date)
- University affiliation (NYU, Columbia, Fordham, CUNY, Pace, The New School)
- Profile visibility toggle
- **Roommate Features:**
  - `Favorite` model: Track favorited roommate profiles
  - `ConnectionRequest` model: Send/receive/accept/reject connection requests
  - Status tracking: pending/accepted/rejected

**listings/** - Housing Listings
- CRUD operations for housing listings
- Multi-image support via `ListingImage` model
- Amenities: predefined choices + custom amenities field (centralized in `listings/constants.py`)
- Date validation: prevents past dates for availability
- Track edit history (`is_edited`, `updated_at`)
- Active/inactive status
- **Search & Filtering:**
  - Keyword search (title, description, address)
  - Budget range filtering (min/max rent)
  - Location filtering (neighborhood/ZIP code)
  - Move-in and move-out date filtering
  - Amenities filtering (multiple selection)
  - Filter persistence after search

**marketplace/** - Buy/Sell Items
- CRUD operations for marketplace items
- Multi-image support via `ItemImage` model
- Condition choices: new, like_new, good, fair, poor (centralized in `marketplace/constants.py`)
- Sold status tracking
- Contact details and pickup location
- Track edit history (`is_edited`, `updated_at`)
- **Browse & Filtering:**
  - Keyword search (title, description)
  - Category filtering (dropdown)
  - Price range filtering (min/max)
  - Filter persistence after search

**messaging/** - Real-Time Messaging System
- Thread-based conversations about housing listings
- Real-time AJAX polling for instant message updates (2-second interval)
- Read/unread message tracking with timestamps
- Modern chat interface (WhatsApp/Slack-style)
- **Key Features:**
  - `Thread` model: One conversation per listing-user-pair (unique constraint)
  - `Message` model: Individual messages with sender, timestamp, read status
  - Smart user ordering: Prevents duplicate threads (user_a.id < user_b.id)
  - Auto-mark messages as read when viewing
  - Self-messaging prevention (database constraint)
  - Integration with listings: "Contact Seller" button creates threads

### Model Relationships

```
User (accounts.User)
├── Profile (1:1) → profiles.Profile
│   ├── Favorites (1:M) → profiles.Favorite
│   └── ConnectionRequests (M:M via ConnectionRequest)
├── Listings (1:M) → listings.Listing
│   ├── ListingImages (1:M) → listings.ListingImage
│   └── Threads (1:M) → messaging.Thread
├── Items (1:M) → marketplace.Item
│   └── ItemImages (1:M) → marketplace.ItemImage
├── Threads as user_a (1:M) → messaging.Thread
├── Threads as user_b (1:M) → messaging.Thread
└── Sent Messages (1:M) → messaging.Message

messaging.Thread
├── user_a (FK) → User
├── user_b (FK) → User
├── listing (FK) → Listing
└── messages (1:M) → messaging.Message
```

### URL Routing Structure

```
/                           → profiles.home
/profiles/view/             → View user's profile
/profiles/create/           → Create profile
/profiles/edit/             → Edit profile
/profiles/admin-dashboard/  → Admin dashboard (staff only)

/roommates/search/          → Search roommates
/roommates/<id>/            → View roommate detail
/roommates/<id>/favorite/   → Toggle favorite
/roommates/<id>/request/    → Send connection request
/roommates/favorites/       → View favorited profiles
/roommates/requests/        → View connection requests
/roommates/requests/<id>/respond/ → Accept/reject request

/accounts/register/         → Register new account
/accounts/login/            → Login
/accounts/logout/           → Logout
/accounts/verify-email/     → Email verification
/accounts/resend-verification/ → Resend verification email
/accounts/password-reset/   → Password reset request
/accounts/password-reset-confirm/ → Password reset confirmation

/listings/browse/           → Browse & search all active listings (with filters)
/listings/my-listings/      → User's listings
/listings/create/           → Create listing
/listings/<id>/             → View listing
/listings/<id>/edit/        → Edit listing
/listings/<id>/delete/      → Delete listing

/marketplace/browse/        → Browse & search all items (with filters)
/marketplace/my-items/      → User's items
/marketplace/create/        → Create item
/marketplace/<id>/          → View item
/marketplace/<id>/edit/     → Edit item
/marketplace/<id>/delete/   → Delete item
/marketplace/<id>/mark-sold/ → Mark item as sold

/messages/inbox/            → View all conversations
/messages/thread/<id>/      → View/send messages in thread
/messages/start/            → Create new conversation (POST)
/messages/send/<id>/        → Send message to thread (POST)
/messages/thread/<id>/get-new-messages/ → AJAX polling endpoint (GET)

/admin/                     → Django admin panel
```

## Static Files & Templates

### Static Files Organization
```
static/
├── css/
│   ├── base.css    # Dark theme, navigation, forms, alerts, responsive design
│   └── home.css    # Home page specific styles
├── js/
│   └── base.js     # Mobile menu toggle, dropdown handlers
└── images/         # Static images

messaging/static/messaging/
├── css/
│   ├── inbox.css   # Professional inbox design with gradients, animations
│   └── thread.css  # Modern chat interface with bubble styling
└── js/
    └── thread.js   # AJAX polling, real-time updates, auto-scroll
```

### Template Structure
```
templates/
└── base.html       # Base template with navigation, messages, footer

<app>/templates/<app>/
├── <app>_specific_templates.html
└── ...
```

**Important:** Static files configuration requires `STATICFILES_DIRS` in settings.py:
```python
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
```

### Static Files Commands
```bash
# Find where Django locates a static file
python manage.py findstatic css/base.css

# Collect static files for production
python manage.py collectstatic --noinput

# Clean static files (custom management command)
python manage.py cleanstatic                    # Clean staticfiles/ directory (with confirmation)
python manage.py cleanstatic --no-confirm       # Clean without confirmation
python manage.py cleanstatic --all              # Clean staticfiles/ + .pyc + __pycache__
python manage.py cleanstatic --pyc-only         # Only clean .pyc files and __pycache__
```

## Media Files

### AWS S3 Integration (Production)
Media files are stored in AWS S3 for production to persist across deployments. Local storage is used as fallback for development.

**Setup Steps:**
1. **Create S3 Bucket:**
   - Bucket name: `campusnest-media` (or your preferred name)
   - Region: `us-east-1` (or your preferred region)
   - Disable "Block all public access" for public-read access
   - Enable versioning (optional but recommended)

2. **Configure Bucket Policy:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::campusnest-media/*"
       }
     ]
   }
   ```

3. **Create IAM User with S3 Permissions:**
   - Create IAM user: `campusnest-s3-user`
   - Attach policy: `AmazonS3FullAccess` (or create custom policy with limited permissions)
   - Generate access keys and save them securely

4. **Configure Environment Variables:**
   ```bash
   USE_S3=True
   AWS_ACCESS_KEY_ID=your-access-key-id
   AWS_SECRET_ACCESS_KEY=your-secret-access-key
   AWS_STORAGE_BUCKET_NAME=campusnest-media
   AWS_S3_REGION_NAME=us-east-1
   ```

5. **Install Dependencies:**
   ```bash
   pip install django-storages boto3
   ```

**Storage Locations:**
- **Profile photos:** `profile_photos/` (in S3 bucket)
- **Listing images:** `listing_photos/` (in S3 bucket)
- **Marketplace images:** `marketplace_photos/` (in S3 bucket)

**Configuration Details:**
- `USE_S3=True`: Enables S3 storage (set to `False` for local development)
- `AWS_S3_FILE_OVERWRITE=False`: Prevents overwriting existing files
- `AWS_DEFAULT_ACL="public-read"`: Makes uploaded files publicly accessible
- `AWS_QUERYSTRING_AUTH=False`: Disables query string authentication for public URLs

**Local Development:**
- Set `USE_S3=False` in your `.env` file
- Media files stored in `media/` directory
- Configuration: `MEDIA_URL = "/media/"` and `MEDIA_ROOT = BASE_DIR / "media"`

**Note:** Profile photos are used in messaging interface for avatars (falls back to initial placeholders if no photo).

## Database

### Current Configuration
- **Development:** SQLite (`db.sqlite3`)
- **Production:** PostgreSQL on AWS RDS (commented out in settings.py)

### Migrations
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View migration SQL without applying
python manage.py sqlmigrate <app> <migration_number>

# Show migration status
python manage.py showmigrations
```

## Key Django Settings Notes

### Authentication
- `AUTH_USER_MODEL = "accounts.User"`
- `LOGIN_REDIRECT_URL = "home"`
- `PASSWORD_RESET_TIMEOUT = 3600` (1 hour)

### Middleware
- WhiteNoise for static file serving in production
- Standard Django security middleware stack

### Installed Apps Order
Order matters for template/static file discovery:
1. Django contrib apps (admin, auth, contenttypes, sessions, messages, staticfiles)
2. CampusNest (project app - for custom management commands)
3. Project apps (accounts, profiles, listings, marketplace, messaging)

## Custom Management Commands

### Available Commands
```bash
# Create test users (no listings or marketplace items)
python manage.py create_test_users --users 5

# Create test users with listings and marketplace items
python manage.py create_test_listings --users 5 --listings 5 --items 5

# Clean static files and Python cache (CampusNest app)
python manage.py cleanstatic                    # Clean staticfiles/ with confirmation
python manage.py cleanstatic --no-confirm       # Clean without confirmation
python manage.py cleanstatic --all              # Clean staticfiles/ + .pyc + __pycache__
python manage.py cleanstatic --pyc-only         # Only clean Python cache files
```

### Creating Custom Management Commands
Custom commands are located in:
- **Project-level:** `CampusNest/management/commands/` (for general utilities)
- **App-level:** `<app>/management/commands/` (for app-specific tasks)

Structure:
```
<app>/
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── command_name.py
```

## Common Development Patterns

### User Access Patterns
- Always use `settings.AUTH_USER_MODEL` for foreign keys to User
- Use `request.user` to access current user
- Check `.edu` email via `User.email` field
- Verify user authentication: `request.user.is_authenticated`
- Check email verification: `request.user.is_verified`

### Image Handling
- All models with images use related `Image` models (e.g., `ListingImage`, `ItemImage`)
- Images require Pillow library
- Use `related_name` for reverse relationships: `listing.images.all()`

### Form Validation
- Date validators prevent past dates (see `validate_future_date` in listings)
- Email validators enforce `.edu` domain (see `validation_edu_email` in accounts)
- Custom validators defined in models.py files

### Template Patterns
- All templates extend `base.html`
- Use `{% load static %}` at top of templates
- Static files referenced via `{% static 'path/to/file' %}`
- Messages framework used for user feedback

## Important Constraints & Validations

### User Model
- Email must be `.edu` domain (strict: `something@university.edu`, NOT `something@subdomain.university.edu`)
- Email must be unique
- Email verification required before full access
- Username still exists but email is primary login field

### Profile Model
- One profile per user
- University field must be from predefined choices
- Budget min/max fields default to 0 and 5000
- All lifestyle preferences have "no_preference" option
- Profile visibility can be toggled (affects roommate search)

### Listing Model
- `availability_start` and `availability_end` cannot be past dates
- Amenities stored as comma-separated string
- Custom amenities supported in separate field
- `is_edited` flag set to True on updates

### Marketplace Item Model
- Contact details required for buyer communication
- `is_sold` flag prevents further edits when marked sold
- Condition must be from predefined choices
- Owner name can differ from user (for selling items on behalf of others)

### Thread Model (Messaging)
- One thread per unique (listing, user_a, user_b) combination
- `user_a.id` must be < `user_b.id` (canonicalization enforced in save method)
- Cannot create thread where `user_a == user_b` (database constraint)
- `updated_at` field refreshed on new messages (for inbox sorting)
- Indexed on: (listing, user_a), (listing, user_b), (updated_at)

### Message Model (Messaging)
- Max 2000 characters per message
- Read tracking: `is_read` boolean + `read_at` timestamp
- Auto-marked as read when recipient views thread
- Default ordering: chronological by `created_at`
- Indexed on: (thread, created_at), (thread, is_read)

## Environment-Specific Behavior

### DEBUG = True (Development)
- Django serves static files automatically
- Email backend falls back to console if credentials not set
- Detailed error pages shown
- Static files served from `STATICFILES_DIRS`

### DEBUG = False (Production)
- Must run `collectstatic` before deployment
- WhiteNoise serves static files
- Email backend requires valid SMTP credentials
- Generic error pages shown
- Static files served from `STATIC_ROOT` (staticfiles/)

## AWS Deployment
- Target: Elastic Beanstalk environment `campusnest-env-v2`
- App name: `CampusNest`
- Region: `us-east-1`
- Deploys only from `develop` branch via Travis CI
- S3 bucket: `elasticbeanstalk-us-east-1-386397332356`

## Messaging System Deep Dive

### Real-Time Messaging Architecture

**Flow Overview:**
1. User clicks "Contact Seller" on listing detail page
2. Modal form appears for initial message
3. POST to `/messages/start/` creates Thread and initial Message
4. Redirects to `/messages/thread/<id>/`
5. JavaScript (`thread.js`) initializes AJAX polling every 2 seconds
6. Backend returns only new messages (filtered by `id > lastMessageId`)
7. JavaScript appends messages to DOM with animations
8. Auto-scrolls to bottom if user was near bottom (smart scrolling)
9. Incoming messages auto-marked as read

### Thread Model Details

**Database Schema:**
```python
class Thread(models.Model):
    listing = ForeignKey(Listing, CASCADE)
    user_a = ForeignKey(User, CASCADE, related_name="threads_a")
    user_b = ForeignKey(User, CASCADE, related_name="threads_b")
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("listing", "user_a", "user_b")]
        constraints = [CheckConstraint(check=~Q(user_a=F("user_b")))]
```

**Key Methods:**
- `save()`: Ensures `user_a.id < user_b.id` (prevents duplicate threads)
- `other_participant(user)`: Returns conversation partner

**Indexes:**
- `(listing, user_a)` - Find all threads for a listing by a specific user
- `(listing, user_b)` - Same but for user_b
- `(updated_at)` - Sort inbox by most recent activity

### Message Model Details

**Database Schema:**
```python
class Message(models.Model):
    thread = ForeignKey(Thread, CASCADE, related_name="messages")
    sender = ForeignKey(User, CASCADE, related_name="sent_messages")
    body = TextField(max_length=2000)
    created_at = DateTimeField(auto_now_add=True)
    is_read = BooleanField(default=False)
    read_at = DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
```

**Key Methods:**
- `mark_read()`: Atomically sets `is_read=True` and `read_at=now()`

**Indexes:**
- `(thread, created_at)` - Efficiently fetch messages in chronological order
- `(thread, is_read)` - Count unread messages per thread

### AJAX Polling Implementation

**Endpoint:** `/messages/thread/<id>/get-new-messages/?last_message_id=<id>`

**Response Format:**
```json
{
  "messages": [
    {
      "id": 123,
      "sender_id": 45,
      "sender_name": "John Doe",
      "sender_first_initial": "J",
      "sender_last_initial": "D",
      "profile_photo_url": "/media/profile_photos/photo.jpg",
      "body": "Message text here",
      "created_at": "Oct 27, 01:30 PM",
      "is_current_user": true
    }
  ],
  "count": 1
}
```

**JavaScript Polling Logic:**
```javascript
// Polls every 2 seconds
setInterval(pollNewMessages, 2000);

// Pauses when page hidden (browser optimization)
if (document.hidden) return;

// Smart auto-scroll (only if user near bottom)
if (shouldAutoScroll()) scrollToBottom();
```

### Integration with Listings

**Listing Detail Page Changes:**
- "Contact Seller" button visible for non-owners
- Modal form for initial message
- Form POSTs to `/messages/start/` with:
  - `listing_id`
  - `recipient_id` (listing owner)
  - `message` (initial message text)

**Validation:**
- User cannot message own listing (403 error)
- Listing must exist (404 error)
- Message cannot be empty (redirects with error)

**Thread Creation:**
```python
# Canonicalize user order
user_a, user_b = sorted([request.user, recipient], key=lambda u: u.id)

# Get or create thread (reuses existing if found)
thread, created = Thread.objects.get_or_create(
    listing=listing,
    user_a=user_a,
    user_b=user_b
)
```

### UI/UX Features

**Inbox Page (`inbox.html`):**
- Conversation cards with avatars (profile photos or initials)
- Unread badge with count (pulsing animation)
- Last message preview (truncated to 80 chars)
- Sorted by most recent activity (`updated_at DESC`)
- Empty state with floating envelope animation
- Responsive mobile layout

**Thread Page (`thread.html`):**
- WhatsApp/Slack-style chat interface
- Message bubbles:
  - **Sent:** Blue gradient, right-aligned
  - **Received:** Gray gradient, left-aligned
- Avatars for each message sender
- Timestamps formatted as "Oct 27, 01:30 PM"
- Sticky header (back button, user info, listing title)
- Sticky footer (auto-expanding textarea, send button)
- Slide-in animation for new messages
- Custom gradient scrollbar

**Animations:**
- `@keyframes pulse-badge` - Unread count pulsing
- `@keyframes float` - Empty state icon floating
- `@keyframes messageSlideIn` - New messages slide in from right

### Security Features

1. **Authentication:** All views require `@login_required`
2. **Authorization:** Users can only view threads they participate in (403 Forbidden)
3. **CSRF Protection:** Django form tokens on all POST requests
4. **XSS Prevention:** JavaScript escapes all message content before DOM insertion
5. **Self-Messaging Prevention:** Database constraint + view validation
6. **Message Length Limit:** 2000 characters enforced in model

### Performance Optimizations

**Query Optimizations:**
```python
# Inbox view - prevents N+1 queries
threads = Thread.objects.filter(...).select_related(
    "listing", "user_a", "user_b"
).prefetch_related("messages")

# Polling endpoint - only fetch new messages
Message.objects.filter(
    thread=thread,
    id__gt=last_message_id
).select_related("sender", "sender__profile")
```

**Database Indexes:**
- 5 indexes on critical query paths
- Unique constraint prevents duplicate threads
- Check constraint prevents self-messaging

**JavaScript Optimizations:**
- Pauses polling when page hidden (reduces server load)
- Only fetches messages with `id > lastMessageId`
- Smart auto-scroll (doesn't interrupt user reading history)

### Custom Template Tags

**File:** `messaging/templatetags/messaging_extras.py`

```python
@register.filter
def other_party(thread, user):
    """Return the other participant in a thread."""
    return thread.user_b if thread.user_a_id == user.id else thread.user_a
```

**Usage in Templates:**
```django
{% load messaging_extras %}
{{ thread|other_party:request.user }}
```

### Related Documentation Files

**Location:** `/home/rgmatr1x/dev/team5-wed-fall25/reference/`

1. **MESSAGING_INTEGRATION.md** - Complete integration guide
2. **MESSAGING_ENHANCEMENTS.md** - UI/UX improvements and AJAX polling details

## Constants Files

### Centralized Constants
To avoid duplication and ensure consistency across the codebase, constants are centralized:

**listings/constants.py:**
```python
AMENITY_CHOICES = [
    ("furnished", "Furnished"),
    ("utilities", "Utilities Included"),
    ("wifi", "WiFi"),
    ("laundry", "Laundry"),
    ("elevator", "Elevator"),
    ("pets", "Pets Allowed"),
    ("ac", "Air Conditioning"),
]
```

**marketplace/constants.py:**
```python
ITEM_CATEGORY_CHOICES = [...]
ITEM_CONDITION_CHOICES = [...]
```

**Usage:**
- Import constants in models, forms, and views
- Use in management commands for test data generation
- Reference in templates via context variables

## Housing Search Filter Details

### Filter Behavior

**Move-in/Move-out Date Filtering:**
- Filters listings where: `availability_start <= move_in_date` AND `availability_end >= move_out_date`
- Ensures listing is available for the entire duration the student needs
- Both dates are optional (can filter by just one)

**Amenities Filtering:**
- Multiple amenities can be selected
- Shows listings that have ALL selected amenities
- Amenities stored as comma-separated strings in database

**Filter Layout (3-column grid):**
- Row 1: Keyword | Budget Range | Location
- Row 2: Move-in Date | Move-out Date
- Row 3: Amenities (full width)
- Row 4: Search & Reset buttons (full width)

### Filter Input Styling
- White background with dark text (#1a1a1a) at all times
- Removed step attribute from price inputs to allow any value
- Filter values persist after search via template context
- Autofill protection prevents browser from changing colors

## Common Gotchas

1. **Static files not loading:** Ensure `STATICFILES_DIRS` is configured in settings.py
2. **Email not sending:** Check `.env` has valid `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
3. **User creation fails:** Email must be `.edu` domain
4. **Login fails after registration:** User must verify email first
5. **Tests fail with email errors:** Tests may need to mock email sending or use console backend
6. **Migration conflicts:** Always pull latest migrations before creating new ones
7. **Media files 404:** Ensure `MEDIA_URL` is configured in urls.py (only in DEBUG mode)
8. **Duplicate thread errors:** Ensure user ordering is canonical (user_a.id < user_b.id) before creating threads
9. **Messages not polling:** Check JavaScript console for errors; ensure thread.js is loaded
10. **AJAX 403 errors:** User might not be a participant in the thread (authorization check failing)
11. **Filter values not persisting:** Ensure template context includes filter parameters (keyword, rent_min, rent_max, location, move_in_date, move_out_date, amenities)
12. **Amenities not showing in filter:** Verify AMENITY_CHOICES is imported from listings/constants.py in views.py
