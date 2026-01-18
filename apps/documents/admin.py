from django.contrib import admin
from .models import Document, DocumentVersion, DocumentAccessRule


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'status', 'created_at']
    list_filter = ['status', 'requires_nft']
    search_fields = ['title']


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'version_number', 'file_size', 'created_at']


@admin.register(DocumentAccessRule)
class DocumentAccessRuleAdmin(admin.ModelAdmin):
    list_display = ['document', 'role', 'can_view', 'can_edit', 'can_approve']
