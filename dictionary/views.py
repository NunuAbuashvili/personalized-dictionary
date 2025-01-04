from openai import OpenAI
from weasyprint import HTML

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import (ListView, DetailView,
                                  CreateView, UpdateView,
                                  DeleteView, TemplateView)
from django.views.generic.list import MultipleObjectMixin
import json
import random

from accounts.decorators import verified_email_required
from accounts.models import CustomUser
from .forms import DictionaryEntryForm
from .filters import (DictionaryEntryFilter, DictionaryFolderFilter,
                      DictionariesFilter, DictionaryFilter, HomeEntrySearchFilter)
from .models import (DictionaryFolder, Language,
                     Dictionary, DictionaryEntry,
                     Meaning, Example)


class HomeView(TemplateView):
    template_name = 'dictionary/home.html'


class SearchResultsView(ListView):
    model = DictionaryEntry
    template_name = 'dictionary/search-results.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        queryset = DictionaryEntry.objects.select_related(
            'dictionary', 'dictionary__folder__user'
        ).prefetch_related('meanings').order_by('word')
        entry_filter = HomeEntrySearchFilter(self.request.GET, queryset=queryset)
        return entry_filter.qs


class CustomLoginRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{self.get_login_url()}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)


# Dictionary Folder views (List, Detail, Create, Update, Delete)
class FolderListView(ListView):
    model = DictionaryFolder
    template_name = 'dictionary/folders.html'
    context_object_name = 'folders'
    ordering = ('-created_at',)
    paginate_by = 4

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        user_slug = self.kwargs.get('user_slug')
        self.folder_author = get_object_or_404(
            CustomUser.objects.select_related('profile'),
            slug=user_slug
        )

    def get_queryset(self):
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

    def get_context_data(self, **kwargs):
        queryset = self.get_queryset()
        folders_filter = DictionaryFolderFilter(self.request.GET, queryset=queryset)
        context = super().get_context_data(object_list=folders_filter.qs, **kwargs)
        context['folder_author'] = self.folder_author
        context['filter'] = folders_filter
        return context


class FolderDetailView(DetailView):
    model = DictionaryFolder
    template_name = 'dictionary/folder-detail.html'
    context_object_name = 'folder'
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'
    paginate_by = 4

    def get_queryset(self):
        return DictionaryFolder.annotate_all_statistics(
            DictionaryFolder.objects.select_related(
                'user',
                'user__profile'
            )
            .prefetch_related('dictionaries__entries')
        ).order_by('-created_at')

    def get_object(self, queryset=None):
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

    def get_context_data(self, **kwargs):
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
    model = DictionaryFolder
    fields = ('name', 'language', 'accessibility')
    template_name = 'dictionary/folder-form.html'

    def dispatch(self, request, *args, **kwargs):
        user_slug = kwargs.get('user_slug')
        if user_slug != request.user.slug:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget.attrs['placeholder'] = 'Enter folder name'
        form.fields['language'].empty_label = 'Select language...'
        form.fields['language'].queryset = Language.objects.all()
        form.fields['accessibility'].label = 'Folder visibility:'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'create'
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, _('A folder with that name already exists.'))
            return self.form_invalid(form)


@method_decorator(verified_email_required, name='dispatch')
class FolderUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DictionaryFolder
    template_name = 'dictionary/folder-form.html'
    fields = ('name', 'language', 'accessibility')
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['language'].queryset = Language.objects.all()
        form.fields['accessibility'].label = 'Folder visibility:'
        return form

    def get_object(self, queryset=None):
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
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'update'
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            response = super().form_valid(form)
            messages.success(self.request, _('Folder updated successfully.'))
            return response
        except IntegrityError:
            messages.error(self.request, _('A folder with that name already exists.'))
            return self.form_invalid(form)

    def test_func(self):
        folder = self.get_object()
        return self.request.user == folder.user


@method_decorator(verified_email_required, name='dispatch')
class FolderDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DictionaryFolder
    template_name = 'dictionary/folder-confirm-delete.html'
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'

    def get_object(self, queryset=None):
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
        folder = self.get_object()
        return self.request.user == folder.user

    def get_success_url(self):
        return reverse_lazy('dictionaries:folder-list', kwargs={'user_slug': self.request.user.slug})


