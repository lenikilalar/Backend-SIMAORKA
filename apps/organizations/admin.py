from django.contrib import admin
from .models import Organization, OrganizationMember, Role, Permission, OrganizationRequest

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'is_private')
    search_fields = ('name', 'slug')
    list_filter = ('status', 'is_private')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'status', 'joined_at')
    list_filter = ('organization', 'status')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'scope')
    list_filter = ('scope',)

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(OrganizationRequest)
class OrganizationRequestAdmin(admin.ModelAdmin):
    list_display = ('proposed_name', 'requester_name', 'status', 'created_at')
    list_filter = ('status',)
