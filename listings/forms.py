from django import forms
from django.core.exceptions import ValidationError
from .models import Listing, ListingImage


class ListingForm(forms.ModelForm):
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

    # def clean(self):
    #     cleaned_data = super().clean()
    #     files = self.files.getlist('images')
    #
    #     if not files:
    #         raise ValidationError({'images': "Please upload at least one image."})
    #
    #     if len(files) > 5:
    #         raise ValidationError({'images': "You can upload a maximum of 5 images."})
    #
    #     for file in files:
    #         if file.content_type and not file.content_type.startswith('image/'):
    #             raise ValidationError({'images': f"{file.name} is not a valid image file."})
    #
    #     return cleaned_data
