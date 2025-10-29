# messaging/views.py
from django.contrib import messages as dj_messages
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from listings.models import Listing
from marketplace.models import Item
from .models import Message, Thread

User = get_user_model()


@login_required
def inbox(request):
    """
    List all conversation threads the user participates in, newest activity first.
    """
    threads = (
        Thread.objects.filter(Q(user_a=request.user) | Q(user_b=request.user))
        .select_related("listing", "user_a", "user_b")
        .prefetch_related("messages")
    )

    rows = []
    for t in threads:
        other = t.other_participant(request.user)
        last = t.messages.last()
        unread = t.messages.filter(is_read=False).exclude(sender=request.user).count()
        rows.append((t, other, last, unread))

    # Sort by last message time (or thread.updated_at if none)
    rows.sort(
        key=lambda item: (item[2].created_at if item[2] else item[0].updated_at),
        reverse=True,
    )

    return render(
        request,
        "messaging/inbox.html",
        {"rows": rows},  # (thread, other_user, last_msg, unread_count)
    )


@login_required
def thread_view(request, thread_id):
    """
    Show a single thread and allow sending a message via POST to the same URL.
    """
    t = get_object_or_404(Thread, id=thread_id)
    if request.user.id not in (t.user_a_id, t.user_b_id):
        return HttpResponseForbidden("Not your conversation.")

    msgs = t.messages.select_related("sender").order_by("created_at")

    # mark incoming as read
    t.messages.filter(is_read=False).exclude(sender=request.user).update(
        is_read=True, read_at=timezone.now()
    )

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()
        if not body:
            messages.error(request, "Message cannot be empty.")
            return redirect("messaging:thread", thread_id=t.id)

        Message.objects.create(thread=t, sender=request.user, body=body)
        messages.success(request, "Message sent.")
        return redirect("messaging:thread", thread_id=t.id)

    return render(
        request,
        "messaging/thread.html",
        {
            "thread": t,
            "chat_messages": msgs,
            "other": t.other_participant(request.user),
        },
    )


@login_required
def start_thread(request):
    """
    Creates (or finds) a thread between request.user and the listing/item owner,
    posts the initial message, and redirects to the thread page.
    """
    # Don't reference listing_id/item_id unless we actually have a POST payload
    if request.method != "POST":
        # Nothing to do – go back to inbox (avoids undefined listing_id/item_id).
        return redirect("messaging:inbox")

    body = (request.POST.get("body") or "").strip()
    listing_id = request.POST.get("listing_id")
    item_id = request.POST.get("item_id")
    recipient_id = request.POST.get("recipient_id")

    # Basic input checks - must have either listing_id or item_id
    if (not listing_id and not item_id) or not recipient_id:
        messages.error(request, "Invalid request.")
        return redirect("public_listings")

    if not body:
        messages.error(request, "Message cannot be empty.")
        if listing_id:
            return redirect("view_listing", listing_id=listing_id)
        else:
            return redirect("view_item", item_id=item_id)

    # Handle listing thread
    if listing_id:
        listing = get_object_or_404(Listing, pk=listing_id)

        if str(listing.user_id) != str(recipient_id):
            messages.error(request, "Invalid recipient.")
            return redirect("view_listing", listing_id=listing_id)

        if request.user.id == listing.user_id:
            messages.error(request, "You cannot message yourself about your own listing.")
            return redirect("view_listing", listing_id=listing_id)

        # Canonicalize participant ordering (user_a < user_b by id)
        user_a, user_b = (request.user, listing.user)
        if user_a.id > user_b.id:
            user_a, user_b = user_b, user_a

        thread, _created = Thread.objects.get_or_create(
            listing=listing,
            item=None,
            user_a=user_a,
            user_b=user_b,
        )

        Message.objects.create(thread=thread, sender=request.user, body=body)
        messages.success(request, "Message sent.")
        return redirect("messaging:thread", thread_id=thread.id)

    # Handle marketplace item thread
    else:
        item = get_object_or_404(Item, pk=item_id)

        if str(item.user_id) != str(recipient_id):
            messages.error(request, "Invalid recipient.")
            return redirect("view_item", item_id=item_id)

        if request.user.id == item.user_id:
            messages.error(request, "You cannot message yourself about your own item.")
            return redirect("view_item", item_id=item_id)

        # Canonicalize participant ordering (user_a < user_b by id)
        user_a, user_b = (request.user, item.user)
        if user_a.id > user_b.id:
            user_a, user_b = user_b, user_a

        thread, _created = Thread.objects.get_or_create(
            listing=None,
            item=item,
            user_a=user_a,
            user_b=user_b,
        )

        Message.objects.create(thread=thread, sender=request.user, body=body)
        messages.success(request, "Message sent.")
        return redirect("messaging:thread", thread_id=thread.id)


@login_required
def send_message(request, thread_id):
    """
    Optional separate endpoint for posting a message to an existing thread.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    t = get_object_or_404(Thread, id=thread_id)
    if request.user.id not in (t.user_a_id, t.user_b_id):
        return HttpResponseForbidden("Not your conversation.")

    body = (request.POST.get("body") or "").strip()
    if not body:
        dj_messages.error(request, "Message cannot be empty.")
        return redirect("messaging:thread", thread_id=thread_id)

    Message.objects.create(thread=t, sender=request.user, body=body)
    dj_messages.success(request, "Message sent.")
    return redirect("messaging:thread", thread_id=thread_id)


@login_required
def get_new_messages(request, thread_id):
    """
    AJAX endpoint to fetch new messages for a thread.
    Returns JSON with new messages since the provided timestamp.
    """
    t = get_object_or_404(Thread, id=thread_id)
    if request.user.id not in (t.user_a_id, t.user_b_id):
        return JsonResponse({"error": "Not your conversation."}, status=403)

    # Get the last message ID the client has
    last_message_id = request.GET.get("last_message_id", 0)

    try:
        last_message_id = int(last_message_id)
    except (ValueError, TypeError):
        last_message_id = 0

    # Fetch messages newer than the last known message
    new_messages = (
        t.messages.filter(id__gt=last_message_id)
        .select_related("sender")
        .order_by("created_at")
    )

    # Mark incoming messages as read
    new_messages.filter(is_read=False).exclude(sender=request.user).update(
        is_read=True, read_at=timezone.now()
    )

    # Build JSON response
    messages_data = []
    for msg in new_messages:
        # Check if sender has a profile with photo
        profile_photo_url = None
        if hasattr(msg.sender, "profile") and msg.sender.profile.profile_photo:
            profile_photo_url = msg.sender.profile.profile_photo.url

        messages_data.append(
            {
                "id": msg.id,
                "sender_id": msg.sender.id,
                "sender_name": msg.sender.first_name or msg.sender.username,
                "sender_first_initial": (msg.sender.first_name or msg.sender.username)[
                    0
                ].upper(),
                "sender_last_initial": (
                    (msg.sender.last_name or "")[0].upper()
                    if msg.sender.last_name
                    else ""
                ),
                "profile_photo_url": profile_photo_url,
                "body": msg.body,
                "created_at": msg.created_at.strftime("%b %d, %I:%M %p"),
                "is_current_user": msg.sender.id == request.user.id,
            }
        )

    return JsonResponse(
        {
            "messages": messages_data,
            "count": len(messages_data),
        }
    )
