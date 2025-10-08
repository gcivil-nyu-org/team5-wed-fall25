from django.urls import path
from django.shortcuts import redirect
from . import views

# Simple redirect view for /profiles/
def profiles_home(request):
    """Redirect /profiles/ to /profiles/view/"""
    return redirect('view_profile')

urlpatterns = [
    path('', views.home, name='home'),  # Root / goes to home
    path('profiles/', profiles_home, name='profiles_home'),  # ✅ /profiles/ → /profiles/view/
    path('profiles/create/', views.create_profile, name='create_profile'),
    path('profiles/view/', views.view_profile, name='view_profile'),
    path('profiles/edit/', views.edit_profile, name='edit_profile'),
    path('profiles/admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
