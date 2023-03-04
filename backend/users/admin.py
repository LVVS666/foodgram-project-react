from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.actions import delete_selected
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .forms import GroupAdminForm
from .models import Follow

User = get_user_model()

# To use custom model
admin.site.unregister(Group)


@admin.register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_display_links = ('user',)
    list_filter = list_display
    search_fields = ('user__username',)


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    filter_horizontal = ['permissions']
    form = GroupAdminForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    actions = ('block_users', 'unblock_users')
    add_fieldsets = (
        (
            None,
            {
                'classes': (
                    'wide',
                ),
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                    'username',
                    'is_staff',
                    'password1',
                    'password2',
                ),
            },
        ),
    )
    fieldsets = (
        (
            None,
            {
                'classes': (
                    'wide',
                ),
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                    'username',
                    'is_active',
                    'is_superuser',
                    'password'
                ),
            },
        ),
    )
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'date_joined',
        'is_active',
        'is_staff',
        'is_superuser',
    )
    list_display_links = ('username',)
    ordering = ('-id',)
    readonly_fields = ['date_joined', 'is_superuser']
    search_fields = ('email', 'username',)
    delete_selected.short_description = 'Удалить'

    @admin.action(description='Заблокировать')
    def block_users(self, request, queryset):
        """
        Set is_active=False for chosen users.

        If this action made admin over superuser - delete all permissions and
        block request's user.
        """
        if queryset.filter(is_superuser=True).count():
            request.user.is_active = False
            request.user.is_staff = False
            request.user.is_superuser = False
            request.user.save()
            return

        for user in queryset:
            user.is_active = False
            user.save()

    def has_change_permission(self, request, obj=None):
        opts = self.opts
        codename = get_permission_codename('change', opts)
        user_change = request.user.has_perm(f'{opts.app_label}.{codename}')
        if user_change and obj and self.is_user_not_allowed(request.user, obj):
            return False

        return user_change

    def is_user_not_allowed(self, user, obj=None):
        if not user.is_superuser and obj and obj.is_superuser or user == obj:
            return True

        return False

    @admin.action(description='Разблокировать')
    def unblock_users(self, request, queryset):
        """
        Set is_active=True for chosen users. Superusers ingored.
        If this action made admin over superuser or another admin - ignore this
        users.
        """
        queryset = queryset.exclude(is_superuser=True)
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_staff=True, is_superuser=True)

        for user in queryset:
            user.is_active = True
            user.save()
