"""
Django admin configuration for communities app.
"""

from django.contrib import admin
from .models import (
    Community,
    CommunityMember,
    Post,
    PostImage,
    PostFile,
    Comment,
    Thread,
    ChatMessage,
    Event,
    EventRSVP,
)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    """Admin interface for Community model."""

    list_display = (
        "name",
        "privacy",
        "university",
        "member_count",
        "created_by",
        "created_at",
        "is_active",
    )
    list_filter = ("privacy", "university", "is_active", "created_at")
    search_fields = ("name", "description", "created_by__username")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "member_count", "post_count")
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "slug", "description", "cover_image")},
        ),
        ("Privacy & Access", {"fields": ("privacy", "university")}),
        (
            "Metadata",
            {"fields": ("created_by", "created_at", "updated_at", "is_active")},
        ),
        ("Statistics", {"fields": ("member_count", "post_count")}),
    )


@admin.register(CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    """Admin interface for CommunityMember model."""

    list_display = ("user", "community", "role", "status", "joined_at")
    list_filter = ("role", "status", "joined_at")
    search_fields = ("user__username", "user__email", "community__name")
    readonly_fields = ("joined_at", "updated_at")
    fieldsets = (
        ("Membership", {"fields": ("community", "user", "role", "status")}),
        ("Join Request", {"fields": ("request_message", "reviewed_by")}),
        ("Timestamps", {"fields": ("joined_at", "updated_at")}),
    )


class PostImageInline(admin.TabularInline):
    """Inline admin for post images."""

    model = PostImage
    extra = 1
    readonly_fields = ("uploaded_at",)


class PostFileInline(admin.TabularInline):
    """Inline admin for post files."""

    model = PostFile
    extra = 1
    readonly_fields = ("uploaded_at", "file_size")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin interface for Post model."""

    list_display = (
        "id",
        "author",
        "community",
        "title_preview",
        "is_pinned",
        "comment_count",
        "created_at",
    )
    list_filter = ("is_pinned", "is_edited", "created_at", "community")
    search_fields = ("title", "content", "author__username", "community__name")
    readonly_fields = ("created_at", "updated_at", "comment_count")
    inlines = [PostImageInline, PostFileInline]
    fieldsets = (
        ("Post Content", {"fields": ("community", "author", "title", "content")}),
        ("Moderation", {"fields": ("is_pinned", "pinned_by")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at", "is_edited", "comment_count")},
        ),
    )

    def title_preview(self, obj):
        """Show title or content preview."""
        return obj.title or obj.content[:50] + "..."

    title_preview.short_description = "Title/Content"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model."""

    list_display = ("id", "author", "post", "content_preview", "parent", "created_at")
    list_filter = ("is_edited", "created_at")
    search_fields = ("content", "author__username", "post__title")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Comment", {"fields": ("post", "author", "content", "parent")}),
        ("Metadata", {"fields": ("created_at", "updated_at", "is_edited")}),
    )

    def content_preview(self, obj):
        """Show content preview."""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content"


class ChatMessageInline(admin.TabularInline):
    """Inline admin for chat messages."""

    model = ChatMessage
    extra = 0
    readonly_fields = ("sender", "created_at", "is_edited", "edited_at")
    fields = ("sender", "content", "created_at", "is_edited", "edited_at")
    can_delete = True
    show_change_link = True


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    """Admin interface for Thread model."""

    list_display = ("id", "community", "message_count", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("community__name",)
    readonly_fields = ("created_at", "updated_at", "message_count")
    inlines = [ChatMessageInline]
    fieldsets = (
        ("Thread", {"fields": ("community",)}),
        ("Statistics", {"fields": ("message_count",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatMessage model."""

    list_display = (
        "id",
        "sender",
        "thread",
        "content_preview",
        "created_at",
        "is_edited",
    )
    list_filter = ("is_edited", "created_at")
    search_fields = ("content", "sender__username", "thread__community__name")
    readonly_fields = ("created_at", "edited_at")
    fieldsets = (
        ("Message", {"fields": ("thread", "sender", "content")}),
        ("Metadata", {"fields": ("created_at", "is_edited", "edited_at")}),
    )

    def content_preview(self, obj):
        """Show content preview."""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content"


class EventRSVPInline(admin.TabularInline):
    """Inline admin for event RSVPs."""

    model = EventRSVP
    extra = 0
    readonly_fields = ("user", "status", "created_at", "updated_at")
    fields = ("user", "status", "created_at", "updated_at")
    can_delete = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for Event model."""

    list_display = (
        "id",
        "title",
        "community",
        "organizer",
        "start_datetime",
        "location",
        "going_count",
        "interested_count",
        "is_cancelled",
    )
    list_filter = ("is_cancelled", "start_datetime", "community")
    search_fields = (
        "title",
        "description",
        "location",
        "organizer__username",
        "community__name",
    )
    readonly_fields = ("created_at", "updated_at", "going_count", "interested_count")
    inlines = [EventRSVPInline]
    fieldsets = (
        (
            "Event Information",
            {
                "fields": (
                    "community",
                    "organizer",
                    "title",
                    "description",
                    "cover_image",
                )
            },
        ),
        ("Date & Time", {"fields": ("start_datetime", "end_datetime")}),
        (
            "Location",
            {"fields": ("location", "location_details", "latitude", "longitude")},
        ),
        ("Status", {"fields": ("is_cancelled",)}),
        ("Statistics", {"fields": ("going_count", "interested_count")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    """Admin interface for EventRSVP model."""

    list_display = ("id", "user", "event", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "event__title",
        "event__community__name",
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("RSVP", {"fields": ("event", "user", "status")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
