"""
URL routes for common endpoints (uploads, etc.)
"""

from django.urls import path
from .views import (
    ProfilePhotoUploadView,
    OrgLogoUploadView,
    NewsCoverUploadView,
    FinanceAttachmentUploadView,
    DocumentUploadView,
    GetSignedUrlView,
)

urlpatterns = [
    path('uploads/profile-photo', ProfilePhotoUploadView.as_view(), name='upload_profile_photo'),
    path('uploads/org-logo', OrgLogoUploadView.as_view(), name='upload_org_logo'),
    path('uploads/news-cover', NewsCoverUploadView.as_view(), name='upload_news_cover'),
    path('uploads/finance-attachment', FinanceAttachmentUploadView.as_view(), name='upload_finance_attachment'),
    path('uploads/document', DocumentUploadView.as_view(), name='upload_document'),
    path('uploads/signed-url', GetSignedUrlView.as_view(), name='get_signed_url'),
]
