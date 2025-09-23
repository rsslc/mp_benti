# MP Benti - Django E-Commerce Platform

A modern Django-based wholesale food ordering system with Tailwind CSS, designed for easy Docker deployment.

## Features

- **Two-level Category System** - Parent and child categories for product organization
- **Product Management** - Complete CRUD operations with image support
- **Order Processing** - Customer order management with status tracking
- **Admin Dashboard** - Comprehensive admin interface for all operations
- **Price Visibility Control** - Admin-controlled price display settings
- **Responsive Design** - Tailwind CSS with Alpine.js for interactive UI
- **Image Processing** - Automatic resizing and optimization
- **User Authentication** - Login system for customers and admin

## Technology Stack

- **Backend**: Django 5.0.7, Python 3.11
- **Frontend**: Tailwind CSS, Alpine.js
- **Database**: PostgreSQL (production), SQLite (development)
- **Server**: Gunicorn, Nginx
- **Containerization**: Docker, Docker Compose

## Quick Start

### Local Development (Docker)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rsslc/mp_benti.git
   cd mp_benti
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Application: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin/
   - Default credentials: admin / admin123

### Local Development (Traditional)

1. **Setup Python environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Setup Node.js for Tailwind**:
   ```bash
   npm install
   npm run build
   ```

3. **Setup database**:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

4. **Run development server**:
   ```bash
   python manage.py runserver
   ```

## Production Deployment

### Docker Deployment (Recommended)

#### Using Docker Compose

1. **Create `.env` file** from `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your production values
   ```

2. **Run production stack**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

This will start:
- Django application (Gunicorn)
- PostgreSQL database
- Nginx reverse proxy

#### Digital Ocean Deployment

1. **Create a Droplet** with Docker pre-installed

2. **Clone and configure**:
   ```bash
   git clone https://github.com/rsslc/mp_benti.git
   cd mp_benti
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Configure domain** and SSL with Certbot:
   ```bash
   # Install Certbot
   apt-get update
   apt-get install certbot python3-certbot-nginx

   # Get SSL certificate
   certbot --nginx -d yourdomain.com
   ```

## Data Migration

The application automatically migrates initial data on first deployment:

- **Categories**: 8 parent/child categories
- **Products**: 252 products with details
- **Settings**: Default site configuration
- **Superuser**: Admin account created from environment variables

To manually load data:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata initial_data.json
```

## Environment Variables

Key environment variables (see `.env.example`):

```bash
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@host/db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=secure-password
```

## Docker Commands

**Development**:
```bash
# Start services
docker-compose up

# Rebuild after changes
docker-compose up --build

# Stop services
docker-compose down
```

**Production**:
```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Execute Django commands
docker-compose -f docker-compose.prod.yml exec web python manage.py [command]

# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U mpbenti mpbenti > backup.sql
```

## Project Structure

```
mp_benti/
├── catalogue/          # Product catalog app
├── customers/          # Customer management
├── orders/            # Order processing
├── dashboard/         # Admin dashboard
├── core/              # Django settings
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── docker-compose.yml # Development Docker config
├── docker-compose.prod.yml # Production Docker config
├── Dockerfile         # Multi-stage Docker build
├── nginx.conf        # Nginx configuration
└── initial_data.json # Initial database fixtures
```

## Development

### Tailwind CSS

Build CSS during development:
```bash
npm run dev  # Watch mode
npm run build  # Production build
```

### Django Management

Common Django commands:
```bash
# Create superuser
python manage.py createsuperuser

# Make migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test
```

## Security Considerations

- Change `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` properly
- Use strong database passwords
- Enable HTTPS with SSL certificates
- Regular security updates

## License

Private project - All rights reserved

## Support

For issues or questions, contact: admin@mpbenti.com.au