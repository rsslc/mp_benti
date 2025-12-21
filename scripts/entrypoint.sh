#!/bin/bash
set -e

echo "🚀 Starting MP Benti Django Application"

# Copy initial media files if media directory is empty
if [ -d "/app/media_initial" ] && [ ! -d "/data/media" ]; then
    echo "📁 Copying initial media files..."
    mkdir -p /data/media
    cp -r /app/media_initial/* /data/media/ 2>/dev/null || true
fi

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

# Create or update superuser
echo "👤 Setting up superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if password:
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    if created:
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f'✅ Superuser {username} created')
    else:
        # Update existing user's password and email
        user.email = email
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f'✅ Superuser {username} password and email updated')
else:
    print('ℹ️  No password provided, skipping superuser setup')
"

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🎉 Setup complete! Starting Gunicorn..."

# Start the main process
exec "$@"