import random

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
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
from weasyprint import HTML

from accounts.decorators import verified_email_required
from accounts.models import CustomUser
from dictionary.filters import DictionaryFilter, DictionaryFolderFilter
from dictionary.models import DictionaryFolder, DictionaryEntry
from .mixins import CustomLoginRequiredMixin


class FolderListView(ListView):
    """
    A view that lists all dictionary folders for a specific user.

    Displays the folders in descending order of creation date,
    with page pagination.
    """
    model = DictionaryFolder
    template_name = 'dictionary/folders.html'
    context_object_name = 'folders'
    ordering = ('-created_at',)
    paginate_by = 4

    def setup(self, request, *args, **kwargs):
        """
        Sets up the view by determining the folder author based on the `user_slug` argument.
        """
        super().setup(request, *args, **kwargs)
        user_slug = self.kwargs.get('user_slug')
        self.folder_author = get_object_or_404(
            CustomUser.objects.select_related('profile'),
            slug=user_slug
        )

    def get_queryset(self):
        """
        Returns the queryset of dictionary folders for the given user, applying filters
        based on the user's authentication status and folder accessibility.
        """
        if self.request.user == self.folder_author:
            # If the request user is the folder author, return all folders
            return DictionaryFolder.objects.filter(
                user=self.folder_author
            ).select_related('user', 'language').order_by('-created_at')
        else:
            # If the request user is not the folder author, return only public folders
            return DictionaryFolder.objects.filter(
                user=self.folder_author,
                accessibility='Public'
            ).select_related('user', 'language').order_by('-created_at')

    def get_context_data(self, **kwargs) -> dict:
        """
        Adds extra context to the template, including the folder author and filtered folder list.
        """
        queryset = self.get_queryset()
        folders_filter = DictionaryFolderFilter(self.request.GET, queryset=queryset)
        context = super().get_context_data(object_list=folders_filter.qs, **kwargs)
        context['folder_author'] = self.folder_author
        context['filter'] = folders_filter
        return context


class FolderDetailView(DetailView):
    """
    A view that displays the details of a specific dictionary folder.

    Displays folder information and its associated dictionaries.
    """
    model = DictionaryFolder
    template_name = 'dictionary/folder-detail.html'
    context_object_name = 'folder'
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'
    paginate_by = 4

    def get_queryset(self):
        """
        Returns a queryset of dictionary folders with related entries.
        """
        return DictionaryFolder.annotate_all_statistics(
            DictionaryFolder.objects.select_related(
                'user',
                'user__profile'
            )
            .prefetch_related('dictionaries__entries')
        ).order_by('-created_at')

    def get_object(self, queryset=None) -> DictionaryFolder:
        """
        Retrieves the folder object based on the user and folder slugs from the URL.
        If the folder is not public and does not belong to the current user, raises a PermissionDenied error.
        """
        queryset = self.get_queryset()

        user_slug = self.kwargs.get('user_slug')
        folder_slug = self.kwargs.get('folder_slug')

        folder = get_object_or_404(
            queryset,
            user__slug=user_slug,
            slug=folder_slug)

        if folder.user != self.request.user and folder.accessibility != 'Public':
            raise PermissionDenied(_('You do not have permission to view this folder.'))

        return folder

    def get_context_data(self, **kwargs) -> dict:
        """
        Adds extra context to the template, including the dictionary author and filtered dictionary list.
        """
        if self.request.user == self.object.user:
            dictionaries = self.object.dictionaries.all().order_by('-created_at')
        else:
            dictionaries = self.object.dictionaries.filter(
                accessibility='Public'
            ).order_by('-created_at')
        dictionary_filter = DictionaryFilter(
            self.request.GET, queryset=dictionaries
        )
        context = super().get_context_data(object_list=dictionary_filter.qs, **kwargs)
        context['dictionary_author'] = self.object.user
        context['filter'] = dictionary_filter
        return context


