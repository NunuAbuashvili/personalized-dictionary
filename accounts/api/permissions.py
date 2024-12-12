from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class IsUserProfileOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, instance):
        if request.method in permissions.SAFE_METHODS:
            return True

        if instance.user == request.user:
            return True

        raise PermissionDenied(
            detail=_('You do not have permission to perform this action.'),
            code='not_own_profile'
        )
