from django.contrib import admin

from .models import ExternalDictionarySource, WordDefinition


@admin.register(ExternalDictionarySource)
class ExternalDictionarySourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url', 'api_key', 'rate_limit', 'language__name')
    list_filter = ('language__name',)


@admin.register(WordDefinition)
class WordDefinitionAdmin(admin.ModelAdmin):
    list_display = ('definition', 'entry__word', 'target_language__name', 'source__name')
