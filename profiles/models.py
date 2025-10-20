from django.db import models
from django.conf import settings


class Profile(models.Model):
    UNIVERSITY_CHOICES = [
        ("NYU", "New York University"),
        ("Columbia", "Columbia University"),
        ("Fordham", "Fordham University"),
        ("CUNY", "City University of New York"),
        ("Pace", "Pace University"),
        ("The New School", "The New School"),
    ]
    
    # Preference Choices
    EATING_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('non_vegetarian', 'Non-Vegetarian'),
        ('no_preference', 'No Preference'),
    ]
    
    SMOKING_CHOICES = [
        ('non_smoker', 'Non-Smoker'),
        ('smoker', 'Smoker'),
        ('occasionally', 'Occasionally'),
    ]
    
    SHARING_CHOICES = [
        ('sharing', 'Open to Sharing'),
        ('non_sharing', 'Prefer Not to Share'),
        ('no_preference', 'No Preference'),
    ]
    
    DRINKING_CHOICES = [
        ('non_drinker', 'Non-Drinker'),
        ('social_drinker', 'Social Drinker'),
        ('regular_drinker', 'Regular Drinker'),
        ('no_preference', 'No Preference'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500)
    university = models.CharField(max_length=100, choices=UNIVERSITY_CHOICES)
    profile_photo = models.ImageField(upload_to="profile_photos/")
    visibility = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Preference Fields
    eating_habit = models.CharField(
        max_length=20,
        choices=EATING_CHOICES,
        default='no_preference',
        verbose_name='Eating Preference'
    )
    smoking_preference = models.CharField(
        max_length=20,
        choices=SMOKING_CHOICES,
        default='non_smoker',
        verbose_name='Smoking Preference'
    )
    sharing_preference = models.CharField(
        max_length=20,
        choices=SHARING_CHOICES,
        default='no_preference',
        verbose_name='Sharing Preference'
    )
    drinking_preference = models.CharField(
        max_length=20,
        choices=DRINKING_CHOICES,
        default='no_preference',
        verbose_name='Drinking Preference'
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_preference_display_with_icon(self, preference_type):
        """Helper method to get preference with appropriate icon"""
        icons = {
            # Eating
            'vegetarian': '🥗',
            'non_vegetarian': '🍖',
            'vegan': '🌱',
            # Smoking
            'non_smoker': '🚭',
            'smoker': '🚬',
            'occasionally': '😶‍🌫️',
            # Sharing
            'sharing': '🤝',
            'non_sharing': '🚫',
            'no_preference': '🤷',
            # Drinking
            'non_drinker': '☕',
            'social_drinker': '🍻',
            'regular_drinker': '🍷',
            'no_preference': '🤷',
        }
        
        if preference_type == 'eating':
            value = self.eating_habit
            display = self.get_eating_habit_display()
        elif preference_type == 'smoking':
            value = self.smoking_preference
            display = self.get_smoking_preference_display()
        elif preference_type == 'sharing':
            value = self.sharing_preference
            display = self.get_sharing_preference_display()
        elif preference_type == 'drinking':
            value = self.drinking_preference
            display = self.get_drinking_preference_display()
        else:
            return ''
        
        icon = icons.get(value, '')
        return f"{icon} {display}"
