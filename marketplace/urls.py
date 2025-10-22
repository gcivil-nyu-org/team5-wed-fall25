from django.urls import path
from django.shortcuts import redirect
from . import views


def marketplace_home(request):
    """Redirect /marketplace/ to /marketplace/my-items/"""
    return redirect("my_items")


urlpatterns = [
    path("", marketplace_home, name="marketplace_home"),
    path("my-items/", views.my_items, name="my_items"),
    path("create/", views.create_item, name="create_item"),
    path("<int:item_id>/", views.view_item, name="view_item"),
    path("<int:item_id>/edit/", views.edit_item, name="edit_item"),
    path("<int:item_id>/delete/", views.delete_item, name="delete_item"),
    path("<int:item_id>/mark-sold/", views.mark_as_sold, name="mark_as_sold"),
]