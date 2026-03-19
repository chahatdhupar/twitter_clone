from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Tweet, Profile, Comment, Message, Notification, Hashtag, Bookmark
from .forms import TweetForm, ProfileForm, RegisterForm, LoginForm, CommentForm, MessageForm


# ─── AUTHENTICATION VIEWS ────────────────────────────────────────────


# Register view
def register_view(request):
    # redirect if already logged in
    if request.user.is_authenticated:
        return redirect('feed')

    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            # create profile automatically when user registers
            Profile.objects.create(user=user)
            messages.success(request, 'Account created! Please login.')
            return redirect('login')

    return render(request, 'twitter/register.html', {'form': form})


# Login view
def login_view(request):
    # redirect if already logged in
    if request.user.is_authenticated:
        return redirect('feed')

    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('feed')
            else:
                messages.error(request, 'Invalid username or password!')

    return render(request, 'twitter/login.html', {'form': form})


# Logout view
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')


# ─── TWEET VIEWS ─────────────────────────────────────────────────────


# Feed - show tweets from followed users + own tweets
@login_required(login_url='login')
def feed(request):
    try:
        profile = Profile.objects.get(user=request.user)
        following_users = profile.followers.all()
    except Profile.DoesNotExist:
        Profile.objects.create(user=request.user)
        following_users = []

    tweets = Tweet.objects.filter(
        user__in=list(following_users) + [request.user]
    )

    # get bookmarked tweet ids for current user
    bookmarked_ids = Bookmark.objects.filter(
        user=request.user
    ).values_list('tweet_id', flat=True)

    trending = Hashtag.objects.annotate(
        tweet_count=Count('tweets')
    ).order_by('-tweet_count')[:5]

    form = TweetForm()

    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tweet      = form.save(commit=False)
            tweet.user = request.user
            tweet.save()

            import re
            words = tweet.content.split()
            for word in words:
                if word.startswith('#'):
                    tag_name = re.sub(r'[^\\w]', '', word[1:]).lower()
                    if tag_name:
                        hashtag, created = Hashtag.objects.get_or_create(
                            name=tag_name
                        )
                        hashtag.tweets.add(tweet)

            messages.success(request, 'Tweet posted!')
            return redirect('feed')

    return render(request, 'twitter/feed.html', {
        'tweets'       : tweets,
        'form'         : form,
        'trending'     : trending,
        'bookmarked_ids': bookmarked_ids,   # ← add this
    })


# Delete tweet
@login_required(login_url='login')
def delete_tweet(request, id):
    tweet = get_object_or_404(Tweet, id=id)

    # make sure user can only delete their own tweets
    if tweet.user == request.user:
        tweet.delete()
        messages.success(request, 'Tweet deleted!')
    else:
        messages.error(request, 'You cannot delete this tweet!')

    return redirect(request.META.get('HTTP_REFERER', 'feed'))


# Like / Unlike tweet
@login_required(login_url='login')
def like_tweet(request, id):
    tweet = get_object_or_404(Tweet, id=id)

    if request.user in tweet.likes.all():
        tweet.likes.remove(request.user)
    else:
        tweet.likes.add(request.user)
        # create notification only if liking someone else's tweet
        if tweet.user != request.user:
            Notification.objects.create(
                recipient=tweet.user,
                sender=request.user,
                notification_type='like',
                tweet=tweet
            )

    return redirect(request.META.get('HTTP_REFERER', 'feed'))


# ─── PROFILE VIEWS ───────────────────────────────────────────────────


# User profile page
@login_required(login_url='login')
def profile(request, username):
    # get the user whose profile we are viewing
    profile_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=profile_user)

    # get all tweets by this user
    tweets = Tweet.objects.filter(user=profile_user)

    # check if current user follows this profile
    is_following = request.user in profile.followers.all()

    return render(request, 'twitter/profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'tweets': tweets,
        'is_following': is_following
    })


# Edit profile
@login_required(login_url='login')
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    form = ProfileForm(instance=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile', username=request.user.username)

    return render(request, 'twitter/edit_profile.html', {'form': form})


# Follow / Unfollow user
@login_required(login_url='login')
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user_to_follow)

    if user_to_follow == request.user:
        messages.error(request, 'You cannot follow yourself!')
        return redirect('profile', username=username)

    if request.user in profile.followers.all():
        profile.followers.remove(request.user)
        messages.success(request, f'Unfollowed {username}!')
    else:
        profile.followers.add(request.user)
        # create follow notification
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            notification_type='follow'
        )
        messages.success(request, f'Following {username}!')

    return redirect('profile', username=username)


# ─── SEARCH VIEW ─────────────────────────────────────────────────────


# Search users
@login_required(login_url='login')
def search(request):
    query = request.GET.get('q', '')
    users = []

    if query:
        # search users by username
        users = User.objects.filter(
            username__icontains=query
        ).exclude(username=request.user.username)

    return render(request, 'twitter/search.html', {
        'users': users,
        'query': query
    })

    # Followers list
