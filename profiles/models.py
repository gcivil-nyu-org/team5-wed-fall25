from django.db import models
from django.conf import settings


class Profile(models.Model):
    UNIVERSITY_CHOICES = [
        ("NYU", "New York University"),
        ("Columbia", "Columbia University"),
        ("Fordham", "Fordham University"),
        ("CUNY", "City University of New York"),
        ("Pace", "Pace University"),
        ("The New School", "The New School"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500)
    university = models.CharField(max_length=100, choices=UNIVERSITY_CHOICES)
    profile_photo = models.ImageField(upload_to="profile_photos/")
    visibility = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
