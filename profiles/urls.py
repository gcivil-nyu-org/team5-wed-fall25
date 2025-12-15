from django.urls import path
from django.shortcuts import redirect
from . import views


# Simple redirect view for /profiles/
def profiles_home(request):
    """Redirect /profiles/ to /profiles/view/"""
    return redirect("view_profile")


urlpatterns = [
    path("", views.home, name="home"),  # Root / goes to home
    path(
        "profiles/", profiles_home, name="profiles_home"
    ),  # /profiles/ → /profiles/view/
    path("profiles/create/", views.create_profile, name="create_profile"),
    path("profiles/view/", views.view_profile, name="view_profile"),
    path("profiles/edit/", views.edit_profile, name="edit_profile"),
    path("profiles/admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    # Roommate search URLs
    path("roommates/search/", views.roommate_search, name="roommate_search"),
    path("roommates/<int:user_id>/", views.roommate_detail, name="roommate_detail"),
    path(
        "roommates/<int:user_id>/favorite/",
        views.toggle_favorite,
        name="toggle_favorite",
    ),
    path(
        "roommates/<int:user_id>/request/",
        views.send_connection_request,
        name="send_connection_request",
    ),
    path("roommates/favorites/", views.my_favorites, name="my_favorites"),
    path("roommates/requests/", views.connection_requests, name="connection_requests"),
    path(
        "roommates/requests/<int:request_id>/respond/",
        views.respond_to_request,
        name="respond_to_request",
    ),
    path(
        "roommates/connections/<int:user_id>/",
        views.my_connections,
        name="my_connections",
    ),
]
