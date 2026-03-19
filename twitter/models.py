from django.db import models
from django.contrib.auth.models import User


# Profile model - extends User with extra info
class Profile(models.Model):
    # OneToOneField because one user has one profile
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    # ManyToManyField because a user can follow many users
    # and be followed by many users
    followers = models.ManyToManyField(
        User,
        related_name='following',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    # get total number of followers
    def get_followers_count(self):
        return self.followers.count()

    # get total number of following
    def get_following_count(self):
        return Profile.objects.filter(followers=self.user).count()


class Tweet(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    image   = models.ImageField(upload_to='tweets/', blank=True, null=True)
    likes   = models.ManyToManyField(User, related_name='liked_tweets', blank=True)

    # retweet fields
    is_retweet    = models.BooleanField(default=False)
    original_tweet = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='retweets'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"

    def get_likes_count(self):
        return self.likes.count()

    def get_retweet_count(self):
        return self.retweets.count()

    class Meta:
        ordering = ['-created_at']

        # Comment model - stores comments on tweets
class Comment(models.Model):
    tweet   = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on {self.tweet.id}: {self.content[:50]}"

    class Meta:
        ordering = ['created_at']    # oldest comments first

        # Direct Message model
class Message(models.Model):
    sender   = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages'
    )
    content   = models.TextField()
    is_read   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content[:50]}"

    class Meta:
        ordering = ['created_at']

        # Bookmark model
class Bookmark(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bookmarked {self.tweet.id}"

    class Meta:
        # user can only bookmark a tweet once
        unique_together = ['user', 'tweet']
        ordering = ['-created_at']

        # Hashtag model
class Hashtag(models.Model):
    name   = models.CharField(max_length=100, unique=True)
    tweets = models.ManyToManyField(Tweet, related_name='hashtags', blank=True)

    def __str__(self):
        return f"#{self.name}"

    def get_tweet_count(self):
        return self.tweets.count()
    
    # Notification model
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like',     'Like'),
        ('comment',  'Comment'),
        ('follow',   'Follow'),
        ('retweet',  'Retweet'),
    ]

    # user who receives notification
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    # user who triggered notification
    sender    = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    tweet   = models.ForeignKey(Tweet, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.notification_type}"

    class Meta:
        ordering = ['-created_at']