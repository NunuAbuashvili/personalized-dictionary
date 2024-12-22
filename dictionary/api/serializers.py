from rest_framework import serializers
from rest_framework.fields import DateTimeField
from django.utils.translation import gettext_lazy as _

from dictionary.models import *
from accounts.models import CustomUser


class MiniCustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email')


class FormattedDateTimeField(DateTimeField):
    def to_representation(self, value):
        return value.strftime('%d/%m/%Y at %H:%M')


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('name',)


class ExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Example
        fields = ('sentence', 'source')


class MeaningSerializer(serializers.ModelSerializer):
    target_language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
    )

    class Meta:
        model = Meaning
        fields = ('description', 'target_language')


class DictionaryEntrySerializer(serializers.ModelSerializer):
    examples = ExampleSerializer(many=True)
    meanings = MeaningSerializer(many=True)

    class Meta:
        model = DictionaryEntry
        fields = ('id', 'word', 'meanings', 'examples', 'notes', 'image')


class DictionarySerializer(serializers.ModelSerializer):
    entries = DictionaryEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Dictionary
        fields = ('id', 'name', 'description', 'entries')


class MiniDictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dictionary
        fields = ('id', 'name', 'description')


class DictionaryFolderSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()
    user = MiniCustomUserSerializer(read_only=True)
    created_at = FormattedDateTimeField(read_only=True)
    updated_at = FormattedDateTimeField(read_only=True)
    dictionaries = MiniDictionarySerializer(many=True, read_only=True)

    class Meta:
        model = DictionaryFolder
        fields = ('id', 'name',
                  'user', 'language', 'dictionaries',
                  'created_at', 'updated_at')


class InitiateEntrySerializer(serializers.Serializer):
    word = serializers.CharField()
    entry_language = serializers.CharField()
    target_languages = serializers.ListField(
        child=serializers.CharField()
    )

    def validate(self, data):
        """
        Remove entry language from target languages and remove duplicates.
        """
        entry_language = data['entry_language'].strip().lower()
        target_languages = [language.lower() for language in data['target_languages']]

        target_languages = set(target_languages)
        target_languages.discard(entry_language)

        data['target_languages'] = [language.title() for language in target_languages]
        data['entry_language'] = entry_language.title()
        return data


class OpenAIResponseSerializer(serializers.Serializer):
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
    meanings = MeaningSerializer(many=True)
    examples = ExampleSerializer(many=True)

    class Meta:
        model = DictionaryEntry
        fields = ('word', 'meanings', 'examples', 'notes', 'image')

    def create(self, validated_data):
        meanings_data = validated_data.pop('meanings', [])
        examples_data = validated_data.pop('examples', [])

        view = self.context.get('view')

        try:
            dictionary = Dictionary.objects.filter(
                folder__pk=view.kwargs.get('dictionary_pk'),
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

    def update(self, instance, validated_data):
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
    meanings = MeaningSerializer(many=True)
    author = MiniCustomUserSerializer(source='dictionary.folder.user', read_only=True)
    dictionary = serializers.StringRelatedField()

    class Meta:
        model = DictionaryEntry
        fields = ('id', 'word', 'author', 'dictionary', 'meanings')


class FlashcardFrontTypeSerializer(serializers.Serializer):
    front_type = serializers.ChoiceField(
        choices=['word', 'meaning']
    )
