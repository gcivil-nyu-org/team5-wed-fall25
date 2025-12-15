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

    # Get connection count for the current user
    connection_count = profile.get_connection_count()

    context = {
        "profile": profile,
        "connection_count": connection_count,
    }

    return render(request, "profiles/view_profile.html", context)


# @login_required
# def roommate_search(request):
#     """Display roommate search page with filters"""
#     # Check if user has a profile
#     user_profile = getattr(request.user, "profile", None)

#     # Check if user wants to clear filters
#     clear_filters = request.GET.get('clear', None)
#     # If no GET parameters and user has a profile,
#     # then auto-populate with user preferences
#     if not request.GET and user_profile:
#         # Auto-populate on first visit (no GET parameters at all)
#         initial_data = {
#             "budget_min": user_profile.budget_min,
#             "budget_max": user_profile.budget_max,
#             "location": user_profile.location,
#             "university": [user_profile.university],
#         }

#         # Only include lifestyle preferences if they're not set to "no_preference"
#         if user_profile.smoking_preference:
#             initial_data["smoking_preference"] = [user_profile.smoking_preference]
#         # and user_profile.smoking_preference != "no_preference":

#         if user_profile.pet_preference:
#             initial_data["pet_preference"] = [user_profile.pet_preference]
#         # and user_profile.pet_preference != "no_preference":

#         if user_profile.cleanliness_preference:
#             initial_data["cleanliness_preference"] = [user_profile.cleanliness_preference]
#             # and user_profile.cleanliness_preference != "no_preference"

#         form = RoommateSearchForm(initial_data)
#     elif clear_filters:
#         # User clicked "Clear Filters" - show empty form with no filters
#         form = RoommateSearchForm()
#     else:
#         # User submitted the form with filters & use GET data
#         form = RoommateSearchForm(request.GET or None)
#     profiles = Profile.objects.filter(visibility=True).exclude(user=request.user)
#     # Apply filters
#     if form.is_valid():
#         # Lifestyle filters - "no_preference" in filter means show ALL profiles
#         # Only apply filter if "no_preference" is NOT selected
#         smoking_prefs = form.cleaned_data.get("smoking_preference")
#         if smoking_prefs and "no_preference" not in smoking_prefs:
#             profiles = profiles.filter(smoking_preference__in=smoking_prefs)

#         pet_prefs = form.cleaned_data.get("pet_preference")
#         if pet_prefs and "no_preference" not in pet_prefs:
#             profiles = profiles.filter(pet_preference__in=pet_prefs)

#         cleanliness_prefs = form.cleaned_data.get("cleanliness_preference")
#         if cleanliness_prefs and "no_preference" not in cleanliness_prefs:
#             profiles = profiles.filter(cleanliness_preference__in=cleanliness_prefs)

#         # Housing filters
#         budget_min = form.cleaned_data.get("budget_min")
#         if budget_min is not None:
#             profiles = profiles.filter(budget_max__gte=budget_min)

#         budget_max = form.cleaned_data.get("budget_max")
#         if budget_max is not None:
#             profiles = profiles.filter(budget_min__lte=budget_max)

#         location = form.cleaned_data.get("location")
#         if location:
#             profiles = profiles.filter(location__icontains=location)

#         universities = form.cleaned_data.get("university")
#         if universities:
#             profiles = profiles.filter(university__in=universities)

#     # Get user's favorites for display
#     user_favorites = Favorite.objects.filter(user=request.user).values_list(
#         "favorite_profile_id", flat=True
#     )

#     # Get connection request statuses
#     sent_requests = ConnectionRequest.objects.filter(
#         from_user=request.user
#     ).values_list("to_user_id", flat=True)

#     context = {
#         "form": form,
#         "profiles": profiles,
#         "user_favorites": user_favorites,
#         "sent_requests": sent_requests,
#     }


