"""
Forms for communities app.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Community, CommunityMember
from profiles.models import Profile


class CommunityForm(forms.ModelForm):
    """Form for creating and editing communities."""

    class Meta:
        model = Community
        fields = ['name', 'description', 'privacy', 'university', 'cover_image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Community Name',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your community...',
                'rows': 4,
                'maxlength': '1000'
            }),
            'privacy': forms.Select(attrs={
                'class': 'form-control'
            }),
            'university': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        help_texts = {
            'name': 'Choose a unique name for your community (max 100 characters)',
            'description': 'Describe what your community is about (max 1000 characters)',
            'privacy': 'Public: Anyone can join | Private: Requires approval | University: Restricted to university students',
            'university': 'Required for university-restricted communities',
            'cover_image': 'Optional: Upload a cover image for your community'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make university field not required by default (will validate in clean())
        self.fields['university'].required = False
        self.fields['cover_image'].required = False

    def clean(self):
        """Validate that university is set for university-restricted communities."""
        cleaned_data = super().clean()
        # Note: Validation is also done in the model's clean() method
        # We rely on model validation instead of duplicating it here
        return cleaned_data


class JoinRequestForm(forms.ModelForm):
    """Form for requesting to join a private community."""

    class Meta:
        model = CommunityMember
        fields = ['request_message']
        widgets = {
            'request_message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell us why you want to join this community (optional)...',
                'rows': 3,
                'maxlength': '500'
            })
        }
        help_texts = {
            'request_message': 'Optional: Add a message with your join request (max 500 characters)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['request_message'].required = False
