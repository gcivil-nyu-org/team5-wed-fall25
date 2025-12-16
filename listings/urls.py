from django.urls import path
from django.shortcuts import redirect
from . import views


# Simple redirect view for /listings/
def listings_home(request):
    """Redirect /listings/ to /listings/my-listings/"""
    return redirect("my_listings")


urlpatterns = [
    path("", listings_home, name="listings_home"),
    path("browse/", views.public_listings, name="public_listings"),
    path("my-listings/", views.my_listings, name="my_listings"),
    path("create/", views.create_listing, name="create_listing"),
    path("<int:listing_id>/", views.view_listing, name="view_listing"),
    path("<int:listing_id>/edit/", views.edit_listing, name="edit_listing"),
    path("<int:listing_id>/delete/", views.delete_listing, name="delete_listing"),
    path("<int:listing_id>/mark-rented/", views.mark_as_rented, name="mark_as_rented"),
]