#     return render(request, "profiles/roommate_search.html", context)
@login_required
def roommate_search(request):
    """Display roommate search page with filters"""
    user_profile = getattr(request.user, "profile", None)
    clear_filters = request.GET.get("clear", None)

    # Determine which form to use
    if not request.GET and user_profile:
        # Auto-populate with user preferences on first visit
        initial_data = _build_initial_filter_data(user_profile)
        form = RoommateSearchForm(initial_data)
    elif clear_filters:
        # Show empty form when clearing filters
        form = RoommateSearchForm()
    else:
        # Use GET data for manual filter submission
        form = RoommateSearchForm(request.GET or None)

    # Get base profiles and apply filters
    profiles = Profile.objects.filter(visibility=True).exclude(user=request.user)
    profiles = _apply_search_filters(profiles, form)

    # Get user-specific data
    user_favorites = Favorite.objects.filter(user=request.user).values_list(
        "favorite_profile_id", flat=True
    )

    # Get connection requests in BOTH directions (LinkedIn-style bidirectional)
    # Check requests sent by current user
    sent_requests = ConnectionRequest.objects.filter(from_user=request.user)
    # Check requests received by current user
    received_requests = ConnectionRequest.objects.filter(to_user=request.user)

    # Build a dictionary mapping user_id to connection info
    connection_status = {}
    for req in sent_requests:
        connection_status[req.to_user_id] = {
            "status": req.status,
            "direction": "sent",  # Current user sent this request
        }
    for req in received_requests:
        # Only add if not already in dict (sent takes precedence for display)
        if req.from_user_id not in connection_status:
            connection_status[req.from_user_id] = {
                "status": req.status,
                "direction": "received",  # Current user received this request
            }

    context = {
        "form": form,
        "profiles": profiles,
        "user_favorites": user_favorites,
        "connection_status": connection_status,
    }

    return render(request, "profiles/roommate_search.html", context)


def _apply_search_filters(profiles, form):
    """Apply search filters to profiles queryset"""
    if not form.is_valid():
        return profiles

    # Lifestyle filters
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

    return profiles


def _build_initial_filter_data(user_profile):
    """Build initial filter data from user profile preferences"""
    initial_data = {
        "budget_min": user_profile.budget_min,
        "budget_max": user_profile.budget_max,
        "location": user_profile.location,
        "university": [user_profile.university],
    }

    # Add lifestyle preferences if they exist
    if user_profile.smoking_preference:
        initial_data["smoking_preference"] = [user_profile.smoking_preference]

    if user_profile.pet_preference:
        initial_data["pet_preference"] = [user_profile.pet_preference]

    if user_profile.cleanliness_preference:
        initial_data["cleanliness_preference"] = [user_profile.cleanliness_preference]

    return initial_data


