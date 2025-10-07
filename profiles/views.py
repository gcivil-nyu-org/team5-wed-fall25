from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfileForm
from .models import Profile
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def create_profile(request):
    if hasattr(request.user, 'profile'):
        messages.info(request, "Profile already exists.")
        return redirect('view_profile')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile created successfully!")
            return redirect('view_profile')  # ✅ this needs to exist
        else:
            print("Form errors:", form.errors)
    else:
        form = ProfileForm()
    return render(request, 'profiles/profile_form.html', {'form': form})


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('view_profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profiles/edit_profile.html', {'form': form})


@login_required
def view_profile(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return redirect('create_profile')
    return render(request, 'profiles/view_profile.html', {'profile': profile})


@staff_member_required
def admin_dashboard(request):
    profiles = Profile.objects.all().order_by('-created_at')
    return render(request, 'profiles/admin_dashboard.html', {'profiles': profiles})