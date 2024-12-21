from django.db.models.signals import post_save
from django.dispatch import receiver

from leaderboard.models import UserStatistics
from .models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(post_save, sender=CustomUser)
def create_user_statistics(sender, instance, created, **kwargs):
    if created:
        UserStatistics.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_statistics(sender, instance, **kwargs):
    instance.statistics.save()
