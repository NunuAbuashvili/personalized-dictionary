from django.urls import path

from .views import dictionaries, entries, folders, home


app_name = 'dictionaries'


urlpatterns = [
    path('', home.HomeView.as_view(), name='home'),
    path('search/', home.SearchResultsView.as_view(), name='search'),
    path('account/profile/<str:user_slug>/folders/', folders.FolderListView.as_view(), name='folder-list'),
    path('account/profile/<str:user_slug>/folders/new/', folders.FolderCreateView.as_view(), name='folder-create'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/update/',
         folders.FolderUpdateView.as_view(), name='folder-update'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/',
         folders.FolderDetailView.as_view(), name='folder-detail'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/pdf/',
         folders.download_folder_pdf, name='folder-pdf-download'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/flashcards/',
         folders.generate_folder_flashcards, name='folder-flashcards'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/delete/',
         folders.FolderDeleteView.as_view(), name='folder-delete'),
    path('account/profile/<str:user_slug>/dictionaries/',
         dictionaries.DictionaryListView.as_view(), name='dictionary-list'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/dictionaries/new/',
         dictionaries.DictionaryCreateView.as_view(), name='dictionary-create'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/',
         dictionaries.DictionaryDetailView.as_view(), name='dictionary-detail'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/pdf/',
         dictionaries.download_dictionary_pdf, name='dictionary-pdf-download'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/flashcards/',
         dictionaries.generate_dictionary_flashcards, name='dictionary-flashcards'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/update/',
         dictionaries.DictionaryUpdateView.as_view(), name='dictionary-update'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/delete/',
         dictionaries.DictionaryDeleteView.as_view(), name='dictionary-delete'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/entries/new/',
         entries.EntryInitiateView.as_view(), name='initiate-entry'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/entries/new/add',
         entries.EntryCreateView.as_view(), name='create-entry'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/',
         entries.EntryDetailView.as_view(), name='entry-detail'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/update/',
         entries.EntryUpdateView.as_view(), name='entry-update'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/delete/',
         entries.EntryDeleteView.as_view(), name='entry-delete'),
]
