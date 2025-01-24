from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from leaderboard.models import UserStatistics
from .serializers import LeaderboardSerializer


@extend_schema(tags=['Leaderboard'])
class LeaderboardAPIListView(ListAPIView):
    """
    API view for retrieving user leaderboard statistics.

    Supports multiple leaderboard categories:
    - Most total entries.
    - Most total examples.
    - Weekly entries.
    - Weekly examples.
    - Top user streaks.
    """
    queryset = UserStatistics.objects.select_related('user')
    serializer_class = LeaderboardSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_top_users(self, field, secondary_field='user__username', limit=5):
        """
        Retrieve top users based on a specific statistical field.

        Args:
            field (str): Primary sorting field.
            secondary_field (str, optional): Secondary sorting field.
            limit (int, optional): Number of top users to return.

        Returns:
            QuerySet: Ordered and limited queryset of top users.
        """
        return self.queryset.order_by(f'-{field}', secondary_field)[:limit]

    def get(self, request, *args, **kwargs):
        """
        Generate leaderboard data across different categories.

        Returns:
            Response: JSON with top users in multiple statistical categories.
        """
        leaderboard = {
            'most_entries': self.serializer_class(self.get_top_users('total_entries'), many=True).data,
            'most_examples': self.serializer_class(self.get_top_users('total_examples'), many=True).data,
            'weekly_entries': self.serializer_class(self.get_top_users('weekly_entries'), many=True).data,
            'weekly_examples': self.serializer_class(self.get_top_users('weekly_examples'), many=True).data,
            'top_streaks': self.serializer_class(self.get_top_users('max_streak'), many=True).data,
        }

        return Response(leaderboard)
