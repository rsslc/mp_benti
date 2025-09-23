# MP Benti - Fly.io Deployment Guide

## Overview

This Django + Tailwind CSS project is configured for deployment on Fly.io with PostgreSQL and persistent media storage.

## Prerequisites

1. **Install Fly CLI**:
   ```bash
   # macOS
   brew install flyctl

   # Linux/Windows
   # Visit: https://fly.io/docs/getting-started/installing-flyctl/
   ```

2. **Login to Fly.io**:
   ```bash
   fly auth login
   ```

3. **Docker** (if building locally)

## Deployment Files

- `Dockerfile` - Multi-stage Docker build (Node.js + Python)
- `fly.toml` - Fly.io application configuration
- `.dockerignore` - Docker build exclusions
- `scripts/fly_deploy.sh` - Automated deployment script
- `scripts/setup_production.sh` - Production environment setup

## Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
./scripts/fly_deploy.sh
```

This script will:
- Create Fly.io app
- Set up PostgreSQL database
- Create persistent volume for media files
- Set environment variables
- Deploy the application

### Option 2: Manual Deployment

1. **Create Application**:
   ```bash
   fly launch --name mpbenti --no-deploy
   ```

2. **Create PostgreSQL Database**:
   ```bash
   fly postgres create --name mpbenti-db --region syd
   fly postgres attach mpbenti-db --app mpbenti
   ```

3. **Create Volume for Media Files**:
   ```bash
   fly volumes create mpbenti_media --region syd --size 1
   ```

4. **Set Environment Variables**:
   ```bash
   fly secrets set \
     DJANGO_SUPERUSER_USERNAME="admin" \
     DJANGO_SUPERUSER_EMAIL="admin@mpbenti.com.au" \
     DJANGO_SUPERUSER_PASSWORD="your-secure-password" \
     --app mpbenti
   ```

5. **Deploy**:
   ```bash
   fly deploy
   ```

## Configuration

### Environment Variables

The app automatically sets up these environment variables:

- `SECRET_KEY` - Auto-generated Django secret key
- `DEBUG` - Set to False in production
- `DATABASE_URL` - PostgreSQL connection (auto-configured)
- `FLY_APP_NAME` - App name for hostname configuration
- `DJANGO_SUPERUSER_*` - Admin account credentials

### Key Features

- **Multi-stage Docker build** - Node.js builds Tailwind CSS, Python runs Django
- **Automatic migrations** - Runs `python manage.py migrate` on deployment
- **Static file serving** - WhiteNoise serves static files efficiently
- **Persistent media storage** - Volume mount at `/app/media`
- **Health checks** - Monitors app health and auto-restarts if needed
- **Auto-scaling** - Starts/stops machines based on traffic

## Database

### Initial Data Migration

Your SQLite data will be automatically migrated to PostgreSQL:

1. **Fixtures loaded** - 263 objects (categories, products, settings)
2. **Superuser created** - Admin account with environment variables
3. **One-time execution** - Safe to redeploy, won't duplicate data

### Database Access

```bash
# Connect to PostgreSQL
fly postgres connect --app mpbenti-db

# Run Django shell
fly ssh console --app mpbenti
python manage.py shell

# View database logs
fly logs --app mpbenti-db
```

## Monitoring & Management

### Application Management

```bash
# View app status
fly status --app mpbenti

# View logs
fly logs --app mpbenti

# Scale application
fly scale count 1 --app mpbenti

# SSH into container
fly ssh console --app mpbenti
```

### Volume Management

```bash
# List volumes
fly volumes list --app mpbenti

# Create snapshot
fly volumes snapshots create mpbenti_media --app mpbenti

# Extend volume size
fly volumes extend mpbenti_media --size 2 --app mpbenti
```

## Troubleshooting

### Common Issues

1. **Build Failures**:
   ```bash
   # Check build logs
   fly logs --app mpbenti

   # Build locally to test
   docker build -t mpbenti .
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database status
   fly status --app mpbenti-db

   # Verify connection string
   fly secrets list --app mpbenti
   ```

3. **Static Files Not Loading**:
   ```bash
   # SSH into app and check files
   fly ssh console --app mpbenti
   ls -la /app/staticfiles/
   ```

4. **Media Files Issues**:
   ```bash
   # Check volume mount
   fly ssh console --app mpbenti
   ls -la /app/media/
   df -h
   ```

### Performance Optimization

- **Machine Size**: Default is 1GB RAM, 1 CPU (shared)
- **Database**: Consider upgrading PostgreSQL for production load
- **Regions**: Deploy closer to users (current: Sydney)
- **Caching**: Consider Redis for session/cache storage

## Cost Estimation

**Fly.io costs** (approximate):
- **Shared CPU (1GB RAM)**: $1.94/month (if always running)
- **PostgreSQL**: $1.94/month (shared-cpu-1x)
- **Volume (1GB)**: $0.15/month
- **Bandwidth**: $0.02/GB

**Total**: ~$4/month for small production deployment

## Security

- ✅ **HTTPS enforced** - All traffic redirected to HTTPS
- ✅ **Environment secrets** - Passwords stored securely
- ✅ **Non-root container** - App runs as django user
- ✅ **Health checks** - Automatic monitoring and restart
- ✅ **Network isolation** - Internal .flycast networking

## Comparison: Render vs Fly.io

| Feature | Render | Fly.io |
|---------|--------|---------|
| **Setup** | render.yaml | Dockerfile + fly.toml |
| **Database** | Auto-created | Manual PostgreSQL creation |
| **Static Files** | Build-time generation | Docker build-time |
| **Scaling** | Auto-scaling | Machine-based scaling |
| **Regions** | Limited regions | Global edge locations |
| **SSH Access** | Limited | Full SSH console |
| **Cost** | $7/month minimum | $4/month typical |

Choose **Fly.io** for:
- Better performance and global reach
- More control and SSH access
- Lower cost for small apps
- Docker-based deployments

Your project now supports **both platforms** - deploy to either one using the same codebase! 🚁