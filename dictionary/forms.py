from celery.bin.control import status
from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser
from .models import DictionaryEntry, Language


class DictionaryEntryForm(forms.ModelForm):
    """
    Form for creating dictionary entries with language validation.

    Ensures that the word being added is unique to the user and validates
    that the entry language is not included in the target translation languages.
    """
    entry_language = forms.ChoiceField(choices=Language.LANGUAGE_CHOICES)
    target_languages = forms.MultipleChoiceField(
        choices=Language.LANGUAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox-input',
        })
    )

    class Meta:
        model = DictionaryEntry
        fields = ('word',)

    def __init__(self, *args, **kwargs):
        self.user_slug = kwargs.pop('user_slug', None)
        super(DictionaryEntryForm, self).__init__(*args, **kwargs)
        self.fields['word'].widget.attrs.update({
            'placeholder': 'Enter a word to create entry...',
            'class': 'form-control',
        })
        self.fields['entry_language'].widget.attrs.update({
            'class': 'form-control'
        })

    def clean_word(self) -> str:
        """
        Validates the 'word' field to ensure the word is unique for the user.

        Returns:
            str: The cleaned word.

        Raises:
            ValidationError: If the word already exists for the user.
        """
        word = self.cleaned_data['word'].capitalize()
        if self.user_slug:
            if DictionaryEntry.objects.filter(
                    word=word,
                    dictionary__folder__user__slug=self.user_slug
            ).exists():
                raise forms.ValidationError(_('You have already added this word.'))
        return word

    def clean_target_languages(self) -> list:
        """
        Validated that the target languages do not include the entry language.

        Returns:
            list: The cleaned list of target languages.

        Raises:
            ValidationError: If the entry is in the target languages.
        """
        target_languages = self.cleaned_data['target_languages']
        entry_language = self.cleaned_data.get('entry_language')

        if entry_language in target_languages:
            raise forms.ValidationError(
                _('Translation language cannot be the same as entry language.')
            )

        return target_languages
