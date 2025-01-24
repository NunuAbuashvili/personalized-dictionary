from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsUserProfileOrReadOnly(permissions.BasePermission):
    """
    Custom permission class to allow only the profile owner to modify their profile.

    Allows read-only access for safe HTTP methods.
    Allows full access only to the user who owns the specific profile instance.
    """
    def has_object_permission(self, request, view, instance):
        """
        Check if the request user has permission to perform actions on the object.

        Args:
            request (Request): The incoming HTTP request.
            view (APIView): The view handling the request.
            instance (Model): The model instance being accessed.

        Returns:
            bool: True if the request is a safe method or the user owns the instance.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if instance.user == request.user:
            return True

        return False
