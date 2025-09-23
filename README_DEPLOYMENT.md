# MP Benti Site - Deployment Guide

## Render Deployment

This Django + Tailwind CSS project is configured for deployment on Render with PostgreSQL.

### Prerequisites

1. **Node.js and npm** - For Tailwind CSS build
2. **Python 3.11+** - For Django application
3. **Git repository** - Connected to Render

### Deployment Files

The project includes these deployment configuration files:

- `render.yaml` - Render service configuration
- `Procfile` - Gunicorn configuration
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

### Automatic Deployment

1. **Push to Git repository** connected to Render
2. **Render will automatically**:
   - Create PostgreSQL database
   - Install Python dependencies
   - Install Node.js dependencies
   - Build Tailwind CSS
   - Collect static files
   - Start Gunicorn server

### Environment Variables

Render will automatically set:
- `SECRET_KEY` - Generated secure key
- `DEBUG` - Set to False
- `DATABASE_URL` - PostgreSQL connection string
- `DJANGO_SUPERUSER_USERNAME` - Admin username (default: admin)
- `DJANGO_SUPERUSER_EMAIL` - Admin email
- `DJANGO_SUPERUSER_PASSWORD` - Generated secure password

### Initial Data & Superuser

The deployment includes automatic data migration that:
- **Loads all existing data** (categories, products, settings) from SQLite fixtures
- **Creates superuser account** using environment variables
- **Runs only once** on fresh database deployment
- **Safely skips** if data already exists

**Important**: After deployment, check the Render logs for the generated superuser password, or set your own in the environment variables.

### Manual Deployment Steps

If you prefer manual configuration:

1. **Create Web Service** on Render
   - Environment: Python
   - Build Command: `pip install -r requirements.txt && npm install && npm run build && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn core.wsgi:application`

2. **Create PostgreSQL Database**
   - Database Name: `mpbenti`
   - User: `mpbenti`

3. **Set Environment Variables**:
   ```
   SECRET_KEY=<generated-secret-key>
   DEBUG=False
   DATABASE_URL=<postgresql-connection-string>
   ```

### Local Testing

Test the production configuration locally:

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Build assets
npm run build
python manage.py collectstatic --noinput

# Test with Gunicorn
gunicorn core.wsgi:application
```

### Project Structure

```
mpbenti_site/
├── core/               # Django settings and configuration
├── catalogue/          # Product catalog app
├── customers/          # Customer management
├── orders/             # Order processing
├── dashboard/          # Admin dashboard
├── templates/          # Django templates
├── static/             # Static files (CSS, images)
├── staticfiles/        # Collected static files (auto-generated)
├── media/              # User uploaded files
├── requirements.txt    # Python dependencies
├── package.json        # Node.js dependencies
├── Procfile           # Gunicorn configuration
├── render.yaml        # Render deployment configuration
└── .env.example       # Environment variables template
```

### Features

- **Two-level product categories** with collapsible navigation
- **Image upload and processing** for categories and products
- **Price visibility controls** for superadmin
- **Responsive design** with Tailwind CSS
- **User authentication** and order management
- **Admin dashboard** for content management

### Production Features

- **WhiteNoise** for static file serving
- **PostgreSQL** database support
- **Environment-based configuration**
- **Compressed static files**
- **Secure secret key generation**
- **Production-ready middleware stack**