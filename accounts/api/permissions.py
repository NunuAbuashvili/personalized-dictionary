from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsUserProfileOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, instance):
        if request.method in permissions.SAFE_METHODS:
            return True

        if instance.user == request.user:
            return True

        return False
