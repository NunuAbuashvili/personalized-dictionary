from django.db import models
from django.utils.translation import gettext_lazy as _

from dictionary.models import Language, DictionaryEntry


class ExternalDictionarySource(models.Model):
    name = models.CharField(max_length=255)
    base_url = models.URLField()
    api_key = models.CharField(max_length=255, blank=True, null=True)
    rate_limit = models.PositiveIntegerField(default=1000)
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='external_dictionary_sources')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('External Dictionary Source')
        verbose_name_plural = _('External Dictionary Sources')


class WordDefinition(models.Model):
    entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name='external_dictionary_definitions'
    )
    target_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='external_dictionary_definitions'
    )
    definition = models.TextField()
    source = models.ForeignKey(
        ExternalDictionarySource,
        on_delete=models.CASCADE,
        related_name='external_dictionary_definitions'
    )

    def __str__(self):
        return self.definition

    class Meta:
        verbose_name = _('Word Definition')
        verbose_name_plural = _('Word Definitions')
