from django.urls import path

from . import views


app_name = 'leaderboard'


urlpatterns = [
    path('', views.LeaderboardView.as_view(), name='leaderboard'),
]