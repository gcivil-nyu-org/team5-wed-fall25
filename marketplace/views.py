from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ItemForm
from .models import Item, ItemImage


@login_required
def my_items(request):
    """Display all items posted by the current user"""
    items = Item.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "marketplace/my_items.html", {"items": items})


@login_required
def create_item(request):
    """Create a new marketplace item"""
    if not request.user.email.endswith(".edu"):
        messages.error(request, "Only verified .edu email addresses can post items.")
        return redirect("view_profile")

    if request.method == "POST":
        form = ItemForm(request.POST)
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
            for file in files:
                if not file.content_type.startswith("image/"):
                    form.add_error(None, f"{file.name} is not a valid image file.")
                    has_image_error = True
                    break
                if file.size > 5 * 1024 * 1024:
                    form.add_error(None, f"{file.name} exceeds 5MB size limit.")
                    has_image_error = True
                    break

        if form.is_valid() and not has_image_error:
            item = form.save(commit=False)
            item.user = request.user
            item.save()

            # Save all uploaded images
            for file in files:
                ItemImage.objects.create(item=item, image=file)

            # Send confirmation email
            send_mail(
                subject="Your CampusNest Item is Live!",
                message=f"Your item '{item.title}' has been posted successfully.",
                from_email="noreply@campusnest.com",
                recipient_list=[request.user.email],
                fail_silently=True,
            )

            messages.success(
                request,
                "Item posted successfully! A confirmation email has been sent.",
            )
            return redirect("view_item", item_id=item.id)
    else:
        form = ItemForm()

    return render(request, "marketplace/create_item.html", {"form": form})


@login_required
def view_item(request, item_id):
    """View a single item"""
    item = get_object_or_404(Item, id=item_id, user=request.user)
    return render(request, "marketplace/view_item.html", {"item": item})


@login_required
def edit_item(request, item_id):
    """Edit an existing item"""
    item = get_object_or_404(Item, id=item_id, user=request.user)

    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        files = request.FILES.getlist("images")

        keep_existing = request.POST.get("keep_existing_images") == "on"

        has_image_error = False
        if files:
            if len(files) > 10:
                form.add_error(None, "You can upload a maximum of 10 images.")
                has_image_error = True
            else:
                for file in files:
                    if not file.content_type.startswith("image/"):
                        form.add_error(None, f"{file.name} is not a valid image file.")
                        has_image_error = True
                        break
                    if file.size > 5 * 1024 * 1024:
                        form.add_error(None, f"{file.name} exceeds 5MB size limit.")
                        has_image_error = True
                        break
        elif not keep_existing and not item.images.exists():
            form.add_error(
                None, "Please upload at least one image or keep existing images."
            )
            has_image_error = True

        if form.is_valid() and not has_image_error:
            item = form.save(commit=False)
            item.is_edited = True
            item.save()

            if files:
                item.images.all().delete()
                for file in files:
                    ItemImage.objects.create(item=item, image=file)

            messages.success(request, "Item updated successfully!")
            return redirect("view_item", item_id=item.id)
    else:
        form = ItemForm(instance=item)

    return render(request, "marketplace/edit_item.html", {"form": form, "item": item})


@login_required
def delete_item(request, item_id):
    """Delete an item with confirmation"""
    item = get_object_or_404(Item, id=item_id, user=request.user)

    if request.method == "POST":
        item_title = item.title
        item.delete()

        send_mail(
            subject="Your CampusNest Item Has Been Deleted",
            message=f"Your item '{item_title}' has been successfully deleted from CampusNest.",
            from_email="noreply@campusnest.com",
            recipient_list=[request.user.email],
            fail_silently=True,
        )

        messages.success(request, f"Item '{item_title}' has been deleted successfully.")
        return redirect("my_items")

    return render(request, "marketplace/delete_item.html", {"item": item})


@login_required
def mark_as_sold(request, item_id):
    """Mark an item as sold"""
    item = get_object_or_404(Item, id=item_id, user=request.user)
    
    if request.method == "POST":
        item.is_sold = True
        item.save()
        messages.success(request, f"Item '{item.title}' marked as sold!")
        return redirect("my_items")
    
    return redirect("view_item", item_id=item.id)