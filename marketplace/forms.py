from django import forms
from django.core.exceptions import ValidationError
from .models import Item
import re


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "title",
            "description",
            "category",
            "condition",
            "price",
            "street_address",
            "city",
            "zipcode",
            "latitude",
            "longitude",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "e.g., iPhone 13 Pro Max",
                    "class": "form-control",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Describe the item, its condition, and any additional details (minimum 20 characters)",
                    "class": "form-control",
                }
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "condition": forms.Select(attrs={"class": "form-control"}),
            "price": forms.NumberInput(
                attrs={
                    "placeholder": "Price in USD",
                    "step": "0.01",
                    "min": "0",
                    "class": "form-control",
                }
            ),
            "street_address": forms.TextInput(
                attrs={
                    "placeholder": "e.g., 70 Washington Square South",
                    "class": "form-control",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "e.g., New York",
                    "class": "form-control",
                }
            ),
            "zipcode": forms.TextInput(
                attrs={
                    "placeholder": "e.g., 10012",
                    "class": "form-control",
                }
            ),
            "latitude": forms.HiddenInput(attrs={"id": "id_latitude"}),
            "longitude": forms.HiddenInput(attrs={"id": "id_longitude"}),
        }
        labels = {
            "title": "Item Title *",
            "description": "Description *",
            "category": "Category *",
            "condition": "Condition *",
            "price": "Price ($) *",
            "street_address": "Street Address *",
            "city": "City *",
            "zipcode": "Zip Code *",
        }

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) < 3:
            raise ValidationError("Title must be at least 3 characters long.")
        if len(title) > 200:
            raise ValidationError("Title cannot exceed 200 characters.")

        # Validate title contains only approved characters
        # Allowed: letters, numbers, spaces, and common punctuation (.,!?'-&)
        if not re.match(r"^[a-zA-Z0-9\s.,!?'\-&]+$", title):
            raise ValidationError(
                "Title contains invalid characters. Only letters, numbers, spaces, "
                "and basic punctuation (.,!?'-&) are allowed."
            )

        return title

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price <= 0:
            raise ValidationError("Price must be a positive value.")
        if price is not None and price < 0.50:
            raise ValidationError(
                "Price must be at least $0.50. Please enter a realistic price."
            )
        if price is not None and price > 100000:
            raise ValidationError("Price amount seems unrealistic. Please verify.")
        return price

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if not description:
            raise ValidationError("Description is required.")
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters long.")
        if len(description) > 2000:
            raise ValidationError("Description cannot exceed 2000 characters.")
        return description

    def clean_street_address(self):
        street_address = self.cleaned_data.get("street_address", "").strip()
        if not street_address:
            raise ValidationError("Street address is required.")
        if len(street_address) < 5:
            raise ValidationError(
                "Please enter a complete street address (at least 5 characters)."
            )
        return street_address

    def clean_city(self):
        city = self.cleaned_data.get("city", "").strip()
        if not city:
            raise ValidationError("City is required.")
        if len(city) < 2:
            raise ValidationError("Please enter a valid city name.")
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", city):
            raise ValidationError(
                "City name can only contain letters, spaces, hyphens, and apostrophes."
            )
        return city

    def clean_zipcode(self):
        zipcode = self.cleaned_data.get("zipcode", "").strip()
        if not zipcode:
            raise ValidationError("Zip code is required.")
        # Allow both 5-digit and 9-digit (with hyphen) zip codes
        if not re.match(r"^\d{5}(-\d{4})?$", zipcode):
            raise ValidationError(
                "Please enter a valid zip code (e.g., 10012 or 10012-1234)."
            )
        return zipcode
