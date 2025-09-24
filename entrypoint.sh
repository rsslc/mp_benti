#!/bin/bash
set -e

echo "🚀 Starting MP Benti Django Application"

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" 2>/dev/null; do
  sleep 1
done
echo "✅ Database is ready"

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