from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser


class UserStatistics(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='statistics')
    total_entries = models.IntegerField(_('total number entries'), default=0)
    weekly_entries = models.IntegerField(_('weekly number of entries'), default=0)
    total_examples = models.IntegerField(_('total number of user-added examples'), default=0)
    weekly_examples = models.IntegerField(_('weekly number of user-added examples'), default=0)
    last_entry_date = models.DateField(_('last entry date'), null=True, blank=True)
    current_streak = models.IntegerField(_('current streak in days'), default=0)
    max_streak = models.IntegerField(_('highest streak in days'), default=0)

    def __str__(self):
        return f'Statistics for {self.user.username}'

    class Meta:
        verbose_name = _('User Statistic')
        verbose_name_plural = _('User Statistics')
