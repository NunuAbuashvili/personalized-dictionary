from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from accounts.api.permissions import IsUserProfileOrReadOnly
from dictionary.models import DictionaryFolder, Dictionary, DictionaryEntry
from .filters import DictionaryFolderFilter, DictionaryFilter, DictionaryEntryFilter
from .permissions import IsDictionaryAuthorOrReadOnly
from .serializers import (DictionaryFolderSerializer,
                          DictionarySerializer,
                          MiniDictionarySerializer,
                          CreateDictionaryEntrySerializer,
                          DictionaryEntrySerializer)


@extend_schema(tags=['Dictionaries'])
class DictionaryFolderViewSet(ModelViewSet):
    queryset = (DictionaryFolder.objects.select_related('user')
                .prefetch_related('dictionaries')
                .order_by('-created_at'))
    serializer_class = DictionaryFolderSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsUserProfileOrReadOnly)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DictionaryFolderFilter


@extend_schema(tags=['Dictionaries'])
class DictionaryViewSet(ModelViewSet):
    queryset = (Dictionary.objects.select_related('folder__user')
                .prefetch_related('entries', 'entries__examples',
                                  'entries__meanings','entries__meanings__target_language')
                .order_by('-created_at'))
    serializer_class = DictionarySerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsDictionaryAuthorOrReadOnly)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DictionaryFilter

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return MiniDictionarySerializer
        return DictionarySerializer


@extend_schema(tags=['Dictionaries'])
class DictionaryEntryViewSet(ModelViewSet):
    queryset = DictionaryEntry.objects.prefetch_related(
        'meanings',
        'meanings__target_language',
        'examples'
    ).order_by('-created_at')
    permission_classes = (IsAuthenticatedOrReadOnly, IsDictionaryAuthorOrReadOnly)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = DictionaryEntryFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return CreateDictionaryEntrySerializer
        return DictionaryEntrySerializer
