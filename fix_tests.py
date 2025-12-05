#!/usr/bin/env python3
"""Script to update test files from old address field to new three-field structure"""

import re

def parse_address(address_str):
    """Parse an address string into street_address, city, zipcode components"""
    # Handle addresses like "123 Main St, Brooklyn, NY 11201"
    if ", NY " in address_str:
        parts = address_str.split(", NY ")
        zipcode = parts[1].strip()
        street_parts = parts[0].split(", ")
        if len(street_parts) > 1:
            street_address = ", ".join(street_parts)
        else:
            street_address = street_parts[0]
        return street_address, "New York", zipcode
    # Handle simple addresses like "123 Main St"
    else:
        return address_str, "New York", "10012"

def replace_model_create(match):
    """Replace address= in Listing.objects.create() calls"""
    address_value = match.group(1)
    street, city, zipcode = parse_address(address_value)
    return f'street_address="{street}",\n            city="{city}",\n            zipcode="{zipcode}",'

def replace_form_data(match):
    """Replace "address": in form data dictionaries"""
    address_value = match.group(1)
    street, city, zipcode = parse_address(address_value)
    return f'"street_address": "{street}",\n            "city": "{city}",\n            "zipcode": "{zipcode}",'

# Read the file
with open('listings/tests.py', 'r') as f:
    content = f.read()

# Replace in Listing.objects.create() calls
# Pattern: address="value",
content = re.sub(
    r'address="([^"]+)",',
    replace_model_create,
    content
)

# Replace in form data dictionaries
# Pattern: "address": "value",
content = re.sub(
    r'"address":\s*"([^"]+)",',
    replace_form_data,
    content
)

# Write back
with open('listings/tests.py', 'w') as f:
    f.write(content)

print("✓ Updated listings/tests.py")

# Now update messaging/tests.py
with open('messaging/tests.py', 'r') as f:
    content = f.read()

content = re.sub(
    r'address="([^"]+)",',
    replace_model_create,
    content
)

with open('messaging/tests.py', 'w') as f:
    f.write(content)

print("✓ Updated messaging/tests.py")
