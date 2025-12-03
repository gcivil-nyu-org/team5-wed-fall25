from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_future_or_today_date(value):
    """Validate that the date is not in the past (today is allowed)"""
    if value and value < timezone.now().date():
        raise ValidationError("Move-in date cannot be in the past.")


class Profile(models.Model):
    UNIVERSITY_CHOICES = [
        ("NYU", "New York University"),
        ("Columbia", "Columbia University"),
        ("Fordham", "Fordham University"),
        ("CUNY", "City University of New York"),
        ("Pace", "Pace University"),
        ("The New School", "The New School"),
    ]

    # Preference Choices
    EATING_CHOICES = [
        ("vegetarian", "Vegetarian"),
        ("vegan", "Vegan"),
        ("no_preference", "No Preference"),
    ]

    SMOKING_CHOICES = [
        ("non_smoker", "Non-Smoker"),
        ("smoker", "Smoker"),
        ("occasionally", "Occasionally"),
    ]

    SHARING_CHOICES = [
        ("sharing", "Open to Sharing"),
        ("non_sharing", "Prefer Not to Share"),
        ("no_preference", "No Preference"),
    ]

    DRINKING_CHOICES = [
        ("non_drinker", "Non-Drinker"),
        ("social_drinker", "Social Drinker"),
        ("regular_drinker", "Regular Drinker"),
        ("no_preference", "No Preference"),
    ]

    PET_CHOICES = [
        ("no_pets", "No Pets"),
        ("cats", "Cats"),
        ("dogs", "Dogs"),
        ("other", "Other"),
        ("no_preference", "No Preference"),
    ]

    CLEANLINESS_CHOICES = [
        ("very_clean", "Very Clean"),
        ("clean", "Clean"),
        ("moderate", "Moderate"),
        ("relaxed", "Relaxed"),
        ("no_preference", "No Preference"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500)
    university = models.CharField(max_length=100, choices=UNIVERSITY_CHOICES)
    profile_photo = models.ImageField(
        upload_to="profile_photos/", blank=True, null=True
    )
    visibility = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Lifestyle Preference Fields
    eating_habit = models.CharField(
        max_length=20,
        choices=EATING_CHOICES,
        default="no_preference",
        verbose_name="Eating Preference",
    )
    smoking_preference = models.CharField(
        max_length=20,
        choices=SMOKING_CHOICES,
        default="non_smoker",
        verbose_name="Smoking Preference",
    )
    sharing_preference = models.CharField(
        max_length=20,
        choices=SHARING_CHOICES,
        default="no_preference",
        verbose_name="Sharing Preference",
    )
    drinking_preference = models.CharField(
        max_length=20,
        choices=DRINKING_CHOICES,
        default="no_preference",
        verbose_name="Drinking Preference",
    )
    pet_preference = models.CharField(
        max_length=20,
        choices=PET_CHOICES,
        default="no_preference",
        verbose_name="Pet Preference",
    )
    cleanliness_preference = models.CharField(
        max_length=20,
        choices=CLEANLINESS_CHOICES,
        default="no_preference",
        verbose_name="Cleanliness Preference",
    )

    # Housing Preference Fields
    budget_min = models.IntegerField(
        default=0, verbose_name="Minimum Monthly Budget ($)"
    )
    budget_max = models.IntegerField(
        default=5000, verbose_name="Maximum Monthly Budget ($)"
    )
    location = models.CharField(
        max_length=200,
        default="",
        blank=True,
        verbose_name="Preferred Location/Neighborhood",
    )
    move_in_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Preferred Move-In Date",
        validators=[validate_future_or_today_date],
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_preference_display_with_icon(self, preference_type):
        """Helper method to get preference with appropriate icon"""
        icons = {
            # Eating
            "vegetarian": "🥗",
            "no_preference": "🤷",
            "vegan": "🌱",
            # Sm
            "non_smoker": "🚭",
            "smoker": "🚬",
            "occasionally": "😶‍🌫️",
            # Sharing
            "sharing": "🤝",
            "non_sharing": "🚫",
            "no_preference": "🤷",
            # Drinking
            "non_drinker": "☕",
            "social_drinker": "🍻",
            "regular_drinker": "🍷",
            "no_preference": "🤷",
            # Pets
            "no_pets": "🚫",
            "cats": "🐱",
            "dogs": "🐕",
            "other": "🐾",
            # Cleanliness
            "very_clean": "✨",
            "clean": "🧹",
            "moderate": "🏠",
            "relaxed": "😎",
        }

        if preference_type == "eating":
            value = self.eating_habit
            display = self.get_eating_habit_display()
        elif preference_type == "smoking":
            value = self.smoking_preference
            display = self.get_smoking_preference_display()
        elif preference_type == "sharing":
            value = self.sharing_preference
            display = self.get_sharing_preference_display()
        elif preference_type == "drinking":
            value = self.drinking_preference
            display = self.get_drinking_preference_display()
        elif preference_type == "pets":
            value = self.pet_preference
            display = self.get_pet_preference_display()
        elif preference_type == "cleanliness":
            value = self.cleanliness_preference
            display = self.get_cleanliness_preference_display()
        else:
            return ""

        icon = icons.get(value, "")
        return f"{icon} {display}"


class Favorite(models.Model):
    """Model to track favorited roommate profiles"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    favorite_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "favorite_profile")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} favorited {self.favorite_profile.user.username}"


class ConnectionRequest(models.Model):
    """Model to track connection requests between users"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connection_requests_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="connection_requests_received",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    message = models.TextField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("from_user", "to_user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"
