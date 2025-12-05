# feed/views.py
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models.functions import Greatest
from listings.models import Listing
from marketplace.models import Item
from messaging.models import Thread, Message
from profiles.models import Favorite, ConnectionRequest
from .models import Announcement


def _popular_listing_ids(limit=4):
    """
    Popular = listings with the most message activity across their threads.
    Falls back to empty list.
    """
    qs = (
        Thread.objects.filter(listing__isnull=False)
        .values("listing")
        .annotate(activity=Count("messages"))
        .order_by("-activity")
    )
    return list(qs.values_list("listing", flat=True)[:limit])


def home_portal(request):
    # Featured: popular (by message activity) then recent fallback
    popular_ids = _popular_listing_ids(limit=4)
    featured = list(Listing.objects.filter(is_active=True, id__in=popular_ids))
    # preserve popular order
    featured.sort(
        key=lambda lam: popular_ids.index(lam.id) if lam.id in popular_ids else 999
    )

    if len(featured) < 4:
        needed = 4 - len(featured)
        recent_fallback = (
            Listing.objects.filter(is_active=True)
            .exclude(id__in=popular_ids)
            .order_by("-created_at")[:needed]
        )
        featured.extend(list(recent_fallback))

    # Latest sections
    latest_listings = (
        Listing.objects.filter(is_active=True)
        .select_related("user")
        .prefetch_related("images")
        .annotate(activity_at=Greatest("created_at", "updated_at"))
        .order_by("-activity_at")[:8]
    )

    latest_items = (
        Item.objects.filter(is_active=True)
        .select_related("user")
        .prefetch_related("images")
        .order_by("-created_at")[:8]
    )

    # Announcements
    announcements = Announcement.objects.filter(is_published=True)[:3]

    # Quick stats (global)
    now = timezone.now()
    last_7 = now - timedelta(days=7)
    stats = {
        "active_listings": Listing.objects.filter(is_active=True).count(),
        "new_last_7": Listing.objects.filter(
            is_active=True, created_at__gte=last_7
        ).count(),
        "market_items": Item.objects.filter(is_active=True).count(),
    }

    # User stats (if logged in)
    user_stats = None
    if request.user.is_authenticated:
        # unread across all threads
        my_threads = Thread.objects.filter(
            Q(user_a=request.user) | Q(user_b=request.user)
        )
        unread = (
            Message.objects.filter(thread__in=my_threads, is_read=False)
            .exclude(sender=request.user)
            .count()
        )

        my_active_listings = Listing.objects.filter(
            user=request.user, is_active=True
        ).count()
        pending_conn = ConnectionRequest.objects.filter(
            to_user=request.user, status="pending"
        ).count()
        favorites = Favorite.objects.filter(user=request.user).count()

        # Simple suggestions: try to match on location & budget if profile exists
        suggestions = Listing.objects.filter(is_active=True)
        prof = getattr(request.user, "profile", None)
        if prof:
            if getattr(prof, "location", None):
                # Search across street_address, city, or zipcode
                suggestions = suggestions.filter(
                    Q(street_address__icontains=prof.location)
                    | Q(city__icontains=prof.location)
                    | Q(zipcode__icontains=prof.location)
                )
            # use budget range if present
            budget_min = getattr(prof, "budget_min", None)
            budget_max = getattr(prof, "budget_max", None)
            if budget_min is not None:
                suggestions = suggestions.filter(rent__gte=budget_min)
            if budget_max is not None:
                suggestions = suggestions.filter(rent__lte=budget_max)
        suggestions = suggestions.order_by("-created_at")[:4]

        user_stats = {
            "unread": unread,
            "my_active_listings": my_active_listings,
            "pending_conn": pending_conn,
            "favorites": favorites,
            "suggestions": suggestions,
        }

    ticker_items = [
        "Student housing in NYC rose by 20% this year",
        "Tip: Complete your profile to get better roommate matches",
    ]

    return render(
        request,
        "feed/home_portal.html",
        {
            "featured": featured,
            "latest_listings": latest_listings,
            "latest_items": latest_items,
            "announcements": announcements,
            "stats": stats,
            "user_stats": user_stats,
            "ticker_items": ticker_items,
        },
    )
