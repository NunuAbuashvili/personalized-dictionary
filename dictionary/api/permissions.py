from django.utils.translation import gettext_lazy as _
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from dictionary.models import Dictionary, DictionaryEntry, DictionaryFolder


class IsFolderAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission to allow only folder authors to modify their folders.

    Provides read-only access for safe methods.
    """
    def has_object_permission(self, request, view, instance):
        """
        Check permission for specific folder instance.

        Args:
            request (Request): HTTP request.
            view (APIView): Current view.
            instance (Model): Folder instance.

        Returns:
            bool: Permission status.
        """
        if request.method in permissions.SAFE_METHODS:
            if view.action != 'download_folder_pdf':
                return True

        if instance.user == request.user:
            return True

        return False


class IsDictionaryAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission to control dictionary and entry access.

    Manages permissions based on dictionary folder ownership.
    """
    def has_permission(self, request, view):
        """
        Check general permission for dictionary actions.

        Args:
            request (Request): HTTP request.
            view (APIView): Current view.

        Returns:
            bool: Permission status.
        """
        if request.method in permissions.SAFE_METHODS:
                return True

        if request.method == 'POST':
            folder = getattr(request, '_cached_folder', None)
            if folder:
                return folder.user == request.user
            return False

        return True

    def has_object_permission(self, request, view, instance):
        """
        Check permission for specific dictionary or entry instance.

        Args:
            request (Request): HTTP request.
            view (APIView): Current view.
            instance (Model): Dictionary or Entry instance.

        Returns:
            bool: Permission status.
        """
        if request.method in permissions.SAFE_METHODS:
            if view.action != 'download_dictionary_pdf':
                return True

        if isinstance(instance, Dictionary):
            if instance.folder.user == request.user:
                return True
        elif isinstance(instance, DictionaryEntry):
            if instance.dictionary.folder.user == request.user:
                return True

        return False
