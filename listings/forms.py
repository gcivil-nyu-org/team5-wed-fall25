from django import forms
from django.core.exceptions import ValidationError
from .models import Listing, ListingImage
from .widgets import MultiFileInput


class ListingForm(forms.ModelForm):
    images = forms.ImageField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=True,
        label="Upload up to 5 images"
    )

    class Meta:
        model = Listing
        fields = [
            'title',
            'address',
            'rent',
            'description',
            'amenities',
            'availability_start',
            'availability_end',
            'images',
        ]

    def clean_rent(self):
        rent = self.cleaned_data.get('rent')
        if rent is not None and rent <= 0:
            raise ValidationError("Rent must be a positive value.")
        return rent

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters long.")
        return description

    def clean_images(self):
        files = self.files.getlist('images')
        if len(files) > 5:
            raise ValidationError("You can upload a maximum of 5 images.")
        for file in files:
            if not file.content_type.startswith('image/'):
                raise ValidationError(f"{file.name} is not a valid image file.")
        return files
