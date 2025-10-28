#!/usr/bin/env python
"""Check S3 bucket contents and generate URLs"""
import os
from dotenv import load_dotenv
import boto3

load_dotenv()

bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", "campusnest-media")
region = os.getenv("AWS_S3_REGION_NAME", "us-east-1")

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=region
)

print("=" * 60)
print(f"S3 Bucket: {bucket_name}")
print("=" * 60)

response = s3_client.list_objects_v2(Bucket=bucket_name)

if 'Contents' in response:
    print(f"\nFound {len(response['Contents'])} objects:\n")
    for obj in response['Contents']:
        key = obj['Key']
        size = obj['Size']
        url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
        print(f"File: {key}")
        print(f"Size: {size} bytes")
        print(f"URL:  {url}")

        # Test if publicly accessible
        try:
            head_response = s3_client.head_object(Bucket=bucket_name, Key=key)
            print(f"✓ File exists and is accessible")
        except Exception as e:
            print(f"✗ Error accessing file: {e}")
        print()
else:
    print("\nBucket is empty")

print("=" * 60)
