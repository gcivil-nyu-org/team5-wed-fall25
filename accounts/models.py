from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import re

def validation_edu_email(value):
    """
    Stricter validation: ensures domain is exactly *.edu (not *.*.edu)
    """
    # This pattern ensures only one domain level before .edu
    # Example: user@university.edu ✅
    # Example: user@sub.university.edu ❌
    
    strict_edu_pattern = r'^[\w\.-]+@[\w-]+\.edu$'
    
    if not re.match(strict_edu_pattern, value):
        raise ValidationError(
            'Please enter a valid .edu email address from your university'
        )
class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        validators=[validation_edu_email]
    )

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def __str__(self):
        return self.email


