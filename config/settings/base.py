"""
Base Django settings for SIMAORKA project.
"""

from pathlib import Path
import os
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialise environment variables
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# Quick-start development settings
SECRET_KEY = env('SECRET_KEY', default='django-insecure-fallback-key-for-dev')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'drf_spectacular',
    'corsheaders',

    # Local Apps - Core
    'apps.accounts',
    'apps.organizations',
    'apps.rbac',
    
    # Local Apps - Features
    'apps.content',
    'apps.events',
    'apps.finance',
    'apps.communication',
    'apps.notifications',
    'apps.documents',
    'apps.voting',
    'apps.org_requests',
    
    # Local Apps - System
    'apps.audit',
    'apps.adminpanel',
    'apps.web3layer',
]

GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='')


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SIMAORKA API',
    'DESCRIPTION': 'API documentation for Sistem Manajemen Organisasi Kampus',
    'VERSION': '2.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Auth', 'description': 'Authentication endpoints (login, register, Google OAuth, refresh, logout)'},
        {'name': 'Users', 'description': 'User profile and account management'},
        {'name': 'Organizations', 'description': 'Organization CRUD and membership management'},
        {'name': 'RBAC', 'description': 'Role-based access control (roles, permissions)'},
        {'name': 'Announcements', 'description': 'Organization announcements'},
        {'name': 'News', 'description': 'Organization news articles'},
        {'name': 'Events', 'description': 'Organization events and calendar'},
        {'name': 'Finance', 'description': 'Financial transactions and reports'},
        {'name': 'Documents', 'description': 'Document management with versioning'},
        {'name': 'Notifications', 'description': 'User notification management'},
        {'name': 'Voting', 'description': 'Voting sessions and vote casting'},
        {'name': 'OrgRequests', 'description': 'Organization creation requests'},
        {'name': 'Communications', 'description': 'Discussions and chat'},
        {'name': 'Web3', 'description': 'Wallet verification, contracts, Role NFTs'},
        {'name': 'Uploads', 'description': 'File upload endpoints'},
        {'name': 'Admin', 'description': 'Admin panel endpoints (stats, org management)'},
        {'name': 'Audit', 'description': 'Audit log viewing'},
    ],
}

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True

# Web3 Settings (optional feature)
WEB3_ENABLED = env.bool('WEB3_ENABLED', default=False)
WEB3_CHAIN = env('WEB3_CHAIN', default='sepolia')
WEB3_CHAIN_ID = env.int('WEB3_CHAIN_ID', default=11155111)
SEPOLIA_RPC_URL = env('SEPOLIA_RPC_URL', default='')
ROLE_NFT_ADDRESS = env('ROLE_NFT_ADDRESS', default='')
GOV_TOKEN_ADDRESS = env('GOV_TOKEN_ADDRESS', default='')
DUES_CONTRACT_ADDRESS = env('DUES_CONTRACT_ADDRESS', default='')



# Storage Backend: 'local', 's3', or 'supabase'
STORAGE_BACKEND = env('STORAGE_BACKEND', default='local')

# Supabase Settings
SUPABASE_URL = env('SUPABASE_URL', default='')
SUPABASE_ANON_KEY = env('SUPABASE_ANON_KEY', default='')
SUPABASE_SERVICE_KEY = env('SUPABASE_SERVICE_KEY', default='')
SUPABASE_STORAGE_BUCKET = env('SUPABASE_STORAGE_BUCKET', default='simaorka')

# Email Settings
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='SIMAORKA <noreply@simaorka.id>')

# Frontend URL for email links
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')
