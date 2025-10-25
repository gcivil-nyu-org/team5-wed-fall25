# listings/urls.py
from django.urls import path
from . import views

app_name = "listings"

urlpatterns = [
    path("", listings_home, name="listings_home"),
    path("browse/", views.public_listings, name="public_listings"),
    path("my-listings/", views.my_listings, name="my_listings"),
    path("create/", views.create_listing, name="create_listing"),
    path("my/", views.my_listings, name="my_listings"),
    # Optional alias so /listings/my-listings/ also works:
    path("my-listings/", views.my_listings),
    # Detail + edit/delete
    path("<int:listing_id>/", views.view_listing, name="view_listing"),
    path("<int:listing_id>/edit/", views.edit_listing, name="edit_listing"),
    path("<int:listing_id>/delete/", views.delete_listing, name="delete_listing"),
]
