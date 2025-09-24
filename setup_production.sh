#!/bin/bash
# Production setup script for MP Benti

set -e

echo "🚀 MP Benti Production Setup"
echo "============================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env

    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 32)
    ADMIN_PASSWORD=$(openssl rand -base64 16)
    SECRET_KEY=$(python3 -c "import secrets; import string; chars = string.ascii_letters + string.digits + '-_'; print(''.join(secrets.choice(chars) for _ in range(50)))")

    # Update .env with secure values
    sed -i "s/SECRET_KEY=your-secret-key-here/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/DEBUG=True/DEBUG=False/" .env
    sed -i "s/POSTGRES_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD/POSTGRES_PASSWORD=$DB_PASSWORD/" .env
    sed -i "s/DJANGO_SUPERUSER_PASSWORD=change-this-secure-password/DJANGO_SUPERUSER_PASSWORD=$ADMIN_PASSWORD/" .env

    echo "✅ Generated secure passwords:"
    echo "   Database Password: $DB_PASSWORD"
    echo "   Admin Password: $ADMIN_PASSWORD"
    echo ""
    echo "⚠️  SAVE THESE PASSWORDS! They are now in your .env file."
    echo ""
else
    echo "✅ .env file already exists"
fi

# Prompt for domain
read -p "🌐 Enter your domain (or press Enter for localhost): " DOMAIN
if [ ! -z "$DOMAIN" ]; then
    sed -i "s/ALLOWED_HOSTS=localhost,127.0.0.1/ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1/" .env
    echo "✅ Updated ALLOWED_HOSTS for domain: $DOMAIN"
fi

echo ""
echo "🐳 Starting Docker containers..."
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "📋 Waiting for services to start..."
sleep 10

# Show the admin credentials
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "🌐 Your site will be available at: http://$(hostname -I | awk '{print $1}')"
if [ ! -z "$DOMAIN" ]; then
    echo "🌐 Or at: http://$DOMAIN (once DNS is configured)"
fi
echo "🔑 Admin URL: http://$(hostname -I | awk '{print $1}')/admin/"
echo "👤 Admin Username: admin"
echo "🔐 Admin Password: $(grep DJANGO_SUPERUSER_PASSWORD .env | cut -d'=' -f2)"
echo ""
echo "📊 Check logs: docker compose -f docker-compose.prod.yml logs -f"
echo "🔧 Manage: docker compose -f docker-compose.prod.yml [up|down|logs]"