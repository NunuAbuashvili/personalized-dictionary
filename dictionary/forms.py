from celery.bin.control import status
from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser
from .models import DictionaryEntry


class DictionaryEntryForm(forms.ModelForm):
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

    def clean_word(self):
        word = self.cleaned_data['word'].capitalize()
        if self.user_slug:
            if DictionaryEntry.objects.filter(
                    word=word,
                    dictionary__folder__user__slug=self.user_slug
            ).exists():
                raise forms.ValidationError(_('You have already added this word.'))
        return word
