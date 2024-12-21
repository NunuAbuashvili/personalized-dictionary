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
            .select_related('user')
            .prefetch_related('user__profile')
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        most_entries = sorted(queryset, key=lambda user: user.total_entries, reverse=True)[:5]
        most_examples = sorted(queryset, key=lambda user: user.total_examples, reverse=True)[:5]
        weekly_entries = sorted(queryset, key=lambda user: user.weekly_entries, reverse=True)[:5]
        weekly_examples = sorted(queryset, key=lambda user: user.weekly_examples, reverse=True)[:5]
        top_streaks = sorted(queryset, key=lambda user: user.max_streak, reverse=True)[:5]

        context['leaderboard'] = {
            'most_entries': most_entries,
            'most_examples': most_examples,
            'weekly_entries': weekly_entries,
            'weekly_examples': weekly_examples,
            'top_streaks': top_streaks,
        }

        return context
