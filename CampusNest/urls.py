# CampusNest/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Home → public listings
    path(
        "",
        RedirectView.as_view(pattern_name="listings:public_listings", permanent=False),
    ),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("profiles/", include(("profiles.urls", "profiles"), namespace="profiles")),
    path("listings/", include(("listings.urls", "listings"), namespace="listings")),
    path("messages/", include(("messaging.urls", "messaging"), namespace="messaging")),
    path(
        "marketplace/",
        include(("marketplace.urls", "marketplace"), namespace="marketplace"),
    ),
]

# ---------- Back-compat alias names (old, non-namespaced template links) ----------
urlpatterns += [
    # Marketplace aliases (names without namespace)
    path(
        "marketplace/my-items/",
        RedirectView.as_view(pattern_name="marketplace:my_items", permanent=False),
        name="my_items",
    ),
    path(
        "marketplace/create/",
        RedirectView.as_view(pattern_name="marketplace:create_item", permanent=False),
        name="create_item",
    ),
    path(
        "marketplace/<int:item_id>/",
        RedirectView.as_view(pattern_name="marketplace:view_item", permanent=False),
        name="view_item",
    ),
    path(
        "marketplace/<int:item_id>/edit/",
        RedirectView.as_view(pattern_name="marketplace:edit_item", permanent=False),
        name="edit_item",
    ),
    path(
        "marketplace/<int:item_id>/delete/",
        RedirectView.as_view(pattern_name="marketplace:delete_item", permanent=False),
        name="delete_item",
    ),
    path(
        "marketplace/<int:item_id>/mark-sold/",
        RedirectView.as_view(pattern_name="marketplace:mark_as_sold", permanent=False),
        name="mark_as_sold",
    ),
    # Profile pages
    path(
        "profiles/view/",
        RedirectView.as_view(pattern_name="profiles:view_profile", permanent=False),
        name="view_profile",
    ),
    path(
        "profiles/edit/",
        RedirectView.as_view(pattern_name="profiles:edit_profile", permanent=False),
        name="edit_profile",
    ),
    path(
        "profiles/create/",
        RedirectView.as_view(pattern_name="profiles:create_profile", permanent=False),
        name="create_profile",
    ),
    path(
        "profiles/admin-dashboard/",
        RedirectView.as_view(pattern_name="profiles:admin_dashboard", permanent=False),
        name="admin_dashboard",
    ),
    # Roommates feature
    path(
        "profiles/roommates/search/",
        RedirectView.as_view(pattern_name="profiles:roommate_search", permanent=False),
        name="roommate_search",
    ),
    path(
        "profiles/roommates/<int:user_id>/",
        RedirectView.as_view(pattern_name="profiles:roommate_detail", permanent=False),
        name="roommate_detail",
    ),
    path(
        "profiles/roommates/<int:user_id>/favorite/",
        RedirectView.as_view(pattern_name="profiles:toggle_favorite", permanent=False),
        name="toggle_favorite",
    ),
    path(
        "profiles/roommates/<int:user_id>/request/",
        RedirectView.as_view(
            pattern_name="profiles:send_connection_request", permanent=False
        ),
        name="send_connection_request",
    ),
    path(
        "profiles/roommates/favorites/",
        RedirectView.as_view(pattern_name="profiles:my_favorites", permanent=False),
        name="my_favorites",
    ),
    path(
        "profiles/roommates/requests/",
        RedirectView.as_view(
            pattern_name="profiles:connection_requests", permanent=False
        ),
        name="connection_requests",
    ),
    path(
        "profiles/roommates/requests/<int:request_id>/respond/",
        RedirectView.as_view(
            pattern_name="profiles:respond_to_request", permanent=False
        ),
        name="respond_to_request",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
