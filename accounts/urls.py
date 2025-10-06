from django.urls import path
from accounts.views import user_profile_view

urlpatterns = [
    path('me/', user_profile_view, name='user-profile'),
]