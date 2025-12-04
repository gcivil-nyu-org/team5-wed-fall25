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
]
