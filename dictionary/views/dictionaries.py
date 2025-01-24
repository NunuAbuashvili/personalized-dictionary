import random

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, render
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView
)
from django.views.generic.list import MultipleObjectMixin
from weasyprint import HTML

from accounts.decorators import verified_email_required
from accounts.models import CustomUser
from dictionary.filters import DictionariesFilter, DictionaryEntryFilter
from dictionary.models import Dictionary, DictionaryEntry, DictionaryFolder
from .mixins import CustomLoginRequiredMixin


class DictionaryListView(ListView):
    """
    View for listing dictionaries for a specific user.

    Supports filtering and pagination of dictionaries.
    Restricts visibility based on user and accessibility settings.
    """
    model = Dictionary
    template_name = 'dictionary/dictionaries.html'
    context_object_name = 'dictionaries'
    ordering = ('-created_at',)
    paginate_by = 5

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        user_slug = self.kwargs.get('user_slug')
        self.dictionary_author = get_object_or_404(
            CustomUser.objects.select_related('profile'),
            slug=user_slug
        )

    def get_queryset(self):
        if self.request.user == self.dictionary_author:
            return Dictionary.objects.filter(
                folder__user=self.dictionary_author
            ).select_related(
                'folder',
                'folder__language'
            ).order_by('-created_at')
        else:
            return Dictionary.objects.filter(
                folder__user=self.dictionary_author,
                accessibility='Public'
            ).select_related(
                'folder',
                'folder__language'
            ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        queryset = self.get_queryset()
        dictionaries_filter = DictionariesFilter(
            self.request.GET,
            dictionary_author=self.dictionary_author,
            queryset=queryset,
        )
        context = super().get_context_data(object_list=dictionaries_filter.qs, **kwargs)
        context['dictionary_author'] = self.dictionary_author
        context['filter'] = dictionaries_filter
        return context


class DictionaryDetailView(DetailView, MultipleObjectMixin):
    """
    Detailed view for a specific dictionary.

    Provides comprehensive dictionary details with paginated entries.
    Enforces access permissions based on dictionary accessibility.
    """
    model = Dictionary
    template_name = 'dictionary/dictionary-detail.html'
    context_object_name = 'dictionary'
    slug_url_kwarg = 'dictionary_slug'
    slug_field = 'slug'
    ordering = ('-created_at',)
    paginate_by = 10

    def get_queryset(self):
        user_slug = self.kwargs.get('user_slug')
        folder_slug = self.kwargs.get('folder_slug')

        entries_queryset = (
            DictionaryEntry.objects
            .select_related('dictionary')
            .prefetch_related('meanings')
            .order_by('-created_at')
        )
        prefetch_entries = Prefetch('entries', queryset=entries_queryset)

        return (
            Dictionary.objects
            .select_related('folder', 'folder__user__profile')
            .prefetch_related(prefetch_entries)
            .filter(
                folder__user__slug=user_slug,
                folder__slug=folder_slug
            ).order_by('-created_at')
        )

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        dictionary_slug = self.kwargs.get('dictionary_slug')
        dictionary = get_object_or_404(queryset, slug=dictionary_slug)

        if dictionary.folder.user != self.request.user and dictionary.accessibility != 'Public':
            raise PermissionDenied(_('You do not have permission to view this dictionary.'))

        return dictionary

    def get_context_data(self, **kwargs):
        dictionary = self.object
        entries = dictionary.entries.all()

        entry_filter = DictionaryEntryFilter(self.request.GET, queryset=entries)
        context = super().get_context_data(object_list=entry_filter.qs, **kwargs)
        context['filter'] = entry_filter
        return context


@method_decorator(verified_email_required, name='dispatch')
class DictionaryCreateView(CustomLoginRequiredMixin, CreateView):
    """
    View for creating a new dictionary.

    Requires verified email and user authentication.
    Validates dictionary creation within a specific folder.
    """
    model = Dictionary
    fields = ('name', 'description', 'accessibility')
    template_name = 'dictionary/dictionary-form.html'

    def dispatch(self, request, *args, **kwargs):
        user_slug = kwargs.get('user_slug')
        if user_slug != request.user.slug:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget.attrs['placeholder'] = 'Enter dictionary name'
        form.fields['description'].widget.attrs['placeholder'] = 'Write a short dictionary description...'
        form.fields['accessibility'].label = 'Dictionary visibility:'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'create'
        return context

    def form_valid(self, form):
        try:
            user_slug = self.kwargs.get('user_slug')
            folder_slug = self.kwargs.get('folder_slug')
            folder = DictionaryFolder.objects.get(user__slug=user_slug, slug=folder_slug)
            form.instance.folder = folder

            try:
                return super().form_valid(form)
            except IntegrityError:
                messages.error(self.request, _('A dictionary with that name already exists in the folder.'))
                return self.form_invalid(form)

        except DictionaryFolder.DoesNotExist:
            messages.error(self.request, _('Selected folder does not exist.'))
            return self.form_invalid(form)


@method_decorator(verified_email_required, name='dispatch')
class DictionaryUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating an existing dictionary.

    Requires verified email, user authentication, and ownership.
    Prevents duplicate dictionary names within a folder.
    """
    model = Dictionary
    fields = ('name', 'description', 'accessibility')
    template_name = 'dictionary/dictionary-form.html'
    slug_url_kwarg = 'dictionary_slug'
    slug_field = 'slug'

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            user_slug = self.kwargs.get('user_slug')
            folder_slug = self.kwargs.get('folder_slug')
            dictionary_slug = self.kwargs.get('dictionary_slug')
            self._object = get_object_or_404(
                Dictionary.objects.select_related('folder__user'),
                folder__user__slug=user_slug,
                folder__slug=folder_slug,
                slug=dictionary_slug
            )
        return self._object

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['accessibility'].label = 'Dictionary visibility:'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'update'
        return context

    def form_valid(self, form):
        try:
            folder_slug = self.kwargs.get('folder_slug')
            folder = DictionaryFolder.objects.get(slug=folder_slug)
            form.instance.folder = folder

            try:
                response = super().form_valid(form)
                messages.success(self.request, _('The dictionary has been updated.'))
                return response
            except IntegrityError:
                messages.error(self.request, _('A dictionary with that name already exists in the folder.'))
                return self.form_invalid(form)

        except DictionaryFolder.DoesNotExist:
            messages.error(self.request, _('Selected folder does not exist.'))
            return self.form_invalid(form)

    def test_func(self):
        dictionary = self.get_object()
        return self.request.user == dictionary.folder.user


@method_decorator(verified_email_required, name='dispatch')
class DictionaryDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting a dictionary.

    Requires verified email, user authentication, and ownership.
    Redirects to folder detail page after deletion.
    """
    model = Dictionary
    template_name = 'dictionary/dictionary-confirm-delete.html'
    slug_url_kwarg = 'dictionary_slug'
    slug_field = 'slug'

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            user_slug = self.kwargs.get('user_slug')
            folder_slug = self.kwargs.get('folder_slug')
            dictionary_slug = self.kwargs.get('dictionary_slug')
            self._object = get_object_or_404(
                Dictionary.objects.select_related('folder__user'),
                folder__user__slug=user_slug,
                folder__slug=folder_slug,
                slug=dictionary_slug
            )
        return self._object

    def test_func(self):
        dictionary = self.get_object()
        return self.request.user == dictionary.folder.user

    def get_success_url(self):
        folder_slug = self.kwargs.get('folder_slug')
        return reverse_lazy('dictionaries:folder-detail', kwargs={
            'user_slug': self.request.user.slug,
            'folder_slug': folder_slug
        })


def generate_dictionary_flashcards(request, user_slug, folder_slug, dictionary_slug):
    """
    Generate flashcards for a given dictionary.

    Creates flashcards with configurable front side (word or meaning).
    Shuffles entries for randomized study experience.

    Args:
        request (HttpRequest): Request object.
        user_slug (str): Slug of dictionary owner.
        folder_slug (str): Slug of dictionary's folder.
        dictionary_slug (str): Slug of target dictionary.

    Returns:
        HttpResponse: Rendered flashcards page.
    """
    dictionary = get_object_or_404(Dictionary, folder__user__slug=user_slug,
                                   folder__slug=folder_slug, slug=dictionary_slug)

    if request.method == "POST":
        front_type = request.POST.get('front_type')
        if front_type not in ['word', 'meaning']:
            messages.error(request, _('Invalid front type selected.'))

        entries = dictionary.entries.prefetch_related('meanings').all()
        flashcards = []

        for entry in entries:
            if front_type == 'word':
                front = entry.word
                meanings = [meaning.description for meaning in entry.meanings.all()]
                back = '\n '.join(meanings)
                flashcards.append({'front': front, 'back': back})
            else:
                meanings = [meaning.description for meaning in entry.meanings.all()]
                front = '\n '.join(meanings)
                back = entry.word
                flashcards.append({'front': front, 'back': back})

        random.shuffle(flashcards)

        return render(request, 'dictionary/flashcards.html',
                      {'flashcards': flashcards, 'front_type': front_type})


def download_dictionary_pdf(request, user_slug, folder_slug, dictionary_slug):
    """
    Generate and download a pdf of dictionary entries.

    Renders dictionary entries in a printable PDF format.

    Args:
        request (HttpRequest): HTTP request object.
        user_slug (str): Slug of dictionary owner.
        folder_slug (str): Slug of dictionary's folder.
        dictionary_slug (str): Slug of target dictionary.

    Returns:
        HttpResponse: PDF file download.
    """
    author = get_object_or_404(CustomUser, slug=user_slug)
    dictionary = get_object_or_404(
        Dictionary,
        folder__user__slug=user_slug,
        slug=dictionary_slug
    )
    entries = dictionary.entries.prefetch_related(
        'meanings',
        'examples'
    ).order_by('word', 'created_at')

    # Data to be passed to the template for rendering
    data = {
        'author': author,
        'dictionary': dictionary,
        'entries': entries
    }

    # Render the HTML content for the PDF using a template
    html_content = render_to_string('dictionary/dictionary-pdf.html', data)

    # Generate the PDF from the HTML
    base_url = request.build_absolute_uri('/')
    pdf = HTML(string=html_content, base_url=base_url).write_pdf()
    filename = f'Dictionary {dictionary.name}.pdf'

    # Return the PDF as a response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
