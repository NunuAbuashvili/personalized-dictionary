import django_filters
from django.db.models import Q
from django.utils.lorem_ipsum import words

from .models import DictionaryEntry


class DictionaryEntryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='',
    )
    ordering = django_filters.OrderingFilter(
        choices=(
            ('word', 'Entry (A-Z)'),
            ('-word', 'Entry (Z-A)'),
            ('-created_at', 'Date Added (Newest First)'),
            ('created_at', 'Date Added (Oldest First)'),
        ),
        fields=(
            ('word', 'word'),
            ('created_at', 'created_at')
        ),
        label='',
        empty_label='Sort by...',
    )

    class Meta:
        model = DictionaryEntry
        fields = []

    def __init__(self, *args, **kwargs):
        super(DictionaryEntryFilter, self).__init__(*args, **kwargs)
        self.filters['search'].field.widget.attrs.update({
            'class': 'search-input',
            'placeholder': 'Search for entries...',
        })
        self.filters['ordering'].field.widget.attrs.update({
            'class': 'search-input sort-value',
        })

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(word__icontains=value) |
            Q(meanings__description__icontains=value) |
            Q(examples__sentence__icontains=value)
        ).distinct()
