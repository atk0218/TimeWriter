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
from wordcloud import WordCloud
from janome.tokenizer import Tokenizer  # 日本語の場合
import os
from django.conf import settings
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUIバックエンドを使用しないように設定
import io
import urllib, base64
from django.utils.timezone import localtime

def home(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile

        # ユーザー自身のツイート
        user_tweets = Tweet.objects.filter(user=request.user).order_by('-created_at')

        # フォローしているユーザーのツイート
        following_ids = user_profile.following.values_list('user', flat=True)
        following_tweets = Tweet.objects.filter(user_id__in=following_ids).order_by('-created_at')

        # フォロー状態を確認
        following_status = {user_id: True for user_id in following_ids}

    else:
        # 未ログインの場合は全てのツイートを表示
        user_tweets = Tweet.objects.none()
        following_tweets = Tweet.objects.all().order_by('-created_at')
        following_status = {}

    return render(request, 'core/home.html', {'user_tweets': user_tweets, 'following_tweets': following_tweets, 'following_status': following_status})


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

@login_required
def follow_user(request, user_id):
    if request.user.is_authenticated:
        user_to_follow = User.objects.get(pk=user_id)
        request.user.userprofile.following.add(user_to_follow.userprofile)
        return HttpResponseRedirect(reverse('home'))
    else:
        return HttpResponseRedirect(reverse('login'))

@login_required
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

@login_required
def followers_list(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        followers = user_profile.followers.all()
    else:
        followers = []

    return render(request, 'core/followers_list.html', {'followers': followers})

@login_required
def following_list(request):
    if request.user.is_authenticated:
        user_profile = request.user.userprofile
        following = user_profile.following.all()
    else:
        following = []

    return render(request, 'core/following_list.html', {'following': following})

@login_required
def tweet_analyze(request):
    if request.user.is_authenticated:
        tweets = Tweet.objects.filter(user=request.user).order_by('-created_at')[:10]
        tweet_texts = [tweet.content for tweet in tweets]
        wordcloud_path = generate_wordcloud(tweet_texts)

        # 過去30日間の日付を生成
        end_date =  localtime(timezone.now())
        start_date = end_date - timedelta(days=14)

        # 日付ごとのツイート数を集計
        daily_tweets = Tweet.objects.filter(created_at__range=[start_date, end_date], user=request.user)
        daily_tweets = daily_tweets.annotate(day=TruncDate('created_at')).values('day').annotate(count=Count('id'))

        # データの整形
        dates = [start_date + timedelta(days=i) for i in range(14)]
        counts = [0] * 14
        for tweet in daily_tweets:
            index = (tweet['day']- start_date.date()).days
            
            # リストのサイズを超えていないことを確認
            if 0 <= index < 14:
                counts[index] = tweet['count']

        # グラフの生成
        plt.figure(figsize=(10, 6))
        plt.plot(dates, counts, marker='o')
        plt.xlabel('Date')
        plt.ylabel('Number of Tweets')
        plt.title('Tweets in the Last 30 Days')

        # グラフをBase64エンコーディングされた画像として保存
        fig = plt.gcf()
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = 'data:image/png;base64,' + urllib.parse.quote(string)
        
        plt.close()  # グラフを閉じる
        
        return render(request, 'core/tweet_analyze.html', {'wordcloud_path': wordcloud_path, 'graph': uri})

    else:
        return HttpResponseRedirect(reverse('login'))

def generate_wordcloud(texts):
    t = Tokenizer()
    words = []

    for text in texts:
        tokens = t.tokenize(text)
        words.extend([token.base_form for token in tokens if token.part_of_speech.startswith(('名詞', '動詞'))])

    font_path = "/Library/Fonts/Arial Unicode.ttf"
    wordcloud = WordCloud(width=800, height=400,background_color='white', font_path=font_path).generate(' '.join(words))

    filename = 'wordcloud.png'
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    wordcloud.to_file(file_path)

    return os.path.join(settings.MEDIA_URL, filename)

@login_required
def delete_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)

    if request.user.is_authenticated and tweet.user == request.user:
        tweet.delete()
        # 削除後のリダイレクト先
        return redirect('home')
    else:
        # アクセス権限がない場合の処理
        return redirect('home')