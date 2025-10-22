# messaging/views.py
from django.contrib import messages as dj_messages
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from listings.models import Listing
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
    Creates (or finds) a thread between request.user and the listing owner,
    posts the initial message, and redirects to the thread page.
    """
    # Don't reference listing_id unless we actually have a POST payload
    if request.method != "POST":
        # Nothing to do – go back to inbox (avoids undefined listing_id).
        return redirect("messaging:inbox")

    body = (request.POST.get("body") or "").strip()
    listing_id = request.POST.get("listing_id")
    recipient_id = request.POST.get("recipient_id")

    # Basic input checks
    if not listing_id or not recipient_id:
        messages.error(request, "Invalid request.")
        return redirect("listings:public_listings")

    if not body:
        messages.error(request, "Message cannot be empty.")
        return redirect("listings:view_listing", listing_id=listing_id)

    listing = get_object_or_404(Listing, pk=listing_id)

    if str(listing.user_id) != str(recipient_id):
        messages.error(request, "Invalid recipient.")
        return redirect("listings:view_listing", listing_id=listing_id)

    if request.user.id == listing.user_id:
        messages.error(request, "You cannot message yourself about your own listing.")
        return redirect("listings:view_listing", listing_id=listing_id)

    # Canonicalize participant ordering (user_a < user_b by id)
    user_a, user_b = (request.user, listing.user)
    if user_a.id > user_b.id:
        user_a, user_b = user_b, user_a

    thread, _created = Thread.objects.get_or_create(
        listing=listing,
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
