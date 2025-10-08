from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model
    """
    # Fields to display in the user list
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_verified', 'is_staff', 'date_joined']
    
    # Fields you can click to open user detail
    list_display_links = ['email', 'username']
    
    # Add filters in the sidebar
    list_filter = ['is_verified', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    
    # Add search functionality
    search_fields = ['email', 'username', 'first_name', 'last_name']
    
    # Fields to show when editing a user
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields to show when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'is_verified'),
        }),
    )
    
    # Default ordering
    ordering = ['-date_joined']


# Register the custom User model with custom admin
admin.site.register(User, UserAdmin)
