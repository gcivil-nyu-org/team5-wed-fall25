from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/messages/thread/<int:thread_id>/", consumers.ChatConsumer.as_asgi()),
    path("ws/messages/inbox/", consumers.InboxConsumer.as_asgi()),
]
