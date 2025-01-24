from django.views.generic import ListView, TemplateView

from dictionary.filters import HomeEntrySearchFilter
from dictionary.models import DictionaryEntry


class HomeView(TemplateView):
    """A view for home page."""
    template_name = 'dictionary/home.html'


class SearchResultsView(ListView):
    """
    A view that displays search results for dictionary entries.
    """
    model = DictionaryEntry
    template_name = 'dictionary/search-results.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        """
        Returns the filtered and ordered queryset for dictionary entries.
        """
        queryset = DictionaryEntry.objects.select_related(
            'dictionary', 'dictionary__folder__user'
        ).prefetch_related('meanings').order_by('word')
        entry_filter = HomeEntrySearchFilter(self.request.GET, queryset=queryset)
        return entry_filter.qs
