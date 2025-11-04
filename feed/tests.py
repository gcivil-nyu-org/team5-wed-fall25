# feed/tests.py
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings
from django.contrib.auth import get_user_model

# Disable Manifest storage so tests don't need collectstatic
@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class HomePortalSmokeTests(TestCase):
    def test_feed_renders_for_anonymous(self):
        resp = self.client.get(reverse("home_portal"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "feed/home_portal.html")
        # minimal context checks
        for k in ("featured", "latest_listings", "latest_items", "ticker_items"):
            self.assertIn(k, resp.context)

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
        # user_stats should be a dict for authenticated users
        self.assertIsInstance(resp.context.get("user_stats"), dict)
