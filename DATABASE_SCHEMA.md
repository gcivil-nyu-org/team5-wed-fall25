# Database Schema Documentation

This file documents the complete database schema for all models in the CampusNest application. Reference this document when adding new features to ensure schema consistency and avoid migration conflicts.

**Last Updated:** October 23, 2025

---

## Table of Contents
- [accounts.User](#accountsuser)
- [profiles.Profile](#profilesprofile)
- [profiles.Favorite](#profilesfavorite)
- [profiles.ConnectionRequest](#profilesconnectionrequest)
- [listings.Listing](#listingslisting)
- [listings.ListingImage](#listingslistingimage)
- [marketplace.Item](#marketplaceitem)
- [marketplace.ItemImage](#marketplaceitemimage)
- [Model Relationships](#model-relationships)
- [Database Indexes](#database-indexes)
- [Constraints Summary](#constraints-summary)

---

## accounts.User

**Extends:** `django.contrib.auth.models.AbstractUser`

**Table Name:** `accounts_user`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `email` | EmailField | UNIQUE, NOT NULL | - | User's email address (must be .edu) |
| `username` | CharField(150) | UNIQUE, NOT NULL | - | Username (inherited from AbstractUser) |
| `password` | CharField(128) | NOT NULL | - | Hashed password |
| `first_name` | CharField(150) | Optional | '' | User's first name |
| `last_name` | CharField(150) | Optional | '' | User's last name |
| `is_verified` | BooleanField | NOT NULL | False | Email verification status |
| `is_staff` | BooleanField | NOT NULL | False | Staff status (inherited) |
| `is_active` | BooleanField | NOT NULL | True | Active status (inherited) |
| `is_superuser` | BooleanField | NOT NULL | False | Superuser status (inherited) |
| `date_joined` | DateTimeField | NOT NULL | now | Account creation timestamp (inherited) |
| `last_login` | DateTimeField | Optional | None | Last login timestamp (inherited) |

### Validators

- **email:** `validation_edu_email` - Enforces strict `.edu` domain pattern: `^[\w\.-]+@[\w-]+\.edu$`

### Settings

- **USERNAME_FIELD:** `'email'` (login with email, not username)
- **REQUIRED_FIELDS:** `['username']` (required for createsuperuser)

### String Representation

```python
def __str__(self):
    return self.email
```

### Notes

- Username field still exists but email is the primary authentication field
- Email must be unique across all users
- Email validation prevents subdomains (e.g., `user@mail.nyu.edu` would be rejected)
- Users must verify email before accessing most features

---

## profiles.Profile

**Table Name:** `profiles_profile`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `user` | ForeignKey(User) | UNIQUE, CASCADE | - | One-to-one with User |
| `bio` | TextField(500) | NOT NULL | - | User biography/description |
| `university` | CharField(100) | NOT NULL, CHOICES | - | User's university affiliation |
| `profile_photo` | ImageField | NOT NULL | - | Profile picture (upload_to='profile_photos/') |
| `visibility` | BooleanField | NOT NULL | True | Profile visibility in roommate search |
| `created_at` | DateTimeField | AUTO_ADD | now | Profile creation timestamp |
| `eating_habit` | CharField(20) | CHOICES | 'no_preference' | Eating preference |
| `smoking_preference` | CharField(20) | CHOICES | 'non_smoker' | Smoking preference |
| `sharing_preference` | CharField(20) | CHOICES | 'no_preference' | Sharing preference |
| `drinking_preference` | CharField(20) | CHOICES | 'no_preference' | Drinking preference |
| `pet_preference` | CharField(20) | CHOICES | 'no_preference' | Pet preference |
| `cleanliness_preference` | CharField(20) | CHOICES | 'no_preference' | Cleanliness preference |
| `budget_min` | IntegerField | NOT NULL | 0 | Minimum monthly budget ($) |
| `budget_max` | IntegerField | NOT NULL | 5000 | Maximum monthly budget ($) |
| `location` | CharField(200) | Optional | '' | Preferred location/neighborhood |
| `move_in_date` | DateField | Optional | None | Preferred move-in date |

### Choices

**UNIVERSITY_CHOICES:**
```python
[
    ("NYU", "New York University"),
    ("Columbia", "Columbia University"),
    ("Fordham", "Fordham University"),
    ("CUNY", "City University of New York"),
    ("Pace", "Pace University"),
    ("The New School", "The New School"),
]
```

**EATING_CHOICES:**
```python
[
    ("vegetarian", "Vegetarian"),
    ("vegan", "Vegan"),
    ("no_preference", "No Preference"),
]
```

**SMOKING_CHOICES:**
```python
[
    ("non_smoker", "Non-Smoker"),
    ("smoker", "Smoker"),
    ("occasionally", "Occasionally"),
]
```

**SHARING_CHOICES:**
```python
[
    ("sharing", "Open to Sharing"),
    ("non_sharing", "Prefer Not to Share"),
    ("no_preference", "No Preference"),
]
```

**DRINKING_CHOICES:**
```python
[
    ("non_drinker", "Non-Drinker"),
    ("social_drinker", "Social Drinker"),
    ("regular_drinker", "Regular Drinker"),
    ("no_preference", "No Preference"),
]
```

**PET_CHOICES:**
```python
[
    ("no_pets", "No Pets"),
    ("cats", "Cats"),
    ("dogs", "Dogs"),
    ("other", "Other"),
    ("no_preference", "No Preference"),
]
```

**CLEANLINESS_CHOICES:**
```python
[
    ("very_clean", "Very Clean"),
    ("clean", "Clean"),
    ("moderate", "Moderate"),
    ("relaxed", "Relaxed"),
    ("no_preference", "No Preference"),
]
```

### String Representation

```python
def __str__(self):
    return f"{self.user.username}'s Profile"
```

### Custom Methods

```python
def get_preference_display_with_icon(self, preference_type):
    """Returns preference with emoji icon"""
    # Returns formatted string: "🥗 Vegetarian"
```

### Notes

- One-to-one relationship with User (CASCADE delete)
- Profile photo is required (not optional)
- Budget defaults allow for wide range (0-5000)
- All preference fields have "no_preference" option
- Visibility toggle affects roommate search results

---

## profiles.Favorite

**Table Name:** `profiles_favorite`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `user` | ForeignKey(User) | CASCADE | - | User who favorited |
| `favorite_profile` | ForeignKey(Profile) | CASCADE | - | Profile that was favorited |
| `created_at` | DateTimeField | AUTO_ADD | now | Favorite creation timestamp |

### Meta Options

```python
class Meta:
    unique_together = ("user", "favorite_profile")
    ordering = ["-created_at"]
```

### String Representation

```python
def __str__(self):
    return f"{self.user.username} favorited {self.favorite_profile.user.username}"
```

### Related Names

- **user → favorites:** `user.favorites.all()` (all favorites by this user)
- **profile → favorited_by:** `profile.favorited_by.all()` (all users who favorited this profile)

### Notes

- Unique constraint prevents duplicate favorites
- Ordered by most recent first
- CASCADE delete: deleting user or profile removes favorites

---

## profiles.ConnectionRequest

**Table Name:** `profiles_connectionrequest`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `from_user` | ForeignKey(User) | CASCADE | - | User who sent the request |
| `to_user` | ForeignKey(User) | CASCADE | - | User who received the request |
| `status` | CharField(20) | CHOICES | 'pending' | Request status |
| `message` | TextField(500) | Optional | '' | Optional message with request |
| `created_at` | DateTimeField | AUTO_ADD | now | Request creation timestamp |
| `updated_at` | DateTimeField | AUTO_UPDATE | now | Last update timestamp |

### Choices

**STATUS_CHOICES:**
```python
[
    ("pending", "Pending"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
]
```

### Meta Options

```python
class Meta:
    unique_together = ("from_user", "to_user")
    ordering = ["-created_at"]
```

### String Representation

```python
def __str__(self):
    return f"{self.from_user.username} → {self.to_user.username} ({self.status})"
```

### Related Names

- **from_user → connection_requests_sent:** `user.connection_requests_sent.all()`
- **to_user → connection_requests_received:** `user.connection_requests_received.all()`

### Notes

- Unique constraint prevents duplicate requests between same users
- Status defaults to 'pending'
- Message is optional (can be blank)
- Updated_at auto-updates on save

---

## listings.Listing

**Table Name:** `listings_listing`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `user` | ForeignKey(User) | CASCADE | - | Listing owner |
| `title` | CharField(200) | NOT NULL | - | Listing title |
| `address` | CharField(300) | NOT NULL | - | Property address |
| `rent` | DecimalField(10,2) | NOT NULL | - | Monthly rent amount |
| `description` | TextField(2000) | NOT NULL | - | Listing description |
| `amenities` | CharField(500) | Optional | '' | Comma-separated amenity keys |
| `custom_amenities` | CharField(300) | Optional | '' | Comma-separated custom amenities |
| `availability_start` | DateField | NOT NULL, VALIDATED | - | Availability start date |
| `availability_end` | DateField | NOT NULL, VALIDATED | - | Availability end date |
| `created_at` | DateTimeField | AUTO_ADD | now | Listing creation timestamp |
| `updated_at` | DateTimeField | AUTO_UPDATE | now | Last update timestamp |
| `is_edited` | BooleanField | NOT NULL | False | Edit flag |
| `is_active` | BooleanField | NOT NULL | True | Active status |

### Choices

**AMENITY_CHOICES:**
```python
[
    ("furnished", "Furnished"),
    ("utilities", "Utilities Included"),
    ("wifi", "WiFi"),
    ("laundry", "Laundry"),
    ("elevator", "Elevator"),
    ("pets", "Pets Allowed"),
    ("ac", "Air Conditioning"),
]
```

### Validators

- **availability_start:** `validate_future_date` - Date cannot be in the past
- **availability_end:** `validate_future_date` - Date cannot be in the past

```python
def validate_future_date(value):
    """Validate that the date is not in the past"""
    if value < timezone.now().date():
        raise ValidationError("Date cannot be in the past.")
```

### String Representation

```python
def __str__(self):
    return f"{self.title} - {self.user.username}"
```

### Custom Methods

```python
def get_amenities_list(self):
    """Return amenities as a list"""
    if self.amenities:
        return self.amenities.split(",")
    return []

def get_amenities_display(self):
    """Return formatted amenities for display (includes custom amenities)"""
    # Returns list of human-readable amenity names
```

### Notes

- Amenities stored as comma-separated string of keys
- Custom amenities allow user-defined amenities
- Both availability dates must be in the future
- Rent stored as decimal with 2 decimal places
- CASCADE delete: deleting user removes their listings

---

## listings.ListingImage

**Table Name:** `listings_listingimage`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `listing` | ForeignKey(Listing) | CASCADE | - | Associated listing |
| `image` | ImageField | NOT NULL | - | Image file (upload_to='listing_photos/') |

### String Representation

```python
def __str__(self):
    return f"Image for {self.listing.title}"
```

### Related Names

- **listing → images:** `listing.images.all()`

### Notes

- Multiple images per listing supported
- CASCADE delete: deleting listing removes all images
- Images stored in `media/listing_photos/`

---

## marketplace.Item

**Table Name:** `marketplace_item`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `user` | ForeignKey(User) | CASCADE | - | Item owner |
| `title` | CharField(200) | NOT NULL | - | Item title |
| `description` | TextField(2000) | NOT NULL | - | Item description |
| `condition` | CharField(20) | CHOICES | - | Item condition |
| `price` | DecimalField(10,2) | NOT NULL | - | Item price |
| `pickup_location` | CharField(300) | NOT NULL | - | Pickup location |
| `owner_name` | CharField(200) | NOT NULL | - | Owner name (can differ from user) |
| `contact_details` | CharField(300) | NOT NULL | - | Phone or email |
| `created_at` | DateTimeField | AUTO_ADD | now | Item creation timestamp |
| `updated_at` | DateTimeField | AUTO_UPDATE | now | Last update timestamp |
| `is_edited` | BooleanField | NOT NULL | False | Edit flag |
| `is_sold` | BooleanField | NOT NULL | False | Sold status |
| `is_active` | BooleanField | NOT NULL | True | Active status |

### Choices

**CONDITION_CHOICES:**
```python
[
    ("new", "New"),
    ("like_new", "Like New"),
    ("good", "Good"),
    ("fair", "Fair"),
    ("poor", "Poor"),
]
```

### Meta Options

```python
class Meta:
    ordering = ["-created_at"]
```

### String Representation

```python
def __str__(self):
    return f"{self.title} - {self.user.username}"
```

### Notes

- Price stored as decimal with 2 decimal places
- Owner name can differ from user (for selling on behalf of others)
- Contact details required for buyer communication
- Ordered by most recent first
- CASCADE delete: deleting user removes their items

---

## marketplace.ItemImage

**Table Name:** `marketplace_itemimage`

### Fields

| Field Name | Type | Constraints | Default | Description |
|------------|------|-------------|---------|-------------|
| `id` | AutoField | PRIMARY KEY | Auto | Auto-incrementing primary key |
| `item` | ForeignKey(Item) | CASCADE | - | Associated item |
| `image` | ImageField | NOT NULL | - | Image file (upload_to='marketplace_photos/') |

### String Representation

```python
def __str__(self):
    return f"Image for {self.item.title}"
```

### Related Names

- **item → images:** `item.images.all()`

### Notes

- Multiple images per item supported
- CASCADE delete: deleting item removes all images
- Images stored in `media/marketplace_photos/`

---

## Model Relationships

### Entity Relationship Diagram

```
┌─────────────────┐
│  accounts.User  │
│   (AUTH_USER)   │
└────────┬────────┘
         │
         │ 1:1
         ├──────────────────┐
         │                  │
         │                  ▼
         │         ┌─────────────────┐
         │         │ profiles.Profile│
         │         └────────┬────────┘
         │                  │
         │                  │ 1:M
         │         ┌────────┴────────┐
         │         │                 │
         │         ▼                 ▼
         │  ┌──────────────┐  ┌─────────────────────┐
         │  │   Favorite   │  │ ConnectionRequest   │
         │  │  (M:M via)   │  │    (M:M via)        │
         │  └──────────────┘  └─────────────────────┘
         │
         │ 1:M
         ├──────────────────┬──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│listings.Listing │  │marketplace.  │  │    Other     │
│                 │  │    Item      │  │  Relations   │
└────────┬────────┘  └──────┬───────┘  └──────────────┘
         │                  │
         │ 1:M             │ 1:M
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌──────────────┐
│ ListingImage    │  │  ItemImage   │
└─────────────────┘  └──────────────┘
```

### Foreign Key Relationships

| Model | Field | References | On Delete | Type |
|-------|-------|------------|-----------|------|
| Profile | user | User | CASCADE | 1:1 |
| Favorite | user | User | CASCADE | M:1 |
| Favorite | favorite_profile | Profile | CASCADE | M:1 |
| ConnectionRequest | from_user | User | CASCADE | M:1 |
| ConnectionRequest | to_user | User | CASCADE | M:1 |
| Listing | user | User | CASCADE | M:1 |
| ListingImage | listing | Listing | CASCADE | M:1 |
| Item | user | User | CASCADE | M:1 |
| ItemImage | item | Item | CASCADE | M:1 |

### Related Name Mapping

| Model | Field | Related Name | Reverse Access |
|-------|-------|--------------|----------------|
| Profile | user | (default) | `user.profile` |
| Favorite | user | favorites | `user.favorites.all()` |
| Favorite | favorite_profile | favorited_by | `profile.favorited_by.all()` |
| ConnectionRequest | from_user | connection_requests_sent | `user.connection_requests_sent.all()` |
| ConnectionRequest | to_user | connection_requests_received | `user.connection_requests_received.all()` |
| Listing | user | (default) | `user.listing_set.all()` |
| ListingImage | listing | images | `listing.images.all()` |
| Item | user | (default) | `user.item_set.all()` |
| ItemImage | item | images | `item.images.all()` |

---

## Database Indexes

### Automatic Indexes

Django automatically creates indexes for:
- All Primary Key fields (`id`)
- All Foreign Key fields
- Fields with `unique=True` constraint

### Explicit Indexes

The following fields have explicit indexes due to `unique_together` or `ordering`:

**profiles.Favorite:**
- Index on `(user, favorite_profile)` - unique_together
- Index on `created_at` - ordering

**profiles.ConnectionRequest:**
- Index on `(from_user, to_user)` - unique_together
- Index on `created_at` - ordering

**marketplace.Item:**
- Index on `created_at` - ordering

### Fields Frequently Used in Queries (Consider Adding Indexes)

If performance issues arise, consider adding indexes to:
- `profiles.Profile.visibility` - filtered in roommate search
- `profiles.Profile.university` - filtered in roommate search
- `listings.Listing.is_active` - filtered in listing views
- `listings.Listing.availability_start` - filtered for date ranges
- `marketplace.Item.is_sold` - filtered in marketplace views
- `marketplace.Item.is_active` - filtered in marketplace views

---

## Constraints Summary

### Unique Constraints

| Model | Fields | Type |
|-------|--------|------|
| User | email | UNIQUE |
| User | username | UNIQUE |
| Profile | user | UNIQUE (1:1) |
| Favorite | (user, favorite_profile) | unique_together |
| ConnectionRequest | (from_user, to_user) | unique_together |

### NOT NULL Constraints

All fields are NOT NULL except:
- User: `first_name`, `last_name`, `last_login`
- Profile: `location`, `move_in_date`
- ConnectionRequest: `message`
- Listing: `amenities`, `custom_amenities`

### Check Constraints (Application Level)

These are enforced by validators, not database constraints:
- User.email: Must match `.edu` pattern
- Listing.availability_start: Cannot be in past
- Listing.availability_end: Cannot be in past

### Default Values

| Model | Field | Default |
|-------|-------|---------|
| User | is_verified | False |
| User | is_active | True |
| User | is_staff | False |
| User | is_superuser | False |
| Profile | visibility | True |
| Profile | eating_habit | 'no_preference' |
| Profile | smoking_preference | 'non_smoker' |
| Profile | sharing_preference | 'no_preference' |
| Profile | drinking_preference | 'no_preference' |
| Profile | pet_preference | 'no_preference' |
| Profile | cleanliness_preference | 'no_preference' |
| Profile | budget_min | 0 |
| Profile | budget_max | 5000 |
| Profile | location | '' |
| ConnectionRequest | status | 'pending' |
| ConnectionRequest | message | '' |
| Listing | amenities | '' |
| Listing | custom_amenities | '' |
| Listing | is_edited | False |
| Listing | is_active | True |
| Item | is_edited | False |
| Item | is_sold | False |
| Item | is_active | True |

---

## Migration Best Practices

### Before Adding New Fields

1. **Check for existing fields** - Review this document to avoid duplicates
2. **Choose appropriate field type** - Match existing patterns (e.g., CharField for choices)
3. **Set appropriate defaults** - Required for adding fields to existing tables
4. **Add to this document** - Update schema after migration

### Before Modifying Existing Fields

1. **Check existing data** - Ensure migration won't fail with existing records
2. **Write data migration if needed** - For complex changes
3. **Test migration on copy of production data**
4. **Update this document** - Reflect changes in schema

### Before Adding New Models

1. **Check relationships** - Ensure proper foreign keys and related_names
2. **Add indexes** - For frequently queried fields
3. **Set Meta options** - ordering, unique_together, etc.
4. **Update this document** - Add complete model schema

### Creating Migrations

```bash
# Create migrations for specific app
python manage.py makemigrations accounts

# Create empty migration for data migration
python manage.py makemigrations --empty accounts --name migrate_user_data

# Check migration SQL before applying
python manage.py sqlmigrate accounts 0001

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

---

## Schema Verification Queries

Use these commands to verify schema in production:

```bash
# Django shell
python manage.py shell

# Get field information
from accounts.models import User
User._meta.get_fields()

# Check field properties
User._meta.get_field('email')

# List all constraints
from django.db import connection
connection.introspection.get_constraints(connection.cursor(), 'accounts_user')
```

---

## Adding New Features: Checklist

When adding new features that require database changes:

- [ ] Review this schema document for existing fields/models
- [ ] Design new fields/models following existing patterns
- [ ] Add appropriate indexes for query performance
- [ ] Set proper defaults for new fields
- [ ] Add validators if needed (application level)
- [ ] Create migration: `python manage.py makemigrations`
- [ ] Review generated migration file
- [ ] Test migration: `python manage.py migrate`
- [ ] Test rollback: `python manage.py migrate <app> <previous_migration>`
- [ ] Update this document with new schema
- [ ] Update CLAUDE.md if architecture changes
- [ ] Commit migration files to git

---

**End of Schema Documentation**
