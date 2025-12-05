from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.utils import IntegrityError
from listings.models import Listing
from profiles.models import Profile
from .models import Thread, Message
from .forms import MessageForm

User = get_user_model()


class ThreadModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            first_name="User",
            last_name="One",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            first_name="User",
            last_name="Two",
            is_verified=True,
        )
        self.user3 = User.objects.create_user(
            email="user3@nyu.edu",
            username="user3",
            password="TestPassword123!",
            is_verified=True,
        )

        # Create profiles (required by listings)
        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")
        Profile.objects.create(user=self.user3, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="A great place",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

    def test_thread_canonicalization_on_save(self):
        """Test that users are automatically ordered by ID on save"""
        # Create thread with user_a > user_b (should be swapped)
        thread = Thread(listing=self.listing, user_a=self.user2, user_b=self.user1)
        thread.save()

        # Verify users were swapped
        self.assertEqual(thread.user_a, self.user1)
        self.assertEqual(thread.user_b, self.user2)

    def test_thread_unique_constraint(self):
        """Test that duplicate threads cannot be created"""
        Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

        with self.assertRaises(IntegrityError):
            Thread.objects.create(
                listing=self.listing, user_a=self.user1, user_b=self.user2
            )

    def test_thread_prevent_self_thread(self):
        """Test that users cannot create threads with themselves"""
        with self.assertRaises(IntegrityError):
            Thread.objects.create(
                listing=self.listing, user_a=self.user1, user_b=self.user1
            )

    def test_other_participant(self):
        """Test other_participant method returns correct user"""
        thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

        self.assertEqual(thread.other_participant(self.user1), self.user2)
        self.assertEqual(thread.other_participant(self.user2), self.user1)

    def test_thread_str_representation(self):
        """Test string representation of thread"""
        thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )
        expected = f"Thread(listing={self.listing.id}, users=({self.user1.id},{self.user2.id}))"
        self.assertEqual(str(thread), expected)


class MessageModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )

        # Create profiles (required by listings)
        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

        self.thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

    def test_message_creation(self):
        """Test message creation"""
        msg = Message.objects.create(
            thread=self.thread, sender=self.user1, body="Test message"
        )
        self.assertEqual(msg.body, "Test message")
        self.assertFalse(msg.is_read)
        self.assertIsNone(msg.read_at)

    def test_mark_read(self):
        """Test mark_read method"""
        msg = Message.objects.create(
            thread=self.thread, sender=self.user1, body="Test message"
        )

        msg.mark_read()
        self.assertTrue(msg.is_read)
        self.assertIsNotNone(msg.read_at)

    def test_mark_read_idempotent(self):
        """Test that mark_read can be called multiple times"""
        msg = Message.objects.create(
            thread=self.thread, sender=self.user1, body="Test message"
        )

        msg.mark_read()
        first_read_at = msg.read_at

        msg.mark_read()
        # read_at should remain the same
        self.assertEqual(msg.read_at, first_read_at)

    def test_message_ordering(self):
        """Test messages are ordered by created_at"""
        msg1 = Message.objects.create(
            thread=self.thread, sender=self.user1, body="First"
        )
        msg2 = Message.objects.create(
            thread=self.thread, sender=self.user2, body="Second"
        )
        msg3 = Message.objects.create(
            thread=self.thread, sender=self.user1, body="Third"
        )

        messages = list(self.thread.messages.all())
        self.assertEqual(messages, [msg1, msg2, msg3])

    def test_message_str_representation(self):
        """Test string representation of message"""
        msg = Message.objects.create(thread=self.thread, sender=self.user1, body="Test")
        str_repr = str(msg)
        self.assertIn(f"thread={self.thread.id}", str_repr)
        self.assertIn(f"from={self.user1.id}", str_repr)


