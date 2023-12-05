from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Tweet, Follow
from .forms import TweetForm
from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth import login, authenticate
from .models import Tweet, UserProfile
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

def home(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        following_ids = user_profile.following.values_list('user', flat=True)
        user_ids = list(following_ids) + [request.user.id]
        tweets = Tweet.objects.filter(user_id__in=user_ids).order_by('-created_at')
        following_status = {user_id: True for user_id in following_ids}

    else:
        tweets = Tweet.objects.all().order_by('-created_at')  # 新しい順にツイートを取得
        following_status = {}
    return render(request, 'core/home.html', {'tweets': tweets, 'following_status': following_status})


@login_required
def post_tweet(request):
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)  # request.FILESを追加
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect('home')
    else:
        form = TweetForm()
    return render(request, 'core/post_tweet.html', {'form': form})

def follow_user(request, user_id):
    if request.user.is_authenticated:
        user_to_follow = User.objects.get(pk=user_id)
        request.user.userprofile.following.add(user_to_follow.userprofile)
        return HttpResponseRedirect(reverse('home'))
    else:
        return HttpResponseRedirect(reverse('login'))

def unfollow_user(request, user_id):
    if request.user.is_authenticated:
        user_to_unfollow = get_object_or_404(User, pk=user_id)
        request.user.userprofile.following.remove(user_to_unfollow.userprofile)
        return redirect('following_list')
    else:
        return redirect('login')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

def search_results(request):
    query = request.GET.get('q', '')
    tweets = Tweet.objects.filter(content__icontains=query)
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        following_ids = user_profile.following.values_list('user', flat=True)
        # フォロー状態を確認
        following_status = {user_id: True for user_id in following_ids}
    else:
        following_status = {}

    return render(request, 'core/search_results.html', {'tweets': tweets, 'following_status': following_status})

def followers_list(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        followers = user_profile.followers.all()
    else:
        followers = []

    return render(request, 'core/followers_list.html', {'followers': followers})

def following_list(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        following = user_profile.following.all()
    else:
        following = []

    return render(request, 'core/following_list.html', {'following': following})