from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ListingForm
from .models import Listing, ListingImage


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
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    return render(request, "listings/view_listing.html", {"listing": listing})


@login_required
def my_listings(request):
    """Display all listings created by the current user"""
    listings = Listing.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "listings/my_listings.html", {"listings": listings})