@method_decorator(verified_email_required, name='dispatch')
class FolderCreateView(CustomLoginRequiredMixin, CreateView):
    """
    A view for creating a new dictionary folder.

    Only accessible by authenticated users who are the folder owner.
    """
    model = DictionaryFolder
    fields = ('name', 'language', 'accessibility')
    template_name = 'dictionary/folder-form.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Checks if the user slug in the URL matches the current user's slug.
        If not, raises a PermissionDenied exception.
        """
        user_slug = kwargs.get('user_slug')
        if user_slug != request.user.slug:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """
        Customizes the form for folder creation by setting placeholder text
        and queryset for the `language` field and changing the `accessibility` label.
        """
        form = super().get_form(form_class)
        form.fields['name'].widget.attrs['placeholder'] = 'Enter folder name'
        form.fields['language'].empty_label = 'Select language...'
        form.fields['language'].queryset = Language.objects.all()
        form.fields['accessibility'].label = 'Folder visibility:'
        return form

    def get_context_data(self, **kwargs) -> dict:
        """
        Adds context for rendering the folder creation form.
        """
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'create'
        return context

    def form_valid(self, form):
        """
        Validates and processes the form, assigning the current user as the folder owner.
        """
        form.instance.user = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, _('A folder with that name already exists.'))
            return self.form_invalid(form)


@method_decorator(verified_email_required, name='dispatch')
class FolderUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    A view for updating an existing dictionary folder.

    Only accessible by the owner of the folder, whose email address has been verified.
    """
    model = DictionaryFolder
    template_name = 'dictionary/folder-form.html'
    fields = ('name', 'language', 'accessibility')
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'

    def get_form(self, form_class=None):
        """
        Customizes the form for folder update by adjusting the `language` queryset
        and the `accessibility` label.
        """
        form = super().get_form(form_class)
        form.fields['language'].queryset = Language.objects.all()
        form.fields['accessibility'].label = 'Folder visibility:'
        return form

    def get_object(self, queryset=None) -> DictionaryFolder:
        """
        Retrieves the folder object based on the user and folder slugs from the URL.
        """
        if not hasattr(self, '_object'):
            user_slug = self.kwargs.get('user_slug')
            folder_slug = self.kwargs.get('folder_slug')
            self._object = get_object_or_404(
                DictionaryFolder.objects.select_related('user'),
                user__slug=user_slug,
                slug=folder_slug
            )
        return self._object

    def get_context_data(self, **kwargs):
        """
        Adds contexts for rendering the folder update form.
        """
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'update'
        return context

    def form_valid(self, form):
        """
        Validates and processes the form, assigning the current user as the folder owner.
        """
        form.instance.user = self.request.user
        try:
            response = super().form_valid(form)
            messages.success(self.request, _('Folder updated successfully.'))
            return response
        except IntegrityError:
            messages.error(self.request, _('A folder with that name already exists.'))
            return self.form_invalid(form)

    def test_func(self):
        """
        Checks if the current user is the owner of the folder.
        """
        folder = self.get_object()
        return self.request.user == folder.user


@method_decorator(verified_email_required, name='dispatch')
class FolderDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    A view for deleting an existing dictionary folder.

    Only accessible by the owner of the folder, whose email address has been verified.
    """
    model = DictionaryFolder
    template_name = 'dictionary/folder-confirm-delete.html'
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'

    def get_object(self, queryset=None):
        """
        Retrieves the folder object based on the user and folder slug from the URL.
        """
        if not hasattr(self, '_object'):
            user_slug = self.kwargs.get('user_slug')
            folder_slug = self.kwargs.get('folder_slug')
            self._object = get_object_or_404(
                DictionaryFolder.objects.select_related('user'),
                user__slug=user_slug,
                slug=folder_slug
            )
        return self._object

    def test_func(self):
        """
        Checks if the current user is the owner of the folder.
        """
        folder = self.get_object()
        return self.request.user == folder.user

    def get_success_url(self):
        """
        Returns the URL to redirect to after successful folder deletion.
        """
        return reverse_lazy('dictionaries:folder-list', kwargs={'user_slug': self.request.user.slug})


def generate_folder_flashcards(request, user_slug, folder_slug):
    """
    Generates flashcards for a dictionary folder,
    based on selected front type (word or meaning).

    Args:
        request (HttpRequest): The HTTP request object.
        user_slug (str): The slug of the user who owns the folder.
        folder_slug (str): The slug of the folder to generate flashcards for.
    """
    folder = get_object_or_404(DictionaryFolder, user__slug=user_slug, slug=folder_slug)

    if request.method == "POST":
        front_type = request.POST.get('front_type')
        if front_type not in ['word', 'meaning']:
            messages.error(request, _('Invalid front type selected.'))

        entries = DictionaryEntry.objects.filter(
            dictionary__folder__user__slug=user_slug,
            dictionary__folder__slug=folder_slug,
        ).prefetch_related('meanings')

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


def download_folder_pdf(request, user_slug, folder_slug):
    """
    Generates and downloads a PDF file of the entries inside the folder.

    Args:
        request (HttpRequest): The HTTP request object.
        user_slug (str): The slug of the user who owns the folder.
        folder_slug (str): The slug of the folder to download as PDF.
    """
    author = get_object_or_404(CustomUser, slug=user_slug)
    folder = get_object_or_404(
        DictionaryFolder,
        user__slug=user_slug,
        slug=folder_slug
    )
    entries = DictionaryEntry.objects.filter(
        dictionary__folder=folder
    ).prefetch_related(
        'meanings',
        'examples'
    ).order_by(
        'dictionary__name',
        'word'
    )

    # Data to be passed to the template for rendering
    data = {
        'author': author,
        'folder': folder,
        'entries': entries
    }

    # Render the HTML content for the PDF using a template
    html_content = render_to_string('dictionary/folder-pdf.html', data)

    # Generate the PDF from the HTML
    base_url = request.build_absolute_uri('/')
    pdf = HTML(string=html_content, base_url=base_url).write_pdf()
    filename = f'Folder {folder.name}.pdf'

    # Return the PDF as a response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
