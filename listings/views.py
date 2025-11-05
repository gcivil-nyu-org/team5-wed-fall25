"""
Updated view functions with geocoding integration.

Key changes:
1. Import geocode_address utility
2. Geocode address when creating/editing listings
3. Store coordinates in database
4. Pass MAPBOX token to templates for map display
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from datetime import datetime
from .forms import ListingForm
from .models import Listing, ListingImage
from .constants import AMENITY_CHOICES
from django.urls import reverse

# Import the geocoding utility
from .utils import geocode_address


def validate_image_files(files, form):
    """Validate uploaded image files. Returns True if validation fails."""
    if len(files) > 10:
        form.add_error(None, "You can upload a maximum of 10 images.")
        return True

    for file in files:
        if not file.content_type.startswith("image/"):
            form.add_error(None, f"{file.name} is not a valid image file.")
            return True
        if file.size > 5 * 1024 * 1024:
            form.add_error(None, f"{file.name} exceeds 5MB size limit.")
            return True

    return False


@login_required
def create_listing(request):
    # Verify .edu email domain
    if not request.user.email.endswith(".edu"):
        messages.error(request, "Only verified .edu email addresses can post listings.")
        return redirect("view_profile")

    if request.method == "POST":
        form = ListingForm(request.POST)
        files = request.FILES.getlist("images")

        # Validate images
        has_image_error = False
        if not files:
            form.add_error(None, "Please upload at least one image.")
            has_image_error = True
        elif len(files) > 10:
            form.add_error(None, "You can upload a maximum of 10 images.")
            has_image_error = True
        else:
            # Validate file types and size
            for file in files:
                if not file.content_type.startswith("image/"):
                    form.add_error(None, f"{file.name} is not a valid image file.")
                    has_image_error = True
                    break
                # Check file size (max 5MB per image)
                if file.size > 5 * 1024 * 1024:
                    form.add_error(None, f"{file.name} exceeds 5MB size limit.")
                    has_image_error = True
                    break

        if form.is_valid() and not has_image_error:
            listing = form.save(commit=False)
            listing.user = request.user
            
            # **NEW: Geocode the address to get coordinates**
            # This happens automatically when user submits the form
            coordinates = geocode_address(listing.address)
            if coordinates:
                # Store coordinates for map display
                listing.longitude = coordinates[0]  # longitude is first in Mapbox format
                listing.latitude = coordinates[1]   # latitude is second
            
            listing.save()

            # Save all uploaded images
            for file in files:
                ListingImage.objects.create(listing=listing, image=file)

            # Send confirmation email
            send_mail(
                subject="Your CampusNest Listing is Live!",
                message=f"Your listing '{listing.title}' has been posted successfully. View it at http://127.0.0.1:8000/listings/{listing.id}/",
                from_email="noreply@campusnest.com",
                recipient_list=[request.user.email],
                fail_silently=True,
            )

            messages.success(
                request,
                "Listing created successfully! A confirmation email has been sent.",
            )
            return redirect("view_listing", listing_id=listing.id)
    else:
        form = ListingForm()

    return render(request, "listings/create_listing.html", {"form": form})


@login_required
def edit_listing(request, listing_id):  # noqa: C901
    """Edit an existing listing"""
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)
        files = request.FILES.getlist("images")
        keep_existing = request.POST.get("keep_existing_images") == "on"

        # Validate images
        has_image_error = _validate_listing_images(files, keep_existing, listing, form)

        if form.is_valid() and not has_image_error:
            listing = form.save(commit=False)
            listing.is_edited = True
            
            # **NEW: Re-geocode if address changed**
            # Check if address was modified
            if 'address' in form.changed_data:
                coordinates = geocode_address(listing.address)
                if coordinates:
                    listing.longitude = coordinates[0]
                    listing.latitude = coordinates[1]
            
            listing.save()

            _handle_listing_images(files, listing)

            messages.success(request, "Listing updated successfully!")
            return redirect("view_listing", listing_id=listing.id)
    else:
        form = ListingForm(instance=listing)
        if listing.amenities:
            form.initial["amenities"] = listing.amenities.split(",")

    return render(
        request, "listings/edit_listing.html", {"form": form, "listing": listing}
    )


def _validate_listing_images(files, keep_existing, listing, form):
    """Validate images for listing edit. Returns True if there's an error."""
    if files:
        return validate_image_files(files, form)
    elif not keep_existing and not listing.images.exists():
        form.add_error(
            None, "Please upload at least one image or keep existing images."
        )
        return True
    return False


