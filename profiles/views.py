from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import ProfileForm, RoommateSearchForm
from .models import Profile, Favorite, ConnectionRequest
from accounts.models import User
from django.contrib.admin.views.decorators import staff_member_required


def home(request):
    """
    Home page - displays dashboard for authenticated users
    """
    if not request.user.is_authenticated:
        # If not logged in, go to login page
        return redirect("login")

    # Get user statistics for the dashboard
    favorites_count = Favorite.objects.filter(user=request.user).count()
    pending_requests = ConnectionRequest.objects.filter(
        to_user=request.user, status="pending"
    ).count()

    context = {
        "favorites_count": favorites_count,
        "pending_requests": pending_requests,
    }

    return render(request, "home.html", context)


@login_required
def create_profile(request):
    if hasattr(request.user, "profile"):
        messages.info(request, "Profile already exists.")
        return redirect("view_profile")

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile created successfully!")
            return redirect("view_profile")  # this needs to exist
    else:
        form = ProfileForm()
    return render(request, "profiles/profile_form.html", {"form": form})


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("view_profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "profiles/edit_profile.html", {"form": form})


@login_required
def view_profile(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        return redirect("create_profile")
    return render(request, "profiles/view_profile.html", {"profile": profile})


@login_required
def roommate_search(request):
    """Display roommate search page with filters"""
    form = RoommateSearchForm(request.GET or None)
    profiles = Profile.objects.filter(visibility=True).exclude(user=request.user)

    # Apply filters
    if form.is_valid():
        # Lifestyle filters - "no_preference" in filter means show ALL profiles
        # Only apply filter if "no_preference" is NOT selected
        smoking_prefs = form.cleaned_data.get("smoking_preference")
        if smoking_prefs and "no_preference" not in smoking_prefs:
            profiles = profiles.filter(smoking_preference__in=smoking_prefs)

        pet_prefs = form.cleaned_data.get("pet_preference")
        if pet_prefs and "no_preference" not in pet_prefs:
            profiles = profiles.filter(pet_preference__in=pet_prefs)

        cleanliness_prefs = form.cleaned_data.get("cleanliness_preference")
        if cleanliness_prefs and "no_preference" not in cleanliness_prefs:
            profiles = profiles.filter(cleanliness_preference__in=cleanliness_prefs)

        # Housing filters
        budget_min = form.cleaned_data.get("budget_min")
        if budget_min is not None:
            profiles = profiles.filter(budget_max__gte=budget_min)

        budget_max = form.cleaned_data.get("budget_max")
        if budget_max is not None:
            profiles = profiles.filter(budget_min__lte=budget_max)

        location = form.cleaned_data.get("location")
        if location:
            profiles = profiles.filter(location__icontains=location)

        universities = form.cleaned_data.get("university")
        if universities:
            profiles = profiles.filter(university__in=universities)

    # Get user's favorites for display
    user_favorites = Favorite.objects.filter(user=request.user).values_list(
        "favorite_profile_id", flat=True
    )

    # Get connection request statuses
    sent_requests = ConnectionRequest.objects.filter(
        from_user=request.user
    ).values_list("to_user_id", flat=True)

    context = {
        "form": form,
        "profiles": profiles,
        "user_favorites": user_favorites,
        "sent_requests": sent_requests,
    }

    return render(request, "profiles/roommate_search.html", context)


@login_required
def roommate_detail(request, user_id):
    """Display full roommate profile details"""
    profile = get_object_or_404(Profile, user_id=user_id, visibility=True)

    # Prevent viewing own profile
    if profile.user == request.user:
        messages.warning(request, "You cannot view your own profile here.")
        return redirect("roommate_search")

    # Check if favorited
    is_favorited = Favorite.objects.filter(
        user=request.user, favorite_profile=profile
    ).exists()

    # Check connection request status
    connection_request = ConnectionRequest.objects.filter(
        from_user=request.user, to_user=profile.user
    ).first()

    context = {
        "profile": profile,
        "is_favorited": is_favorited,
        "connection_request": connection_request,
    }

    return render(request, "profiles/roommate_detail.html", context)


@login_required
@require_POST
def toggle_favorite(request, user_id):
    """Toggle favorite status for a profile"""
    profile = get_object_or_404(Profile, user_id=user_id)

    if profile.user == request.user:
        return JsonResponse({"error": "Cannot favorite your own profile"}, status=400)

    favorite, created = Favorite.objects.get_or_create(
        user=request.user, favorite_profile=profile
    )

    if not created:
        favorite.delete()
        return JsonResponse({"favorited": False, "message": "Removed from favorites"})

    return JsonResponse({"favorited": True, "message": "Added to favorites"})


@login_required
@require_POST
def send_connection_request(request, user_id):
    """Send a connection request to another user"""
    to_user = get_object_or_404(User, id=user_id)

    if to_user == request.user:
        messages.error(request, "You cannot send a request to yourself.")
        return redirect("roommate_search")

    # Check if profile exists
    if not hasattr(to_user, "profile"):
        messages.error(request, "This user does not have a profile.")
        return redirect("roommate_search")

    # Check if request already exists
    existing_request = ConnectionRequest.objects.filter(
        from_user=request.user, to_user=to_user
    ).first()

    if existing_request:
        if existing_request.status == "pending":
            messages.info(request, "You already sent a request to this user.")
        elif existing_request.status == "accepted":
            messages.info(request, "You are already connected with this user.")
        else:
            messages.info(request, "Your previous request was rejected.")
        return redirect("roommate_detail", user_id=user_id)

    # Create new connection request
    message = request.POST.get("message", "")
    ConnectionRequest.objects.create(
        from_user=request.user, to_user=to_user, message=message
    )

    messages.success(request, f"Connection request sent to {to_user.first_name}!")
    return redirect("roommate_detail", user_id=user_id)


@login_required
def my_favorites(request):
    """Display user's favorited profiles"""
    favorites = Favorite.objects.filter(user=request.user).select_related(
        "favorite_profile"
    )

    context = {
        "favorites": favorites,
    }

    return render(request, "profiles/my_favorites.html", context)


@login_required
def connection_requests(request):
    """Display received connection requests"""
    received_requests = (
        ConnectionRequest.objects.filter(to_user=request.user)
        .select_related("from_user", "from_user__profile")
        .order_by("-created_at")
    )

    context = {
        "received_requests": received_requests,
    }

    return render(request, "profiles/connection_requests.html", context)


@login_required
@require_POST
def respond_to_request(request, request_id):
    """Accept or reject a connection request"""
    conn_request = get_object_or_404(
        ConnectionRequest, id=request_id, to_user=request.user
    )
    action = request.POST.get("action")

    if action == "accept":
        conn_request.status = "accepted"
        conn_request.save()
        messages.success(
            request, f"Connected with {conn_request.from_user.first_name}!"
        )
    elif action == "reject":
        conn_request.status = "rejected"
        conn_request.save()
        messages.info(request, "Request rejected.")

    return redirect("connection_requests")


@staff_member_required
def admin_dashboard(request):
    profiles = Profile.objects.all().order_by("-created_at")
    return render(request, "profiles/admin_dashboard.html", {"profiles": profiles})
