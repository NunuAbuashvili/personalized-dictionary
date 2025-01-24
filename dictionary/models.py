from django.db import models
from django.db.models import UniqueConstraint, Count
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser


class Language(models.Model):
    """
    Represents a language with a predefined set of choices and a unique slug.
    """
    LANGUAGE_CHOICES = [
        ('English', _('English')),
        ('Georgian', _('Georgian')),
        ('Korean', _('Korean')),
        ('French', _('French')),
        ('Spanish', _('Spanish')),
        ('German', _('German')),
        ('Mandarin', _('Chinese Simplified')),
    ]
    name = models.CharField(choices=LANGUAGE_CHOICES, max_length=15)
    slug = models.SlugField(_('slug'), unique=True)

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class DictionaryFolder(models.Model):
    """Represents a dictionary folder."""
    ACCESSIBILITY_CHOICES = [
        ('Public', _('Public')),
        ('Private', _('Private')),
    ]
    name = models.CharField(_('dictionary folder name'), max_length=255)
    slug = models.SlugField(_('slug'), allow_unicode=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='folders')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='folders')
    accessibility = models.CharField(choices=ACCESSIBILITY_CHOICES, max_length=10, default='Public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Dictionary Folder')
        verbose_name_plural = _('Dictionary Folders')
        constraints = [
            UniqueConstraint(fields=('user', 'name'), name='unique_folder_per_user'),
            UniqueConstraint(fields=('user', 'slug'), name='unique_slug_per_user'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """
        Returns the URL to view the details of the folder.
        """
        return reverse(
            'dictionaries:folder-detail',
            kwargs={'folder_slug': self.slug, 'user_slug': self.user.slug}
        )

    @classmethod
    def annotate_all_statistics(cls, queryset):
        """
        Annotates the folder queryset with dictionary and entry counts.
        """
        return queryset.annotate(
            dictionary_count=Count('dictionaries', distinct=True),
            entry_count=Count('dictionaries__entries', distinct=True),
        )


class Dictionary(models.Model):
    """Represents a dictionary inside a folder."""
    ACCESSIBILITY_CHOICES = [
        ('Public', _('Public')),
        ('Private', _('Private')),
    ]
    name = models.CharField(_('dictionary name'), max_length=255)
    slug = models.SlugField(_('slug'), allow_unicode=True)
    description = models.TextField(_('dictionary description'), blank=True, null=True)
    folder = models.ForeignKey(DictionaryFolder, on_delete=models.CASCADE, related_name='dictionaries')
    accessibility = models.CharField(choices=ACCESSIBILITY_CHOICES, max_length=10, default='Public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Dictionary')
        verbose_name_plural = _('Dictionaries')
        constraints = [
            UniqueConstraint(fields=('folder', 'name'), name='unique_dictionary_per_folder'),
            UniqueConstraint(fields=('folder', 'slug'), name='unique_slug_per_folder'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """
        Returns the URL to view the details of the dictionary.
        """
        return reverse('dictionaries:dictionary-detail', kwargs={
            'user_slug': self.folder.user.slug,
            'folder_slug': self.folder.slug,
            'dictionary_slug': self.slug
        })


class DictionaryEntry(models.Model):
    """Represents a word entry in a dictionary."""
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE, related_name='entries')
    word = models.CharField(_('dictionary entry'), max_length=255)
    slug = models.SlugField(_('slug'), allow_unicode=True)
    notes = models.TextField(_('entry notes'), blank=True, null=True)
    image = models.ImageField(upload_to='entry_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Dictionary Entry')
        verbose_name_plural = _('Dictionary Entries')
        constraints = [
            UniqueConstraint(fields=('dictionary', 'word'), name='unique_entry_per_dictionary'),
            UniqueConstraint(fields=('dictionary', 'slug'), name='unique_slug_per_dictionary'),
        ]

    def __str__(self):
        return self.word

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.word, allow_unicode=True)
        self.word = self.word.title()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """
        Returns the URL to view the details of the dictionary entry.
        """
        return reverse('dictionaries:entry-detail', kwargs={
            'user_slug': self.dictionary.folder.user.slug,
            'folder_slug': self.dictionary.folder.slug,
            'dictionary_slug': self.dictionary.slug,
            'entry_slug': self.slug,
        })


class Example(models.Model):
    """
    Represents an example sentence associated with a dictionary entry.
    """
    sentence = models.TextField(_('example sentence'))
    source = models.CharField(_('source'), max_length=120, null=True, blank=True)
    entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE, related_name='examples')

    class Meta:
        verbose_name = _('Example')
        verbose_name_plural = _('Examples')

    def __str__(self):
        return self.sentence


class Meaning(models.Model):
    """
    Represents the meaning of a word entry in a specific language.
    """
    entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE, related_name='meanings')
    description = models.TextField(_('word meaning'))
    target_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='meanings')

    class Meta:
        verbose_name = _('Meaning')
        verbose_name_plural = _('Meanings')

    def __str__(self):
        return self.description
