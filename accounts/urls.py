from django.urls import path
from django.shortcuts import redirect
from . import views

# Simple redirect view for /accounts/
def accounts_home(request):
    """Redirect /accounts/ to /accounts/login/"""
    return redirect('login')

urlpatterns = [
    path('', accounts_home, name='accounts_home'),  # ✅ /accounts/ → /accounts/login/
    path('register/', views.register, name='register'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]