# Dictionary views (Detail, Create, Update, Delete)
class DictionaryListView(ListView):
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


# Fetch entry-related data from OpenAI API
def fetch_data_from_openai(entry_word, entry_language, target_languages):
    client = OpenAI(api_key=settings.OPEN_API_KEY)
    word = entry_word
    language = entry_language
    languages = target_languages

    prompt = (
        f"Please check if the word '{word}' is in language '{language}'. "
        f"If the word '{word}' does **not** belong to the language '{language}', "
        "return **only** this message: 'Incorrect Instructions'."
        "If it does belong, proceed with the following steps:\n"
        f"Please provide a dictionary definition and example sentences for the word '{word}'. "
        f"The word is in {language}. If the word is valid in {language}, then the definition should be in "
        "the word's original language, and translations should **only** be provided in the "
        f"following strict list of languages: {languages}. "
        "This is a strict and exhaustive list of target languages. **Do not** add or include any other languages. "
        "If a translation for a requested language is unavailable, "
        "indicate it explicitly as 'No translation available'.\n\n"
        "References:\n"
        "- For Georgian translations, use this as a reference: https://dictionary.ge/.\n"
        "- For example sentences in Korean, use this as a reference: https://wordrow.kr/basicn/ko/meaning/.\n\n"
        "Create a total of 6 example sentences in the word's original language, "
        "ensuring they are clear, relevant, and suitable for language learners. "
        "Adjust the complexity of the sentences to match the word's difficulty. "
        "Include:\n"
        "- 2 beginner-level sentences,\n"
        "- 2 intermediate-level sentences,\n"
        "- 2 advanced-level sentences.\n\n"
        "Do not include any formatting markers like ```json or other delimiters. "
        "Do **not** include any text before or after the JSON."
        "Create the response strictly as a valid JSON object, ready for parsing, in the format as follows:\n\n"
        "{\n"
        '  "word": "{word}",\n'
        '  "definition": [\n'
        '    {"language": "{language}", "definition": "{definition}"},\n'
        "  ],\n"
        '  "translations": [\n'
        '    {"language": "{language1}", "translation": "{translation1}"},\n'
        '    {"language": "{language2}", "translation": "{translation2}"}\n'
        "  ],\n"
        '  "examples": [\n'
        '    {"sentence": "{example1}"},\n'
        '    {"sentence": "{example2}"},\n'
        '    {"sentence": "{example3}"},\n'
        '    {"sentence": "{example4}"},\n'
        '    {"sentence": "{example5}"},\n'
        '    {"sentence": "{example6}"},\n'
        "  ]\n"
        "}"
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
    )

    content = completion.choices[0].message.content
    if content.startswith('Incorrect'):
        return None
    if content.startswith("```json"):
        content = content.lstrip("```json").rstrip("```").strip()

    # Parse content
    data = json.loads(content)
    definition = data['definition'][0]['definition']
    translations_data = data['translations']
    examples_data = data['examples']

    return definition, translations_data, examples_data


# Dictionary Entry views (Detail, Create, Update, Delete)
class EntryDetailView(DetailView):
    model = DictionaryEntry
    template_name = 'dictionary/entry-detail.html'
    context_object_name = 'entry'
    slug_url_kwarg = 'entry_slug'
    slug_field = 'slug'

    def get_object(self, queryset=None):
        user_slug = self.kwargs.get('user_slug')
        folder_slug = self.kwargs.get('folder_slug')
        dictionary_slug = self.kwargs.get('dictionary_slug')

        return get_object_or_404(
            DictionaryEntry.objects.select_related(
                'dictionary',
                'dictionary__folder__user__profile'
            ).prefetch_related(
                'meanings',
                'meanings__target_language',
                'examples'
            ),
            dictionary__folder__user__slug=user_slug,
            dictionary__folder__slug=folder_slug,
            dictionary__slug=dictionary_slug,
            slug=self.kwargs.get('entry_slug'),
        )


