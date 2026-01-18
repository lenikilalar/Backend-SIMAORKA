from django.contrib import admin
from .models import OrganizationRequest


@admin.register(OrganizationRequest)
class OrganizationRequestAdmin(admin.ModelAdmin):
    list_display = ['proposed_name', 'requester_email', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['proposed_name', 'requester_email']
