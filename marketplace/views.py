from __future__ import annotations

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItemForm
from .models import Item, ItemImage

log = logging.getLogger(__name__)


def send_item_confirmation_email(
    user_email: str, item_title: str, action: str = "posted"
) -> None:
    """Send confirmation email for item actions (posted, edited, deleted, sold)."""
    log.debug("send_item_confirmation_email action=%s title=%s", action, item_title)

    subject_map = {
        "posted": "Your CampusNest Item is Live!",
        "edited": "Your CampusNest Item Has Been Edited",
        "deleted": "Your CampusNest Item Has Been Deleted",
        "sold": "Your CampusNest Item Has Been Sold",
    }
    message_map = {
        "posted": f"Your item '{item_title}' has been posted successfully.",
        "edited": f"Your item '{item_title}' has been successfully edited.",
        "deleted": f"Your item '{item_title}' has been successfully deleted from CampusNest.",
        "sold": f"Your item '{item_title}' has been sold successfully.",
    }

    send_mail(
        subject=subject_map.get(action, "CampusNest Item Update"),
        message=message_map.get(action, f"Your item '{item_title}' has been updated."),
        from_email="noreply@campusnest.com",
        recipient_list=[user_email],
        fail_silently=True,
    )


def parse_removed_image_ids(removed_images_str: str | None) -> list[int]:
    """Parse comma-separated string of image IDs to remove."""
    if not removed_images_str:
        return []
    return [int(s) for s in removed_images_str.split(",") if s.strip()]


def validate_uploaded_files(files, form) -> bool:
    """Validate uploaded image files. Returns True if there's an error."""
    if len(files) > 10:
        form.add_error(None, "You can upload a maximum of 10 images.")
        return True

    for f in files:
        ct = getattr(f, "content_type", "") or ""
        if not ct.startswith("image/"):
            form.add_error(
                None, f"{getattr(f, 'name', 'File')} is not a valid image file."
            )
            return True
        if f.size and f.size > 5 * 1024 * 1024:
            form.add_error(
                None, f"{getattr(f, 'name', 'File')} exceeds 5MB size limit."
            )
            return True

    return False


def validate_image_requirements(
    item: Item, files, removed_image_ids: list[int], form
) -> bool:
    """Ensure at least one image will remain after edit. Returns True if there's an error."""
    if files:
        return validate_uploaded_files(files, form)

    remaining = item.images.exclude(id__in=removed_image_ids).count()
    if remaining == 0:
        form.add_error(
            None,
            "Please upload at least one image or keep at least one existing image.",
        )
        return True
    return False


def process_item_images(item: Item, files, removed_image_ids: list[int]) -> None:
    """Remove marked images and add new uploaded images."""
    if removed_image_ids:
        item.images.filter(id__in=removed_image_ids).delete()

    for f in files or []:
        ItemImage.objects.create(item=item, image=f)


def handle_item_form_submission(
    request, item: Item, form: ItemForm, files, removed_image_ids
):
    """Process valid item form submission."""
    has_image_error = validate_image_requirements(item, files, removed_image_ids, form)

    if form.is_valid() and not has_image_error:
        obj = form.save(commit=False)
        obj.is_edited = True
        obj.save()

        process_item_images(obj, files, removed_image_ids)

        send_item_confirmation_email(request.user.email, obj.title, "edited")
        messages.success(
            request, "Item updated successfully! A confirmation email has been sent."
        )
        return redirect("marketplace:view_item", item_id=obj.id)

    return None


def validate_create_item_images(files, form) -> bool:
    """Validate images for create_item view. Returns True if there's an error."""
    if not files:
        form.add_error(None, "Please upload at least one image.")
        return True
    return validate_uploaded_files(files, form)


@login_required
def edit_item(request, item_id: int):
    """Edit an existing item."""
    item = get_object_or_404(Item, id=item_id, user=request.user)

    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        files = request.FILES.getlist("images")
        removed_image_ids = parse_removed_image_ids(
            request.POST.get("removed_images", "")
        )

        resp = handle_item_form_submission(
            request, item, form, files, removed_image_ids
        )
        if resp:
            return resp
    else:
        form = ItemForm(instance=item)

    return render(request, "marketplace/edit_item.html", {"form": form, "item": item})


@login_required
def my_items(request):
    """Display all items posted by the current user."""
    items = Item.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "marketplace/my_items.html", {"items": items})


@login_required
def create_item(request):
    """Create a new marketplace item."""
    if not (request.user.email.endswith(".edu")):
        messages.error(request, "Only verified .edu email addresses can post items.")
        return redirect("view_profile")

    if request.method == "POST":
        form = ItemForm(request.POST)
        files = request.FILES.getlist("images")

        has_image_error = validate_create_item_images(files, form)

        if form.is_valid() and not has_image_error:
            item = form.save(commit=False)
            item.user = request.user
            item.save()

            for f in files:
                ItemImage.objects.create(item=item, image=f)

            send_item_confirmation_email(request.user.email, item.title, "posted")
            messages.success(
                request, "Item posted successfully! A confirmation email has been sent."
            )
            return redirect("marketplace:view_item", item_id=item.id)
    else:
        form = ItemForm()

    return render(request, "marketplace/create_item.html", {"form": form})


@login_required
def view_item(request, item_id: int):
    """View a single item (owner-only here; make public by removing user filter)."""
    item = get_object_or_404(Item, id=item_id, user=request.user)
    return render(request, "marketplace/view_item.html", {"item": item})


@login_required
def delete_item(request, item_id: int):
    """Delete an item with confirmation."""
    item = get_object_or_404(Item, id=item_id, user=request.user)
    log.debug("delete_item item_id=%s title=%s", item.id, item.title)

    if request.method == "POST":
        title = item.title
        email = request.user.email
        item.delete()

        send_item_confirmation_email(email, title, "deleted")
        messages.success(request, f"Item '{title}' has been deleted successfully.")
        return redirect("marketplace:my_items")

    return render(request, "marketplace/delete_item.html", {"item": item})


@login_required
def mark_as_sold(request, item_id: int):
    """Mark an item as sold."""
    item = get_object_or_404(Item, id=item_id, user=request.user)

    if request.method == "POST":
        item.is_sold = True
        item.save()

        send_item_confirmation_email(request.user.email, item.title, "sold")
        messages.success(request, f"Item '{item.title}' marked as sold!")
        return redirect("marketplace:my_items")

    return redirect("marketplace:view_item", item_id=item.id)
