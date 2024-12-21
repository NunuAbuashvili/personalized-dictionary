from django.db.models import Count
from django.http import HttpRequest

from accounts.models import UserProfile
from .filters import HomeEntrySearchFilter
from .models import Language, DictionaryEntry


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


def search_filter(request):
    queryset = DictionaryEntry.objects.select_related(
        'dictionary',
        'dictionary__folder__user'
    ).prefetch_related('meanings').order_by('word')
    entry_filter = HomeEntrySearchFilter(request.GET, queryset=queryset)
    return {'search_filter': entry_filter}