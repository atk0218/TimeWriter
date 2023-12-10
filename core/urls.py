from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('tweet/', views.post_tweet, name='post_tweet'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('search/', views.search_results, name='search_results'),
    path('followers/', views.followers_list, name='followers_list'),
    path('following/', views.following_list, name='following_list'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('tweet_analyze/', views.tweet_analyze, name='tweet_analyze'),
    path('delete_tweet/<int:tweet_id>/', views.delete_tweet, name='delete_tweet'),
    path('tweet_generate/', views.tweet_generate_view, name='tweet_generate'),
    path('tweet_create/', views.tweet_create_view, name='tweet_create'),
    path('tweet_post/', views.tweet_post_view, name='tweet_post'),
    path('like_tweet_ajax/', views.like_tweet_ajax, name='like_tweet_ajax'),
    path('delete_tweet_ajax/', views.delete_tweet_ajax, name='delete_tweet_ajax'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
