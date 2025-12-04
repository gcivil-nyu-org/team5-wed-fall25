# messaging/context_processors.py
from django.db.models import Q
from .models import Message


def unread_message_count(request):
    """
    Context processor to inject unread message count into all templates.
    """
    if not request.user.is_authenticated:
        return {"unread_message_count": 0}

    # Count unread messages across all threads where user is a participant
    count = Message.objects.filter(
        Q(thread__user_a=request.user) | Q(thread__user_b=request.user)
    ).filter(is_read=False).exclude(sender=request.user).count()

    return {"unread_message_count": count}
