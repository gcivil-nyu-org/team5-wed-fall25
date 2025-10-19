from django.test import TestCase
from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from .models import Profile
from accounts.models import User


# Create your tests here.
class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.edu", username="testuser", password="testpw0rd"
        )
        self.profile = Profile.objects.create(
            user=self.user,
            bio="test bio",
            university="New York University",
            profile_photo="pfp/images.jpg",
            visibility=True,
            eating_habit="no_preference",
            smoking_preference="non_smoker",
            sharing_preference="depends",
            drinking_preference="no_preference",
        )

    def test_create_profile_success(self):
        profile = self.profile
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, "test bio")
        self.assertEqual(profile.university, "New York University")
        self.assertEqual(profile.profile_photo, "pfp/images.jpg")
        self.assertTrue(profile.visibility)
        self.assertEqual(profile.eating_habit, "no_preference")
        self.assertEqual(profile.smoking_preference, "non_smoker")
        self.assertEqual(profile.sharing_preference, "depends")
        self.assertEqual(profile.drinking_preference, "no_preference")
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)

    def test_create_duplicate_profile(self):
        with self.assertRaises(IntegrityError):
            profile = Profile.objects.create(
                user=self.user,
                bio="test bio",
                university="New York University",
                profile_photo="pfp/images.jpg",
                visibility=True,
            )

    def test_invalid_bio(self):
        with self.assertRaises(ValidationError):
            self.profile.bio = "a" * 501
            self.profile.full_clean()

    def test_invalid_university(self):
        with self.assertRaises(ValidationError):
            self.profile.university = "Fake University"
            self.profile.full_clean()

    def test_invalid_eating_habit(self):
        with self.assertRaises(ValidationError):
            self.profile.eating_habit = "Fake diet"
            self.profile.full_clean()

    def test_invalid_smoking_preference(self):
        with self.assertRaises(ValidationError):
            self.profile.smoking_preference = "Super smoker"
            self.profile.full_clean()

    def test_invalid_sharing_preference(self):
        with self.assertRaises(ValidationError):
            self.profile.sharing_preference = "Open to Chering"
            self.profile.full_clean()

    def test_invalid_drinking_preference(self):
        with self.assertRaises(ValidationError):
            self.profile.drinking_preference = "Liver failure"
            self.profile.full_clean()

    def test_defaults(self):
        user2 = User.objects.create_user(
            email="test2@example.edu", username="test2user", password="testpw0rd"
        )
        before = timezone.now()
        profile = Profile.objects.create(
            user=user2,
            bio="bio 2",
            university="New York Univesity",
            profile_photo="pfp/images.jpg",
        )
        after = timezone.now()
        self.assertTrue(profile.visibility)
        self.assertGreaterEqual(profile.created_at, before)
        self.assertLessEqual(profile.created_at, after)
        self.assertEqual(profile.eating_habit, "no_preference")
        self.assertEqual(profile.smoking_preference, "non_smoker")
        self.assertEqual(profile.sharing_preference, "depends")
        self.assertEqual(profile.drinking_preference, "no_preference")

    def test_delete_cascade(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        self.user.delete()
        self.assertFalse(Profile.objects.filter(user_id=self.user.id).exists())
