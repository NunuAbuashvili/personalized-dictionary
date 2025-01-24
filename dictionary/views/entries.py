import json

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView
)
from openai import OpenAI

from accounts.decorators import verified_email_required
from dictionary.forms import DictionaryEntryForm
from dictionary.models import Dictionary, DictionaryEntry, Example, Language, Meaning
from .mixins import CustomLoginRequiredMixin


def fetch_data_from_openai(entry_word, entry_language, target_languages):
    """
    Fetch data for a word using OpenAI's API.

    Generates dictionary definition, translations, and example sentences
    for a given word in a specific language.

    Args:
        entry_word (str): The word to look up.
        entry_language (str): The language of the word to look up.
        target_languages (list): A list of languages for translation.

    Returns:
        tuple: A tuple containing:
            - definition (str): Word definition
            - translations_data (list): Translations in target languages.
            - examples_data (list): Example sentences.
        Returns None if word is invalid in the given language.
    """
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


class EntryDetailView(DetailView):
    """
    Detailed view for a dictionary entry.

    Retrieves and displays comprehensive information about a specific
    dictionary entry, including associated meanings and examples.
    """
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
    """
    Initial view for creating a new dictionary entry.

    Handles the first step of entry creation, collecting basic
    information like word, language, and translation targets.

    Requires verified email and user authentication.
    """
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
    """
    View for completing dictionary entry creation.

    Retrieves entry data from OpenAI, and allows user to
    review and modify, then saves the complete entry.

    Requires verified email and user authentication.
    """
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
    """
    View for updating an existing dictionary entry.

    Allows entry modifications including word, notes, and image.
    Supports updating meanings and examples.

    Requires verified email, user authentication, and entry ownership.
    """
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

            # Handle meanings
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

            # Handle examples
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
    """
    View for deleting a dictionary entry.

    Provides confirmation and handles entry deletion.

    Requires verified email, user authentication, and entry ownership.
    """
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