def _handle_listing_images(files, listing):
    """Handle image uploads for a listing."""
    if files:
        listing.images.all().delete()
        for file in files:
            ListingImage.objects.create(listing=listing, image=file)


@login_required
def delete_listing(request, listing_id):
    """Delete a listing with confirmation"""
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)

    if request.method == "POST":
        # Store listing title for success message
        listing_title = listing.title

        # Delete the listing (images will be deleted automatically via CASCADE)
        listing.delete()

        # Send confirmation email
        send_mail(
            subject="Your CampusNest Listing Has Been Deleted",
            message=f"Your listing '{listing_title}' has been successfully deleted from CampusNest.\n\nIf you didn't perform this action, please contact us immediately.\n\nBest regards,\nThe CampusNest Team",
            from_email="noreply@campusnest.com",
            recipient_list=[request.user.email],
            fail_silently=True,
        )

        messages.success(
            request, f"Listing '{listing_title}' has been deleted successfully."
        )
        return redirect("my_listings")

    # GET request - show confirmation page
    return render(request, "listings/delete_listing.html", {"listing": listing})


@login_required
def view_listing(request, listing_id):
    """View listing details. Shows different options based on ownership."""
    listing = get_object_or_404(Listing, id=listing_id)
    is_owner = listing.user == request.user
    print("mapbox token: ", settings.MAPBOX_ACCESS_TOKEN)

    # Only owners can view inactive listings
    if not listing.is_active and not is_owner:
        return get_object_or_404(Listing, id=listing_id, user=request.user)

    share_url = request.build_absolute_uri(reverse("view_listing", args=[listing.id]))
    share_text = f"Check out this CampusNest listing: {listing.title} — ${listing.rent}/mo at {listing.address}. {share_url}"

    context = {
            "listing": listing,
            "is_owner": is_owner,
            "share_url": share_url,
            "share_text": share_text,
            'mapbox_token': settings.MAPBOX_ACCESS_TOKEN
        }

    return render(
        request,
        "listings/view_listing.html",
        context,
    )

@login_required
def my_listings(request):
    """Display all listings created by the current user"""
    listings = Listing.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "listings/my_listings.html", {"listings": listings})


@login_required
def public_listings(request):  # noqa: C901
    """Display all active listings including user's own with search and filtering"""
    listings = (
        Listing.objects.filter(is_active=True)
        .select_related("user")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    # Get filter parameters
    keyword = request.GET.get("keyword", "").strip()
    rent_min = request.GET.get("rent_min", "").strip()
    rent_max = request.GET.get("rent_max", "").strip()
    location = request.GET.get("location", "").strip()
    move_in_date = request.GET.get("move_in_date", "").strip()
    move_out_date = request.GET.get("move_out_date", "").strip()
    amenities = request.GET.getlist("amenities")  # Get list of selected amenities

    # Apply keyword filter (search in title, description, and address)
    if keyword:
        listings = listings.filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(address__icontains=keyword)
        )

    # Apply rent filter
    if rent_min:
        try:
            listings = listings.filter(rent__gte=float(rent_min))
        except ValueError:
            messages.warning(request, "Invalid minimum rent entered.")

    if rent_max:
        try:
            listings = listings.filter(rent__lte=float(rent_max))
        except ValueError:
            messages.warning(request, "Invalid maximum rent entered.")

    # Apply location filter
    if location:
        listings = listings.filter(address__icontains=location)

    # Apply move-in and move-out date filters
    if move_in_date or move_out_date:
        try:
            if move_in_date:
                move_in = datetime.strptime(move_in_date, "%Y-%m-%d").date()
                # Listing's availability_start must be <= move_in_date
                listings = listings.filter(availability_start__lte=move_in)

            if move_out_date:
                move_out = datetime.strptime(move_out_date, "%Y-%m-%d").date()
                # Listing's availability_end must be >= move_out_date
                listings = listings.filter(availability_end__gte=move_out)
        except ValueError:
            messages.warning(request, "Invalid date format.")

    # Apply amenities filter
    if amenities:
        for amenity in amenities:
            listings = listings.filter(amenities__icontains=amenity)

    context = {
        "listings": listings,
        "keyword": keyword,
        "rent_min": rent_min,
        "rent_max": rent_max,
        "location": location,
        "move_in_date": move_in_date,
        "move_out_date": move_out_date,
        "amenities": amenities,
        "amenity_choices": AMENITY_CHOICES,
        "has_filters": bool(
            keyword
            or rent_min
            or rent_max
            or location
            or move_in_date
            or move_out_date
            or amenities
        ),
    }

    return render(request, "listings/public_listings.html", context)