@method_decorator(verified_email_required, name='dispatch')
class EntryInitiateView(CustomLoginRequiredMixin, CreateView):
    model = DictionaryEntry
    template_name = 'dictionary/entry-form.html'
    form_class = DictionaryEntryForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_slug = self.kwargs.get('user_slug')
        folder_slug = self.kwargs.get('folder_slug')
        dictionary_slug = self.kwargs.get('dictionary_slug')
        dictionary = Dictionary.objects.get(
            folder__user__slug=user_slug,
            folder__slug=folder_slug,
            slug=dictionary_slug
        )
        context['languages'] = Language.objects.only('name')
        context['dictionary'] = dictionary
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_slug'] = self.kwargs.get('user_slug')
        return kwargs

    def form_valid(self, form):
        user_slug = self.kwargs.get('user_slug')
        folder_slug = self.kwargs.get('folder_slug')
        dictionary_slug = self.kwargs.get('dictionary_slug')
        dictionary = Dictionary.objects.get(
            folder__user__slug=user_slug,
            folder__slug=folder_slug,
            slug=dictionary_slug
        )

        word = form.cleaned_data['word']
        entry_language = form.cleaned_data['entry_language'],
        entry_language = entry_language[0]
        target_languages = form.cleaned_data['target_languages'],
        target_languages = target_languages[0]

        # Store data in session for further processing
        self.request.session['entry_creation_data'] = {
            'word': word,
            'target_languages': ', '.join(target_languages),
            'entry_language': entry_language,
            'user_slug': user_slug,
            'folder_slug': folder_slug,
            'dictionary_slug': dictionary_slug,
        }

        # Redirect to the next step
        url = reverse('dictionaries:create-entry', kwargs={
            'user_slug': user_slug,
            'folder_slug': folder_slug,
            'dictionary_slug': dictionary_slug,
        })
        return redirect(url)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'Translation Languages: {str(error)}')
        return super().form_invalid(form)


