import random

from django.template.loader import render_to_string
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from weasyprint import HTML

from accounts.models import CustomUser
from dictionary.models import Dictionary, DictionaryEntry, DictionaryFolder
from dictionary.views.entries import fetch_data_from_openai
from .filters import *
from .permissions import IsDictionaryAuthorOrReadOnly, IsFolderAuthorOrReadOnly
from .serializers import (
    CreateDictionaryEntrySerializer,
    DictionaryEntrySerializer,
    DictionaryFolderSerializer,
    DictionarySerializer,
    FlashcardFrontTypeSerializer,
    InitiateEntrySerializer,
    MiniDictionarySerializer,
    SearchDictionaryEntrySerializer
)


@extend_schema(tags=['Dictionaries'])
class HomeSearchAPIListView(ListAPIView):
    """
    API view for searching dictionary entries across all dictionaries.

    Provides a paginated list of dictionary entries with
    search and filtering capabilities.
    """
    queryset = DictionaryEntry.objects.select_related(
        'dictionary',
        'dictionary__folder__user'
    ).prefetch_related(
        'meanings',
        'meanings__target_language'
    ).order_by('-created_at')
    serializer_class = SearchDictionaryEntrySerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = HomeEntrySearchFilter


@extend_schema(tags=['Dictionaries'])
class DictionaryFolderViewSet(ModelViewSet):
    """
    ViewSet for managing dictionary folders.

    Supports CRUD operations on dictionary folders with
    additional actions for PDF download and flashcard generation.
    """
    queryset = DictionaryFolder.objects.select_related(
        'user',
        'language'
    ).prefetch_related(
        'dictionaries'
    ).order_by('-created_at')
    serializer_class = DictionaryFolderSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsFolderAuthorOrReadOnly)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DictionaryFolderFilter

    def get_serializer_class(self):
        """
        Dynamically select serializer based on action.

        Returns:
            Serializer class appropriate for current action.
        """
        if self.action == 'generate_folder_flashcards':
            return FlashcardFrontTypeSerializer
        return DictionaryFolderSerializer

    def get_serializer_context(self) -> dict:
        """
        Add request to serializer context.

        Returns:
            Context dictionary with request.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(
        detail=True,
        methods=['get'],
        url_path='pdf',
        permission_classes=(IsAuthenticatedOrReadOnly, IsFolderAuthorOrReadOnly)
    )
    def download_folder_pdf(self, request, *args, **kwargs):
        """
        Generate and download a PDF of all entries in the folder.

        Args:
            request (Request): Incoming hTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns: HTTP Response with PDF attachment.
        """
        folder = self.get_object()
        author = folder.user
        entries = DictionaryEntry.objects.filter(
            dictionary__folder=folder
        ).prefetch_related(
            'meanings',
            'examples'
        ).order_by(
            'dictionary__name',
            'word'
        )

        # Data to be passed to the template for rendering
        data = {
            'author': author,
            'folder': folder,
            'entries': entries
        }

        # Render the HTML content for the PDF using a template
        html_content = render_to_string('dictionary/folder-pdf.html', data)

        # Generate PDF from HTML
        pdf = HTML(string=html_content).write_pdf()
        filename = f'Folder {folder.name}.pdf'

        # Return PDF as a response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(
        detail=True,
        methods=['post'],
        url_path='flashcards',
        permission_classes=(IsAuthenticatedOrReadOnly, IsFolderAuthorOrReadOnly)
    )
    def generate_folder_flashcards(self, request, *args, **kwargs):
        """
        Generate flashcards for all entries in the folder.

        Args:
            request: Incoming HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response with generated flashcards.
        """
        folder = self.get_object()
        front_type = request.data.get('front_type')

        if front_type not in ['word', 'meaning']:
            return Response(
                {'detail': 'Invalid front type selected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        entries = DictionaryEntry.objects.filter(
            dictionary__folder=folder
        ).prefetch_related(
            'meanings'
        )
        flashcards = []

        for entry in entries:
            if front_type == 'word':
                front = entry.word
                meanings = [meaning.description for meaning in entry.meanings.all()]
                back = '\n '.join(meanings)
                flashcards.append({'front': front, 'back': back})
            else:
                meanings = [meaning.description for meaning in entry.meanings.all()]
                front = '\n '.join(meanings)
                back = entry.word
                flashcards.append({'front': front, 'back': back})

        random.shuffle(flashcards)

        return Response(flashcards, status=status.HTTP_200_OK)


@extend_schema(tags=['Dictionaries'])
class DictionaryViewSet(ModelViewSet):
    """
    ViwSet for managing dictionaries within a folder.

    Supports CRUD operations on dictionaries with additional actions
    for PDF download and flashcard generation.
    """
    serializer_class = DictionarySerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsDictionaryAuthorOrReadOnly)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DictionaryFilter

    def get_queryset(self):
        """
        Filter queryset to dictionaries within a specific folder.

        Returns:
            Filtered queryset of dictionaries.
        """
        folder_pk = self.kwargs.get('folder_pk', '')
        return Dictionary.objects.filter(
            folder__pk=folder_pk
        ).select_related(
            'folder__user'
        ).prefetch_related(
            'entries',
            'entries__examples',
            'entries__meanings',
            'entries__meanings__target_language'
        ).order_by('-created_at')

    def dispatch(self, request, *args, **kwargs):
        """
        Cache folder information before dispatching request.

        Args:
            request: Incoming HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            HTTP response
        """
        if hasattr(self, 'kwargs') and 'folder_pk' in self.kwargs:
            folder_pk = self.kwargs['folder_pk']
            request._cached_folder = DictionaryFolder.objects.filter(
                pk=folder_pk
            ).select_related('user').first()
        return super().dispatch(request, *args, **kwargs)

    def get_serializer_class(self):
        """
        Dynamically select serializer based on action.

        Returns:
            Serializer class appropriate for current action.
        """
        if self.action in ['list', 'create']:
            return MiniDictionarySerializer
        if self.action == 'generate_dictionary_flashcards':
            return FlashcardFrontTypeSerializer
        return DictionarySerializer

    def get_serializer_context(self) -> dict:
        """
        Add folder to serializer context.

        Returns:
            Context dictionary with folder.
        """
        context = super().get_serializer_context()
        folder_pk = self.kwargs.get('folder_pk', '')
        folder = DictionaryFolder.objects.filter(pk=folder_pk).first()
        context['folder'] = folder
        return context

    @action(
        detail=True,
        methods=['get'],
        url_path='pdf',
        permission_classes=(IsAuthenticatedOrReadOnly, IsDictionaryAuthorOrReadOnly)
    )
    def download_dictionary_pdf(self, request, *args, **kwargs):
        """
        Generate and download a PDF of all entries in the dictionary.

        Args:
            request: Incoming HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response with PDF attachment.
        """
        dictionary = self.get_object()
        folder_pk = self.kwargs.get('folder_pk', '')
        author = CustomUser.objects.filter(
            folders__pk=folder_pk
        ).first()
        entries = dictionary.entries.all()

        # Data to be passed to the template for rendering
        data = {
            'author': author,
            'dictionary': dictionary,
            'entries': entries
        }

        # Render the HTML content for the PDF using a template
        html_content = render_to_string('dictionary/dictionary-pdf.html', data)

        # Generate PDF from HTML
        pdf = HTML(string=html_content).write_pdf()
        filename = f'Dictionary {dictionary.name}.pdf'

        # Return PDF as a response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(
        detail=True,
        methods=['post'],
        url_path='flashcards',
        permission_classes=(IsAuthenticatedOrReadOnly, IsDictionaryAuthorOrReadOnly)
    )
    def generate_dictionary_flashcards(self, request, *args, **kwargs):
        """
        Generate flashcards for all entries in the dictionary.

        Args:
            request: Incoming HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response with generated flashcards.
        """
        dictionary = self.get_object()
        front_type = request.data.get('front_type')

        if front_type not in ['word', 'meaning']:
            return Response(
                {'detail': 'Invalid front type selected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        entries = dictionary.entries.all()
        flashcards = []

        for entry in entries:
            if front_type == 'word':
                front = entry.word
                meanings = [meaning.description for meaning in entry.meanings.all()]
                back = ', '.join(meanings)
                flashcards.append({'front': front, 'back': back})
            else:
                meanings = [meaning.description for meaning in entry.meanings.all()]
                front = '\n '.join(meanings)
                back = entry.word
                flashcards.append({'front': front, 'back': back})

        random.shuffle(flashcards)

        return Response(flashcards, status=status.HTTP_200_OK)


@extend_schema(tags=['Dictionaries'])
class DictionaryEntryViewSet(ModelViewSet):
    """
    ViewSet for managing dictionary entries within a dictionary.

    Supports CRUD operations on dictionary entries with additional
    actions for entry generation using OpenAI.
    """
    permission_classes = (IsAuthenticatedOrReadOnly, IsDictionaryAuthorOrReadOnly)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DictionaryEntryFilter

    def get_queryset(self):
        """
        Filter queryset to entries within a specific dictionary and folder.

        Returns:
            Filtered queryset of dictionary entries.
        """
        folder_pk = self.kwargs.get('folder_pk', '')
        dictionary_pk = self.kwargs.get('dictionary_pk', '')
        return DictionaryEntry.objects.filter(
            dictionary__pk=dictionary_pk,
            dictionary__folder__pk=folder_pk
        ).select_related(
            'dictionary__folder__user'
        ).prefetch_related(
            'meanings',
            'meanings__target_language',
            'examples'
        ).order_by('-created_at')

    def dispatch(self, request, *args, **kwargs):
        """
        Cache folder information before dispatching request.

        Args:
            request: Incoming HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response.
        """
        if hasattr(self, 'kwargs') and 'folder_pk' in self.kwargs:
            folder_pk = self.kwargs['folder_pk']
            request._cached_folder = DictionaryFolder.objects.filter(
                pk=folder_pk
            ).select_related('user').first()
        return super().dispatch(request, *args, **kwargs)

    def get_serializer_class(self):
        """
        Dynamically select serializer based on action.

        Returns:
            Serializer class appropriate for current action.
        """
        if self.action == 'generate':
            return InitiateEntrySerializer
        if self.action in ['create', 'update']:
            return CreateDictionaryEntrySerializer
        return DictionaryEntrySerializer

    @action(detail=False, methods=['post'])
    def generate(self, request, *args, **kwargs):
        """
        Generate dictionary entry data using OpenAI.

        Args:
            request: Incoming HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HTTP response with generated entry data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        word = serializer.validated_data['word']
        entry_language = serializer.validated_data['entry_language']
        target_languages = serializer.validated_data['target_languages']

        try:
            result = fetch_data_from_openai(word, entry_language, target_languages)

            if result is None:
                return Response(
                    {'error': 'Incorrect instructions. Please check again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            definition, translations, examples = result

            response_data = {
                'word': word,
                'definition': definition,
                'translations': translations,
                'examples': examples
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as error:
            return Response(
                {'error': f'Error generating data: {str(error)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
