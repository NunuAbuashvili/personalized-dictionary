import django_filters
from django.db.models import Q

from .models import DictionaryEntry, DictionaryFolder, Dictionary


class HomeEntrySearchFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='',
    )

    class Meta:
        model = DictionaryEntry
        fields = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('dictionary_author', None)
        super(HomeEntrySearchFilter, self).__init__(*args, **kwargs)

        self.filters['search'].field.widget.attrs.update({
            'class': 'search-input',
            'placeholder': 'Search for entries...',
        })

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(word__icontains=value) |
            Q(meanings__description__icontains=value)
        ).distinct()


class DictionaryFolderFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='',
    )

    class Meta:
        model = DictionaryFolder
        fields = []

    def __init__(self, *args, **kwargs):
        super(DictionaryFolderFilter, self).__init__(*args, **kwargs)
        self.filters['search'].field.widget.attrs.update({
            'class': 'search-input',
            'placeholder': 'Search for folders...',
        })

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(language__name__icontains=value) |
            Q(dictionaries__name__icontains=value)
        ).distinct()


class DictionaryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='',
    )

    class Meta:
        model = Dictionary
        fields = []

    def __init__(self, *args, **kwargs):
        super(DictionaryFilter, self).__init__(*args, **kwargs)
        self.filters['search'].field.widget.attrs.update({
            'class': 'search-input',
            'placeholder': 'Search inside the folder...',
        })

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(entries__word__icontains=value)
        ).distinct()


class DictionariesFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='',
    )
    folder = django_filters.ModelChoiceFilter(
        queryset=None,
        label='',
        empty_label='All Folders',
        method='filter_by_folder'
    )

    class Meta:
        model = Dictionary
        fields = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('dictionary_author', None)
        super(DictionariesFilter, self).__init__(*args, **kwargs)

        self.filters['folder'].extra.update({
            'queryset': DictionaryFolder.objects.filter(user=self.user)
        })

        self.filters['search'].field.widget.attrs.update({
            'class': 'search-input',
            'placeholder': 'Search inside the folder...',
        })
        self.filters['folder'].field.widget.attrs.update({
            'class': 'search-input sort-value',
        })

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(entries__word__icontains=value)
        ).distinct()

    def filter_by_folder(self, queryset, name, value):
        if value:
            return queryset.filter(folder=value)
        return queryset


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
