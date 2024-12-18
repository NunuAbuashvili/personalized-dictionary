from django.db import models
from django.db.models import UniqueConstraint, Count
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser


class Language(models.Model):
    LANGUAGE_CHOICES = [
        ('English', _('English')),
        ('Georgian', _('Georgian')),
        ('Korean', _('Korean')),
    ]
    name = models.CharField(choices=LANGUAGE_CHOICES, max_length=15)
    slug = models.SlugField(_('slug'), unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')


class DictionaryFolder(models.Model):
    name = models.CharField(_('dictionary folder name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True, allow_unicode=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='folders')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='folders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.language.name})'

    class Meta:
        verbose_name = _('Dictionary Folder')
        verbose_name_plural = _('Dictionary Folders')
        constraints = [
            UniqueConstraint(fields=('user', 'name'), name='unique_folder_per_user')
        ]

    def get_absolute_url(self):
        return reverse(
            'dictionaries:folder-detail',
            kwargs={'folder_slug': self.slug, 'user_slug': self.user.slug}
        )

    @classmethod
    def annotate_all_statistics(cls, queryset):
        return queryset.annotate(
            dictionary_count=Count('dictionaries', distinct=True),
            entry_count=Count('dictionaries__entries', distinct=True),
        )


class Dictionary(models.Model):
    name = models.CharField(_('dictionary name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True, allow_unicode=True)
    description = models.TextField(_('dictionary description'), blank=True, null=True)
    folder = models.ForeignKey(DictionaryFolder, on_delete=models.CASCADE, related_name='dictionaries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Dictionary')
        verbose_name_plural = _('Dictionaries')
        constraints = [
            UniqueConstraint(fields=('folder', 'name'), name='unique_dictionary_per_folder')
        ]

    def get_absolute_url(self):
        return reverse('dictionaries:dictionary-detail', kwargs={
            'user_slug': self.folder.user.slug,
            'folder_slug': self.folder.slug,
            'dictionary_slug': self.slug
        })


class Example(models.Model):
    sentence = models.TextField(_('example sentence'))
    source = models.CharField(_('source'), max_length=120, null=True, blank=True)

    def __str__(self):
        return self.sentence

    class Meta:
        verbose_name = _('Example')
        verbose_name_plural = _('Examples')


class DictionaryEntry(models.Model):
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='entries')
    word = models.CharField(_('dictionary entry'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True, allow_unicode=True)
    examples = models.ManyToManyField(Example, related_name='entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.word)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.word

    class Meta:
        verbose_name = _('Dictionary Entry')
        verbose_name_plural = _('Dictionary Entries')
        constraints = [
            UniqueConstraint(fields=('dictionary', 'word'), name='unique_entry_per_dictionary')
        ]

    def get_absolute_url(self):
        return reverse('dictionaries:entry-detail', kwargs={
            'user_slug': self.dictionary.folder.user.slug,
            'folder_slug': self.dictionary.folder.slug,
            'dictionary_slug': self.dictionary.slug,
            'entry_slug': self.slug,
        })


class Meaning(models.Model):
    entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE, related_name='meanings')
    description = models.TextField(_('word meaning'))
    target_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='meanings')

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = _('Meaning')
        verbose_name_plural = _('Meanings')
