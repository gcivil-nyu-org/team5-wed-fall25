from django import forms
from django.core.exceptions import ValidationError
from .models import Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "title",
            "description",
            "category",
            "condition",
            "price",
            "address",
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
            "address": forms.TextInput(
                attrs={
                    "placeholder": "e.g., Bobst Library, NYU",
                    "class": "form-control",
                }
            ),
        }
        labels = {
            "title": "Item Title *",
            "description": "Description *",
            "category": "Category *",
            "condition": "Condition *",
            "price": "Price ($) *",
            "address": "Pickup Location *",
        }

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) < 3:
            raise ValidationError("Title must be at least 3 characters long.")
        if len(title) > 200:
            raise ValidationError("Title cannot exceed 200 characters.")
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

    def clean_address(self):
        address = self.cleaned_data.get("address", "").strip()
        if not address:
            raise ValidationError("Pickup location is required.")
        if len(address) < 5:
            raise ValidationError(
                "Please enter a complete pickup location (at least 5 characters)."
            )
        return address
