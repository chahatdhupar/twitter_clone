from django.contrib import admin
from .models import Profile, Tweet, Comment


# Profile Admin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_followers_count', 'created_at']
    search_fields = ['user__username', 'bio']


# Tweet Admin
@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'get_likes_count', 'created_at']
    search_fields = ['user__username', 'content']
    list_filter = ['created_at']


# Comment Admin
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'tweet', 'content', 'created_at']
    search_fields = ['user__username', 'content']