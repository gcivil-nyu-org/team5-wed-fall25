#!/usr/bin/env python
"""
Test script to verify production settings work correctly.
Temporarily sets DEBUG=False to test static files.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CampusNest.settings")
os.environ["DEBUG"] = "False"

django.setup()

from django.conf import settings

print("=" * 60)
print("Production Settings Check")
print("=" * 60)

print(f"\nDEBUG: {settings.DEBUG}")
print(f"STATIC_URL: {settings.STATIC_URL}")
print(f"STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"MEDIA_URL: {settings.MEDIA_URL}")
print(f"\nSTORAGES Configuration:")
print(f"  default: {settings.STORAGES['default']['BACKEND']}")
print(f"  staticfiles: {settings.STORAGES['staticfiles']['BACKEND']}")

# Check if staticfiles directory exists and has files
import os

staticfiles_path = settings.STATIC_ROOT
if os.path.exists(staticfiles_path):
    file_count = sum(len(files) for _, _, files in os.walk(staticfiles_path))
    print(f"\nStatic files collected: {file_count} files in {staticfiles_path}")
else:
    print(f"\n⚠ Static files directory not found: {staticfiles_path}")
    print("  Run: python manage.py collectstatic")

print("\n" + "=" * 60)
print("To test in browser:")
print("1. Set DEBUG=False in .env")
print("2. Restart Django server")
print("3. Visit http://localhost:8000")
print("=" * 60)
