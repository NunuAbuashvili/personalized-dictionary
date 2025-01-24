from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault, DateTimeField

from accounts.models import CustomUser
from dictionary.models import *


class MiniCustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for a minimal representation of a custom user.
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email')


class FormattedDateTimeField(DateTimeField):
    """
    Custom DateTime field that formats datetime objects to a specific string representation.

    Formats the datetime as 'DD/MM/YYYY at HH:MM'.
    """
    def to_representation(self, value):
        return value.strftime('%d/%m/%Y at %H:%M')


class LanguageSerializer(serializers.ModelSerializer):
    """
    Serializer for Language model, exposing only the name field.
    """
    class Meta:
        model = Language
        fields = ('name',)


class ExampleSerializer(serializers.ModelSerializer):
    """
    Serializer for Example model, including sentence and source.
    """
    class Meta:
        model = Example
        fields = ('sentence', 'source')


class MeaningSerializer(serializers.ModelSerializer):
    """
    Serializer for dictionary entry meanings.

    Includes description and target language as a slug-related field.
    """
    target_language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
    )

    class Meta:
        model = Meaning
        fields = ('description', 'target_language')


class DictionaryEntrySerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for dictionary entries.

    Includes nested serialization of examples and meanings.
    """
    examples = ExampleSerializer(many=True)
    meanings = MeaningSerializer(many=True)

    class Meta:
        model = DictionaryEntry
        fields = ('id', 'word', 'meanings', 'examples', 'notes', 'image')


class DictionarySerializer(serializers.ModelSerializer):
    """
    Serializer for Dictionary model with nested entries.

    Provides detailed dictionary information including all entries.
    """
    entries = DictionaryEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Dictionary
        fields = ('id', 'name', 'description', 'accessibility', 'entries')


class MiniDictionarySerializer(serializers.ModelSerializer):
    """
    Minimal serializer for Dictionary model.

    Supports custom create and update methods with folder context.
    """
    class Meta:
        model = Dictionary
        fields = ('id', 'name', 'description', 'accessibility')

    def create(self, validated_data: dict) -> Dictionary:
        """
        Create a new dictionary within a specific folder.

        Args:
            validated_data (dict): Validated dictionary data.

        Returns:
            Created Dictionary instance.
        """
        folder = self.context.get('folder')
        dictionary = Dictionary.objects.create(
            folder=folder,
            **validated_data
        )
        return dictionary

    def update(self, instance: Dictionary, validated_data: dict) -> Dictionary:
        """
        Update dictionary with folder context and additional data processing.

        Args:
            instance (Dictionary): Existing Dictionary instance.
            validated_data (dict): Updated dictionary data.

        Returns:
            Updated Dictionary instance.
        """
        folder = self.context.get('folder')
        instance.folder = folder
        instance.name = validated_data.get('name', instance.name).title()
        instance.description = validated_data.get('description', instance.description).capitalize()
        instance.accessibility = validated_data.get('accessibility', instance.accessibility)
        instance.save()
        return instance


class DictionaryFolderSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for DictionaryFolder model.

    Includes nested serialization of language, user, and dictionaries.
    Supports custom create and update methods.
    """
    language = LanguageSerializer()
    user = MiniCustomUserSerializer(read_only=True)
    created_at = FormattedDateTimeField(read_only=True)
    updated_at = FormattedDateTimeField(read_only=True)
    dictionaries = MiniDictionarySerializer(many=True, read_only=True)

    class Meta:
        model = DictionaryFolder
        fields = ('id', 'name', 'user', 'language',
                  'accessibility', 'dictionaries',
                  'created_at', 'updated_at')

    def create(self, validated_data: dict) -> DictionaryFolder:
        """
        Create a new dictionary folder with associated user and language.

        Args:
            validated_data (dict): Validated dictionary folder data.

        Returns:
            Created DictionaryFolder instance.
        """
        request = self.context.get('request')
        language_data = validated_data.pop('language')
        language = Language.objects.filter(
            name=language_data['name']
        ).first()
        folder = DictionaryFolder.objects.create(
            user=request.user,
            language=language,
            **validated_data
        )
        return folder

    def update(self, instance: DictionaryFolder, validated_data: dict) -> DictionaryFolder:
        """
        Update dictionary folder with new data and language.

        Args:
            instance (DictionaryFolder): Existing DictionaryFolder instance.
            validated_data (dict): Updated dictionary folder data.

        Returns:
            Updated DictionaryFolder instance.
        """
        request = self.context.get('request')
        language_data = validated_data.pop('language', None)

        instance.user = request.user
        instance.name = validated_data.get('name', instance.name).title()

        if language_data:
            language = Language.objects.get(name=language_data['name'])
            instance.language = language

        instance.accessibility = validated_data.get('accessibility', instance.accessibility)

        instance.save()
        return instance


