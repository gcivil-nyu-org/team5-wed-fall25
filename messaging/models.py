# messaging/models.py
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from listings.models import Listing
from marketplace.models import Item


class Thread(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="threads", null=True, blank=True
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="threads", null=True, blank=True
    )
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads_a"
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads_b"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "user_a", "user_b"],
                name="unique_thread_per_listing_pair",
            ),
            models.UniqueConstraint(
                fields=["item", "user_a", "user_b"],
                name="unique_thread_per_item_pair",
            ),
            models.CheckConstraint(
                condition=~Q(user_a=F("user_b")), name="prevent_self_thread"
            ),
        ]
        indexes = [
            models.Index(fields=["listing", "user_a"]),
            models.Index(fields=["listing", "user_b"]),
            models.Index(fields=["item", "user_a"]),
            models.Index(fields=["item", "user_b"]),
            models.Index(fields=["updated_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.user_a_id and self.user_b_id and self.user_a_id > self.user_b_id:
            self.user_a_id, self.user_b_id = self.user_b_id, self.user_a_id
        super().save(*args, **kwargs)

    def other_participant(self, user):
        return self.user_b if user.id == self.user_a_id else self.user_a

    def get_related_object(self):
        """Return the listing or item associated with this thread."""
        return self.listing if self.listing else self.item

    def __str__(self):
        if self.listing:
            return f"Thread(listing={self.listing_id}, users=({self.user_a_id},{self.user_b_id}))"
        else:
            return f"Thread(item={self.item_id}, users=({self.user_a_id},{self.user_b_id}))"


class Message(models.Model):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread", "created_at"]),
            models.Index(fields=["thread", "is_read"]),
        ]

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def __str__(self):
        return f"Msg(thread={self.thread_id}, from={self.sender_id}, at={self.created_at:%Y-%m-%d %H:%M})"
