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
from django.http import Http404
from datetime import datetime
from .forms import ListingForm
from .models import Listing, ListingImage
from .constants import AMENITY_CHOICES, NYC_NEIGHBORHOOD_BOROUGH_MAP
from django.urls import reverse

# Import the geocoding utility
from map_utils.python.utils import geocode_address


def get_neighborhoods_for_search(location_query):
    """
    Given a location search query, return list of neighborhoods to search for.
    If the query matches a borough, return all neighborhoods in that borough.
    Otherwise, return just the query itself for direct matching.
    """
    location_lower = location_query.lower().strip()

    # Check if the search term is a borough
    if location_lower in NYC_NEIGHBORHOOD_BOROUGH_MAP:
        return NYC_NEIGHBORHOOD_BOROUGH_MAP[location_lower]

    # Otherwise, return the original query for direct matching
    return [location_query]


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
    # Restrict to .edu emails
    if not request.user.email.endswith(".edu"):
        messages.error(request, "Only verified .edu email addresses can post listings.")
        return redirect("view_profile")

    if request.method == "POST":
        form = ListingForm(request.POST)
        files = request.FILES.getlist("images")

        # Validate images
        error_message = validate_images(files)
        if error_message:
            form.add_error(None, error_message)

        if form.is_valid() and not error_message:
            listing = form.save(commit=False)
            listing.user = request.user

            # Geocode address - construct full address from components
            full_address = f"{listing.street_address}, {listing.city}, NY {listing.zipcode}"
            coords = geocode_address(full_address)
            if coords:
                listing.longitude, listing.latitude = coords[0], coords[1]

            listing.save()

            # Save uploaded images
            for file in files:
                ListingImage.objects.create(listing=listing, image=file)

            # Send confirmation email
            send_mail(
                "Your CampusNest Listing is Live!",
                f"Your listing '{listing.title}' has been posted successfully. "
                f"View it at http://127.0.0.1:8000/listings/{listing.id}/",
                "noreply@campusnest.com",
                [request.user.email],
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


def validate_images(files):
    """Validate uploaded image files. Returns error message or None."""
    if not files:
        return "Please upload at least one image."
    if len(files) > 10:
        return "You can upload a maximum of 10 images."

    for file in files:
        if not file.content_type.startswith("image/"):
            return f"{file.name} is not a valid image file."
        if file.size > 5 * 1024 * 1024:  # 5MB limit
            return f"{file.name} exceeds 5MB size limit."
    return None


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
            # Check if any address component was modified
            if any(field in form.changed_data for field in ["street_address", "city", "zipcode"]):
                full_address = f"{listing.street_address}, {listing.city}, NY {listing.zipcode}"
                coordinates = geocode_address(full_address)
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
    listing = get_object_or_404(Listing, id=listing_id)

    # Only the owner or a staff (moderator) user can delete the listing
    if listing.user != request.user and not request.user.is_staff:
        raise Http404()

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
            recipient_list=[listing.user.email],
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
    # print("mapbox token: ", settings.MAPBOX_ACCESS_TOKEN)

    # Only owners can view inactive listings
    if not listing.is_active and not is_owner:
        return get_object_or_404(Listing, id=listing_id, user=request.user)

    share_url = request.build_absolute_uri(reverse("view_listing", args=[listing.id]))
    full_address = f"{listing.street_address}, {listing.city}, NY {listing.zipcode}"
    share_text = f"Check out this CampusNest listing: {listing.title} — ${listing.rent}/mo at {full_address}. {share_url}"

    context = {
        "listing": listing,
        "is_owner": is_owner,
        "share_url": share_url,
        "share_text": share_text,
        "mapbox_token": settings.MAPBOX_ACCESS_TOKEN,
    }

    return render(
        request,
        "listings/view_listing_with_map.html",
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
            | Q(street_address__icontains=keyword)
            | Q(city__icontains=keyword)
            | Q(zipcode__icontains=keyword)
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

    # Apply location filter with smart neighborhood/borough matching
    if location:
        neighborhoods = get_neighborhoods_for_search(location)
        # Create OR query for all neighborhoods across all address fields
        location_query = Q()
        for neighborhood in neighborhoods:
            location_query |= (
                Q(street_address__icontains=neighborhood)
                | Q(city__icontains=neighborhood)
                | Q(zipcode__icontains=neighborhood)
            )
        listings = listings.filter(location_query)

    # Apply move-in and move-out date filters
    if move_in_date or move_out_date:
        try:
            if move_in_date:
                move_in = datetime.strptime(move_in_date, "%Y-%m-%d").date()
            else:
                move_in = None

            if move_out_date:
                move_out = datetime.strptime(move_out_date, "%Y-%m-%d").date()
            else:
                move_out = None

            # Validate that move-out date is not before move-in date
            if move_in and move_out and move_out < move_in:
                messages.error(
                    request,
                    "Move-out date cannot be before move-in date. "
                    "Please adjust your search filters.",
                )
                # Clear the results by returning empty queryset
                listings = Listing.objects.none()
            else:
                # Apply filters only if date validation passes
                if move_in:
                    # Listing's availability_start must be <= move_in_date
                    listings = listings.filter(availability_start__lte=move_in)

                if move_out:
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
