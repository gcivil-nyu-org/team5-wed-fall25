from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ListingForm
from .models import Listing, ListingImage

@login_required
def create_listing(request):
    # Verify .edu email domain
    if not request.user.email.endswith('.edu'):
        messages.error(request, "Only verified .edu email addresses can post listings.")
        return redirect('view_profile')

    if request.method == 'POST':
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        print("FILES.getlist('images'):", request.FILES.getlist('images'))
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user
            listing.save()

            # Save all uploaded images
            for file in request.FILES.getlist('images'):
                ListingImage.objects.create(listing=listing, image=file)

            # Send confirmation email
            send_mail(
                subject="Your CampusNest Listing is Live!",
                message=f"Your listing '{listing.title}' has been posted successfully. View it at http://127.0.0.1:8000/listings/{listing.id}/",
                from_email="noreply@campusnest.com",
                recipient_list=[request.user.email],
                fail_silently=True,
            )

            messages.success(request, "Listing created successfully! A confirmation email has been sent.")
            return redirect('view_listing', listing_id=listing.id)
        else:
            print("Form errors:", form.errors)
    else:
        form = ListingForm()

    return render(request, 'listings/create_listing.html', {'form': form})


@login_required
def view_listing(request, listing_id):
    listing = Listing.objects.get(id=listing_id, user=request.user)
    return render(request, 'listings/view_listing.html', {'listing': listing})
