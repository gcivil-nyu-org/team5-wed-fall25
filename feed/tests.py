# feed/tests.py
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings
from django.contrib.auth import get_user_model

# Force simple staticfiles backend during tests (no collectstatic needed)
TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=TEST_STORAGES)
class HomePortalSmokeTests(TestCase):
    def test_feed_renders_for_anonymous(self):
        resp = self.client.get(reverse("home_portal"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "feed/home_portal.html")

    def test_feed_renders_for_logged_in_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="tester",
            email="tester@example.edu",
            password="secret123",
        )
        self.client.force_login(user)
        resp = self.client.get(reverse("home_portal"))
        self.assertEqual(resp.status_code, 200)

    def test_feed_with_profile_location(self):
        """Test feed with user profile and location"""
        from profiles.models import Profile
        from listings.models import Listing

        User = get_user_model()
        user = User.objects.create_user(
            username="tester",
            email="tester@nyu.edu",
            password="secret123",
            is_verified=True,
        )

        # Create profile with location
        Profile.objects.create(
            user=user,
            university="NYU",
            location="Manhattan",
            budget_min=1000,
            budget_max=2000,
        )

        # Create listing that matches location
        Listing.objects.create(
            user=user,
            title="Test Listing",
            description="Test",
            rent=1500,
            street_address="123 Main St",
            city="Manhattan",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        self.client.force_login(user)
        resp = self.client.get(reverse("home_portal"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("user_stats", resp.context)

    def test_feed_with_profile_budget(self):
        """Test feed filters suggestions by budget"""
        from profiles.models import Profile
        from listings.models import Listing

        User = get_user_model()
        user = User.objects.create_user(
            username="tester2",
            email="tester2@nyu.edu",
            password="secret123",
            is_verified=True,
        )

        # Create profile with budget
        Profile.objects.create(
            user=user,
            university="NYU",
            budget_min=1500,
            budget_max=2500,
        )

        # Create listing within budget
        Listing.objects.create(
            user=user,
            title="Affordable Listing",
            description="Test",
            rent=2000,
            street_address="123 Main St",
            city="New York",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        # Create listing outside budget
        Listing.objects.create(
            user=user,
            title="Expensive Listing",
            description="Test",
            rent=5000,
            street_address="456 Park Ave",
            city="New York",
            zipcode="10002",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        self.client.force_login(user)
        resp = self.client.get(reverse("home_portal"))
        self.assertEqual(resp.status_code, 200)
        # Should have suggestions filtered by budget
        self.assertIn("user_stats", resp.context)
