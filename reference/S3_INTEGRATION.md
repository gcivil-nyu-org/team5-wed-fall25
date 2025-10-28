# AWS S3 Integration Guide

This document explains how AWS S3 is integrated into CampusNest for persistent media storage across deployments.

## Overview

CampusNest uses AWS S3 to store user-uploaded media files (profile photos, listing images, marketplace images) to ensure they persist across deployments. Static files (CSS, JS) are served using WhiteNoise.

## Table of Contents

1. [Architecture](#architecture)
2. [AWS S3 Setup](#aws-s3-setup)
3. [Django Configuration](#django-configuration)
4. [Environment Variables](#environment-variables)
5. [Testing & Verification](#testing--verification)
6. [Troubleshooting](#troubleshooting)
7. [Important Notes](#important-notes)

---

## Architecture

### Storage Strategy

- **Media Files (User Uploads)**: AWS S3
  - Profile photos (`profile_photos/`)
  - Listing images (`listing_photos/`)
  - Marketplace images (`marketplace_photos/`)

- **Static Files (CSS/JS/Images)**: WhiteNoise (local serving)
  - Collected to `staticfiles/` directory
  - Served efficiently by WhiteNoise middleware

### Why This Approach?

- **S3 for Media**: Persists user uploads across deployments (Elastic Beanstalk deployments wipe local files)
- **WhiteNoise for Static**: Efficient static file serving without needing a separate S3 bucket/CDN
- **Cost-Effective**: Only pay for S3 storage of user uploads, not static files

---

## AWS S3 Setup

### 1. Create S3 Bucket

1. Go to **AWS S3 Console**
2. Click **Create bucket**
3. Configure:
   - **Bucket name**: `campusnest-media` (or your preferred name)
   - **Region**: `us-east-1` (or match your AWS region)
   - **Block Public Access settings**: **UNCHECK** "Block all public access"
   - Click **Create bucket**

### 2. Configure Bucket Policy (Public Read Access)

1. Select your bucket → **Permissions** tab
2. Scroll to **Bucket policy** → Click **Edit**
3. Paste this policy (replace `campusnest-media` with your bucket name):

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

4. Click **Save changes**

**Important**: This policy makes all objects in the bucket publicly readable via direct URLs.

### 3. Disable ACLs (Object Ownership)

Modern S3 buckets have ACLs disabled by default. If your bucket has ACLs enabled:

1. Go to **Permissions** → **Object Ownership**
2. Click **Edit**
3. Select **ACLs disabled (recommended)**
4. Click **Save changes**

This is why we set `AWS_DEFAULT_ACL = None` in Django settings.

### 4. Create IAM User with S3 Permissions

1. Go to **IAM Console** → **Users** → **Add users**
2. User name: `campusnest-s3-user`
3. Enable **Access key - Programmatic access**
4. Click **Next: Permissions**
5. **Attach policies directly**: Select `AmazonS3FullAccess` (or create a custom policy with limited permissions)
6. Click through to **Create user**
7. **IMPORTANT**: Save the **Access Key ID** and **Secret Access Key** (you can't view the secret again)

#### Custom IAM Policy (More Secure)

Instead of `AmazonS3FullAccess`, create a custom policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::campusnest-media",
        "arn:aws:s3:::campusnest-media/*"
      ]
    }
  ]
}
```

---

## Django Configuration

### Required Packages

Add to `requirements.txt`:

```txt
django-storages==1.14.6
boto3==1.40.60
```

Install:
```bash
pip install django-storages boto3
```

### Settings Configuration (`CampusNest/settings.py`)

#### 1. AWS S3 Settings

```python
# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "campusnest-media")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # Bucket has ACLs disabled, use bucket policy instead
AWS_S3_VERIFY = True
AWS_QUERYSTRING_AUTH = False
```

**Important Settings Explained:**
- `AWS_S3_FILE_OVERWRITE = False`: Prevents overwriting files with the same name (Django adds random suffix)
- `AWS_DEFAULT_ACL = None`: Required for buckets with ACLs disabled (uses bucket policy instead)
- `AWS_QUERYSTRING_AUTH = False`: Disables signed URLs (since bucket is public)

#### 2. Storage Backend Configuration (Django 4.2+)

```python
# Media files configuration
USE_S3 = os.getenv("USE_S3", "False") == "True"

if USE_S3:
    # S3 Media Storage Settings (Django 4.2+ STORAGES setting)
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
else:
    # Local Media Storage (for development) - Fallback
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
```

**Important**: Django 5.2 uses the new `STORAGES` setting, not the deprecated `DEFAULT_FILE_STORAGE`.

#### 3. Installed Apps

Add `storages` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "storages",
    # ...
]
```

#### 4. Middleware (WhiteNoise)

Ensure `WhiteNoiseMiddleware` is configured:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Must be after SecurityMiddleware
    # ... other middleware
]
```

#### 5. Static Files Configuration

```python
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
```

---

## Environment Variables

### Required Variables (`.env`)

```bash
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True  # Set to False in production

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# AWS S3 Configuration (REQUIRED FOR PRODUCTION)
USE_S3=True  # Set to False for local development
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=campusnest-media
AWS_S3_REGION_NAME=us-east-1

# AWS RDS Database (optional - falls back to SQLite if not set)
# RDS_HOSTNAME=your-rds-endpoint.rds.amazonaws.com
# RDS_DB_NAME=campusnest_db
# RDS_USERNAME=postgres
# RDS_PASSWORD=your-db-password
# RDS_PORT=5432
```

### Development vs Production

**Local Development:**
```bash
USE_S3=False
DEBUG=True
```
- Uses local `media/` folder for uploads
- Django serves static files automatically

**Production (AWS Elastic Beanstalk):**
```bash
USE_S3=True
DEBUG=False
```
- Uses S3 for media uploads
- WhiteNoise serves static files

---

## Testing & Verification

### Test Scripts

Located in project root:

1. **`test_s3_connection.py`** - Test S3 credentials and connectivity
2. **`check_s3_images.py`** - List all objects in S3 bucket with URLs
3. **`test_public_access.py`** - Verify images are publicly accessible
4. **`check_storage.py`** - Verify Django storage backend configuration
5. **`test_production.py`** - Test production settings (DEBUG=False)

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Test S3 connection and permissions
python test_s3_connection.py

# Check S3 bucket contents
python check_s3_images.py

# Test if images are publicly accessible
python test_public_access.py

# Verify storage backend
python check_storage.py

# Test production settings
python test_production.py
```

### Expected Output (test_s3_connection.py)

```
============================================================
S3 Configuration Test
============================================================

1. Environment Variables:
   USE_S3: True
   AWS_ACCESS_KEY_ID: AKIAVT5YTM...
   AWS_SECRET_ACCESS_KEY: ********************
   AWS_STORAGE_BUCKET_NAME: campusnest-media
   AWS_S3_REGION_NAME: us-east-1

2. Django Settings:
   USE_S3: True
   STORAGES['default']: storages.backends.s3boto3.S3Boto3Storage
   MEDIA_URL: https://campusnest-media.s3.amazonaws.com/
   AWS_STORAGE_BUCKET_NAME: campusnest-media
   AWS_S3_REGION_NAME: us-east-1

3. Testing S3 Connection:
   Checking bucket 'campusnest-media'...
   ✓ Bucket exists and is accessible

4. Bucket Contents:
   Found 2 objects (showing first 10):
     - profile_photos/Profile_Photo.jpeg (188715 bytes)
     - profile_photos/Profile_Photo_Copy_5.jpeg (188715 bytes)

5. Testing Upload Permissions:
   ✓ Successfully uploaded test file: test_upload.txt
   ✓ Successfully deleted test file

============================================================
Test Complete
============================================================
```

### Manual Testing

1. **Upload a profile photo** through Django admin or app
2. **Check S3 bucket** in AWS Console - image should appear
3. **Check local file system** - NO `profile_photos/` folder should exist in project root
4. **View the image** in browser - should load from S3 URL

---

## Troubleshooting

### Problem: Images not uploading to S3

**Symptoms**: Images saved locally instead of S3

**Solutions**:

1. **Verify environment variables are loaded**:
   ```bash
   python check_storage.py
   ```
   Should show: `Storage class: S3Storage`

2. **Restart Django server**:
   Django caches settings on startup. Stop server (Ctrl+C) and restart:
   ```bash
   python manage.py runserver
   ```

3. **Check `.env` file**:
   ```bash
   USE_S3=True  # Must be exactly "True" (case-sensitive)
   ```

4. **Verify `storages` is installed**:
   ```bash
   pip list | grep django-storages
   ```

---

### Problem: 403 Access Denied when viewing images

**Symptoms**: Images upload to S3 but show 403 error in browser

**Solutions**:

1. **Add bucket policy** (see [AWS S3 Setup](#2-configure-bucket-policy-public-read-access))

2. **Disable "Block Public Access"**:
   - S3 Console → Bucket → Permissions → Block public access → Edit → Uncheck all → Save

3. **Test public access**:
   ```bash
   python test_public_access.py
   ```

---

### Problem: AccessControlListNotSupported error

**Symptoms**: Error when uploading: `The bucket does not allow ACLs`

**Solution**: Set `AWS_DEFAULT_ACL = None` in settings (already configured)

```python
AWS_DEFAULT_ACL = None  # Bucket has ACLs disabled, use bucket policy instead
```

---

### Problem: Images stored in both S3 AND locally

**Symptoms**: Images appear in S3 but also in `profile_photos/` folder in project root

**Solutions**:

1. **Remove `AWS_LOCATION` setting** (if present):
   ```python
   # Remove this line:
   # AWS_LOCATION = ""
   ```

2. **Delete local folder**:
   ```bash
   rm -rf profile_photos/
   ```

3. **Restart Django server**

4. **Test upload again** - local folder should NOT be recreated

---

### Problem: Static files (CSS/JS) not loading with DEBUG=False

**Symptoms**: CSS/JS broken in production mode

**Solutions**:

1. **Run collectstatic**:
   ```bash
   python manage.py collectstatic --noinput
   ```

2. **Verify WhiteNoise is configured** (see [Django Configuration](#4-middleware-whitenoise))

3. **Check STORAGES setting**:
   ```python
   STORAGES = {
       "staticfiles": {
           "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
       },
   }
   ```

4. **Test production settings**:
   ```bash
   python test_production.py
   ```

---

### Problem: Django tests fail with S3 imports

**Symptoms**: Test suite shows import errors from test scripts

**Solution**: Flake8 picks up test scripts as modules. Scripts are correctly named with `test_` prefix but are standalone utilities, not Django tests. They should not cause test failures as they're not in a Django app's `tests/` directory.

If errors persist, ensure scripts don't have syntax errors:
```bash
flake8 test_*.py check_*.py
```

---

## Important Notes

### Do NOT commit sensitive data

**Never commit** `.env` file or AWS credentials to version control!

Ensure `.gitignore` includes:
```
.env
*.env
```

### AWS Costs

- **S3 Storage**: ~$0.023 per GB/month (first 50 TB)
- **S3 Requests**: PUT/POST ~$0.005 per 1,000 requests
- **Data Transfer**: Free for first 100 GB/month out to internet

Estimated cost for small app: **< $1/month**

### Production Deployment Checklist

Before deploying to AWS Elastic Beanstalk:

- [ ] Set `USE_S3=True` in production environment variables
- [ ] Set `DEBUG=False` in production
- [ ] Run `python manage.py collectstatic --noinput` (include in deployment script)
- [ ] Verify S3 bucket policy is configured
- [ ] Verify IAM credentials have correct permissions
- [ ] Test image upload after deployment

### File Upload Limits

Django default: **2.5 MB**

To increase, add to `settings.py`:
```python
# 10 MB max upload
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760
```

### Bucket Naming Rules

- Must be globally unique across all AWS accounts
- Only lowercase letters, numbers, hyphens
- 3-63 characters long
- Cannot start/end with hyphen

---

## Additional Resources

- **django-storages Documentation**: https://django-storages.readthedocs.io/
- **boto3 Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **WhiteNoise Documentation**: http://whitenoise.evans.io/
- **AWS S3 Pricing**: https://aws.amazon.com/s3/pricing/
- **Django Static Files**: https://docs.djangoproject.com/en/5.2/howto/static-files/

---

## Maintenance

### Regular Tasks

1. **Monitor S3 costs** in AWS Billing Console
2. **Review IAM credentials** - rotate every 90 days
3. **Check for unused files** in S3 (consider lifecycle policies)
4. **Test S3 integration** after Django/boto3 upgrades

### Backup Strategy

S3 provides 99.999999999% durability, but consider:

- **Enable S3 Versioning** (protection against accidental deletion)
- **Set up S3 Lifecycle Policies** (archive old files to Glacier)
- **Cross-Region Replication** (disaster recovery)

---

## Version History

- **v1.0** (2025-10-28): Initial S3 integration
  - django-storages: 1.14.6
  - boto3: 1.40.60
  - Django: 5.2.7
  - Bucket: `campusnest-media`
  - Region: `us-east-1`

---

**Last Updated**: October 28, 2025
**Maintained By**: CampusNest Development Team
