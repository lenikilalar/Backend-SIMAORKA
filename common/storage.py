"""
Storage utilities for SIMAORKA API.
Supports Supabase Storage, S3/MinIO, and local filesystem.
"""

import os
import uuid
import hashlib
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


def generate_upload_path(instance, filename, folder='uploads'):
    """
    Generate a unique upload path for files.
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return os.path.join(folder, unique_name)


def get_file_hash(file):
    """
    Calculate SHA256 hash of a file.
    """
    sha256 = hashlib.sha256()
    for chunk in file.chunks():
        sha256.update(chunk)
    file.seek(0)  # Reset file pointer
    return sha256.hexdigest()


class SupabaseStorage:
    """
    Supabase Storage client for file operations.
    Uses Supabase's S3-compatible API.
    """
    
    def __init__(self):
        self.supabase_url = getattr(settings, 'SUPABASE_URL', '')
        self.supabase_key = getattr(settings, 'SUPABASE_SERVICE_KEY', '')
        self.bucket_name = getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'simaorka')
        
    @property
    def base_url(self):
        return f"{self.supabase_url}/storage/v1"
    
    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.supabase_key}',
            'apikey': self.supabase_key,
        }
    
    def create_bucket(self):
        """
        Create the storage bucket if it doesn't exist.
        """
        url = f"{self.base_url}/bucket"
        try:
            requests.post(
                url, 
                headers=self.headers, 
                json={'name': self.bucket_name, 'id': self.bucket_name, 'public': True}
            )
        except Exception as e:
            pass  # Best effort

    def upload(self, file, path, content_type=None):
        """
        Upload a file to Supabase Storage.
        
        Args:
            file: File object or bytes
            path: Storage path (e.g., 'avatars/user-uuid.jpg')
            content_type: MIME type (auto-detected if not provided)
        
        Returns:
            dict with 'path' and 'url' keys
        """
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not configured")
        
        url = f"{self.base_url}/object/{self.bucket_name}/{path}"
        
        # Read file content
        if hasattr(file, 'read'):
            content = file.read()
            if hasattr(file, 'seek'):
                file.seek(0)
        else:
            content = file
        
        headers = self.headers.copy()
        if content_type:
            headers['Content-Type'] = content_type
        else:
            # Try to detect content type
            headers['Content-Type'] = 'application/octet-stream'
        
        response = requests.post(url, headers=headers, data=content)
        
        # Handle Bucket Not Found -> Create and Retry
        if response.status_code == 404:
            try:
                err_resp = response.json()
                if err_resp.get('message') == 'Bucket not found' or err_resp.get('error') == 'Bucket not found':
                    self.create_bucket()
                    # Retry upload
                    response = requests.post(url, headers=headers, data=content)
            except Exception:
                pass

        if response.status_code in [200, 201]:
            return {
                'path': path,
                'url': self.get_public_url(path),
                'size': len(content)
            }
        else:
            raise Exception(f"Upload failed: {response.text}")
    
    def download(self, path):
        """
        Download a file from Supabase Storage.
        
        Returns:
            File content as bytes
        """
        url = f"{self.base_url}/object/{self.bucket_name}/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Download failed: {response.text}")
    
    def delete(self, path):
        """
        Delete a file from Supabase Storage.
        """
        url = f"{self.base_url}/object/{self.bucket_name}/{path}"
        response = requests.delete(url, headers=self.headers)
        return response.status_code in [200, 204]
    
    def get_public_url(self, path):
        """
        Get the public URL for a file.
        Only works if bucket is public.
        """
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{path}"
    
    def get_signed_url(self, path, expires_in=3600):
        """
        Generate a signed URL for private file access.
        
        Args:
            path: File path in bucket
            expires_in: Seconds until URL expires (default: 1 hour)
        
        Returns:
            Signed URL string
        """
        url = f"{self.base_url}/object/sign/{self.bucket_name}/{path}"
        
        response = requests.post(
            url,
            headers=self.headers,
            json={'expiresIn': expires_in}
        )
        
        if response.status_code == 200:
            data = response.json()
            signed_token = data.get('signedURL', '')
            return f"{self.supabase_url}/storage/v1{signed_token}"
        else:
            raise Exception(f"Failed to generate signed URL: {response.text}")
    
    def list_files(self, prefix='', limit=100, offset=0):
        """
        List files in the bucket.
        
        Args:
            prefix: Path prefix to filter
            limit: Maximum number of files
            offset: Pagination offset
        """
        url = f"{self.base_url}/object/list/{self.bucket_name}"
        
        response = requests.post(
            url,
            headers=self.headers,
            json={
                'prefix': prefix,
                'limit': limit,
                'offset': offset
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"List failed: {response.text}")
    
    def move(self, from_path, to_path):
        """
        Move/rename a file.
        """
        url = f"{self.base_url}/object/move"
        
        response = requests.post(
            url,
            headers=self.headers,
            json={
                'bucketId': self.bucket_name,
                'sourceKey': from_path,
                'destinationKey': to_path
            }
        )
        
        return response.status_code == 200
    
    def copy(self, from_path, to_path):
        """
        Copy a file.
        """
        url = f"{self.base_url}/object/copy"
        
        response = requests.post(
            url,
            headers=self.headers,
            json={
                'bucketId': self.bucket_name,
                'sourceKey': from_path,
                'destinationKey': to_path
            }
        )
        
        return response.status_code == 200


# Global instance
_supabase_storage = None

def get_supabase_storage():
    """Get or create Supabase storage instance."""
    global _supabase_storage
    if _supabase_storage is None:
        _supabase_storage = SupabaseStorage()
    return _supabase_storage


def get_signed_url(file_path, expiration=3600):
    """
    Generate a signed URL for private file access.
    Supports Supabase Storage, S3, and local fallback.
    """
    storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
    
    # Supabase Storage
    if storage_backend == 'supabase':
        try:
            storage = get_supabase_storage()
            return storage.get_signed_url(file_path, expiration)
        except Exception:
            pass
    
    # S3/MinIO Storage
    if hasattr(default_storage, 'bucket'):
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


def upload_file(file, folder='uploads', use_supabase=None):
    """
    Upload a file and return its path.
    
    Args:
        file: Django UploadedFile
        folder: Destination folder
        use_supabase: Force Supabase (None = auto-detect from settings)
    
    Returns:
        dict with path, url, size, and hash
    """
    storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
    
    if use_supabase is None:
        use_supabase = storage_backend == 'supabase'
    
    path = generate_upload_path(None, file.name, folder)
    file_hash = get_file_hash(file)
    
    if use_supabase:
        try:
            storage = get_supabase_storage()
            content_type = getattr(file, 'content_type', None)
            result = storage.upload(file, path, content_type)
            result['hash'] = file_hash
            return result
        except Exception as e:
            # Log error and fallback to default storage
            logger.error(f"Supabase upload failed: {str(e)}")
            logger.error(f"Supabase Config: URL={settings.SUPABASE_URL}, Bucket={settings.SUPABASE_STORAGE_BUCKET}")
            pass
    
    # Default Django storage
    saved_path = default_storage.save(path, file)
    return {
        'path': saved_path,
        'url': default_storage.url(saved_path),
        'size': file.size,
        'hash': file_hash
    }


def delete_file(file_path, use_supabase=None):
    """
    Delete a file from storage.
    """
    storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
    
    if use_supabase is None:
        use_supabase = storage_backend == 'supabase'
    
    if use_supabase:
        try:
            storage = get_supabase_storage()
            return storage.delete(file_path)
        except Exception:
            pass
    
    if default_storage.exists(file_path):
        default_storage.delete(file_path)
        return True
    return False


def get_public_url(file_path):
    """
    Get the public URL for a file (no authentication required).
    Only works for public buckets.
    """
    storage_backend = getattr(settings, 'STORAGE_BACKEND', 'local')
    
    if storage_backend == 'supabase':
        storage = get_supabase_storage()
        return storage.get_public_url(file_path)
    
    return default_storage.url(file_path)