@method_decorator(verified_email_required, name='dispatch')
class EntryCreateView(CustomLoginRequiredMixin, CreateView):
    model = DictionaryEntry
    fields = ('notes', 'image')
    template_name = 'dictionary/entry-create-form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['notes'].widget.attrs.update({
            'cols': '21',
            'rows': '7',
        })
        return form

    def get(self, request, *args, **kwargs):
        entry_data = request.session.get('entry_creation_data')

        if not entry_data:
            messages.error(request, _('No word data found. Please start again.'))
            return redirect('dictionaries:initiate-entry',
                            user_slug=kwargs.get('user_slug'),
                            folder_slug=kwargs.get('folder_slug'),
                            dictionary_slug=kwargs.get('dictionary_slug'))

        try:
            # Extract data from session
            word = entry_data['word']
            entry_language = entry_data['entry_language']
            target_languages = entry_data['target_languages']

            result = fetch_data_from_openai(word, entry_language, target_languages)

            if result is None:
                messages.error(request, _('Incorrect instructions. Please, check again.'))
                return redirect('dictionaries:initiate-entry',
                                user_slug=entry_data['user_slug'],
                                folder_slug=entry_data['folder_slug'],
                                dictionary_slug=entry_data['dictionary_slug'])

            definition, translations, examples = result
            form = self.get_form()

            context = {
                'form': form,
                'word': word,
                'definition': definition,
                'translations': translations,
                'examples': examples,
                'languages': [language[0] for language in Language.LANGUAGE_CHOICES],
                'user_slug': entry_data['user_slug'],
                'folder_slug': entry_data['folder_slug'],
                'dictionary_slug': entry_data['dictionary_slug'],
            }

            return render(request, self.template_name, context)

        except Exception as error:
            messages.error(request, f'Error generating data: {str(error)}')
            return redirect('dictionaries:initiate-entry',
                            user_slug=entry_data['user_slug'],
                            folder_slug=entry_data['folder_slug'],
                            dictionary_slug=entry_data['dictionary_slug'])

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = self.get_form()

        try:
            with transaction.atomic():
                entry_data = request.session.get('entry_creation_data')
                if not entry_data:
                    messages.error(request, _('Session expired. Please start again.'))
                    return redirect('dictionaries:initiate-entry',
                                    user_slug=entry_data['user_slug'],
                                    folder_slug=entry_data['folder_slug'],
                                    dictionary_slug=entry_data['dictionary_slug'])

                dictionary = Dictionary.objects.get(
                    folder__user__slug=entry_data['user_slug'],
                    folder__slug=entry_data['folder_slug'],
                    slug=entry_data['dictionary_slug']
                )

                # Save the entry with the image
                entry = form.save(commit=False)
                entry.dictionary = dictionary
                entry.word = entry_data['word']
                if request.FILES.get('image'):
                    entry.image = request.FILES['image']
                entry.save()

                # Create meanings
                definition = request.POST.get('definition', '').strip()
                translations = request.POST.getlist('translations[]')
                translation_languages = request.POST.getlist('translation_languages[]')
                meanings = request.POST.getlist('meaning_description[]')
                meaning_languages = request.POST.getlist('meaning_language[]')

                if definition:
                    Meaning.objects.create(
                        entry=entry,
                        description=definition,
                        target_language=entry.dictionary.folder.language,
                    )

                for language, translation in zip(translation_languages, translations):
                    if language and translation:
                        target_language = Language.objects.get(name=language)
                        Meaning.objects.create(
                            entry=entry,
                            description=translation,
                            target_language=target_language,
                        )

                for language, description in zip(meaning_languages, meanings):
                    if language and description:
                        Meaning.objects.create(
                            entry=entry,
                            description=description,
                            target_language=Language.objects.get(name=language)
                        )

                # Handle example sentences
                example_sentences_json = request.POST.get('example_sentences[]', '[]')
                try:
                    example_sentences = json.loads(example_sentences_json)
                    for sentence_data in example_sentences:
                        if sentence_data['sentence'].strip():
                            Example.objects.create(
                                sentence=sentence_data['sentence'],
                                source='user' if sentence_data['isCustom'] else 'generated',
                                entry=entry
                            )
                except json.JSONDecodeError as error:
                    print("Error decoding JSON:", error)

                del request.session['entry_creation_data']
                messages.success(request, _('Entry created successfully.'))
                return redirect(entry.get_absolute_url())

        except Exception as error:
            messages.error(request, f'Error creating entry: {str(error)}')
            context = {
                'form': form,
                'word': entry_data.get('word', ''),
                'definition': request.POST.get('definition', ''),
                'translations': request.POST.getlist('translations[]', []),
                'examples': json.loads(request.POST.get('example_sentences[]', '[]')),
                'languages': [language[0] for language in Language.LANGUAGE_CHOICES],
                'user_slug': entry_data.get('user_slug', ''),
                'folder_slug': entry_data.get('folder_slug', ''),
                'dictionary_slug': entry_data.get('dictionary_slug', ''),
            }
            return render(request, self.template_name, context)