@login_required
def roommate_detail(request, user_id):
    """Display full roommate profile details"""
    # Check if user exists
    user = get_object_or_404(User, id=user_id)

    # Check if user has a profile
    if not hasattr(user, "profile"):
        messages.error(request, "This user has not completed their profile yet.")
        return redirect("roommate_search")

    # Check if profile is visible
    if not user.profile.visibility:
        messages.error(request, "This profile is not visible.")
        return redirect("roommate_search")

    profile = user.profile

    # Prevent viewing own profile
    if profile.user == request.user:
        messages.warning(request, "You cannot view your own profile here.")
        return redirect("roommate_search")

    # Check if favorited
    is_favorited = Favorite.objects.filter(
        user=request.user, favorite_profile=profile
    ).exists()

    # Check connection request status in BOTH directions (LinkedIn-style bidirectional)
    # Check if current user sent a request
    connection_request = ConnectionRequest.objects.filter(
        from_user=request.user, to_user=profile.user
    ).first()

    # If no request sent by current user, check if they received one
    if not connection_request:
        connection_request = ConnectionRequest.objects.filter(
            from_user=profile.user, to_user=request.user
        ).first()
        # Mark that this request was received (for template to show different UI)
        if connection_request:
            connection_request.is_received = True

    # Get connection count for the profile being viewed
    connection_count = profile.get_connection_count()

    # Get the "next" parameter for context-aware back button
    next_url = request.GET.get("next", None)

    context = {
        "profile": profile,
        "is_favorited": is_favorited,
        "connection_request": connection_request,
        "connection_count": connection_count,
        "next_url": next_url,
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

    # Check if sender has a profile
    if not hasattr(request.user, "profile"):
        messages.error(
            request, "Please complete your profile before sending connection requests."
        )
        return redirect("create_profile")

    # Check if recipient has a profile
    if not hasattr(to_user, "profile"):
        messages.error(request, "This user does not have a profile.")
        return redirect("roommate_search")

    # Check if request already exists in EITHER direction (LinkedIn-style bidirectional)
    # Check if current user already sent a request
    existing_sent_request = ConnectionRequest.objects.filter(
        from_user=request.user, to_user=to_user
    ).first()

    # Check if the other user already sent a request to current user
    existing_received_request = ConnectionRequest.objects.filter(
        from_user=to_user, to_user=request.user
    ).first()

    # If current user already sent a request
    if existing_sent_request:
        if existing_sent_request.status == "pending":
            messages.info(request, "You already sent a request to this user.")
        elif existing_sent_request.status == "accepted":
            messages.info(request, "You are already connected with this user.")
        else:
            messages.info(request, "Your previous request was rejected.")
        return redirect("roommate_detail", user_id=user_id)

    # If the other user already sent a request (redirect to connection requests page)
    if existing_received_request:
        if existing_received_request.status == "pending":
            messages.info(
                request,
                f"{to_user.first_name} already sent you a connection request. "
                f"Please respond to their request instead.",
            )
            return redirect("connection_requests")
        elif existing_received_request.status == "accepted":
            messages.info(request, "You are already connected with this user.")
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
    """Display received connection requests (pending only)"""
    # Only show pending requests - accepted ones are in "My Connections"
    received_requests = (
        ConnectionRequest.objects.filter(to_user=request.user, status="pending")
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


@login_required
def my_connections(request, user_id):
    """Display a user's connections (LinkedIn-style)"""
    # Get the user whose connections we want to view
    user = get_object_or_404(User, id=user_id)

    # Check if user has a profile
    if not hasattr(user, "profile"):
        messages.error(request, "This user has not completed their profile yet.")
        return redirect("roommate_search")

    profile = user.profile

    # Get all connections for this user
    connections = profile.get_connections()

    # Get profiles for all connections (filter out users without profiles)
    connection_profiles = []
    for connection_user in connections:
        if hasattr(connection_user, "profile"):
            connection_profiles.append(connection_user.profile)

    context = {
        "profile": profile,
        "connections": connection_profiles,
        "is_own_profile": user == request.user,
    }

    return render(request, "profiles/my_connections.html", context)


@login_required
@require_POST
def disconnect(request, user_id):
    """Remove a connection with another user"""
    from django.db.models import Q

    other_user = get_object_or_404(User, id=user_id)

    # Prevent disconnecting from yourself
    if other_user == request.user:
        messages.error(request, "You cannot disconnect from yourself.")
        return redirect("my_connections", user_id=request.user.id)

    # Find the connection request (could be in either direction)
    connection_request = ConnectionRequest.objects.filter(
        Q(from_user=request.user, to_user=other_user, status="accepted")
        | Q(from_user=other_user, to_user=request.user, status="accepted")
    ).first()

    if connection_request:
        connection_request.delete()
        messages.success(
            request, f"You are no longer connected with {other_user.first_name}."
        )
    else:
        messages.error(request, "Connection not found.")

    return redirect("my_connections", user_id=request.user.id)


@staff_member_required
def admin_dashboard(request):
    profiles = Profile.objects.all().order_by("-created_at")
    return render(request, "profiles/admin_dashboard.html", {"profiles": profiles})
