from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Listing
from .constants import AMENITY_CHOICES


class ListingForm(forms.ModelForm):
    # Create individual checkbox fields for amenities
    amenities = forms.MultipleChoiceField(
        choices=AMENITY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "amenity-checkbox"}),
        required=False,
        label="Amenities",
    )

    custom_amenities = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": 'Add custom amenities (comma-separated, e.g., "Balcony, Dishwasher, Pool")',
                "class": "form-control",
            }
        ),
        label="Other Amenities (Optional)",
        help_text="Enter additional amenities separated by commas",
    )

    class Meta:
        model = Listing
        fields = [
            "title",
            "description",
            "address",
            "rent",
            "amenities",
            "custom_amenities",
            "availability_start",
            "availability_end",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "e.g., Cozy Studio near NYU Campus",
                    "class": "form-control",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Describe your space, neighborhood, and what makes it special (minimum 20 characters)",
                    "class": "form-control",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "placeholder": "e.g., 123 Main St, Brooklyn, NY 11201",
                    "class": "form-control",
                }
            ),
            "rent": forms.NumberInput(
                attrs={
                    "placeholder": "Monthly rent in USD",
                    "step": "0.01",
                    "min": "0",
                    "class": "form-control",
                }
            ),
            "availability_start": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "availability_end": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
        labels = {
            "title": "Listing Title *",
            "description": "Description *",
            "address": "Full Address *",
            "rent": "Monthly Rent ($) *",
            "availability_start": "Available From *",
            "availability_end": "Available Until *",
        }

    def clean_rent(self):
        rent = self.cleaned_data.get("rent")
        if rent is not None and rent <= 0:
            raise ValidationError("Rent must be a positive value.")
        if rent is not None and rent < 100:
            raise ValidationError(
                "Rent must be at least $100/month. Please enter a realistic rent amount."
            )
        if rent is not None and rent > 100000:
            raise ValidationError("Rent amount seems unrealistic. Please verify.")
        return rent

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters long.")
        if len(title) > 200:
            raise ValidationError("Title cannot exceed 200 characters.")
        return title

    def clean_address(self):
        address = self.cleaned_data.get("address", "").strip()
        if not address:
            raise ValidationError("Address is required.")
        if len(address) < 10:
            raise ValidationError(
                "Please enter a complete address (at least 10 characters)."
            )
        # Check if address contains basic components (street number, street name, city/state)
        if "," not in address:
            raise ValidationError(
                "Please enter a complete address including street, city, and state (e.g., '123 Main St, Brooklyn, NY 11201')."
            )
        return address

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if not description:
            raise ValidationError("Description is required.")
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters long.")
        if len(description) > 2000:
            raise ValidationError("Description cannot exceed 2000 characters.")
        return description

    def clean_availability_start(self):
        start_date = self.cleaned_data.get("availability_start")
        if start_date and start_date < timezone.now().date():
            raise ValidationError("Start date cannot be in the past.")
        return start_date

    def clean_availability_end(self):
        end_date = self.cleaned_data.get("availability_end")
        if end_date and end_date < timezone.now().date():
            raise ValidationError("End date cannot be in the past.")
        return end_date

    def clean_custom_amenities(self):
        custom = self.cleaned_data.get("custom_amenities", "")
        if custom:
            # Clean up the input
            amenities_list = [a.strip() for a in custom.split(",") if a.strip()]
            return ", ".join(amenities_list)
        return custom

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("availability_start")
        end_date = cleaned_data.get("availability_end")

        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError("End date must be after start date.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert amenities list to comma-separated string
        amenities_list = self.cleaned_data.get("amenities", [])
        instance.amenities = ",".join(amenities_list)
        # Custom amenities are already saved by default
        if commit:
            instance.save()
        return instance
