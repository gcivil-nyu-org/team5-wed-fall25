from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Listing, ListingImage


class ListingForm(forms.ModelForm):
    # Create individual checkbox fields for amenities
    amenities = forms.MultipleChoiceField(
        choices=Listing.AMENITY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'amenity-checkbox'
        }),
        required=False,
        label='Amenities'
    )
    
    custom_amenities = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Add custom amenities (comma-separated, e.g., "Balcony, Dishwasher, Pool")',
            'class': 'form-control'
        }),
        label='Other Amenities (Optional)',
        help_text='Enter additional amenities separated by commas'
    )
    
    class Meta:
        model = Listing
        fields = [
            'title',
            'description',
            'address',
            'rent',
            'amenities',
            'custom_amenities',
            'availability_start',
            'availability_end',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Cozy Studio near NYU Campus',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe your space, neighborhood, and what makes it special (minimum 20 characters)',
                'class': 'form-control'
            }),
            'address': forms.TextInput(attrs={
                'placeholder': 'e.g., 123 Main St, Brooklyn, NY 11201',
                'class': 'form-control'
            }),
            'rent': forms.NumberInput(attrs={
                'placeholder': 'Monthly rent in USD',
                'step': '0.01',
                'min': '0',
                'class': 'form-control'
            }),
            'availability_start': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'availability_end': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Listing Title *',
            'description': 'Description *',
            'address': 'Full Address *',
            'rent': 'Monthly Rent ($) *',
            'availability_start': 'Available From *',
            'availability_end': 'Available Until *',
        }

    def clean_rent(self):
        rent = self.cleaned_data.get('rent')
        if rent is not None and rent <= 0:
            raise ValidationError("Rent must be a positive value.")
        if rent is not None and rent > 100000:
            raise ValidationError("Rent amount seems unrealistic. Please verify.")
        return rent

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters long.")
        return description

    def clean_availability_start(self):
        start_date = self.cleaned_data.get('availability_start')
        if start_date and start_date < timezone.now().date():
            raise ValidationError("Start date cannot be in the past.")
        return start_date

    def clean_availability_end(self):
        end_date = self.cleaned_data.get('availability_end')
        if end_date and end_date < timezone.now().date():
            raise ValidationError("End date cannot be in the past.")
        return end_date

    def clean_custom_amenities(self):
        custom = self.cleaned_data.get('custom_amenities', '')
        if custom:
            # Clean up the input
            amenities_list = [a.strip() for a in custom.split(',') if a.strip()]
            return ', '.join(amenities_list)
        return custom

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('availability_start')
        end_date = cleaned_data.get('availability_end')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError("End date must be after start date.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert amenities list to comma-separated string
        amenities_list = self.cleaned_data.get('amenities', [])
        instance.amenities = ','.join(amenities_list)
        # Custom amenities are already saved by default
        if commit:
            instance.save()
        return instance
