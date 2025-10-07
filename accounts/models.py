from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


def validation_edu_email(value):
    if not value.endswith('.edu'):
        raise ValidationError('You must use a valid .edu email address to register.')


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


