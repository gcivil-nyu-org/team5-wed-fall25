"""
URL routing for communities app.
"""
from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    # Browse & My Communities
    path('', views.browse_communities, name='browse'),
    path('my/', views.my_communities, name='my_communities'),

    # Create
    path('create/', views.create_community, name='create'),

    # Community Detail & Management
    path('<slug:slug>/', views.community_detail, name='detail'),
    path('<slug:slug>/settings/', views.community_settings, name='settings'),

    # Membership Actions
    path('<slug:slug>/join/', views.join_community, name='join'),
    path('<slug:slug>/leave/', views.leave_community, name='leave'),

    # Members Management
    path('<slug:slug>/members/', views.member_list, name='members'),
    path('<slug:slug>/members/<int:user_id>/promote/', views.promote_member, name='promote_member'),
    path('<slug:slug>/members/<int:user_id>/demote/', views.demote_member, name='demote_member'),
    path('<slug:slug>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    path('<slug:slug>/members/<int:user_id>/ban/', views.ban_member, name='ban_member'),

    # Join Requests (Private Communities)
    path('<slug:slug>/requests/', views.join_requests, name='join_requests'),
    path('<slug:slug>/requests/<int:user_id>/approve/', views.approve_request, name='approve_request'),
    path('<slug:slug>/requests/<int:user_id>/reject/', views.reject_request, name='reject_request'),

    # Posts (Phase 2)
    path('<slug:slug>/posts/create/', views.create_post, name='create_post'),
    path('<slug:slug>/posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('<slug:slug>/posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('<slug:slug>/posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('<slug:slug>/posts/<int:post_id>/pin/', views.toggle_pin_post, name='toggle_pin_post'),

    # Comments (Phase 2)
    path('<slug:slug>/posts/<int:post_id>/comments/create/', views.create_comment, name='create_comment'),
    path('<slug:slug>/posts/<int:post_id>/comments/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('<slug:slug>/posts/<int:post_id>/comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    # Chat (Phase 3)
    path('<slug:slug>/chat/', views.chat_thread, name='chat_thread'),
    path('<slug:slug>/chat/send/', views.send_message, name='send_message'),
    path('<slug:slug>/chat/poll/', views.poll_messages, name='poll_messages'),
]
