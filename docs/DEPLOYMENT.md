# PythonAnywhere Deployment Guide

This guide will help you deploy the MP Benti wholesale ordering platform to PythonAnywhere.

## Prerequisites

1. A [PythonAnywhere account](https://www.pythonanywhere.com/) (Free tier available, or Hacker plan at ~$7 AUD/month for custom domains)
2. Your code pushed to a GitHub repository (or you can upload directly)

## Cost Estimate

- **Free (Beginner) account**: Limited - Good for testing
- **Hacker account ($5 USD/month)**: Recommended - Includes custom domain support
- **Web Developer ($12 USD/month)**: For higher traffic and multiple sites

## Deployment Steps

### 1. Sign Up and Open a Bash Console

1. Create an account at [PythonAnywhere](https://www.pythonanywhere.com/)
2. Once logged in, go to the **"Consoles"** tab
3. Start a new **Bash console**

### 2. Clone Your Repository

In the Bash console:

```bash
# Clone your repository
git clone https://github.com/yourusername/mpbenti_site.git
cd mpbenti_site

# Or if you prefer to upload files directly, you can use the Files tab
```

### 3. Create a Virtual Environment

```bash
# Create a Python 3.11 virtual environment
mkvirtualenv mpbenti --python=/usr/bin/python3.11

# The virtualenv will be created at: ~/.virtualenvs/mpbenti
# It will be automatically activated
```

### 4. Install Dependencies

```bash
# Make sure you're in the project directory and virtualenv is active
cd ~/mpbenti_site
pip install -r requirements.txt
```

### 5. Set Up Environment Variables

Create a `.env` file in your project root:

```bash
nano ~/mpbenti_site/.env
```

Add the following content (press Ctrl+X, then Y to save):

```bash
# Django Settings
SECRET_KEY=your-super-secret-key-generate-with-python
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com,yourcustomdomain.com
CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com,https://yourcustomdomain.com

# Database (SQLite - will be stored in your home directory)
DATABASE_URL=sqlite:////home/yourusername/mpbenti_site/db.sqlite3

# Admin User
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@mpbenti.com.au
DJANGO_SUPERUSER_PASSWORD=your-secure-admin-password

# Email Configuration (optional - defaults to console output)
# For Gmail API setup, see docs/EMAIL_TESTING.md
# For production, consider using SendGrid, Mailgun, or Amazon SES
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@mpbenti.com.au
```

**Generate a secure SECRET_KEY:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Note on Email Configuration:**
- By default, emails are logged to the console (terminal output)
- To send real emails, you'll need to configure Gmail API or a transactional email service
- See [EMAIL_TESTING.md](EMAIL_TESTING.md) for detailed setup instructions
- Gmail no longer supports SMTP with app passwords - you must use Gmail API
- **Gmail API token**: After one-time authentication, token.json is automatically stored and refreshed - no repeated login needed

### 6. Run Database Migrations

```bash
cd ~/mpbenti_site
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
# Follow the prompts to create your admin user
```

### 8. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 9. Load Initial Data (Optional)

If you have products and categories to import:

```bash
# Load initial data without users
python manage.py loaddata initial_data_no_users.json

# Or if you have product fixtures
python manage.py loaddata catalogue/fixtures/products.json
```

### 10. Configure the Web App

1. Go to the **"Web"** tab in PythonAnywhere dashboard
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** (not the Django wizard)
4. Select **Python 3.11**

### 11. Configure Web App Settings

In the **Web** tab, update the following sections:

#### A. Source Code

- **Source code**: `/home/yourusername/mpbenti_site`
- **Working directory**: `/home/yourusername/mpbenti_site`

#### B. Virtualenv

- **Virtualenv**: `/home/yourusername/.virtualenvs/mpbenti`

#### C. WSGI Configuration File

Click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)

Replace the entire contents with:

```python
import os
import sys
from pathlib import Path

# Add your project directory to the sys.path
project_home = '/home/yourusername/mpbenti_site'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable to tell Django where your settings module is
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Load environment variables from .env file
from pathlib import Path
env_file = Path(project_home) / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Important**: Replace `yourusername` with your actual PythonAnywhere username!

#### D. Static Files

Add the following static file mappings:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/mpbenti_site/staticfiles` |
| `/media/` | `/home/yourusername/mpbenti_site/media` |

#### E. Enable HTTPS

- Check the **"Force HTTPS"** option (recommended for production)

### 12. Reload Your Web App

- Click the green **"Reload yourusername.pythonanywhere.com"** button at the top of the Web tab

### 13. Test Your Application

Visit your site:
- Main site: `https://yourusername.pythonanywhere.com`
- Admin panel: `https://yourusername.pythonanywhere.com/admin`

## Post-Deployment Tasks

### Setting Up a Custom Domain (Hacker Plan or Higher)

1. In the **Web** tab, add your custom domain
2. Update your domain's DNS settings:
   - Add a CNAME record pointing to `yourusername.pythonanywhere.com`
3. Add your custom domain to the `ALLOWED_HOSTS` in your `.env` file
4. Reload the web app

### Updating Your Application

To deploy updates:

```bash
# Open a Bash console
cd ~/mpbenti_site
git pull origin main

# Activate virtualenv
workon mpbenti

# Install any new dependencies
pip install -r requirements.txt

# Run migrations if needed
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Then reload your web app from the Web tab
```

You can also create a simple deploy script:

```bash
nano ~/mpbenti_site/deploy.sh
```

Add:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying MP Benti..."

cd ~/mpbenti_site
git pull origin main

source ~/.virtualenvs/mpbenti/bin/activate

pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "✅ Deployment complete! Remember to reload the web app."
```

Make it executable:

```bash
chmod +x ~/mpbenti_site/deploy.sh
```

### Scheduled Tasks (Cron Jobs)

If you need to run periodic tasks (e.g., cleanup, email reminders):

1. Go to the **"Tasks"** tab in PythonAnywhere
2. Add scheduled tasks with commands like:

```bash
cd /home/yourusername/mpbenti_site && /home/yourusername/.virtualenvs/mpbenti/bin/python manage.py your_management_command
```

### Database Backups

For SQLite, back up your database regularly:

```bash
# Create a backup script
nano ~/backup_db.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cp ~/mpbenti_site/db.sqlite3 $BACKUP_DIR/db_backup_$DATE.sqlite3

# Keep only last 10 backups
cd $BACKUP_DIR
ls -t db_backup_*.sqlite3 | tail -n +11 | xargs -r rm

echo "✅ Database backed up to $BACKUP_DIR/db_backup_$DATE.sqlite3"
```

Make it executable and schedule it:

```bash
chmod +x ~/backup_db.sh
```

Add to **Tasks** tab to run daily.

## Troubleshooting

### Check Error Logs

1. Go to the **Web** tab
2. Click on the **error log** and **server log** links
3. Check for Python errors or Django issues

### Common Issues

#### 1. Static files not loading

- Make sure you've run `python manage.py collectstatic`
- Check that static file mappings are correct in the Web tab
- Verify `STATIC_ROOT` in settings.py points to `staticfiles`

#### 2. Database errors

- Ensure the database file path in `.env` uses your actual username
- Make sure migrations have been run: `python manage.py migrate`
- Check file permissions: `chmod 664 db.sqlite3`

#### 3. Import errors

- Verify virtualenv is correctly configured in the Web tab
- Check that all dependencies are installed: `pip list`
- Make sure the WSGI file has the correct project path

#### 4. 502 Bad Gateway

- Check the error log for Python exceptions
- Verify the WSGI file syntax is correct
- Ensure Django settings are properly configured

### Reload Web App

After making any configuration changes, always click **Reload** in the Web tab.

## Performance Optimization

### For SQLite (Small to Medium Traffic)

1. **Enable WAL mode** for better concurrent access:

```python
# Add to settings.py
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["timeout"] = 20
    DATABASES["default"]["OPTIONS"]["check_same_thread"] = False
```

2. **Optimize queries** in your code
3. **Use caching** for frequently accessed data

### For High Traffic, Consider MySQL

PythonAnywhere provides MySQL databases. To migrate:

1. Create a MySQL database in the **Databases** tab
2. Update your `.env` file with the MySQL connection string
3. Run migrations to create tables
4. Export data from SQLite and import to MySQL

## Security Checklist

- ✅ `DEBUG=False` in production
- ✅ Strong `SECRET_KEY` generated
- ✅ `ALLOWED_HOSTS` configured correctly
- ✅ `CSRF_TRUSTED_ORIGINS` includes your domains
- ✅ HTTPS enabled ("Force HTTPS" in Web tab)
- ✅ Strong admin password
- ✅ Regular database backups
- ✅ `.env` file not committed to git (add to `.gitignore`)

## Support

- **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Django Documentation**: https://docs.djangoproject.com/

## Differences from Railway

| Feature | Railway | PythonAnywhere |
|---------|---------|----------------|
| **Deployment** | Docker-based, auto-deploy from Git | Manual setup, Git pull for updates |
| **Database** | Persistent volumes | File-based (SQLite) or MySQL included |
| **Static Files** | Served via Gunicorn/WhiteNoise | Served directly by PythonAnywhere |
| **WSGI Server** | Gunicorn (you configure) | Managed by PythonAnywhere |
| **Cost** | Pay-as-you-go (~$5-7/month) | Fixed tiers ($5-12/month) |
| **SSL/HTTPS** | Automatic | Automatic (free Let's Encrypt) |
| **Custom Domain** | All plans | Hacker plan and above |

---

**You're all set!** Your Django application should now be running on PythonAnywhere. 🎉

