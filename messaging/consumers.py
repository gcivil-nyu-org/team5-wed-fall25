import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from messaging.models import Thread, Message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time messaging in threads.
    Handles chat messages, typing indicators, and read receipts.
    """

    async def connect(self):
        """
        Handle WebSocket connection.
        Authenticate user, verify thread access, and join thread group.
        """
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.thread_group_name = f"thread_{self.thread_id}"
        self.user = self.scope["user"]

        # Reject anonymous users
        if self.user.is_anonymous:
            logger.warning(f"Anonymous user attempted to connect to thread {self.thread_id}")
            await self.close()
            return

        # Verify user is a participant in this thread
        try:
            thread = await self.get_thread(self.thread_id)
            if self.user.id not in (thread.user_a_id, thread.user_b_id):
                logger.warning(
                    f"User {self.user.id} attempted to access unauthorized thread {self.thread_id}"
                )
                await self.close()
                return
        except ObjectDoesNotExist:
            logger.error(f"Thread {self.thread_id} does not exist")
            await self.close()
            return

        # Join thread group
        await self.channel_layer.group_add(self.thread_group_name, self.channel_name)

        # Accept WebSocket connection
        await self.accept()

        # Mark unread messages as read
        await self.mark_messages_as_read(thread)

        logger.info(
            f"User {self.user.id} connected to thread {self.thread_id}"
        )

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Leave thread group.
        """
        # Leave thread group
        await self.channel_layer.group_discard(self.thread_group_name, self.channel_name)

        logger.info(
            f"User {self.user.id} disconnected from thread {self.thread_id} (code: {close_code})"
        )

    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket.
        Supports message types: chat_message, typing_indicator.
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
            return

        message_type = data.get("type")

        if message_type == "chat_message":
            await self.handle_chat_message(data)
        elif message_type == "typing_indicator":
            await self.handle_typing_indicator(data)
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def handle_chat_message(self, data):
        """
        Handle incoming chat message.
        Save to database and broadcast to thread group.
        """
        body = data.get("body", "").strip()

        if not body:
            await self.send(text_data=json.dumps({"error": "Message body cannot be empty"}))
            return

        if len(body) > 2000:
            await self.send(text_data=json.dumps({"error": "Message too long (max 2000 characters)"}))
            return

        # Save message to database
        message = await self.save_message(self.thread_id, self.user.id, body)

        # Get thread to find both participants
        thread = await self.get_thread(self.thread_id)

        # Broadcast message to thread group (with message ID, not formatted data)
        # Each recipient will format it based on their own perspective
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                "type": "chat_message",
                "message_id": message.id,
            },
        )

        # Notify both users' inboxes (Phase 2)
        await self.channel_layer.group_send(
            f"inbox_{thread.user_a_id}",
            {"type": "inbox_update", "thread_id": self.thread_id}
        )
        await self.channel_layer.group_send(
            f"inbox_{thread.user_b_id}",
            {"type": "inbox_update", "thread_id": self.thread_id}
        )

        logger.info(f"Message {message.id} sent to thread {self.thread_id}")

    async def handle_typing_indicator(self, data):
        """
        Handle typing indicator.
        Broadcast to thread group (handled in Phase 3).
        """
        is_typing = data.get("is_typing", False)

        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                "type": "typing_status",
                "user_id": self.user.id,
                "user_name": self.user.first_name or self.user.username,
                "is_typing": is_typing,
            },
        )

    async def chat_message(self, event):
        """
        Broadcast handler for chat messages.
        Fetch and format message based on current user's perspective.
        """
        message_id = event["message_id"]

        # Fetch message from database
        message = await self.get_message(message_id)

        # Format message data with correct is_current_user flag for this recipient
        message_data = await self.format_message(message)

        # Debug logging
        logger.info(
            f"Broadcasting to user {self.user.id}: message {message_id} "
            f"from sender {message.sender.id}, is_current_user={message_data['is_current_user']}"
        )

        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message_data,
        }))

    async def typing_status(self, event):
        """
        Broadcast handler for typing indicators.
        Send typing status to WebSocket (don't send back to sender).
        """
        # Don't send typing indicator back to the person typing
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps({
                "type": "typing_indicator",
                "user_name": event["user_name"],
                "is_typing": event["is_typing"],
            }))

    # Database helper methods (wrapped in database_sync_to_async)

    @database_sync_to_async
    def get_thread(self, thread_id):
        """
        Get thread from database with related users.
        """
        return Thread.objects.select_related("user_a", "user_b").get(id=thread_id)

    @database_sync_to_async
    def get_message(self, message_id):
        """
        Get message from database with sender profile.
        """
        return Message.objects.select_related("sender", "sender__profile").get(id=message_id)

    @database_sync_to_async
    def save_message(self, thread_id, sender_id, body):
        """
        Save message to database.
        """
        thread = Thread.objects.get(id=thread_id)
        message = Message.objects.create(
            thread=thread,
            sender_id=sender_id,
            body=body,
        )
        return message

    @database_sync_to_async
    def format_message(self, message):
        """
        Format message data for JSON response.
        Matches the format from the old AJAX endpoint.
        """
        # Get profile photo URL
        profile_photo_url = None
        if hasattr(message.sender, "profile") and message.sender.profile.profile_photo:
            profile_photo_url = message.sender.profile.profile_photo.url

        return {
            "id": message.id,
            "sender_id": message.sender.id,
            "sender_name": message.sender.first_name or message.sender.username,
            "sender_first_initial": (
                message.sender.first_name or message.sender.username
            )[0].upper(),
            "sender_last_initial": (
                (message.sender.last_name or "")[0].upper()
                if message.sender.last_name
                else ""
            ),
            "profile_photo_url": profile_photo_url,
            "body": message.body,
            "created_at": message.created_at.strftime("%b %d, %I:%M %p"),
            "is_current_user": message.sender.id == self.user.id,
        }

    @database_sync_to_async
    def mark_messages_as_read(self, thread):
        """
        Mark unread messages as read when user connects to thread.
        """
        Message.objects.filter(
            thread=thread,
            is_read=False
        ).exclude(
            sender=self.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )


class InboxConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time inbox updates.
    Notifies user when new messages arrive in any thread.
    """

    async def connect(self):
        """
        Handle WebSocket connection for inbox updates.
        Join user-specific inbox group.
        """
        self.user = self.scope["user"]

        # Reject anonymous users
        if self.user.is_anonymous:
            logger.warning("Anonymous user attempted to connect to inbox")
            await self.close()
            return

        # Create user-specific inbox group
        self.inbox_group_name = f"inbox_{self.user.id}"

        # Join inbox group
        await self.channel_layer.group_add(self.inbox_group_name, self.channel_name)

        # Accept WebSocket connection
        await self.accept()

        logger.info(f"User {self.user.id} connected to inbox updates")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Leave inbox group.
        """
        # Leave inbox group
        await self.channel_layer.group_discard(self.inbox_group_name, self.channel_name)

        logger.info(f"User {self.user.id} disconnected from inbox (code: {close_code})")

    async def inbox_update(self, event):
        """
        Broadcast handler for inbox updates.
        Fetch thread preview data and send to client.
        """
        thread_id = event["thread_id"]

        # Fetch thread preview data
        thread_data = await self.get_thread_preview(thread_id)

        await self.send(text_data=json.dumps({
            "type": "inbox_update",
            "thread": thread_data,
        }))

        logger.info(f"Sent inbox update to user {self.user.id} for thread {thread_id}")

    # Database helper methods

    @database_sync_to_async
    def get_thread_preview(self, thread_id):
        """
        Get thread preview data for inbox display.
        """
        from django.db.models import Q, Count

        thread = Thread.objects.select_related(
            "listing", "item", "user_a", "user_b",
            "user_a__profile", "user_b__profile"
        ).prefetch_related("messages").get(id=thread_id)

        # Get the other participant
        other = thread.user_b if thread.user_a_id == self.user.id else thread.user_a

        # Get last message
        last_message = thread.messages.order_by("-created_at").first()

        # Count unread messages for this user
        unread_count = thread.messages.filter(
            is_read=False
        ).exclude(sender=self.user).count()

        # Get profile photo URL
        profile_photo_url = None
        if hasattr(other, "profile") and other.profile.profile_photo:
            profile_photo_url = other.profile.profile_photo.url

        # Format thread data for inbox display
        return {
            "id": thread.id,
            "other_user": {
                "id": other.id,
                "name": other.first_name or other.username,
                "first_initial": (other.first_name or other.username)[0].upper(),
                "last_initial": (other.last_name or "")[0].upper() if other.last_name else "",
                "profile_photo_url": profile_photo_url,
            },
            "related_object": {
                "type": "listing" if thread.listing else "item",
                "title": thread.listing.title if thread.listing else thread.item.title,
            },
            "last_message": {
                "body": last_message.body if last_message else "",
                "created_at": last_message.created_at.strftime("%b %d, %I:%M %p") if last_message else "",
                "sender_name": (last_message.sender.first_name or last_message.sender.username) if last_message else "",
            } if last_message else None,
            "unread_count": unread_count,
            "updated_at": thread.updated_at.strftime("%b %d, %I:%M %p"),
        }
