#!/bin/bash
# Fly.io deployment script with database setup

set -e

echo "🚁 MP Benti - Fly.io Deployment Script"
echo "======================================"

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Please install it first:"
    echo "   brew install flyctl  # On macOS"
    echo "   # Or visit: https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Check if logged in to Fly.io
if ! fly auth whoami &> /dev/null; then
    echo "🔐 Please log in to Fly.io first:"
    echo "   fly auth login"
    exit 1
fi

echo "📦 Building and deploying application..."

# Check if app exists
APP_NAME="mpbenti"
if ! fly apps list | grep -q "$APP_NAME"; then
    echo "🆕 Creating new Fly.io app..."
    fly launch --no-deploy --name "$APP_NAME"
else
    echo "✅ App $APP_NAME already exists"
fi

# Check if PostgreSQL database exists
DB_NAME="${APP_NAME}-db"
if ! fly postgres list | grep -q "$DB_NAME"; then
    echo "🗄️  Creating PostgreSQL database..."
    fly postgres create --name "$DB_NAME" --region syd

    echo "🔗 Attaching database to app..."
    fly postgres attach "$DB_NAME" --app "$APP_NAME"
else
    echo "✅ Database $DB_NAME already exists"
fi

# Create volume for media files if it doesn't exist
VOLUME_NAME="mpbenti_media"
if ! fly volumes list --app "$APP_NAME" | grep -q "$VOLUME_NAME"; then
    echo "💾 Creating volume for media files..."
    fly volumes create "$VOLUME_NAME" --region syd --size 1 --app "$APP_NAME"
else
    echo "✅ Volume $VOLUME_NAME already exists"
fi

# Set environment variables
echo "🔧 Setting environment variables..."
fly secrets set \
    DJANGO_SUPERUSER_USERNAME="admin" \
    DJANGO_SUPERUSER_EMAIL="admin@mpbenti.com.au" \
    DJANGO_SUPERUSER_PASSWORD="$(openssl rand -base64 32)" \
    --app "$APP_NAME"

# Deploy the application
echo "🚀 Deploying application..."
fly deploy --app "$APP_NAME"

# Get app URL
APP_URL="https://${APP_NAME}.fly.dev"

echo ""
echo "🎉 Deployment completed successfully!"
echo "======================================"
echo "🌐 Your app is available at: $APP_URL"
echo "🔑 Admin panel: $APP_URL/admin/"
echo ""
echo "📋 Next steps:"
echo "1. Check deployment logs: fly logs --app $APP_NAME"
echo "2. Access your app: $APP_URL"
echo "3. View superuser password: fly secrets list --app $APP_NAME"
echo "4. Connect to database: fly postgres connect --app $DB_NAME"
echo ""
echo "🛠️  Troubleshooting:"
echo "- SSH into app: fly ssh console --app $APP_NAME"
echo "- View app status: fly status --app $APP_NAME"
echo "- Scale app: fly scale count 1 --app $APP_NAME"