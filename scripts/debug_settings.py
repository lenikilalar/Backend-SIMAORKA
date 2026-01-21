import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    print("Attempting django.setup()...")
    django.setup()
    print("django.setup() successful.")
    print(f"SECRET_KEY: {settings.SECRET_KEY}")
    print(f"AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
    from django.apps import apps
    print("Installed apps:")
    for app in apps.get_app_configs():
        print(f" - {app.name} (label: {app.label})")
except Exception as e:
    print(f"Error during setup: {e}")
    import traceback
    traceback.print_exc()
