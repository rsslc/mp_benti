# PythonAnywhere Quick Reference

This is a quick reference guide for common tasks when managing your MP Benti application on PythonAnywhere.

## Initial Setup Commands

```bash
# Clone repository
cd ~
git clone https://github.com/yourusername/mpbenti_site.git
cd mpbenti_site

# Create virtual environment
mkvirtualenv mpbenti --python=/usr/bin/python3.11

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.pythonanywhere.example .env
nano .env  # Edit with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Daily Operations

### Activate Virtual Environment

```bash
workon mpbenti
```

### Deploy Updates

```bash
cd ~/mpbenti_site
workon mpbenti
./deploy_pythonanywhere.sh
# Then reload web app from Web tab
```

### Manual Deployment Steps

```bash
cd ~/mpbenti_site
workon mpbenti
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# Then reload web app from Web tab
```

### Database Operations

```bash
# Run migrations
python manage.py migrate

# Create new migration
python manage.py makemigrations

# View migration status
python manage.py showmigrations

# Reset database (CAREFUL - deletes all data!)
rm ~/mpbenti_site/db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Load Initial Data

```bash
cd ~/mpbenti_site
workon mpbenti

# Load products and categories (without users)
python manage.py loaddata initial_data_no_users.json

# Or load from fixtures
python manage.py loaddata catalogue/fixtures/products.json
```

### User Management

```bash
# Create superuser
python manage.py createsuperuser

# Create staff user
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.create_user('staffuser', 'staff@example.com', 'password')
>>> user.is_staff = True
>>> user.save()
>>> exit()

# Check staff users
python check_staff_users.py
```

### View Logs

From the PythonAnywhere Web tab:
- Click on "error log" link to see Python errors
- Click on "server log" link to see access logs

Or from console:

```bash
# View last 50 lines of error log
tail -50 /var/log/yourusername.pythonanywhere.com.error.log

# View last 50 lines of server log
tail -50 /var/log/yourusername.pythonanywhere.com.server.log

# Follow error log in real-time
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

## Database Backup & Restore

### Backup SQLite Database

```bash
# Create backup directory
mkdir -p ~/backups

# Backup database with timestamp
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/mpbenti_site/db.sqlite3 ~/backups/db_backup_$DATE.sqlite3

# List backups
ls -lh ~/backups/
```

### Restore Database

```bash
# Restore from backup (replace YYYYMMDD_HHMMSS with actual date)
cp ~/backups/db_backup_YYYYMMDD_HHMMSS.sqlite3 ~/mpbenti_site/db.sqlite3

# Reload web app from Web tab
```

### Automated Backup Script

Create `~/backup_mpbenti.sh`:

```bash
#!/bin/bash
BACKUP_DIR=~/backups/mpbenti
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
cp ~/mpbenti_site/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C ~/mpbenti_site media/

# Keep only last 10 backups
cd $BACKUP_DIR
ls -t db_*.sqlite3 | tail -n +11 | xargs -r rm
ls -t media_*.tar.gz | tail -n +11 | xargs -r rm

echo "✅ Backup completed: $DATE"
```

Make it executable and schedule in Tasks tab:

```bash
chmod +x ~/backup_mpbenti.sh
```

Add to Tasks tab (daily at 2 AM):
```
/home/yourusername/backup_mpbenti.sh
```

## Troubleshooting

### Web App Won't Start

1. Check error log from Web tab
2. Verify WSGI file configuration
3. Check virtual environment path in Web tab
4. Ensure .env file exists with correct values

### Static Files Not Loading

```bash
cd ~/mpbenti_site
workon mpbenti
python manage.py collectstatic --noinput --clear
# Reload web app
```

Check static file mappings in Web tab:
- URL: `/static/`
- Directory: `/home/yourusername/mpbenti_site/staticfiles`

### Database Locked Errors

SQLite can have locking issues with concurrent access:

```bash
# Check if database is locked
lsof ~/mpbenti_site/db.sqlite3

# If locked, reload web app from Web tab
# Or restart the web app process
```

Consider upgrading to MySQL for better concurrent access:
- Create MySQL database in Databases tab
- Update DATABASE_URL in .env
- Migrate data from SQLite to MySQL

### Import Errors

```bash
# Check installed packages
workon mpbenti
pip list

# Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.11
```

### Permission Errors

```bash
# Fix database permissions
chmod 664 ~/mpbenti_site/db.sqlite3

# Fix media directory permissions
chmod -R 755 ~/mpbenti_site/media
```

## Performance Optimization

### Enable Django Caching

Add to settings.py:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/home/yourusername/mpbenti_site/cache',
    }
}
```

Create cache directory:

```bash
mkdir -p ~/mpbenti_site/cache
```

### Database Optimization

```bash
# Optimize SQLite database
cd ~/mpbenti_site
workon mpbenti
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("VACUUM")
>>> exit()
```

## Useful Django Commands

```bash
# Django shell
python manage.py shell

# Database shell
python manage.py dbshell

# Check Django setup
python manage.py check

# Show URLs
python manage.py show_urls  # If django-extensions installed

# Clear sessions
python manage.py clearsessions

# Create dummy data (if you have fixtures)
python manage.py loaddata your_fixture.json
```

## Scheduled Tasks Examples

Add in the Tasks tab:

### Daily database backup (2:00 AM)
```bash
/home/yourusername/backup_mpbenti.sh
```

### Weekly database cleanup (Sunday 3:00 AM)
```bash
cd /home/yourusername/mpbenti_site && /home/yourusername/.virtualenvs/mpbenti/bin/python manage.py clearsessions
```

### Monthly optimization (1st of month, 4:00 AM)
```bash
cd /home/yourusername/mpbenti_site && /home/yourusername/.virtualenvs/mpbenti/bin/python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('VACUUM')"
```

## Environment Variables Reference

Key variables in your `.env` file:

```bash
SECRET_KEY=                    # Django secret key
DEBUG=False                    # Never True in production
ALLOWED_HOSTS=                 # Comma-separated list of domains
CSRF_TRUSTED_ORIGINS=          # HTTPS URLs (with protocol)
DATABASE_URL=                  # Database connection string
DJANGO_SUPERUSER_USERNAME=     # Admin username
DJANGO_SUPERUSER_EMAIL=        # Admin email
DJANGO_SUPERUSER_PASSWORD=     # Admin password
```

## Getting Help

- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
- **Django Documentation**: https://docs.djangoproject.com/
- **Project Documentation**: See PYTHONANYWHERE_DEPLOY.md

## Quick Links

- **Dashboard**: https://www.pythonanywhere.com/user/yourusername/
- **Web Tab**: https://www.pythonanywhere.com/user/yourusername/webapps/
- **Files**: https://www.pythonanywhere.com/user/yourusername/files/
- **Consoles**: https://www.pythonanywhere.com/user/yourusername/consoles/
- **Tasks**: https://www.pythonanywhere.com/user/yourusername/tasks_tab/

---

**Remember**: After making configuration changes or deploying updates, always reload your web app from the Web tab!

