from django.db.models import Count
from django.http import HttpRequest

from accounts.models import UserProfile
from .models import Language


def folder_language_data(request: HttpRequest):
    if request.user.is_authenticated:
        folder_languages = Language.objects.filter(
            folders__user=request.user
        ).distinct()
        return {
            'folder_languages': folder_languages,
        }
    return {
        'folder_languages': None,
    }
