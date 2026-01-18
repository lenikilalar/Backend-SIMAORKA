"""
Development settings for SIMAORKA project.
"""

from .base import *

DEBUG = True

# Database - use SQLite for dev if DATABASE_URL not set
DATABASES = {
    'default': env.db(default='sqlite:///db.sqlite3'),
}

# Allow all hosts in dev
ALLOWED_HOSTS = ['*']

# CORS - allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Email - console backend for dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Storage - local filesystem for dev
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
