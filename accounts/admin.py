from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Admin configuration for CustomUser model."""
    list_display = ('username', 'email', 'is_verified')
    search_fields = ('username', 'email')
    search_help_text = _('Search by username or email')
    list_filter = ('is_verified',)
    ordering = ('email',)

    fieldsets = (
        (_('Account Information'), {
            'fields': ('username', 'email', 'slug', 'password', 'is_active', 'is_verified')
        }),
        (_('Personal Details'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Permissions'), {
            'fields': ('groups', 'user_permissions', 'is_staff', 'is_superuser'),
            'classes': ('collapse',),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for UserProfile model."""
    list_display = ('user', 'user__username', 'country', 'date_of_birth', 'user__is_verified')
    search_fields = ('user', 'user__username', 'country')
    search_help_text = _('Search by user email, username or country')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')
