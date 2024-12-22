from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from dictionary.models import Dictionary, DictionaryEntry, DictionaryFolder


class IsFolderAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, instance):
        if request.method in permissions.SAFE_METHODS:
            if view.action != 'download_folder_pdf':
                return True

        if instance.user == request.user:
            return True

        return False


class IsDictionaryAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
                return True

        if request.method == 'POST':
            folder = getattr(request, '_cached_folder', None)
            if folder:
                return folder.user == request.user
            return False

        return True

    def has_object_permission(self, request, view, instance):
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
