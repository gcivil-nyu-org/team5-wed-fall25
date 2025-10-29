from django.db import models
from django.conf import settings
from .constants import ITEM_CATEGORY_CHOICES, ITEM_CONDITION_CHOICES

# from django.core.exceptions import ValidationError


class Item(models.Model):
    CONDITION_CHOICES = ITEM_CONDITION_CHOICES
    CATEGORY_CHOICES = ITEM_CATEGORY_CHOICES

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    condition = models.CharField(max_length=20, choices=ITEM_CONDITION_CHOICES)
    category = models.CharField(max_length=50, choices=ITEM_CATEGORY_CHOICES, default="other")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pickup_location = models.CharField(max_length=300)
    owner_name = models.CharField(max_length=200)
    contact_details = models.CharField(max_length=300)  # Phone or email
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ["-created_at"]


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="marketplace_photos/")

    def __str__(self):
        return f"Image for {self.item.title}"
