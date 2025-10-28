#!/usr/bin/env python
"""Test if S3 URLs are publicly accessible"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", "campusnest-media")

# Test URLs
test_urls = [
    f"https://{bucket_name}.s3.amazonaws.com/profile_photos/Profile_Photo.jpeg",
    f"https://{bucket_name}.s3.amazonaws.com/profile_photos/Profile_Photo_Copy_5.jpeg",
]

print("=" * 60)
print("Testing Public Access to S3 URLs")
print("=" * 60)

for url in test_urls:
    print(f"\nTesting: {url}")
    try:
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            print(f"✓ Publicly accessible (Status: {response.status_code})")
        elif response.status_code == 403:
            print(f"✗ Access Denied (Status: {response.status_code})")
            print("  → Bucket policy needed to make objects public")
        else:
            print(f"⚠ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("If you see 403 errors, you need to add a bucket policy:")
print("Go to AWS Console → S3 → campusnest-media → Permissions → Bucket Policy")
print("=" * 60)
