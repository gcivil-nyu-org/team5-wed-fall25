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


@override_settings(STORAGES=TEST_STORAGES)
class FeaturedListingsTests(TestCase):
    """Test the featured listings logic (popular by message activity)."""

    def setUp(self):
        from listings.models import Listing
        from messaging.models import Thread, Message

        User = get_user_model()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@nyu.edu", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@nyu.edu", password="pass123"
        )

        # Create listings
        self.listing1 = Listing.objects.create(
            user=self.user1,
            title="Popular Listing 1",
            description="Most messages",
            rent=1000,
            street_address="123 Main St",
            city="New York",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        self.listing2 = Listing.objects.create(
            user=self.user1,
            title="Popular Listing 2",
            description="Some messages",
            rent=1200,
            street_address="456 Park Ave",
            city="New York",
            zipcode="10002",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        self.listing3 = Listing.objects.create(
            user=self.user1,
            title="Unpopular Listing",
            description="No messages",
            rent=1500,
            street_address="789 Broadway",
            city="New York",
            zipcode="10003",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        # Create threads and messages to simulate popularity
        self.thread1 = Thread.objects.create(
            listing=self.listing1, user_a=self.user1, user_b=self.user2
        )
        # Create 5 messages for listing1 (most popular)
        for i in range(5):
            Message.objects.create(
                thread=self.thread1,
                sender=self.user2,
                body=f"Message {i} about listing 1",
            )

        self.thread2 = Thread.objects.create(
            listing=self.listing2, user_a=self.user1, user_b=self.user2
        )
        # Create 2 messages for listing2
        for i in range(2):
            Message.objects.create(
                thread=self.thread2,
                sender=self.user2,
                body=f"Message {i} about listing 2",
            )

        # listing3 has no threads/messages

    def test_popular_listings_ordered_by_message_activity(self):
        """Test that featured listings are ordered by message activity."""
        resp = self.client.get(reverse("home_portal"))

        featured = resp.context["featured"]
        # listing1 should come first (5 messages), then listing2 (2 messages)
        self.assertGreaterEqual(len(featured), 2)
        self.assertEqual(featured[0].id, self.listing1.id)
        self.assertEqual(featured[1].id, self.listing2.id)

    def test_featured_fallback_to_recent_when_less_than_4(self):
        """Test that featured fills up to 4 with recent listings if needed."""
        from listings.models import Listing

        # Create one more recent listing (total 4 listings: 2 with messages, 2 without)
        Listing.objects.create(
            user=self.user1,
            title="Recent Listing",
            description="Newest",
            rent=1800,
            street_address="999 New St",
            city="New York",
            zipcode="10004",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        resp = self.client.get(reverse("home_portal"))
        featured = resp.context["featured"]

        # Should have 4 featured listings (2 popular + 2 recent fallback)
        self.assertEqual(len(featured), 4)


@override_settings(STORAGES=TEST_STORAGES)
class UserStatsTests(TestCase):
    """Test user statistics calculations in the home portal."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@nyu.edu",
            password="pass123",
            is_verified=True,
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="otheruser@nyu.edu",
            password="pass123",
            is_verified=True,
        )

    def test_unread_messages_count(self):
        """Test that unread messages are counted correctly."""
        from listings.models import Listing
        from messaging.models import Thread, Message

        # Create a listing and thread
        listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            description="Test",
            rent=1000,
            street_address="123 Main St",
            city="New York",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        thread = Thread.objects.create(
            listing=listing, user_a=self.user, user_b=self.other_user
        )

        # Create 3 unread messages from other_user
        for i in range(3):
            Message.objects.create(
                thread=thread, sender=self.other_user, body=f"Unread message {i}"
            )

        # Create 1 read message from other_user
        msg = Message.objects.create(
            thread=thread, sender=self.other_user, body="Read message"
        )
        msg.mark_read()

        # Create 1 message from self (should not count as unread)
        Message.objects.create(thread=thread, sender=self.user, body="My message")

        self.client.force_login(self.user)
        resp = self.client.get(reverse("home_portal"))

        user_stats = resp.context["user_stats"]
        self.assertEqual(user_stats["unread"], 3)

    def test_active_listings_count(self):
        """Test that active listings count is correct."""
        from listings.models import Listing

        # Create 2 active listings
        Listing.objects.create(
            user=self.user,
            title="Active 1",
            description="Test",
            rent=1000,
            street_address="123 Main St",
            city="New York",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        Listing.objects.create(
            user=self.user,
            title="Active 2",
            description="Test",
            rent=1200,
            street_address="456 Park Ave",
            city="New York",
            zipcode="10002",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        # Create 1 inactive listing (should not count)
        Listing.objects.create(
            user=self.user,
            title="Inactive",
            description="Test",
            rent=1500,
            street_address="789 Broadway",
            city="New York",
            zipcode="10003",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=False,
        )

        self.client.force_login(self.user)
        resp = self.client.get(reverse("home_portal"))

        user_stats = resp.context["user_stats"]
        self.assertEqual(user_stats["my_active_listings"], 2)

    def test_pending_connection_requests_count(self):
        """Test that pending connection requests are counted."""
        from profiles.models import Profile, ConnectionRequest

        User = get_user_model()
        # Create another user for second pending request
        user3 = User.objects.create_user(
            username="user3",
            email="user3@nyu.edu",
            password="pass123",
            is_verified=True,
        )

        # Create profiles
        Profile.objects.create(user=self.user, university="NYU")
        Profile.objects.create(user=self.other_user, university="NYU")
        Profile.objects.create(user=user3, university="NYU")

        # Create 2 pending connection requests TO self.user (from different users)
        ConnectionRequest.objects.create(
            from_user=self.other_user, to_user=self.user, status="pending"
        )
        ConnectionRequest.objects.create(
            from_user=user3, to_user=self.user, status="pending"
        )

        # Create 1 accepted request (should not count)
        User = get_user_model()
        user4 = User.objects.create_user(
            username="user4",
            email="user4@nyu.edu",
            password="pass123",
            is_verified=True,
        )
        Profile.objects.create(user=user4, university="NYU")
        ConnectionRequest.objects.create(
            from_user=user4, to_user=self.user, status="accepted"
        )

        self.client.force_login(self.user)
        resp = self.client.get(reverse("home_portal"))

        user_stats = resp.context["user_stats"]
        self.assertEqual(user_stats["pending_conn"], 2)

    def test_favorites_count(self):
        """Test that favorites are counted correctly."""
        from profiles.models import Profile, Favorite

        User = get_user_model()
        # Create more users for multiple favorites
        user3 = User.objects.create_user(
            username="user3",
            email="user3@nyu.edu",
            password="pass123",
            is_verified=True,
        )
        user4 = User.objects.create_user(
            username="user4",
            email="user4@nyu.edu",
            password="pass123",
            is_verified=True,
        )

        # Create profiles
        profile1 = Profile.objects.create(user=self.user, university="NYU")
        profile2 = Profile.objects.create(user=self.other_user, university="NYU")
        profile3 = Profile.objects.create(user=user3, university="NYU")
        profile4 = Profile.objects.create(user=user4, university="NYU")

        # Create 3 favorites (note: field is 'favorite_profile', not 'profile')
        Favorite.objects.create(user=self.user, favorite_profile=profile2)
        Favorite.objects.create(user=self.user, favorite_profile=profile3)
        Favorite.objects.create(user=self.user, favorite_profile=profile4)

        self.client.force_login(self.user)
        resp = self.client.get(reverse("home_portal"))

        user_stats = resp.context["user_stats"]
        self.assertEqual(user_stats["favorites"], 3)

    def test_user_stats_not_present_for_anonymous(self):
        """Test that user_stats is None for anonymous users."""
        resp = self.client.get(reverse("home_portal"))
        self.assertIsNone(resp.context["user_stats"])


@override_settings(STORAGES=TEST_STORAGES)
class SuggestionsTests(TestCase):
    """Test personalized suggestions based on user profile."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@nyu.edu",
            password="pass123",
            is_verified=True,
        )

    def test_suggestions_filtered_by_location(self):
        """Test that suggestions are filtered by profile location."""
        from profiles.models import Profile
        from listings.models import Listing

        # Create profile with location "Brooklyn"
        Profile.objects.create(
            user=self.user,
            university="NYU",
            location="Brooklyn",
            budget_min=1000,
            budget_max=3000,
        )

        # Create listing in Brooklyn (should appear in suggestions)
        brooklyn_listing = Listing.objects.create(
            user=self.user,
            title="Brooklyn Listing",
            description="Test",
            rent=1500,
            street_address="123 Main St",
            city="Brooklyn",
            zipcode="11201",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        # Create listing in Manhattan (should NOT appear)
        Listing.objects.create(
            user=self.user,
            title="Manhattan Listing",
            description="Test",
            rent=1500,
            street_address="456 Park Ave",
            city="Manhattan",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        self.client.force_login(self.user)
        resp = self.client.get(reverse("home_portal"))

        suggestions = resp.context["user_stats"]["suggestions"]
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].id, brooklyn_listing.id)

    def test_suggestions_filtered_by_budget(self):
        """Test that suggestions respect budget min/max."""
        from profiles.models import Profile
        from listings.models import Listing

        # Create profile with budget 1500-2500
        Profile.objects.create(
            user=self.user,
            university="NYU",
            budget_min=1500,
            budget_max=2500,
        )

        # Create listing within budget
        affordable = Listing.objects.create(
            user=self.user,
            title="Affordable",
            description="Test",
            rent=2000,
            street_address="123 Main St",
            city="New York",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        # Create listing below budget (should NOT appear)
        Listing.objects.create(
            user=self.user,
            title="Too Cheap",
            description="Test",
            rent=1000,
            street_address="456 Park Ave",
            city="New York",
            zipcode="10002",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        # Create listing above budget (should NOT appear)
        Listing.objects.create(
            user=self.user,
            title="Too Expensive",
            description="Test",
            rent=5000,
            street_address="789 Broadway",
            city="New York",
            zipcode="10003",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        self.client.force_login(self.user)
        resp = self.client.get(reverse("home_portal"))

        suggestions = resp.context["user_stats"]["suggestions"]
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].id, affordable.id)

    def test_suggestions_without_profile(self):
        """Test that suggestions work without a profile (no filtering)."""
        from listings.models import Listing

        # No profile created for self.user

        # Create a listing
        Listing.objects.create(
            user=self.user,
            title="Test Listing",
            description="Test",
            rent=1500,
            street_address="123 Main St",
            city="New York",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )

        self.client.force_login(self.user)
        resp = self.client.get(reverse("home_portal"))

        # Should still have suggestions (no profile means no filtering)
        suggestions = resp.context["user_stats"]["suggestions"]
        self.assertGreaterEqual(len(suggestions), 1)


@override_settings(STORAGES=TEST_STORAGES)
class GlobalStatsTests(TestCase):
    """Test global statistics displayed on home portal."""

    def test_active_listings_count(self):
        """Test that global active listings count is correct."""
        from listings.models import Listing

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@nyu.edu", password="pass123"
        )

        # Create 3 active listings
        for i in range(3):
            Listing.objects.create(
                user=user,
                title=f"Active {i}",
                description="Test",
                rent=1000 + i * 100,
                street_address=f"{i} Main St",
                city="New York",
                zipcode="10001",
                availability_start="2025-01-01",
                availability_end="2025-12-31",
                is_active=True,
            )

        # Create 1 inactive listing (should not count)
        Listing.objects.create(
            user=user,
            title="Inactive",
            description="Test",
            rent=1500,
            street_address="999 Park Ave",
            city="New York",
            zipcode="10002",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=False,
        )

        resp = self.client.get(reverse("home_portal"))
        stats = resp.context["stats"]
        self.assertEqual(stats["active_listings"], 3)

    def test_new_listings_last_7_days(self):
        """Test that new listings from last 7 days are counted."""
        from listings.models import Listing
        from django.utils import timezone
        from datetime import timedelta

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@nyu.edu", password="pass123"
        )

        # Create listing from 3 days ago
        recent_listing = Listing.objects.create(
            user=user,
            title="Recent",
            description="Test",
            rent=1000,
            street_address="123 Main St",
            city="New York",
            zipcode="10001",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )
        recent_listing.created_at = timezone.now() - timedelta(days=3)
        recent_listing.save()

        # Create listing from 10 days ago (should not count)
        old_listing = Listing.objects.create(
            user=user,
            title="Old",
            description="Test",
            rent=1200,
            street_address="456 Park Ave",
            city="New York",
            zipcode="10002",
            availability_start="2025-01-01",
            availability_end="2025-12-31",
            is_active=True,
        )
        old_listing.created_at = timezone.now() - timedelta(days=10)
        old_listing.save()

        resp = self.client.get(reverse("home_portal"))
        stats = resp.context["stats"]
        self.assertEqual(stats["new_last_7"], 1)

    def test_market_items_count(self):
        """Test that market items count is correct."""
        from marketplace.models import Item

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@nyu.edu", password="pass123"
        )

        # Create 2 active items
        for i in range(2):
            Item.objects.create(
                user=user,
                title=f"Item {i}",
                description="Test item",
                price=50 + i * 10,
                condition="good",
                category="electronics",
                is_active=True,
            )

        # Create 1 inactive item (should not count)
        Item.objects.create(
            user=user,
            title="Inactive Item",
            description="Test",
            price=100,
            condition="good",
            category="books",
            is_active=False,
        )

        resp = self.client.get(reverse("home_portal"))
        stats = resp.context["stats"]
        self.assertEqual(stats["market_items"], 2)


@override_settings(STORAGES=TEST_STORAGES)
class AnnouncementsTests(TestCase):
    """Test announcements display on home portal."""

    def test_published_announcements_displayed(self):
        """Test that only published announcements are shown."""
        from feed.models import Announcement

        # Create 2 published announcements
        Announcement.objects.create(
            title="Announcement 1", body="Published 1", is_published=True
        )
        Announcement.objects.create(
            title="Announcement 2", body="Published 2", is_published=True
        )

        # Create 1 unpublished announcement
        Announcement.objects.create(
            title="Announcement 3", body="Unpublished", is_published=False
        )

        resp = self.client.get(reverse("home_portal"))
        announcements = resp.context["announcements"]

        self.assertEqual(len(announcements), 2)

    def test_max_3_announcements_shown(self):
        """Test that maximum 3 announcements are displayed."""
        from feed.models import Announcement

        # Create 5 published announcements
        for i in range(5):
            Announcement.objects.create(
                title=f"Announcement {i}", body=f"Body {i}", is_published=True
            )

        resp = self.client.get(reverse("home_portal"))
        announcements = resp.context["announcements"]

        self.assertEqual(len(announcements), 3)
