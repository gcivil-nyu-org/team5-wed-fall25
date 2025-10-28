#!/usr/bin/env python
"""
Test script to verify S3 configuration and connection.
Run with: python test_s3_connection.py
"""
import os
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CampusNest.settings')
django.setup()

from django.conf import settings
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

print("=" * 60)
print("S3 Configuration Test")
print("=" * 60)

# Check environment variables
print("\n1. Environment Variables:")
print(f"   USE_S3: {os.getenv('USE_S3')}")
print(f"   AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')[:10]}..." if os.getenv('AWS_ACCESS_KEY_ID') else "   AWS_ACCESS_KEY_ID: Not set")
print(f"   AWS_SECRET_ACCESS_KEY: {'*' * 20}" if os.getenv('AWS_SECRET_ACCESS_KEY') else "   AWS_SECRET_ACCESS_KEY: Not set")
print(f"   AWS_STORAGE_BUCKET_NAME: {os.getenv('AWS_STORAGE_BUCKET_NAME')}")
print(f"   AWS_S3_REGION_NAME: {os.getenv('AWS_S3_REGION_NAME')}")

# Check Django settings
print("\n2. Django Settings:")
print(f"   USE_S3: {settings.USE_S3}")
print(f"   DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE if settings.USE_S3 else 'Local storage'}")
print(f"   MEDIA_URL: {settings.MEDIA_URL}")
print(f"   AWS_STORAGE_BUCKET_NAME: {settings.AWS_STORAGE_BUCKET_NAME}")
print(f"   AWS_S3_REGION_NAME: {settings.AWS_S3_REGION_NAME}")

# Test S3 connection
print("\n3. Testing S3 Connection:")
try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    # Check if bucket exists
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    print(f"   Checking bucket '{bucket_name}'...")

    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
        print(f"   ✓ Bucket exists and is accessible")

        # List objects in bucket
        print(f"\n4. Bucket Contents:")
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
        if 'Contents' in response:
            print(f"   Found {len(response['Contents'])} objects (showing first 10):")
            for obj in response['Contents'][:10]:
                print(f"     - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("   Bucket is empty")

        # Test upload permissions
        print(f"\n5. Testing Upload Permissions:")
        test_key = 'test_upload.txt'
        test_content = b'This is a test file'

        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        print(f"   ✓ Successfully uploaded test file: {test_key}")

        # Clean up test file
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"   ✓ Successfully deleted test file")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"   ✗ Bucket '{bucket_name}' does not exist")
            print(f"   → Please create the bucket in AWS Console")
        elif error_code == '403':
            print(f"   ✗ Access denied to bucket '{bucket_name}'")
            print(f"   → Check IAM permissions for your AWS credentials")
        else:
            print(f"   ✗ Error: {e}")

except NoCredentialsError:
    print("   ✗ AWS credentials not found")
    print("   → Check your .env file")
except Exception as e:
    print(f"   ✗ Unexpected error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
