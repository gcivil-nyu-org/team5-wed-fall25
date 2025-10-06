from django.urls import path
from accounts.views import *

urlpatterns = [
    path('me/', user_profile_view, name='user-profile'),
]