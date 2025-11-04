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
