from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
]
