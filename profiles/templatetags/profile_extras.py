from django import template
from django.core.files.storage import default_storage
import os

register = template.Library()


@register.filter
def file_exists(file_field):
    """
    Check if a file field's file actually exists on the filesystem.
    Returns True if the file exists, False otherwise.
    """
    if not file_field:
        return False

    try:
        # Check if the file exists using Django's storage backend
        return default_storage.exists(file_field.name)
    except Exception:
        return False
