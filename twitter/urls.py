from django.urls import path
from . import views

urlpatterns = [

    # authentication urls
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # tweet urls
    path('', views.feed, name='feed'),
    path('tweet/<int:id>/', views.tweet_detail, name='tweet_detail'),
    path('tweet/delete/<int:id>/', views.delete_tweet, name='delete_tweet'),
    path('tweet/like/<int:id>/', views.like_tweet, name='like_tweet'),

    # comment urls
    path('comment/delete/<int:id>/', views.delete_comment, name='delete_comment'),

    # profile urls
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),

    # followers and following urls
    path('profile/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('profile/<str:username>/following/', views.following_list, name='following_list'),

    # search url
    path('search/', views.search, name='search'),

    path('tweet/retweet/<int:id>/', views.retweet, name='retweet'),
    path('inbox/', views.inbox, name='inbox'),
    path('chat/<str:username>/', views.chat, name='chat'),
    path('tweet/bookmark/<int:id>/', views.bookmark_tweet, name='bookmark_tweet'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('hashtag/<str:name>/', views.hashtag_tweets, name='hashtag_tweets'),
    path('notifications/', views.notifications, name='notifications'),
]