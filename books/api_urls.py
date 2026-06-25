from rest_framework.routers import DefaultRouter
from .api_views import BookViewSet, AuthorViewSet, GenreViewSet
from django.urls import path, include

router = DefaultRouter()

router.register(r'books', BookViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)

urlpatterns = [
    path('', include(router.urls)),
]