from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, RolePermission, Module, UserPermission


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'location', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phone', 'location', 'bio')}),
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'module', 'is_view', 'is_add', 'is_edit', 'is_delete']
    list_filter = ['role', 'module', 'is_view', 'is_add', 'is_edit', 'is_delete']
    search_fields = ['role__name', 'module__module_name']
    fieldsets = (
        ('Role & Module', {
            'fields': ('role', 'module')
        }),
        ('Permissions', {
            'fields': ('is_view', 'is_add', 'is_edit', 'is_delete')
        }),
    )


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['module_name', 'module_url', 'display_order', 'is_menu', 'is_active']
    list_filter = ['is_menu', 'is_active']
    search_fields = ['module_name', 'module_url']
    fieldsets = (
        ('Basic Info', {
            'fields': ('module_name', 'module_url', 'parent')
        }),
        ('Settings', {
            'fields': ('is_menu', 'is_active', 'display_order')
        }),
    )


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'is_view', 'is_add', 'is_edit', 'is_delete']
    list_filter = ['module', 'is_view', 'is_add', 'is_edit', 'is_delete']
    search_fields = ['user__username', 'module__module_name']
    fieldsets = (
        ('User & Module', {
            'fields': ('user', 'module', 'domain_user')
        }),
        ('Permissions', {
            'fields': ('is_view', 'is_add', 'is_edit', 'is_delete')
        }),
    )

