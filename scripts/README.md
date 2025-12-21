# Scripts
This directory contains deployment and setup scripts.
## Files
- **entrypoint.sh** - Setup script that runs migrations, creates superuser, and collects static files
- **deploy_pythonanywhere.sh** - PythonAnywhere deployment helper script
- **pythonanywhere_wsgi.py** - WSGI configuration for PythonAnywhere
## Usage
### entrypoint.sh
Run this script after deploying to set up the application:
```bash
bash scripts/entrypoint.sh
```
This will:
1. Run database migrations
2. Create superuser (if environment variables are set)
3. Collect static files
### pythonanywhere_wsgi.py
Copy this to your PythonAnywhere WSGI configuration file and update the paths.
