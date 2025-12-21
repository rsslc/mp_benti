import os
import sys

# IMPORTANT: point this at the folder that contains manage.py AND the "core/" package
project_path = "/home/mpbenti/mpbenti"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()