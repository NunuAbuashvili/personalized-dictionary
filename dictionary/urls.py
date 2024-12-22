from django.urls import path

from . import views


app_name = 'dictionaries'


urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchResultsView.as_view(), name='search'),
    path('account/profile/<str:user_slug>/folders/', views.FolderListView.as_view(), name='folder-list'),
    path('account/profile/<str:user_slug>/folders/new/', views.FolderCreateView.as_view(), name='folder-create'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/update/',
         views.FolderUpdateView.as_view(), name='folder-update'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/',
         views.FolderDetailView.as_view(), name='folder-detail'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/pdf/',
         views.download_folder_pdf, name='folder-pdf-download'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/flashcards/',
         views.generate_folder_flashcards, name='folder-flashcards'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/delete/',
         views.FolderDeleteView.as_view(), name='folder-delete'),
    path('account/profile/<str:user_slug>/dictionaries/', views.DictionaryListView.as_view(), name='dictionary-list'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/dictionaries/new/',
         views.DictionaryCreateView.as_view(), name='dictionary-create'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/',
         views.DictionaryDetailView.as_view(), name='dictionary-detail'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/pdf/',
         views.download_dictionary_pdf, name='dictionary-pdf-download'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/flashcards/',
         views.generate_dictionary_flashcards, name='dictionary-flashcards'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/update/',
         views.DictionaryUpdateView.as_view(), name='dictionary-update'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/delete/',
         views.DictionaryDeleteView.as_view(), name='dictionary-delete'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/entries/new/',
         views.EntryInitiateView.as_view(), name='initiate-entry'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/entries/new/add',
         views.EntryCreateView.as_view(), name='create-entry'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/',
         views.EntryDetailView.as_view(), name='entry-detail'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/update/',
         views.EntryUpdateView.as_view(), name='entry-update'),
    path('account/profile/<str:user_slug>/folders/<str:folder_slug>/<str:dictionary_slug>/<str:entry_slug>/delete/',
         views.EntryDeleteView.as_view(), name='entry-delete'),
]