# listings/views.py
from __future__ import annotations

import re
from typing import List, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ListingForm
from .models import Listing, ListingImage

# ---------- config ----------
MAX_IMAGES = 10
MAX_IMAGE_MB = 5

# allow foo.edu or foo.bar.edu, etc.
_EDU_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+edu$",
    re.IGNORECASE,
)


def validate_image_files(files, form=None):
    """
    Back-compat helper expected by tests.
    Signature: validate_image_files(files, form) -> bool

    IMPORTANT (per tests):
    - Return **True** if there is a validation error (i.e., something is wrong)
    - Return **False** if everything is valid
    - If form is provided, attach non-field errors to the form
    """

    def _add(msg):
        if form is not None:
            form.add_error(None, msg)

    # Must have at least one image
    if not files:
        _add("Please upload at least one image.")
        return True  # error

    # Too many images
    if len(files) > MAX_IMAGES:
        _add(f"You can upload a maximum of {MAX_IMAGES} images.")
        return True  # error

    # Validate each file
    for f in files:
        name = getattr(f, "name", "File")
        ctype = getattr(f, "content_type", "") or ""
        size = getattr(f, "size", 0)

        if not ctype.startswith("image/"):
            _add(f"{name} is not a valid image file.")
            return True  # error

        if size > MAX_IMAGE_MB * 1024 * 1024:
            _add(f"{name} exceeds {MAX_IMAGE_MB}MB size limit.")
            return True  # error

    return False


def _is_edu_email(email: str) -> bool:
    """Return True if email is a .edu address (subdomains allowed)."""
    return bool(email and _EDU_REGEX.match(email))


def _build_abs(request, url_name: str, *args, **kwargs) -> str:
    """Build absolute URL for emails in dev/prod."""
    rel = reverse(url_name, args=args, kwargs=kwargs)
    return request.build_absolute_uri(rel)


def _validate_images_for_edit(
    files, keep_existing: bool, listing: Listing
) -> Optional[str]:
    """
    Return an error message if validation fails, otherwise None.
    This is split out to keep edit_listing complexity low.
    """
    if files:
        if len(files) > MAX_IMAGES:
            return f"You can upload a maximum of {MAX_IMAGES} images."
        for f in files:
            content_type = getattr(f, "content_type", "") or ""
            if not content_type.startswith("image/"):
                return f"{f.name} is not a valid image file."
            if f.size > MAX_IMAGE_MB * 1024 * 1024:
                return f"{f.name} exceeds {MAX_IMAGE_MB}MB size limit."
        return None

    # No new files uploaded
    if not keep_existing and not listing.images.exists():
        return "Please upload at least one image or keep existing images."
    return None


# ---------- public browse ----------
def public_listings(request):
    """
    Public browse page for all published (active, not expired) listings,
    with optional q/min/max filters and pagination.
    """
    today = timezone.now().date()
    qs = (
        Listing.objects.filter(is_active=True, availability_end__gte=today)
        .select_related("user")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    q = request.GET.get("q", "").strip()
    min_rent = request.GET.get("min", "").strip()
    max_rent = request.GET.get("max", "").strip()

    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(address__icontains=q)
            | Q(description__icontains=q)
        )
    if min_rent.isdigit():
        qs = qs.filter(rent__gte=int(min_rent))
    if max_rent.isdigit():
        qs = qs.filter(rent__lte=int(max_rent))

    paginator = Paginator(qs, 12)  # 12 cards/page
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = {
        "page_obj": page_obj,
        "q": q,
        "min_rent": min_rent,
        "max_rent": max_rent,
    }
    return render(request, "listings/public_listings.html", ctx)


