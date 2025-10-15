from django.urls import path
from django.shortcuts import redirect
from . import views

# Simple redirect view for /listings/
def listings_home(request):
    """Redirect /listings/ to /listings/create/"""
    return redirect('my_listings')
urlpatterns = [
    path('', listings_home, name='listings_home'),  # Add this line
    path('my-listings/', views.my_listings, name='my_listings'),
    path('create/', views.create_listing, name='create_listing'),
    path('<int:listing_id>/', views.view_listing, name='view_listing'),
]
