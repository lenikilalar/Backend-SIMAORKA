import os
import sys
import traceback

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'

import django
django.setup()

from apps.rbac.models import Permission

try:
    perm, created = Permission.objects.update_or_create(
        code='TEST_PERM',
        defaults={'name': 'Test Permission', 'description': 'Test'}
    )
    print(f"Created: {created}, Perm: {perm}")
    perm.delete()
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
