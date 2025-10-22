# messaging/admin.py
from django.contrib import admin
from .models import Thread, Message

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'user_a', 'user_b', 'created_at', 'updated_at')
    search_fields = ('listing__title', 'user_a__username', 'user_b__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('sender__username', 'body')
