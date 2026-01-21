import os
import sys
import traceback

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'

try:
    import django
    django.setup()
    with open('debug_output.txt', 'w') as f:
        f.write("Django setup successful!\n")
except Exception as e:
    with open('debug_output.txt', 'w') as f:
        f.write("ERROR:\n")
        f.write(traceback.format_exc())