class MessageFormTests(TestCase):
    def test_valid_message(self):
        """Test form with valid message"""
        form = MessageForm(data={"body": "This is a valid message"})
        self.assertTrue(form.is_valid())

    def test_empty_message(self):
        """Test form rejects empty message"""
        form = MessageForm(data={"body": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_whitespace_only_message(self):
        """Test form rejects whitespace-only message"""
        form = MessageForm(data={"body": "   "})
        self.assertFalse(form.is_valid())

    def test_message_too_long(self):
        """Test form rejects message over 2000 characters"""
        form = MessageForm(data={"body": "x" * 2001})
        self.assertFalse(form.is_valid())
        self.assertIn("body", form.errors)

    def test_message_exactly_2000_chars(self):
        """Test form accepts message exactly 2000 characters"""
        form = MessageForm(data={"body": "x" * 2000})
        self.assertTrue(form.is_valid())


class InboxViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )

        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

    def test_inbox_requires_login(self):
        """Test inbox view requires authentication"""
        response = self.client.get(reverse("messaging:inbox"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_inbox_shows_threads(self):
        """Test inbox displays user's threads"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )
        Message.objects.create(thread=thread, sender=self.user2, body="Hello")

        response = self.client.get(reverse("messaging:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("rows", response.context)
        self.assertEqual(len(response.context["rows"]), 1)

    def test_inbox_empty_state(self):
        """Test inbox with no threads"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(reverse("messaging:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["rows"]), 0)


class ThreadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            first_name="User1",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user3 = User.objects.create_user(
            email="user3@nyu.edu",
            username="user3",
            password="TestPassword123!",
            is_verified=True,
        )

        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")
        Profile.objects.create(user=self.user3, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

        self.thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

    def test_thread_view_requires_login(self):
        """Test thread view requires authentication"""
        response = self.client.get(
            reverse("messaging:thread", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_thread_view_forbidden_non_participant(self):
        """Test non-participants cannot view thread"""
        self.client.login(username="user3@nyu.edu", password="TestPassword123!")
        response = self.client.get(
            reverse("messaging:thread", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_thread_view_success(self):
        """Test thread view for participant"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")
        Message.objects.create(thread=self.thread, sender=self.user2, body="Hello")

        response = self.client.get(
            reverse("messaging:thread", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("thread", response.context)
        self.assertIn("chat_messages", response.context)

    def test_thread_view_marks_messages_read(self):
        """Test viewing thread marks incoming messages as read"""
        msg = Message.objects.create(
            thread=self.thread, sender=self.user2, body="Hello", is_read=False
        )

        self.client.login(username="user1@nyu.edu", password="TestPassword123!")
        self.client.get(
            reverse("messaging:thread", kwargs={"thread_id": self.thread.id})
        )

        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_thread_view_post_message(self):
        """Test posting a message to thread"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:thread", kwargs={"thread_id": self.thread.id}),
            {"body": "Test message"},
        )

        self.assertRedirects(
            response, reverse("messaging:thread", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(self.thread.messages.count(), 1)
        self.assertEqual(self.thread.messages.first().body, "Test message")

    def test_thread_view_post_empty_message(self):
        """Test posting empty message fails"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:thread", kwargs={"thread_id": self.thread.id}),
            {"body": ""},
        )

        self.assertRedirects(
            response, reverse("messaging:thread", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(self.thread.messages.count(), 0)


class StartThreadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )

        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

    def test_start_thread_requires_login(self):
        """Test start thread requires authentication"""
        response = self.client.post(reverse("messaging:start_thread"))
        self.assertEqual(response.status_code, 302)

    def test_start_thread_get_redirects(self):
        """Test GET request redirects to inbox"""
        self.client.login(username="user2@nyu.edu", password="TestPassword123!")
        response = self.client.get(reverse("messaging:start_thread"))
        self.assertRedirects(response, reverse("messaging:inbox"))

    def test_start_thread_success(self):
        """Test creating new thread"""
        self.client.login(username="user2@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:start_thread"),
            {
                "listing_id": self.listing.id,
                "recipient_id": self.user1.id,
                "body": "Interested in your listing",
            },
        )

        # Should create thread and redirect
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.first()
        self.assertRedirects(
            response, reverse("messaging:thread", kwargs={"thread_id": thread.id})
        )
        self.assertEqual(thread.messages.count(), 1)

    def test_start_thread_reuses_existing(self):
        """Test starting thread reuses existing thread"""
        self.client.login(username="user2@nyu.edu", password="TestPassword123!")

        # Create first thread
        self.client.post(
            reverse("messaging:start_thread"),
            {
                "listing_id": self.listing.id,
                "recipient_id": self.user1.id,
                "body": "First message",
            },
        )

        # Try to create another thread for same listing/users
        self.client.post(
            reverse("messaging:start_thread"),
            {
                "listing_id": self.listing.id,
                "recipient_id": self.user1.id,
                "body": "Second message",
            },
        )

        # Should still only have one thread
        self.assertEqual(Thread.objects.count(), 1)
        # But two messages
        self.assertEqual(Message.objects.count(), 2)

    def test_start_thread_empty_message(self):
        """Test starting thread with empty message fails"""
        self.client.login(username="user2@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:start_thread"),
            {
                "listing_id": self.listing.id,
                "recipient_id": self.user1.id,
                "body": "",
            },
        )

        self.assertEqual(Thread.objects.count(), 0)
        self.assertRedirects(
            response, reverse("view_listing", kwargs={"listing_id": self.listing.id})
        )

    def test_start_thread_own_listing(self):
        """Test user cannot message own listing"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:start_thread"),
            {
                "listing_id": self.listing.id,
                "recipient_id": self.user1.id,
                "body": "Test",
            },
        )

        self.assertEqual(Thread.objects.count(), 0)
        self.assertRedirects(
            response, reverse("view_listing", kwargs={"listing_id": self.listing.id})
        )

    def test_start_thread_invalid_recipient(self):
        """Test starting thread with wrong recipient"""
        self.client.login(username="user2@nyu.edu", password="TestPassword123!")

        self.client.post(
            reverse("messaging:start_thread"),
            {
                "listing_id": self.listing.id,
                "recipient_id": 9999,  # Wrong ID
                "body": "Test",
            },
        )

        self.assertEqual(Thread.objects.count(), 0)


class SendMessageViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )

        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

        self.thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

    def test_send_message_post_only(self):
        """Test send message only accepts POST"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")
        response = self.client.get(
            reverse("messaging:send", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_send_message_success(self):
        """Test sending message via send endpoint"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:send", kwargs={"thread_id": self.thread.id}),
            {"body": "Test message"},
        )

        self.assertRedirects(
            response, reverse("messaging:thread", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(self.thread.messages.count(), 1)

    def test_send_message_empty_body(self):
        """Test sending empty message fails"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        self.client.post(
            reverse("messaging:send", kwargs={"thread_id": self.thread.id}),
            {"body": ""},
        )

        self.assertEqual(self.thread.messages.count(), 0)


class GetNewMessagesViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            first_name="User",
            last_name="One",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            first_name="User",
            last_name="Two",
            is_verified=True,
        )
        self.user3 = User.objects.create_user(
            email="user3@nyu.edu",
            username="user3",
            password="TestPassword123!",
            is_verified=True,
        )

        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")
        Profile.objects.create(user=self.user3, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

        self.thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

    def test_get_new_messages_requires_login(self):
        """Test AJAX endpoint requires authentication"""
        response = self.client.get(
            reverse("messaging:get_new_messages", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_get_new_messages_forbidden_non_participant(self):
        """Test non-participants get 403"""
        self.client.login(username="user3@nyu.edu", password="TestPassword123!")
        response = self.client.get(
            reverse("messaging:get_new_messages", kwargs={"thread_id": self.thread.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_get_new_messages_success(self):
        """Test fetching new messages"""
        msg1 = Message.objects.create(
            thread=self.thread, sender=self.user1, body="First"
        )
        msg2 = Message.objects.create(
            thread=self.thread, sender=self.user2, body="Second"
        )

        self.client.login(username="user1@nyu.edu", password="TestPassword123!")
        response = self.client.get(
            reverse("messaging:get_new_messages", kwargs={"thread_id": self.thread.id}),
            {"last_message_id": msg1.id},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["id"], msg2.id)

    def test_get_new_messages_marks_as_read(self):
        """Test fetching messages marks them as read"""
        msg = Message.objects.create(
            thread=self.thread, sender=self.user2, body="Test", is_read=False
        )

        self.client.login(username="user1@nyu.edu", password="TestPassword123!")
        self.client.get(
            reverse("messaging:get_new_messages", kwargs={"thread_id": self.thread.id}),
            {"last_message_id": 0},
        )

        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_get_new_messages_invalid_last_id(self):
        """Test with invalid last_message_id parameter"""
        Message.objects.create(thread=self.thread, sender=self.user1, body="Test")

        self.client.login(username="user1@nyu.edu", password="TestPassword123!")
        response = self.client.get(
            reverse("messaging:get_new_messages", kwargs={"thread_id": self.thread.id}),
            {"last_message_id": "invalid"},
        )

        self.assertEqual(response.status_code, 200)
        # Should default to 0 and return all messages
        data = response.json()
        self.assertEqual(data["count"], 1)


class StartThreadMissingParametersTests(TestCase):
    """Test start_thread with missing parameters"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="user@nyu.edu",
            username="user",
            password="TestPassword123!",
            is_verified=True,
        )
        Profile.objects.create(user=self.user, university="nyu")

    def test_start_thread_missing_listing_id(self):
        """Test starting thread without listing_id"""
        self.client.login(username="user@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:start_thread"),
            {"recipient_id": self.user.id, "body": "Test"},
        )

        self.assertRedirects(response, reverse("public_listings"))

    def test_start_thread_missing_recipient_id(self):
        """Test starting thread without recipient_id"""
        self.client.login(username="user@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:start_thread"),
            {"listing_id": 1, "body": "Test"},
        )

        self.assertRedirects(response, reverse("public_listings"))


