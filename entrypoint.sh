#!/bin/bash
set -e

echo "🚀 Starting MP Benti Django Application"

# Copy initial media files if media directory is empty
if [ -d "/app/media_initial" ] && [ ! "$(ls -A /app/media)" ]; then
    echo "📁 Copying initial media files..."
    cp -r /app/media_initial/* /app/media/ 2>/dev/null || true
fi

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists() and password:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'✅ Superuser {username} created')
else:
    print('ℹ️  Superuser already exists or password not provided')
"

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🎉 Setup complete! Starting Gunicorn..."

# Start the main process
exec "$@"