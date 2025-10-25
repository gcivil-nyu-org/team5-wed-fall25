# CampusNest/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Home → public listings (namespaced)
    path(
        "",
        RedirectView.as_view(pattern_name="listings:public_listings", permanent=False),
    ),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("listings/", include("listings.urls")),
    path("marketplace/", include("marketplace.urls")),
    path("messages/", include("chat.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
