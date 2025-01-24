from django.db.models.signals import post_save
from django.dispatch import receiver

from leaderboard.models import UserStatistics
from .models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create UserProfile automatically when a new CustomUser is created.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Ensure user profile is saved when CustomUser is updated.
    """
    instance.profile.save()


@receiver(post_save, sender=CustomUser)
def create_user_statistics(sender, instance, created, **kwargs):
    """
    Create UserStatistics automatically when a new CustomUser is created.
    """
    if created:
        UserStatistics.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_statistics(sender, instance, **kwargs):
    """
    Ensure user statistics are saved when CustomUser is updated.
    """
    instance.statistics.save()