# ---------- create ----------
@login_required
def create_listing(request):
    # Verify .edu email domain
    if not _is_edu_email(request.user.email):
        messages.error(
            request,
            "Only verified .edu email addresses can post listings.",
        )
        return redirect("profiles:view_profile")

    if request.method == "POST":
        form = ListingForm(request.POST)
        files: List = request.FILES.getlist("images")

        # Validate images
        has_image_error = False
        if not files:
            form.add_error(None, "Please upload at least one image.")
            has_image_error = True
        elif len(files) > MAX_IMAGES:
            form.add_error(None, f"You can upload a maximum of {MAX_IMAGES} images.")
            has_image_error = True
        else:
            for f in files:
                if not (getattr(f, "content_type", "") or "").startswith("image/"):
                    form.add_error(None, f"{f.name} is not a valid image file.")
                    has_image_error = True
                    break
                if f.size > MAX_IMAGE_MB * 1024 * 1024:
                    form.add_error(
                        None, f"{f.name} exceeds {MAX_IMAGE_MB}MB size limit."
                    )
                    has_image_error = True
                    break

        if form.is_valid() and not has_image_error:
            with transaction.atomic():
                listing = form.save(commit=False)
                listing.user = request.user
                listing.save()

                for f in files:
                    ListingImage.objects.create(listing=listing, image=f)

            # Email confirmation
            view_url = _build_abs(
                request, "listings:view_listing", listing_id=listing.id
            )
            send_mail(
                subject="Your CampusNest Listing is Live!",
                message=(
                    f"Your listing '{listing.title}' has been posted successfully.\n"
                    f"View it at {view_url}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL or "noreply@campusnest.com",
                recipient_list=[request.user.email],
                fail_silently=True,
            )

            messages.success(
                request,
                "Listing created successfully! A confirmation email has been sent.",
            )
            return redirect("listings:view_listing", listing_id=listing.id)
    else:
        form = ListingForm()

    return render(request, "listings/create_listing.html", {"form": form})


# ---------- edit ----------
@login_required
def edit_listing(request, listing_id: int):  # noqa: C901
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)
        files = request.FILES.getlist("images")
        keep_existing = request.POST.get("keep_existing_images") == "on"

        # Validate images
        has_image_error = False
        if files:
            if len(files) > MAX_IMAGES:
                form.add_error(
                    None, f"You can upload a maximum of {MAX_IMAGES} images."
                )
                has_image_error = True
            else:
                for f in files:
                    if not (getattr(f, "content_type", "") or "").startswith("image/"):
                        form.add_error(None, f"{f.name} is not a valid image file.")
                        has_image_error = True
                        break
                    if f.size > MAX_IMAGE_MB * 1024 * 1024:
                        form.add_error(
                            None, f"{f.name} exceeds {MAX_IMAGE_MB}MB size limit."
                        )
                        has_image_error = True
                        break
        elif not keep_existing and not listing.images.exists():
            form.add_error(
                None, "Please upload at least one image or keep existing images."
            )
            has_image_error = True

        if form.is_valid() and not has_image_error:
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.is_edited = True
                obj.save()

                if files:
                    # replace old images with new ones
                    listing.images.all().delete()
                    for f in files:
                        ListingImage.objects.create(listing=listing, image=f)

            messages.success(request, "Listing updated successfully!")
            return redirect("listings:view_listing", listing_id=listing.id)
    else:
        form = ListingForm(instance=listing)

    # Pre-populate amenities on initial GET
    if request.method != "POST" and getattr(listing, "amenities", ""):
        form.initial["amenities"] = listing.amenities.split(",")

    return render(
        request, "listings/edit_listing.html", {"form": form, "listing": listing}
    )


# ---------- delete ----------
@login_required
def delete_listing(request, listing_id: int):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == "POST":
        title = listing.title
        listing.delete()

        send_mail(
            subject="Your CampusNest Listing Has Been Deleted",
            message=(
                f"Your listing '{title}' has been successfully deleted from "
                f"CampusNest.\n\nIf you didn't perform this action, please contact "
                f"us immediately.\n\nBest regards,\nThe CampusNest Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL or "noreply@campusnest.com",
            recipient_list=[request.user.email],
            fail_silently=True,
        )

        messages.success(request, f"Listing '{title}' has been deleted successfully.")
        return redirect("listings:my_listings")

    return render(request, "listings/delete_listing.html", {"listing": listing})


# ---------- detail (public) ----------


@login_required
def view_listing(request, listing_id):
    """View listing details. Shows different options based on ownership."""
    listing = get_object_or_404(Listing, id=listing_id)
    is_owner = listing.user == request.user

    # Only owners can view inactive listings
    if not listing.is_active and not is_owner:
        return get_object_or_404(Listing, id=listing_id, user=request.user)

    return render(
        request,
        "listings/view_listing.html",
        {"listing": listing, "is_owner": is_owner},
    )


# ---------- my listings ----------
@login_required
def my_listings(request):
    listings = Listing.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "listings/my_listings.html", {"listings": listings})


@login_required
def public_listings(request):
    """Display all active listings from other users"""
    listings = (
        Listing.objects.filter(is_active=True)
        .exclude(user=request.user)
        .select_related("user")
        .prefetch_related("images")
        .order_by("-created_at")
    )
    return render(request, "listings/public_listings.html", {"listings": listings})
