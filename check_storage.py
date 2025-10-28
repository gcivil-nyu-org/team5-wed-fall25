#!/usr/bin/env python
"""
Check what storage backend Django is using for file uploads.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CampusNest.settings')
django.setup()

from django.conf import settings
from profiles.models import Profile

print("=" * 60)
print("Django Storage Backend Check")
print("=" * 60)

print("\n1. Environment Variable (from .env):")
from dotenv import load_dotenv
load_dotenv()
print(f"   USE_S3 from .env: {os.getenv('USE_S3')}")

print("\n2. Django Settings:")
print(f"   settings.USE_S3: {settings.USE_S3}")
print(f"   settings.DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
print(f"   settings.MEDIA_URL: {settings.MEDIA_URL}")
print(f"   settings.MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'Not set')}")

print("\n3. Profile Model Storage:")
profile_photo_field = Profile._meta.get_field('profile_photo')
storage_class = profile_photo_field.storage.__class__.__name__
storage_location = str(profile_photo_field.storage.location) if hasattr(profile_photo_field.storage, 'location') else 'N/A'
print(f"   Storage class: {storage_class}")
print(f"   Storage location: {storage_location}")
print(f"   Storage module: {profile_photo_field.storage.__class__.__module__}")

if hasattr(profile_photo_field.storage, 'bucket_name'):
    print(f"   S3 Bucket: {profile_photo_field.storage.bucket_name}")
else:
    print(f"   S3 Bucket: Not using S3 storage")

print("\n" + "=" * 60)
