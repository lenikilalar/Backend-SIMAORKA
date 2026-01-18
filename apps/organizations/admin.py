from django.contrib import admin
from .models import Organization, OrganizationMember


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

