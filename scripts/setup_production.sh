#!/bin/bash
# Production setup script for Fly.io deployment

set -e  # Exit on any error

echo "🚀 Setting up production environment..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import os
import sys
import time
import psycopg2
from urllib.parse import urlparse

# Parse DATABASE_URL
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print('❌ DATABASE_URL not found')
    sys.exit(1)

url = urlparse(database_url)

# Test database connection with retries
max_retries = 30
for i in range(max_retries):
    try:
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password
        )
        conn.close()
        print('✅ Database connection successful')
        break
    except psycopg2.OperationalError as e:
        if i == max_retries - 1:
            print(f'❌ Database connection failed after {max_retries} attempts')
            print(f'Error: {e}')
            sys.exit(1)
        print(f'⏳ Attempt {i+1}/{max_retries}: Database not ready, waiting...')
        time.sleep(2)
"

# Run Django migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

# Check if we need to create a superuser
echo "👤 Checking for superuser..."
python -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

# Check if any superuser exists
if not User.objects.filter(is_superuser=True).exists():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if password:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'✅ Superuser {username} created successfully')
    else:
        print('⚠️  DJANGO_SUPERUSER_PASSWORD not set, skipping superuser creation')
else:
    print('✅ Superuser already exists')
"

echo "✅ Production setup complete!"