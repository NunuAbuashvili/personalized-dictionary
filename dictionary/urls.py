from django.urls import path

from . import views


app_name = 'dictionaries'


urlpatterns = [
    path('folders/', views.FolderListView.as_view(), name='folder-list'),
    path('folders/new/', views.FolderCreateView.as_view(), name='folder-create'),
    path('folders/<str:folder_slug>/update/',
         views.FolderUpdateView.as_view(),
         name='folder-update'),
    path('folders/<str:folder_slug>/',
         views.FolderDetailView.as_view(),
         name='folder-detail'),
    path('folders/<str:folder_slug>/delete/',
         views.FolderDeleteView.as_view(),
         name='folder-delete'),
    path('dictionaries/', views.DictionaryListView.as_view(), name='dictionary-list'),
    path('folders/<str:folder_slug>/dictionaries/new/',
         views.DictionaryCreateView.as_view(),
         name='dictionary-create'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/',
         views.DictionaryDetailView.as_view(),
         name='dictionary-detail'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/update/',
         views.DictionaryUpdateView.as_view(),
         name='dictionary-update'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/delete/',
         views.DictionaryDeleteView.as_view(),
         name='dictionary-delete'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/entries/new/',
         views.EntryCreateView.as_view(),
         name='entry-create'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/entries/new/add',
         views.GenerateEntryDataView.as_view(),
         name='generate-entry-data'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/',
         views.EntryDetailView.as_view(), name='entry-detail'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/update/',
         views.EntryUpdateView.as_view(), name='entry-update'),
    path('folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/delete/',
         views.EntryDeleteView.as_view(), name='entry-delete'),
]