from django.db import models
from django.conf import settings

class Listing(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=2000)
    amenities = models.CharField(max_length=300, blank=True)
    availability_start = models.DateField()
    availability_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_photos/')

    def __str__(self):
        return f"Image for {self.listing.title}"
