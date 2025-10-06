import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class MyUserManager(BaseUserManager):
    def create_user(self, cognito_sub, email, **extra_fields):
        if not email:
            raise ValueError("Email required")
        user = self.model(
            cognito_sub=cognito_sub,
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_unusable_password()  # Since Cognito handles auth
        user.save(using=self._db)
        return user

    def create_superuser(self, cognito_sub, email, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(cognito_sub, email, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cognito_sub = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    objects = MyUserManager()

    USERNAME_FIELD = 'cognito_sub'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email

