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
```

**Note:** Email functionality requires Gmail App Password (not regular password). If not configured, Django falls back to console email backend for development.

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
- Amenities: predefined choices + custom amenities field
- Date validation: prevents past dates for availability
- Track edit history (`is_edited`, `updated_at`)
- Active/inactive status

**marketplace/** - Buy/Sell Items
- CRUD operations for marketplace items
- Multi-image support via `ItemImage` model
- Condition choices: new, like_new, good, fair, poor
- Sold status tracking
- Contact details and pickup location
- Track edit history (`is_edited`, `updated_at`)

### Model Relationships

```
User (accounts.User)
├── Profile (1:1) → profiles.Profile
│   ├── Favorites (1:M) → profiles.Favorite
│   └── ConnectionRequests (M:M via ConnectionRequest)
├── Listings (1:M) → listings.Listing
│   └── ListingImages (1:M) → listings.ListingImage
└── Items (1:M) → marketplace.Item
    └── ItemImages (1:M) → marketplace.ItemImage
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

/listings/my-listings/      → User's listings
/listings/create/           → Create listing
/listings/<id>/             → View listing
/listings/<id>/edit/        → Edit listing
/listings/<id>/delete/      → Delete listing

/marketplace/my-items/      → User's items
/marketplace/create/        → Create item
/marketplace/<id>/          → View item
/marketplace/<id>/edit/     → Edit item
/marketplace/<id>/delete/   → Delete item
/marketplace/<id>/mark-sold/ → Mark item as sold

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

# Clean up compiled Python and static files
find . -type f -name "*.pyc" -delete && \
find . -type d -name "__pycache__" -delete && \
rm -rf staticfiles/
```

## Media Files
- **Profile photos:** `media/profile_photos/`
- **Listing images:** `media/listing_photos/`
- **Marketplace images:** `media/marketplace_photos/`
- **Configuration:** `MEDIA_URL = "/media/"` and `MEDIA_ROOT = BASE_DIR / "media"`
- **AWS S3 integration:** Commented out but available in settings.py

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
2. Project apps (accounts, profiles, listings, marketplace)

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

## Common Gotchas

1. **Static files not loading:** Ensure `STATICFILES_DIRS` is configured in settings.py
2. **Email not sending:** Check `.env` has valid `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
3. **User creation fails:** Email must be `.edu` domain
4. **Login fails after registration:** User must verify email first
5. **Tests fail with email errors:** Tests may need to mock email sending or use console backend
6. **Migration conflicts:** Always pull latest migrations before creating new ones
7. **Media files 404:** Ensure `MEDIA_URL` is configured in urls.py (only in DEBUG mode)
