from django.contrib import admin
from .models import UserShelf, ReviewComment


@admin.register(UserShelf)
class UserShelfAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'shelf_type', 'rating', 'reviewed_at')
    list_filter = ('shelf_type',)


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'shelf', 'parent', 'created_at')
    search_fields = ('body', 'user__username')
