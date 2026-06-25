from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    path('add_to_shelf/', views.add_to_shelf, name='add_to_shelf'),
    path('review/<int:shelf_id>/', views.review_book, name='review_book'),
    path('review/<int:shelf_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/reply/', views.add_reply, name='add_reply'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('book_detail/<int:book_id>/', views.book_detail, name='book_detail'),
    path('genre/<int:genre_id>/', views.genre_detail, name='genre_detail'),
    path('author/<int:author_id>/', views.author_detail, name='author_detail'),
]