@login_required(login_url='login')
def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=profile_user)

    # get all users who follow this profile
    followers = profile.followers.all()

    return render(request, 'twitter/followers_list.html', {
        'profile_user': profile_user,
        'followers': followers,
    })


# Following list
@login_required(login_url='login')
def following_list(request, username):
    profile_user = get_object_or_404(User, username=username)

    # get all profiles this user follows
    following = Profile.objects.filter(followers=profile_user)

    return render(request, 'twitter/following_list.html', {
        'profile_user': profile_user,
        'following': following,
    })

# Tweet detail page with comments
@login_required(login_url='login')
def tweet_detail(request, id):
    tweet    = get_object_or_404(Tweet, id=id)
    comments = tweet.comment_set.all()
    form     = CommentForm()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment         = form.save(commit=False)
            comment.tweet   = tweet
            comment.user    = request.user
            comment.save()
            messages.success(request, 'Comment added!')
            return redirect('tweet_detail', id=id)

    return render(request, 'twitter/tweet_detail.html', {
        'tweet'   : tweet,
        'comments': comments,
        'form'    : form
    })


# Delete comment
@login_required(login_url='login')
def delete_comment(request, id):
    comment = get_object_or_404(Comment, id=id)
    tweet_id = comment.tweet.id

    # make sure user can only delete their own comments
    if comment.user == request.user:
        comment.delete()
        messages.success(request, 'Comment deleted!')
    else:
        messages.error(request, 'You cannot delete this comment!')

    return redirect('tweet_detail', id=tweet_id)

# Retweet
@login_required(login_url='login')
def retweet(request, id):
    original_tweet = get_object_or_404(Tweet, id=id)

    # check if user already retweeted this tweet
    already_retweeted = Tweet.objects.filter(
        user=request.user,
        is_retweet=True,
        original_tweet=original_tweet
    ).exists()

    if already_retweeted:
        messages.error(request, 'You already retweeted this!')
    else:
        # create a new tweet as retweet
        Tweet.objects.create(
            user=request.user,
            content=original_tweet.content,
            is_retweet=True,
            original_tweet=original_tweet
        )
        messages.success(request, 'Retweeted successfully!')

    return redirect(request.META.get('HTTP_REFERER', 'feed'))

# Inbox - list of conversations
@login_required(login_url='login')
def inbox(request):
    # get all users current user has chatted with
    sent     = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)

    # combine and get unique users
    user_ids  = set(list(sent) + list(received))
    chat_users = User.objects.filter(id__in=user_ids)

    return render(request, 'twitter/inbox.html', {
        'chat_users': chat_users
    })


# Chat with a specific user
@login_required(login_url='login')
def chat(request, username):
    other_user = get_object_or_404(User, username=username)
    form = MessageForm()

    # get all messages between these two users
    messages_list = Message.objects.filter(
        sender=request.user, receiver=other_user
    ) | Message.objects.filter(
        sender=other_user, receiver=request.user
    )

    # mark received messages as read
    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message          = form.save(commit=False)
            message.sender   = request.user
            message.receiver = other_user
            message.save()
            return redirect('chat', username=username)

    return render(request, 'twitter/chat.html', {
        'other_user'   : other_user,
        'messages_list': messages_list,
        'form'         : form
    })

# Bookmark / Unbookmark tweet
@login_required(login_url='login')
def bookmark_tweet(request, id):
    tweet = get_object_or_404(Tweet, id=id)

    # check if already bookmarked
    bookmark = Bookmark.objects.filter(user=request.user, tweet=tweet)

    if bookmark.exists():
        bookmark.delete()
        messages.success(request, 'Bookmark removed!')
    else:
        Bookmark.objects.create(user=request.user, tweet=tweet)
        messages.success(request, 'Tweet bookmarked!')

    return redirect(request.META.get('HTTP_REFERER', 'feed'))


# Bookmarks page
@login_required(login_url='login')
def bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user)
    return render(request, 'twitter/bookmarks.html', {
        'bookmarks': bookmarks
    })

# Hashtag tweets page
@login_required(login_url='login')
def hashtag_tweets(request, name):
    hashtag = get_object_or_404(Hashtag, name=name)
    tweets  = hashtag.tweets.all()

    return render(request, 'twitter/hashtag_tweets.html', {
        'hashtag': hashtag,
        'tweets' : tweets
    })

# Notifications page
@login_required(login_url='login')
def notifications(request):
    notifications = Notification.objects.filter(recipient=request.user)

    # mark ALL as read when user opens notifications page
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return render(request, 'twitter/notifications.html', {
        'notifications': notifications
    })

# Unread notifications count - used in navbar
def get_unread_count(request):
    if request.user.is_authenticated:
        return Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    return 0