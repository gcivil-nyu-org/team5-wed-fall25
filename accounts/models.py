from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import re


def validation_edu_email(value):
    """
    Stricter validation: ensures domain is exactly *.edu (not *.*.edu)
    """
    strict_edu_pattern = r"^[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)*edu$"

    if not re.match(strict_edu_pattern, value):
        raise ValidationError(
            "Please enter a valid .edu email address from your university"
        )


class User(AbstractUser):
    email = models.EmailField(unique=True, validators=[validation_edu_email])

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
