from celery import shared_task

from .models import UserStatistics


@shared_task
def reset_weekly_stats():
    UserStatistics.objects.all().update(
        weekly_entries=0,
        weekly_examples=0
    )
