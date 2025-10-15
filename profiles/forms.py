# profiles/forms.py
from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'bio', 
            'university', 
            'profile_photo', 
            'eating_habit',
            'smoking_preference',
            'sharing_preference',
            'drinking_preference',
            'visibility'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Tell us about yourself... (10–500 chars)',
                'style': 'width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;'
            }),
            'university': forms.Select(attrs={
                'style': 'width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;'
            }),
            'profile_photo': forms.FileInput(attrs={
                'style': 'width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;'
            }),
            'eating_habit': forms.Select(attrs={
                'style': 'width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;'
            }),
            'smoking_preference': forms.Select(attrs={
                'style': 'width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;'
            }),
            'sharing_preference': forms.Select(attrs={
                'style': 'width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;'
            }),
            'drinking_preference': forms.Select(attrs={
                'style': 'width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;'
            }),
            'visibility': forms.CheckboxInput(attrs={
                'style': 'width: 20px; height: 20px;'
            }),
        }
        labels = {
            'eating_habit': '🍽️ Eating Preference',
            'smoking_preference': '🚬 Smoking',
            'sharing_preference': '🤝 Sharing Items',
            'drinking_preference': '🍷 Drinking',
        }
        help_texts = {
            'eating_habit': 'Your dietary preferences',
            'smoking_preference': 'Your smoking habits',
            'sharing_preference': 'Are you comfortable with sharing ?',
            'drinking_preference': 'Your drinking preferences',
        }

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '')
        if not (10 <= len(bio) <= 500):
            raise forms.ValidationError("Bio must be between 10–500 characters.")
        return bio

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        
        # Only validate if a NEW file was uploaded
        if photo and hasattr(photo, 'content_type'):
            # Check file size
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 5MB.")
            
            # Check file type
            if photo.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
                raise forms.ValidationError("Only JPG, PNG, and WebP formats allowed.")
        
        return photo