@method_decorator(verified_email_required, name='dispatch')
class EntryUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DictionaryEntry
    fields = ('word', 'notes', 'image')
    template_name = 'dictionary/entry-update.html'
    slug_url_kwarg = 'entry_slug'
    slug_field = 'slug'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['image'].widget = forms.FileInput(attrs={
            'accept': 'image/*',
            'id': 'id_image',
            'class': 'form-control',
        })
        return form

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            user_slug = self.kwargs.get('user_slug')
            folder_slug = self.kwargs.get('folder_slug')
            dictionary_slug = self.kwargs.get('dictionary_slug')

            self._object = get_object_or_404(
                DictionaryEntry.objects.select_related(
                    'dictionary__folder__user',
                    'dictionary__folder__language'
                ).prefetch_related(
                    'meanings',
                    'meanings__target_language',
                    'examples'
                ),
                dictionary__folder__user__slug=user_slug,
                dictionary__folder__slug=folder_slug,
                dictionary__slug=dictionary_slug,
                slug=self.kwargs.get('entry_slug'),
            )
        return self._object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entry = self.get_object()
        dictionary = Dictionary.objects.get(
            folder__user__slug=self.kwargs.get('user_slug'),
            folder__slug=self.kwargs.get('folder_slug'),
            slug=self.kwargs.get('dictionary_slug')
        )
        languages = [language[0] for language in Language.LANGUAGE_CHOICES]
        context['dictionary'] = dictionary
        context['meanings'] = entry.meanings.all()
        context['examples'] = entry.examples.all()
        context['languages'] = languages
        return context

    @transaction.atomic
    def form_valid(self, form):
        try:
            dictionary = Dictionary.objects.get(
                folder__user__slug=self.kwargs.get('user_slug'),
                folder__slug=self.kwargs.get('folder_slug'),
                slug=self.kwargs.get('dictionary_slug')
            )
            form.instance.dictionary = dictionary

            entry = form.save()

            meaning_descriptions = self.request.POST.getlist('meaning_description[]')
            meaning_languages = self.request.POST.getlist('meaning_language[]')
            valid_meanings = []

            for description, language_name in zip(meaning_descriptions, meaning_languages):
                if description.strip():
                    language = Language.objects.get(name=language_name)
                    meaning, created = Meaning.objects.get_or_create(
                        entry=entry,
                        description=description,
                        target_language=language,
                    )
                    valid_meanings.append(meaning.id)

            entry.meanings.exclude(id__in=valid_meanings).delete()

            example_sentences = self.request.POST.getlist('example_sentence[]')
            example_sources = self.request.POST.getlist('example_source[]')
            valid_examples = []

            for sentence, source in zip(example_sentences, example_sources):
                if sentence.strip():
                    example, created = Example.objects.get_or_create(
                        sentence=sentence.strip(),
                        source=source.strip(),
                        entry=entry,
                    )
                    valid_examples.append(example.id)

            entry.examples.exclude(id__in=valid_examples).delete()

            messages.success(self.request, _('Entry updated successfully.'))
            try:
                return super().form_valid(form)
            except IntegrityError:
                messages.error(self.request, _('You have already added this word.'))
                return self.form_invalid(form)

        except Dictionary.DoesNotExist:
            messages.error(self.request, _('Selected dictionary does not exist.'))
            return self.form_invalid(form)
        except Language.DoesNotExist:
            messages.error(self.request, _('One of the selected languages does not exist.'))
            return self.form_invalid(form)
        except json.JSONDecodeError:
            messages.error(self.request, _('Invalid example sentences format.'))
            return self.form_invalid(form)

    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.dictionary.folder.user


@method_decorator(verified_email_required, name='dispatch')
class EntryDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DictionaryEntry
    template_name = 'dictionary/entry-confirm-delete.html'
    slug_url_kwarg = 'entry_slug'
    slug_field = 'slug'

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            user_slug = self.kwargs.get('user_slug')
            folder_slug = self.kwargs.get('folder_slug')
            dictionary_slug = self.kwargs.get('dictionary_slug')

            self._object = get_object_or_404(
                DictionaryEntry.objects.select_related(
                    'dictionary__folder__user',
                ),
                dictionary__folder__user__slug=user_slug,
                dictionary__folder__slug=folder_slug,
                dictionary__slug=dictionary_slug,
                slug=self.kwargs.get('entry_slug'),
            )
        return self._object

    def test_func(self):
        entry = self.get_object()
        return self.request.user == entry.dictionary.folder.user

    def get_success_url(self):
        dictionary_slug = self.kwargs.get('dictionary_slug')
        folder_slug = self.kwargs.get('folder_slug')
        return reverse_lazy('dictionaries:dictionary-detail', kwargs={
            'user_slug': self.request.user.slug,
            'folder_slug': folder_slug,
            'dictionary_slug': dictionary_slug,
        })


# Flashcards (Folder Flashcards, Dicitonary Flashcards)
def generate_folder_flashcards(request, user_slug, folder_slug):
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


def generate_dictionary_flashcards(request, user_slug, folder_slug, dictionary_slug):
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


def download_folder_pdf(request, user_slug, folder_slug):
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
