from django.contrib import admin
from .models import Community, CommunityMembership, CommunityPost, PostComment


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_by', 'is_public', 'created_at')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CommunityMembership)
class CommunityMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'role', 'joined_at')
    list_filter = ('role',)


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'community', 'author', 'created_at')
    search_fields = ('title', 'body')


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'parent', 'created_at')
