from django.db.models import Count
from django.http import HttpRequest

from accounts.models import UserProfile
from .filters import HomeEntrySearchFilter
from .models import Language, DictionaryEntry


def folder_language_data(request: HttpRequest) -> dict:
    """
    Retrieve distinct languages for the authenticated user's folders.

    Args:
        request (HttpRequest): Request object.

    Returns:
        Dictionary with folder languages or None if user is not authenticated.
    """
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


def search_filter(request: HttpRequest) -> dict:
    """
    Create a search filter for dictionary entries.

    Args:
        request (HttpRequest): Request object.

    Returns:
        Dictionary containing the search filter for entries.
    """
    queryset = DictionaryEntry.objects.select_related(
        'dictionary',
        'dictionary__folder__user'
    ).prefetch_related('meanings').order_by('word')
    entry_filter = HomeEntrySearchFilter(request.GET, queryset=queryset)
    return {'search_filter': entry_filter}
