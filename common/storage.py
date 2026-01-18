"""
Storage utilities for SIMAORKA API.
"""

import os
import uuid
from datetime import timedelta
from django.conf import settings
from django.core.files.storage import default_storage


def generate_upload_path(instance, filename, folder='uploads'):
    """
    Generate a unique upload path for files.
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return os.path.join(folder, unique_name)


def get_signed_url(file_path, expiration=3600):
    """
    Generate a signed URL for private file access.
    Only works with S3-compatible storage.
    For local storage, returns the media URL directly.
    """
    if hasattr(default_storage, 'url') and hasattr(default_storage, 'bucket'):
        # S3 storage - generate presigned URL
        try:
            import boto3
            from botocore.config import Config
            
            s3_client = boto3.client(
                's3',
                endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
                config=Config(signature_version='s3v4')
            )
            
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': file_path,
                },
                ExpiresIn=expiration
            )
            return url
        except Exception:
            pass
    
    # Fallback to direct URL
    return default_storage.url(file_path)


def upload_file(file, folder='uploads'):
    """
    Upload a file and return its path.
    """
    path = generate_upload_path(None, file.name, folder)
    saved_path = default_storage.save(path, file)
    return saved_path


def delete_file(file_path):
    """
    Delete a file from storage.
    """
    if default_storage.exists(file_path):
        default_storage.delete(file_path)
        return True
    return False
