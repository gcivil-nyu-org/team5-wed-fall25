# messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('thread/<int:thread_id>/', views.thread_view, name='thread'),
    path('start/', views.start_thread, name='start_thread'),        # receives POST from listing page
    path('send/<int:thread_id>/', views.send_message, name='send'), # optional separate send endpoint
]