class SendMessageForbiddenTests(TestCase):
    """Test send_message endpoint with non-participant"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user3 = User.objects.create_user(
            email="user3@nyu.edu",
            username="user3",
            password="TestPassword123!",
            is_verified=True,
        )

        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")
        Profile.objects.create(user=self.user3, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

        self.thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

    def test_send_message_forbidden_non_participant(self):
        """Test non-participants get 403 when trying to send message"""
        self.client.login(username="user3@nyu.edu", password="TestPassword123!")

        response = self.client.post(
            reverse("messaging:send", kwargs={"thread_id": self.thread.id}),
            {"body": "Test message"},
        )

        self.assertEqual(response.status_code, 403)


class GetNewMessagesWithProfilePhotoTests(TestCase):
    """Test get_new_messages with profile photo"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            first_name="User",
            last_name="One",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )

        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create profile with photo for user1
        photo = SimpleUploadedFile(
            "test.jpg", b"file_content", content_type="image/jpeg"
        )
        Profile.objects.create(user=self.user1, university="nyu", profile_photo=photo)
        Profile.objects.create(user=self.user2, university="nyu")

        self.listing = Listing.objects.create(
            user=self.user1,
            title="Test Apartment",
            description="Test",
            street_address="123 Test St",
            city="New York",
            zipcode="10012",
            rent=1000,
            availability_start=timezone.now().date(),
            availability_end=(timezone.now() + timezone.timedelta(days=365)).date(),
        )

        self.thread = Thread.objects.create(
            listing=self.listing, user_a=self.user1, user_b=self.user2
        )

    def test_get_new_messages_includes_profile_photo(self):
        """Test that profile photo URL is included in message data"""
        Message.objects.create(thread=self.thread, sender=self.user1, body="Test")

        self.client.login(username="user2@nyu.edu", password="TestPassword123!")
        response = self.client.get(
            reverse("messaging:get_new_messages", kwargs={"thread_id": self.thread.id}),
            {"last_message_id": 0},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 1)
        # Check that profile_photo_url is present and not None
        self.assertIsNotNone(data["messages"][0]["profile_photo_url"])
