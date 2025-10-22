# profiles/forms.py
from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "bio",
            "university",
            "profile_photo",
            "eating_habit",
            "smoking_preference",
            "sharing_preference",
            "drinking_preference",
<<<<<<< HEAD
=======
            "pet_preference",
            "cleanliness_preference",
            "budget_min",
            "budget_max",
            "location",
            "move_in_date",
>>>>>>> origin/develop
            "visibility",
        ]
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tell us about yourself... (10–500 chars)",
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;",
                }
            ),
            "university": forms.Select(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
            "profile_photo": forms.FileInput(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
            "eating_habit": forms.Select(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
            "smoking_preference": forms.Select(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
            "sharing_preference": forms.Select(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
            "drinking_preference": forms.Select(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
<<<<<<< HEAD
=======
            "pet_preference": forms.Select(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
            "cleanliness_preference": forms.Select(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;"
                }
            ),
            "budget_min": forms.NumberInput(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;",
                    "placeholder": "Minimum monthly budget",
                }
            ),
            "budget_max": forms.NumberInput(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;",
                    "placeholder": "Maximum monthly budget",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;",
                    "placeholder": "e.g., Manhattan, Brooklyn, Queens",
                }
            ),
            "move_in_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;",
                }
            ),
>>>>>>> origin/develop
            "visibility": forms.CheckboxInput(
                attrs={"style": "width: 20px; height: 20px;"}
            ),
        }
        labels = {
            "eating_habit": "🍽️ Eating Preference",
<<<<<<< HEAD
            "smoking_preference": "🚬 Smoking",
            "sharing_preference": "🤝 Sharing Items",
            "drinking_preference": "🍷 Drinking",
=======
            "smoking_preference": "🚬Sm",
            "sharing_preference": "🤝 Sharing Items",
            "drinking_preference": "🍷 Drinking",
            "pet_preference": "🐾 Pet Preference",
            "cleanliness_preference": "✨ Cleanliness Level",
            "budget_min": "💰 Minimum Monthly Budget",
            "budget_max": "💰 Maximum Monthly Budget",
            "location": "📍 Preferred Location",
            "move_in_date": "📅 Preferred Move-In Date",
>>>>>>> origin/develop
        }
        help_texts = {
            "eating_habit": "Your dietary preferences",
            "smoking_preference": "Your smoking habits",
<<<<<<< HEAD
            "sharing_preference": "Are you comfortable with sharing ?",
            "drinking_preference": "Your drinking preferences",
=======
            "sharing_preference": "Are you comfortable with sharing?",
            "drinking_preference": "Your drinking preferences",
            "pet_preference": "Your pet preferences",
            "cleanliness_preference": "Your cleanliness standards",
            "budget_min": "Minimum monthly rent budget",
            "budget_max": "Maximum monthly rent budget",
            "location": "Where you prefer to live",
            "move_in_date": "When you plan to move in",
>>>>>>> origin/develop
        }

    def clean_bio(self):
        bio = self.cleaned_data.get("bio", "")
        if not (10 <= len(bio) <= 500):
            raise forms.ValidationError("Bio must be between 10–500 characters.")
        return bio

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")

        # Only validate if a NEW file was uploaded
        if photo and hasattr(photo, "content_type"):
            # Check file size
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 5MB.")

            # Check file type
            if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
                raise forms.ValidationError("Only JPG, PNG, and WebP formats allowed.")
<<<<<<< HEAD

        return photo
=======

        return photo

    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get("budget_min")
        budget_max = cleaned_data.get("budget_max")

        if budget_min is not None and budget_max is not None:
            if budget_min > budget_max:
                raise forms.ValidationError(
                    "Minimum budget cannot be greater than maximum budget."
                )

        return cleaned_data


class RoommateSearchForm(forms.Form):
    """Form for filtering roommate search"""

    # Lifestyle filters
    smoking_preference = forms.MultipleChoiceField(
        choices=Profile.SMOKING_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"style": "margin: 5px 0;"}),
        label="🚬Sm Preference",
    )

    pet_preference = forms.MultipleChoiceField(
        choices=Profile.PET_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"style": "margin: 5px 0;"}),
        label="🐾 Pet Preference",
    )

    cleanliness_preference = forms.MultipleChoiceField(
        choices=Profile.CLEANLINESS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"style": "margin: 5px 0;"}),
        label="✨ Cleanliness Level",
    )

    # Housing filters
    budget_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;",
                "placeholder": "Min budget",
            }
        ),
        label="💰 Minimum Budget",
    )

    budget_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;",
                "placeholder": "Max budget",
            }
        ),
        label="💰 Maximum Budget",
    )

    location = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "style": "width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;",
                "placeholder": "e.g., Manhattan, Brooklyn",
            }
        ),
        label="📍 Location",
    )

    university = forms.MultipleChoiceField(
        choices=Profile.UNIVERSITY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"style": "margin: 5px 0;"}),
        label="🎓 University",
    )
>>>>>>> origin/develop
