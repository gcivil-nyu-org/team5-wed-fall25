from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # new: send "/" to the public listings page
    path(
        "",
        RedirectView.as_view(pattern_name="listings:public_listings", permanent=False),
    ),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("profiles/", include("profiles.urls")),
    path("listings/", include(("listings.urls", "listings"), namespace="listings")),
    path("messages/", include(("messaging.urls", "messaging"), namespace="messaging")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
