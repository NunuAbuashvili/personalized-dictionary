from rest_framework_nested import routers
from django.urls import path, include

from . import views


app_name = 'dictionaries_api'

router = routers.DefaultRouter()
router.register(r'', views.DictionaryFolderViewSet, basename='folder')

folders_router = routers.NestedSimpleRouter(router, r'', lookup='folder')
folders_router.register(r'dictionaries', views.DictionaryViewSet, basename='dictionary')

dictionaries_router = routers.NestedSimpleRouter(folders_router, r'dictionaries', lookup='dictionary')
dictionaries_router.register(r'entries', views.DictionaryEntryViewSet, basename='entry')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(folders_router.urls)),
    path('', include(dictionaries_router.urls)),
]