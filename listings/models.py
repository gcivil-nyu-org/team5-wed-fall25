from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_future_date(value):
    """Validate that the date is not in the past"""
    if value < timezone.now().date():
        raise ValidationError('Date cannot be in the past.')

class Listing(models.Model):
    AMENITY_CHOICES = [
        ('furnished', 'Furnished'),
        ('utilities', 'Utilities Included'),
        ('wifi', 'WiFi'),
        ('laundry', 'Laundry'),
        ('elevator', 'Elevator'),
        ('pets', 'Pets Allowed'),
        ('ac', 'Air Conditioning'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=2000)
    amenities = models.CharField(max_length=500, blank=True)
    custom_amenities = models.CharField(max_length=300, blank=True)
    availability_start = models.DateField(validators=[validate_future_date])
    availability_end = models.DateField(validators=[validate_future_date])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Add this field
    is_edited = models.BooleanField(default=False)  # Add this field
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_amenities_list(self):
        """Return amenities as a list"""
        if self.amenities:
            return self.amenities.split(',')
        return []
    
    def get_amenities_display(self):
        """Return formatted amenities for display"""
        amenities_dict = dict(self.AMENITY_CHOICES)
        amenities_list = self.get_amenities_list()
        display_list = [amenities_dict.get(amenity, amenity) for amenity in amenities_list]
        
        # Add custom amenities if they exist
        if self.custom_amenities:
            custom_list = [a.strip() for a in self.custom_amenities.split(',') if a.strip()]
            display_list.extend(custom_list)
        
        return display_list


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_photos/')

    def __str__(self):
        return f"Image for {self.listing.title}"
