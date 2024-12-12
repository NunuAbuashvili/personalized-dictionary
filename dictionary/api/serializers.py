from rest_framework import serializers
from rest_framework.fields import DateTimeField
from django.utils.translation import gettext_lazy as _

from dictionary.models import (DictionaryFolder,
                               Dictionary,
                               DictionaryEntry,
                               Language,
                               Example,
                               Meaning)
from accounts.models import CustomUser


class MiniCustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')


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
        fields = ('sentence',)


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
        fields = ('id', 'word', 'meanings', 'examples')


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


class CreateDictionaryEntrySerializer(serializers.ModelSerializer):
    meanings = MeaningSerializer(many=True)
    examples = ExampleSerializer(many=True)

    class Meta:
        model = DictionaryEntry
        fields = ('word', 'meanings', 'examples')

    def create(self, validated_data):
        meanings_data = validated_data.pop('meanings')
        examples_data = validated_data.pop('examples')

        view = self.context.get('view')
        dictionary_id = view.kwargs.get('dictionary_pk')

        try:
            dictionary = Dictionary.objects.get(pk=dictionary_id)
        except Dictionary.DoesNotExist:
            raise serializers.ValidationError(_('Dictionary not found.'))

        entry = DictionaryEntry.objects.create(
            dictionary=dictionary,
            **validated_data
        )

        for meaning_data in meanings_data:
            Meaning.objects.create(
                entry=entry,
                description=meaning_data.get('description'),
                target_language=meaning_data.get('target_language')
            )

        for example_data in examples_data:
            example = Example.objects.create(
                sentence=example_data.get('sentence'),
                source='User generated'
            )
            entry.examples.add(example)

        return entry
