"""
PythonAnywhere WSGI Configuration for MP Benti
===============================================

This file should be copied to your PythonAnywhere WSGI configuration file.

Location: /var/www/yourusername_pythonanywhere_com_wsgi.py

Instructions:
1. Go to the PythonAnywhere Web tab
2. Click on the WSGI configuration file link
3. Replace the entire contents with this file
4. Update 'yourusername' with your actual PythonAnywhere username
5. Save and reload your web app
"""

import os
import sys
from pathlib import Path

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Replace 'yourusername' with your actual PythonAnywhere username
PYTHONANYWHERE_USERNAME = 'yourusername'

# Project name (should match your project directory)
PROJECT_NAME = 'mpbenti_site'

# ============================================================================
# DO NOT MODIFY BELOW THIS LINE (unless you know what you're doing)
# ============================================================================

# Build paths
project_home = f'/home/{PYTHONANYWHERE_USERNAME}/{PROJECT_NAME}'

# Add your project directory to sys.path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Load environment variables from .env file
env_file = Path(project_home) / '.env'
if env_file.exists():
    print(f"Loading environment variables from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())
else:
    print(f"Warning: .env file not found at {env_file}")

# Import and configure Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

print(f"✅ WSGI application loaded successfully for {PROJECT_NAME}")

