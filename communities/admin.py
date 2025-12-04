"""
Django admin configuration for communities app.
"""
from django.contrib import admin
from .models import Community, CommunityMember


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
