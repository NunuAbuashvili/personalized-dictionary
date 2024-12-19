from openai import OpenAI
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (ListView,
                                  DetailView,
                                  CreateView,
                                  UpdateView,
                                  DeleteView, TemplateView)
from django.views.generic.list import MultipleObjectMixin
import json

from accounts.models import CustomUser
from .filters import DictionaryEntryFilter
from .models import (DictionaryFolder,
                     Language,
                     Dictionary,
                     DictionaryEntry,
                     Meaning,
                     Example)


class CustomLoginRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{self.get_login_url()}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)

# Dictionary Folder views (List, Detail, Create, Update, Delete)
class FolderListView(CustomLoginRequiredMixin, ListView):
    model = DictionaryFolder
    template_name = 'dictionary/folders.html'
    context_object_name = 'folders'
    ordering = ('-created_at',)
    paginate_by = 4

    def get_queryset(self):
        user_slug = self.kwargs.get('user_slug')
        user = get_object_or_404(CustomUser, slug=user_slug)
        return (DictionaryFolder.objects.select_related('language')
                .filter(user=user))


class FolderDetailView(CustomLoginRequiredMixin, DetailView):
    model = DictionaryFolder
    template_name = 'dictionary/folder-detail.html'
    context_object_name = 'folder'
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'

    def get_queryset(self):
        return DictionaryFolder.annotate_all_statistics(
            DictionaryFolder.objects.filter(
                slug=self.kwargs.get('folder_slug')
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder = self.get_object()
        dictionaries = folder.dictionaries.all().order_by('-created_at')
        context['dictionaries'] = dictionaries

        return context


class FolderCreateView(CustomLoginRequiredMixin, CreateView):
    model = DictionaryFolder
    fields = ('name', 'language')
    template_name = 'dictionary/folder-form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget.attrs['placeholder'] = 'Enter folder name'
        form.fields['language'].empty_label = 'Select language...'
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


class FolderUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DictionaryFolder
    template_name = 'dictionary/folder-form.html'
    fields = ('name', 'language')
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'update'
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, _('A folder with that name already exists.'))
            return self.form_invalid(form)

    def test_func(self):
        folder = self.get_object()
        if self.request.user == folder.user:
            return True
        return False


class FolderDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DictionaryFolder
    template_name = 'dictionary/folder-confirm-delete.html'
    slug_url_kwarg = 'folder_slug'
    slug_field = 'slug'

    def test_func(self):
        folder = self.get_object()
        if self.request.user == folder.user:
            return True
        return False

    def get_success_url(self):
        return reverse_lazy('dictionaries:folder-list', kwargs={'user_slug': self.request.user.slug})


# Dictionary views (List, Detail, Create, Update, Delete)
class DictionaryListView(CustomLoginRequiredMixin, ListView):
    model = Dictionary
    template_name = 'dictionary/dictionaries.html'
    context_object_name = 'dictionaries'
    ordering = ('-created_at',)
    paginate_by = 4

    def get_queryset(self):
        user_slug = self.kwargs.get('user_slug')
        user = get_object_or_404(CustomUser, slug=user_slug)
        return (Dictionary.objects.select_related('folder', 'folder__language')
                .filter(folder__user=user))


class DictionaryDetailView(CustomLoginRequiredMixin,
                           DetailView,
                           MultipleObjectMixin):
    model = Dictionary
    template_name = 'dictionary/dictionary-detail.html'
    context_object_name = 'dictionary'
    slug_url_kwarg = 'dictionary_slug'
    slug_field = 'slug'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        dictionary = self.get_object()
        entries = dictionary.entries.prefetch_related(
            'meanings',
            'meanings__target_language',
            'examples'
        ).order_by('-created_at')
        entry_filter = DictionaryEntryFilter(self.request.GET, queryset=entries)

        context = super().get_context_data(object_list=entry_filter.qs, **kwargs)
        context['filter'] = entry_filter

        return context


class DictionaryCreateView(CustomLoginRequiredMixin, CreateView):
    model = Dictionary
    fields = ('name', 'description')
    template_name = 'dictionary/dictionary-form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget.attrs['placeholder'] = 'Enter dictionary name'
        form.fields['description'].widget.attrs['placeholder'] = 'Write a short dictionary description...'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'create'
        return context

    def form_valid(self, form):
        try:
            folder_slug = self.kwargs.get('folder_slug')
            folder = DictionaryFolder.objects.get(slug=folder_slug)
            form.instance.folder = folder

            try:
                return super().form_valid(form)
            except IntegrityError:
                messages.error(self.request, _('A dictionary with that name already exists in the folder.'))
                return self.form_invalid(form)

        except DictionaryFolder.DoesNotExist:
            messages.error(self.request, _('Selected folder does not exist.'))
            return self.form_invalid(form)


class DictionaryUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Dictionary
    fields = ('name', 'description')
    template_name = 'dictionary/dictionary-form.html'
    slug_url_kwarg = 'dictionary_slug'
    slug_field = 'slug'

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
                return super().form_valid(form)
            except IntegrityError:
                messages.error(self.request, _('A dictionary with that name already exists in the folder.'))
                return self.form_invalid(form)

        except DictionaryFolder.DoesNotExist:
            messages.error(self.request, _('Selected folder does not exist.'))
            return self.form_invalid(form)

    def test_func(self):
        dictionary = self.get_object()
        if self.request.user == dictionary.folder.user:
            return True
        return False


class DictionaryDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Dictionary
    template_name = 'dictionary/dictionary-confirm-delete.html'
    slug_url_kwarg = 'dictionary_slug'
    slug_field = 'slug'

    def test_func(self):
        dictionary = self.get_object()
        if self.request.user == dictionary.folder.user:
            return True
        return False

    def get_success_url(self):
        folder_slug = self.kwargs.get('folder_slug')
        return reverse_lazy('dictionaries:folder-detail', kwargs={
            'user_slug': self.request.user.slug,
            'folder_slug': folder_slug
        })


# Fetch entry-related data from OpenAI API
def fetch_data_from_openai(entry_word, target_languages):
    client = OpenAI(api_key=settings.OPEN_API_KEY)
    word = entry_word
    languages = target_languages

    prompt = (
        f"Please provide a dictionary definition and example sentences for the word '{word}'. "
        "The definition should be in the word's original language, and translations should **only** be provided "
        f"in the following strict list of languages: {languages}. "
        "This is a strict and exhaustive list of target languages. **Do not** add or include any other languages. "
        "If a translation for a requested language is unavailable, "
        "indicate it explicitly as 'No translation available'.\n\n"
        "References:\n"
        "- For Georgian translations, use this as a reference: https://dictionary.ge/.\n"
        "- For example sentences in Korean, us e this as a reference: https://wordrow.kr/basicn/ko/meaning/.\n\n"
        "Create a total of 6 example sentences in the word's original language, "
        " ensuring they are clear, relevant, and suitable for language learners. "
        "Adjust the complexity of the sentences to match the word's difficulty. "
        "Include:\n"
        "- 2 beginner-level sentences,\n"
        "- 2 intermediate-level sentences,\n"
        "- 2 advanced-level sentences.\n\n"
        "Do not include any formatting markers like ```json or other delimiters. "
        "Create the response strictly as a valid JSON object, ready for parsing.\n\n"
        "Return the response **only** in JSON format as follows:\n\n"
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
    if content.startswith("```json"):
        content = content.lstrip("```json").rstrip("```").strip()

    # Parse content
    data = json.loads(content)
    definition = data['definition'][0]['definition']
    translations_data = data['translations']
    examples_data = data['examples']

    return definition, translations_data, examples_data


# Dictionary Entry views (Detail, Create, Update, Delete)
class EntryDetailView(CustomLoginRequiredMixin, DetailView):
    model = DictionaryEntry
    template_name = 'dictionary/entry-detail.html'
    context_object_name = 'entry'
    slug_url_kwarg = 'entry_slug'
    slug_field = 'slug'


class EntryCreateView(CustomLoginRequiredMixin, CreateView):
    model = DictionaryEntry
    template_name = 'dictionary/entry-form.html'
    fields = ('word',)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['word'].widget.attrs.update({
            'placeholder': 'Enter a word to create entry...',
            'class': 'form-control',
        })
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dictionary_slug = self.kwargs.get('dictionary_slug')
        dictionary = Dictionary.objects.get(slug=dictionary_slug)
        context['languages'] = Language.objects.only('name')
        context['dictionary'] = dictionary
        return context

    def post(self, request, *args, **kwargs):
        dictionary_slug = self.kwargs.get('dictionary_slug')
        dictionary = Dictionary.objects.get(slug=dictionary_slug)
        folder_slug = dictionary.folder.slug
        user_slug = self.kwargs.get('user_slug')
        word = request.POST.get('word', '').strip()
        target_languages = request.POST.get('translation_languages')

        request.session['entry_creation_data'] = {
            'word': word,
            'target_languages': target_languages,
            'user_slug': user_slug,
            'folder_slug': folder_slug,
            'dictionary_slug': dictionary_slug,
        }

        url = reverse('dictionaries:generate-entry-data', kwargs={
            'user_slug': user_slug,
            'folder_slug': folder_slug,
            'dictionary_slug': dictionary_slug,
        })
        return redirect(url)


class GenerateEntryDataView(CustomLoginRequiredMixin, TemplateView):
    template_name = 'dictionary/entry-create-form.html'

    def get(self, request, *args, **kwargs):
        entry_data = request.session.get('entry_creation_data')

        if not entry_data:
            messages.error(request, _('No word data found. Please start again.'))
            return redirect('dictionaries:entry-create',
                            user_slug=entry_data['user_slug'],
                            folder_slug=entry_data['folder_slug'],
                            dictionary_slug=entry_data['dictionary_slug'])

        try:
            word = entry_data['word']
            target_languages = entry_data['target_languages']

            definition, translations, examples = fetch_data_from_openai(word, target_languages)

            context = {
                'word': word,
                'definition': definition,
                'translations': translations,
                'examples': examples,
                'languages': Language.objects.only('name'),
                'user_slug': entry_data['user_slug'],
                'folder_slug': entry_data['folder_slug'],
                'dictionary_slug': entry_data['dictionary_slug'],
            }

            return render(request, self.template_name, context)

        except Exception as error:
            messages.error(request, f'Error generating data: {str(error)}')
            return redirect('dictionaries:entry-create',
                            user_slug=entry_data['user_slug'],
                            folder_slug=entry_data['folder_slug'],
                            dictionary_slug=entry_data['dictionary_slug'])

    def post(self, request, *args, **kwargs):
        try:
            entry_data = request.session.get('entry_creation_data')
            if not entry_data:
                messages.error(request, _('Session expired. Please start again.'))
                return redirect('dictionaries:entry-create',
                                user_slug=entry_data['user_slug'],
                                folder_slug=entry_data['folder_slug'],
                                dictionary_slug=entry_data['dictionary_slug'])

            dictionary_slug = entry_data['dictionary_slug']
            dictionary = Dictionary.objects.get(slug=dictionary_slug)

            entry = DictionaryEntry.objects.create(
                dictionary=dictionary,
                word=entry_data['word']
            )

            definition = request.POST.get('definition', '').strip()
            translations = request.POST.getlist('translations[]')
            translation_languages = request.POST.getlist('translation_languages[]')

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

            meaning_descriptions = request.POST.getlist('meaning_description[]')
            meaning_languages = self.request.POST.getlist('meaning_language[]')

            for description, language_name in zip(meaning_descriptions, meaning_languages):
                if description.strip():
                    language = Language.objects.get(name=language_name)
                    Meaning.objects.create(
                        entry=entry,
                        description=description,
                        target_language=language
                    )

            example_sentences_json = request.POST.get('example_sentences[]', '[]')

            try:
                # Parse the JSON string into a Python list
                example_sentences = json.loads(example_sentences_json)

                # Save each sentence as an Example object
                for sentence_data in example_sentences:
                    sentence = sentence_data['sentence']
                    is_custom = sentence_data['isCustom']

                    if sentence.strip():
                        example = Example.objects.create(
                            sentence=sentence,
                            source='user' if is_custom else 'generated'
                        )
                        entry.examples.add(example)
            except json.JSONDecodeError as error:
                print("Error decoding JSON:", error)

            del request.session['entry_creation_data']

            messages.success(self.request, _('Entry created successfully.'))
            return redirect(entry.get_absolute_url())

        except Dictionary.DoesNotExist:
            messages.error(self.request, _('Selected dictionary does not exist.'))
            return self.get(request, *args, **kwargs)
        except Exception as error:
            messages.error(request, f_('Error creating entry: {str(error)}'))
            return self.get(request, *args, **kwargs)


class EntryUpdateView(CustomLoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DictionaryEntry
    fields = ('word',)
    template_name = 'dictionary/entry-update.html'
    slug_url_kwarg = 'entry_slug'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entry = self.get_object()
        dictionary = self.kwargs.get('dictionary_slug')
        dictionary = Dictionary.objects.get(slug=dictionary)
        context['dictionary'] = dictionary
        context['meanings'] = entry.meanings.all()
        context['examples'] = entry.examples.all()
        context['languages'] = Language.objects.only('name')
        return context

    @transaction.atomic
    def form_valid(self, form):
        try:
            dictionary_slug = self.kwargs.get('dictionary_slug')
            dictionary = Dictionary.objects.get(slug=dictionary_slug)
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
                        source=source.strip()
                    )
                    valid_examples.append(example.id)
                    entry.examples.add(example)

            entry.examples.exclude(id__in=valid_examples).delete()

            # Cleanup orphaned examples
            Example.objects.filter(entries=None).delete()

            messages.success(self.request, _('Entry updated successfully.'))
            try:
                return super().form_valid(form)
            except IntegrityError:
                messages.error(self.request, _('You have already added this word to the dictionary.'))
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
        if self.request.user == entry.dictionary.folder.user:
            return True
        return False


class EntryDeleteView(CustomLoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DictionaryEntry
    template_name = 'dictionary/entry-confirm-delete.html'
    slug_url_kwarg = 'entry_slug'
    slug_field = 'slug'

    def test_func(self):
        entry = self.get_object()
        if self.request.user == entry.dictionary.folder.user:
            return True
        return False

    def get_success_url(self):
        dictionary_slug = self.kwargs.get('dictionary_slug')
        folder_slug = self.kwargs.get('folder_slug')
        return reverse_lazy('dictionaries:dictionary-detail', kwargs={
            'user_slug': self.request.user.slug,
            'folder_slug': folder_slug,
            'dictionary_slug': dictionary_slug,
        })
