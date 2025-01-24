from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dictionary.urls', namespace='dictionaries')),
    path('api/', include('dictionary.api.urls', namespace='dictionaries_api')),
    path('leaderboard/', include('leaderboard.urls'), name='leaderboard'),
    path('api/leaderboard/', include('leaderboard.api.urls'), name='leaderboard_api'),
    path('account/', include('accounts.urls', namespace='accounts')),
    path('api/account/', include('accounts.api.urls', namespace='accounts_api')),
    path('api-auth/', include('rest_framework.urls')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
] + debug_toolbar_urls()


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
