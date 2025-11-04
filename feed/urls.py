# feed/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_portal, name="home_portal"),
]
