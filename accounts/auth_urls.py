from django.urls import path
from accounts.views import *

urlpatterns = [
    path('callback/', cognito_callback_view, name='cognito-callback'),
    path('exchange/', token_exchange_view, name='token-exchange'),
    path('login/', login_page_view, name='login-page'),
    path('debug/', debug_cognito_config, name='cognito-debug'),
]