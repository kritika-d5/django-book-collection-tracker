from django.urls import path
from . import views

urlpatterns = [
    path('', views.community_list, name='community_list'),
    path('create/', views.community_create, name='community_create'),
    path('<slug:slug>/', views.community_detail, name='community_detail'),
    path('<slug:slug>/join/', views.join_community, name='join_community'),
    path('<slug:slug>/leave/', views.leave_community, name='leave_community'),
    path('<slug:slug>/post/new/', views.post_create, name='post_create'),
    path('<slug:slug>/post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('<slug:slug>/post/<int:post_id>/comment/', views.add_post_comment, name='add_post_comment'),
    path('<slug:slug>/comment/<int:comment_id>/reply/', views.add_post_reply, name='add_post_reply'),
    path('<slug:slug>/comment/<int:comment_id>/delete/', views.delete_post_comment, name='delete_post_comment'),
    path('<slug:slug>/post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
]
