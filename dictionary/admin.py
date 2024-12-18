from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import *


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(DictionaryFolder)
class DictionaryFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'user__username', 'user__email', 'language')


@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder', 'folder__user__username')


@admin.register(DictionaryEntry)
class DictionaryEntryAdmin(admin.ModelAdmin):
    list_display = ('word', 'dictionary',
                    'dictionary__folder',
                    'dictionary__folder__user__username')


@admin.register(Meaning)
class MeaningAdmin(admin.ModelAdmin):
    list_display = ('description', 'entry',
                    'target_language', 'entry__dictionary',
                    'entry__dictionary__folder',
                    'entry__dictionary__folder__user')


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ('sentence', 'show_entries')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('entries')

    def show_entries(self, instance):
        return ', '.join([entry.word for entry in instance.entries.all()])

    show_entries.short_description = _('Dictionary Entries')
