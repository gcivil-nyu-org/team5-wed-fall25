from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "university", "visibility", "created_at")
    search_fields = ("user__username", "university")
    list_filter = ("university", "visibility")
