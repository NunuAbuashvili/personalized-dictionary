from django.urls import include, path
from rest_framework_nested import routers

from . import views

app_name = 'dictionaries_api'

router = routers.DefaultRouter()
router.register(r'', views.DictionaryFolderViewSet, basename='folder')

folders_router = routers.NestedSimpleRouter(router, r'', lookup='folder')
folders_router.register(r'dictionaries', views.DictionaryViewSet, basename='dictionary')

dictionaries_router = routers.NestedSimpleRouter(folders_router, r'dictionaries', lookup='dictionary')
dictionaries_router.register(r'entries', views.DictionaryEntryViewSet, basename='entry')


urlpatterns = [
    path('folders/', include(router.urls)),
    path('folders/', include(folders_router.urls)),
    path('folders/', include(dictionaries_router.urls)),
    path('search/', views.HomeSearchAPIListView.as_view(), name='search'),
]