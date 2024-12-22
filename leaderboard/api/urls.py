from django.urls import path, include

from . import views


app_name = 'leaderboard_api'


urlpatterns = [
    path('', views.LeaderboardAPIListView.as_view(), name='leaderboard'),
]
