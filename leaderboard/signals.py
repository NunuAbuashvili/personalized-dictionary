from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import date, timedelta

from dictionary.models import DictionaryEntry, Example
from .models import UserStatistics


@receiver(post_save, sender=DictionaryEntry)
def update_user_statistics_on_entry_creation(sender, instance, created, **kwargs):
    if created:
        today = date.today()
        statistics, _ = UserStatistics.objects.get_or_create(user=instance.dictionary.folder.user)

        if statistics.last_entry_date:
            days_difference = (today - statistics.last_entry_date).days

            if days_difference == 1:  # Entry added on consecutive day
                statistics.current_streak += 1
            elif days_difference > 1:  # Break in streak
                statistics.current_streak = 1
        else:
            # First-ever entry
            statistics.current_streak = 1

        statistics.total_entries += 1
        statistics.weekly_entries += 1
        statistics.last_entry_date = today
        statistics.max_streak = max(statistics.max_streak, statistics.current_streak)
        statistics.save()


@receiver(post_delete, sender=DictionaryEntry)
def update_user_statistics_on_entry_deletion(sender, instance, **kwargs):
    UserStatistics.objects.filter(user=instance.dictionary.folder.user).update(
        total_entries=F('total_entries') - 1,
        weekly_entries=F('weekly_entries') - 1,
    )


@receiver(post_save, sender=Example)
def update_statistics_on_example_creation(sender, instance, created, **kwargs):
    if created and instance.source == 'user':
        UserStatistics.objects.filter(
            user=instance.entry.dictionary.folder.user
        ).update(
            total_examples=F('total_examples') + 1,
            weekly_examples=F('weekly_examples') + 1,
        )


@receiver(post_delete, sender=Example)
def update_statistics_on_example_deletion(sender, instance, **kwargs):
    UserStatistics.objects.filter(
        user=instance.entry.dictionary.folder.user
    ).update(
        total_examples=F('total_examples') - 1,
        weekly_examples=F('weekly_examples') - 1,
    )
