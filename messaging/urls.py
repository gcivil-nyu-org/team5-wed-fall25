# messaging/urls.py
from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("thread/<int:thread_id>/", views.thread_view, name="thread"),
    path(
        "start/", views.start_thread, name="start_thread"
    ),  # receives POST from listing/item page
    path(
        "start-roommate/", views.start_roommate_thread, name="start_roommate_thread"
    ),  # receives POST from roommate profile page
    path(
        "with-user/<int:user_id>/", views.get_or_create_roommate_thread, name="with_user"
    ),  # get or create roommate thread and redirect
    path(
        "send/<int:thread_id>/", views.send_message, name="send"
    ),  # optional separate send endpoint
    path(
        "thread/<int:thread_id>/get-new-messages/",
        views.get_new_messages,
        name="get_new_messages",
    ),  # AJAX endpoint for polling new messages
]
