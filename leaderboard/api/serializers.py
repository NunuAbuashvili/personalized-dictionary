from rest_framework import serializers

from dictionary.api.serializers import (
    FormattedDateTimeField,
    MiniCustomUserSerializer
)
from leaderboard.models import UserStatistics


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer for user leaderboard statistics.

    Includes user details and formatted last entry date.
    """
    user = MiniCustomUserSerializer(read_only=True)
    last_entry_date = FormattedDateTimeField()

    class Meta:
        model = UserStatistics
        fields = '__all__'
