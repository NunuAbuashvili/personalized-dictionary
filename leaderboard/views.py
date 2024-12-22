from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView

from .models import UserStatistics


class LeaderboardView(LoginRequiredMixin, ListView):
    model = UserStatistics
    template_name = 'leaderboard/leaderboard.html'

    def get_queryset(self):
        queryset = (
            UserStatistics.objects
            .select_related('user', 'user__profile')
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        context['leaderboard'] = {
            'most_entries': queryset.order_by('-total_entries', 'user__username')[:5],
            'most_examples': queryset.order_by('-total_examples', 'user__username')[:5],
            'weekly_entries': queryset.order_by('-weekly_entries', 'user__username')[:5],
            'weekly_examples': queryset.order_by('-weekly_examples', 'user__username')[:5],
            'top_streaks': queryset.order_by('-max_streak', 'user__username')[:5],
        }

        return context
