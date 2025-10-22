from django import forms
from django.core.exceptions import ValidationError
from .models import Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "title",
            "description",
            "condition",
            "price",
            "pickup_location",
            "owner_name",
            "contact_details",
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
            "condition": forms.Select(attrs={"class": "form-control"}),
            "price": forms.NumberInput(
                attrs={
                    "placeholder": "Price in USD",
                    "step": "0.01",
                    "min": "0",
                    "class": "form-control",
                }
            ),
            "pickup_location": forms.TextInput(
                attrs={
                    "placeholder": "e.g., Bobst Library, NYU",
                    "class": "form-control",
                }
            ),
            "owner_name": forms.TextInput(
                attrs={
                    "placeholder": "Your name",
                    "class": "form-control",
                }
            ),
            "contact_details": forms.TextInput(
                attrs={
                    "placeholder": "Phone number or email",
                    "class": "form-control",
                }
            ),
        }
        labels = {
            "title": "Item Title *",
            "description": "Description *",
            "condition": "Condition *",
            "price": "Price ($) *",
            "pickup_location": "Pickup Location *",
            "owner_name": "Your Name *",
            "contact_details": "Contact (Phone/Email) *",
        }

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price <= 0:
            raise ValidationError("Price must be a positive value.")
        if price is not None and price > 100000:
            raise ValidationError("Price amount seems unrealistic. Please verify.")
        return price

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters long.")
        return description

    def clean_contact_details(self):
        contact = self.cleaned_data.get("contact_details", "")
        if len(contact) < 5:
            raise ValidationError("Please provide valid contact details.")
        return contact