class InitiateEntrySerializer(serializers.Serializer):
    """
    Serialization for initiating a dictionary entry with word and language details.

    Validates and processes entry and target languages.
    """
    word = serializers.CharField()
    entry_language = serializers.CharField()
    target_languages = serializers.ListField(
        child=serializers.CharField()
    )

    def validate(self, data: dict) -> dict:
        """
        Validate and clean entry and target languages.

        Removes entry language from target languages, as well as duplicates.

        Args:
            data (dict): Raw input data with entry and target languages.

        Returns:
            Cleaned and processed language data.
        """
        entry_language = data['entry_language'].strip().lower()
        target_languages = [language.lower() for language in data['target_languages']]

        target_languages = set(target_languages)
        target_languages.discard(entry_language)

        data['target_languages'] = [language.title() for language in target_languages]
        data['entry_language'] = entry_language.title()
        return data


class OpenAIResponseSerializer(serializers.Serializer):
    """
    Serializer for processing OpenAI API responses for dictionary entries.

    Handles word definition, translations, and example sentences.
    """
    word = serializers.CharField()
    definition = serializers.ListField(
        child=serializers.DictField()
    )
    translations = serializers.ListField(
        child=serializers.DictField()
    )
    examples = serializers.ListField(
        child=serializers.DictField()
    )


class CreateDictionaryEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating dictionary entries.

    Supports nested creation of meanings and examples with validation.
    """
    meanings = MeaningSerializer(many=True)
    examples = ExampleSerializer(many=True)

    class Meta:
        model = DictionaryEntry
        fields = ('word', 'meanings', 'examples', 'notes', 'image')

    def create(self, validated_data: dict) -> DictionaryEntry:
        """
        Create a new dictionary entry with meanings and examples.

        Validates unique word per user and associates entry with dictionary.

        Args:
            validated_data (dict): Validated entry data.

        Returns:
            Created DictionaryEntry instance.

        Raises:
            ValidationError: If word already exists or dictionary is not found.
        """
        meanings_data = validated_data.pop('meanings', [])
        examples_data = validated_data.pop('examples', [])

        view = self.context.get('view')

        try:
            dictionary = Dictionary.objects.filter(
                folder__pk=view.kwargs.get('folder_pk'),
                pk=view.kwargs.get('dictionary_pk')
            ).first()
        except Dictionary.DoesNotExist:
            raise serializers.ValidationError(_('Dictionary not found.'))

        user = dictionary.folder.user
        word = validated_data.get('word').title()

        if DictionaryEntry.objects.filter(dictionary__folder__user=user, word=word).exists():
            raise serializers.ValidationError(
                _('A dictionary entry with this word already exists in your dictionaries.')
            )

        entry = DictionaryEntry.objects.create(
            dictionary=dictionary,
            **validated_data
        )

        for meaning_data in meanings_data:
            Meaning.objects.create(entry=entry, **meaning_data)

        for example_data in examples_data:
            Example.objects.create(entry=entry, **example_data)

        return entry

    def update(self, instance: DictionaryEntry, validated_data: dict) -> DictionaryEntry:
        """
        Update an existing dictionary entry with new meanings and examples.

        Deletes and recreates nested meanings and examples.

        Args:
            instance (DictionaryEntry): Existing DictionaryEntry to update.
            validated_data (dict): Updated entry data.

        Returns:
            Updated DictionaryEntry instance.
        """
        meanings_data = validated_data.pop('meanings', [])
        examples_data = validated_data.pop('examples', [])

        # Update the main entry fields
        instance.word = validated_data.get('word', instance.word).title()
        instance.notes = validated_data.get('notes', instance.notes)
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        # Handle the nested `meanings` updates
        if meanings_data:
            instance.meanings.all().delete()
            for meaning_data in meanings_data:
                Meaning.objects.create(entry=instance, **meaning_data)

        # Handle the nested `examples` updates
        if examples_data:
            instance.examples.all().delete()
            for example_data in examples_data:
                Example.objects.create(entry=instance, **example_data)

        return instance


class SearchDictionaryEntrySerializer(serializers.ModelSerializer):
    """Serializer for searching dictionary entries."""
    meanings = MeaningSerializer(many=True)
    author = MiniCustomUserSerializer(source='dictionary.folder.user', read_only=True)
    dictionary = serializers.StringRelatedField()

    class Meta:
        model = DictionaryEntry
        fields = ('id', 'word', 'author', 'dictionary', 'meanings')


class FlashcardFrontTypeSerializer(serializers.Serializer):
    """
    Serializer for selecting flashcard front display type.

    Allows choosing between showing the word or its meaning(s).
    """
    front_type = serializers.ChoiceField(
        choices=['word', 'meaning']
    )
