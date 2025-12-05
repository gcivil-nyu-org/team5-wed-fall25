"""
Django admin configuration for communities app.
"""
from django.contrib import admin
from .models import Community, CommunityMember, Post, PostImage, PostFile, Comment


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    """Admin interface for Community model."""
    list_display = ('name', 'privacy', 'university', 'member_count', 'created_by', 'created_at', 'is_active')
    list_filter = ('privacy', 'university', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'member_count', 'post_count')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'cover_image')
        }),
        ('Privacy & Access', {
            'fields': ('privacy', 'university')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active')
        }),
        ('Statistics', {
            'fields': ('member_count', 'post_count')
        }),
    )


@admin.register(CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    """Admin interface for CommunityMember model."""
    list_display = ('user', 'community', 'role', 'status', 'joined_at')
    list_filter = ('role', 'status', 'joined_at')
    search_fields = ('user__username', 'user__email', 'community__name')
    readonly_fields = ('joined_at', 'updated_at')
    fieldsets = (
        ('Membership', {
            'fields': ('community', 'user', 'role', 'status')
        }),
        ('Join Request', {
            'fields': ('request_message', 'reviewed_by')
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'updated_at')
        }),
    )


class PostImageInline(admin.TabularInline):
    """Inline admin for post images."""
    model = PostImage
    extra = 1
    readonly_fields = ('uploaded_at',)


class PostFileInline(admin.TabularInline):
    """Inline admin for post files."""
    model = PostFile
    extra = 1
    readonly_fields = ('uploaded_at', 'file_size')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin interface for Post model."""
    list_display = ('id', 'author', 'community', 'title_preview', 'is_pinned', 'comment_count', 'created_at')
    list_filter = ('is_pinned', 'is_edited', 'created_at', 'community')
    search_fields = ('title', 'content', 'author__username', 'community__name')
    readonly_fields = ('created_at', 'updated_at', 'comment_count')
    inlines = [PostImageInline, PostFileInline]
    fieldsets = (
        ('Post Content', {
            'fields': ('community', 'author', 'title', 'content')
        }),
        ('Moderation', {
            'fields': ('is_pinned', 'pinned_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_edited', 'comment_count')
        }),
    )

    def title_preview(self, obj):
        """Show title or content preview."""
        return obj.title or obj.content[:50] + '...'
    title_preview.short_description = 'Title/Content'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model."""
    list_display = ('id', 'author', 'post', 'content_preview', 'parent', 'created_at')
    list_filter = ('is_edited', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Comment', {
            'fields': ('post', 'author', 'content', 'parent')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_edited')
        }),
    )

    def content_preview(self, obj):
        """Show content preview."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
