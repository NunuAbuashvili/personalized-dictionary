from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import UserStatistics


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'total_entries',
                    'weekly_entries', 'total_examples',
                    'weekly_examples', 'last_entry_date',
                    'current_streak', 'max_streak')
