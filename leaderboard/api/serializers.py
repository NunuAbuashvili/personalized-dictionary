from rest_framework import serializers
from rest_framework.fields import DateTimeField
from django.utils.translation import gettext_lazy as _

from dictionary.api.serializers import MiniCustomUserSerializer, FormattedDateTimeField
from leaderboard.models import UserStatistics



class LeaderboardSerializer(serializers.ModelSerializer):
    user = MiniCustomUserSerializer(read_only=True)
    last_entry_date = FormattedDateTimeField()

    class Meta:
        model = UserStatistics
        fields = '__all__'
