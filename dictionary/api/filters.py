from django_filters import rest_framework as filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from dictionary.models import DictionaryFolder, Dictionary, DictionaryEntry


class DictionaryFolderFilter(filters.FilterSet):
    search = filters.CharFilter(
        method='multi_field_search',
        label=_('Search by folder, language or dictionary name')
    )

    class Meta:
        model = DictionaryFolder
        fields = ('user', 'language')

    def multi_field_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(language__name__icontains=value) |
                Q(dictionaries__name__icontains=value)
            ).distinct()
        return queryset


class DictionaryFilter(filters.FilterSet):
    search = filters.CharFilter(
        method='multi_field_search',
        label=_('Search by dictionary name, entry words or their meanings')
    )

    def multi_field_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value) |
                Q(entries__word__icontains=value) |
                Q(entries__meanings__description__icontains=value)
            ).distinct()


class DictionaryEntryFilter(filters.FilterSet):
    search = filters.CharFilter(
        method='multi_field_search',
        label=_('Search through the dictionary entries')
    )

    ordering = filters.OrderingFilter(
        fields=('word', 'created_at')
    )

    def multi_field_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(word__icontains=value) |
                Q(meanings__description__icontains=value) |
                Q(examples__sentence__icontains=value)
            ).distinct()


class HomeEntrySearchFilter(filters.FilterSet):
    search = filters.CharFilter(
        method='multi_field_search',
        label=_('Search through the dictionary entries')
    )

    def multi_field_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(word__icontains=value) |
                Q(meanings__description__icontains=value)
            ).distinct()
