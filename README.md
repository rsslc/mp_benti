# MP Benti - Wholesale Food Ordering Platform

A modern Django-based wholesale ordering system with Tailwind CSS, designed for PythonAnywhere deployment.

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
- **Database**: SQLite (development/production)
- **Deployment**: PythonAnywhere

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd mpbenti_site
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run migrations and create superuser**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

4. **Run development server**:
   ```bash
   python manage.py runserver
   ```

5. **Access the application**:
   - Application: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin/

### Production Deployment

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for complete PythonAnywhere deployment instructions.

## Documentation

- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Complete deployment guide
- **[docs/SETUP.md](docs/SETUP.md)** - Initial setup and configuration
- **[docs/ADMIN.md](docs/ADMIN.md)** - Admin user management
- **[docs/PRODUCTION.md](docs/PRODUCTION.md)** - Production checklist

## Project Structure

```
mpbenti_site/
├── catalogue/          # Product and category management
├── customers/          # Customer models and management
├── dashboard/          # Admin dashboard views
├── orders/             # Order processing
├── core/              # Django settings and configuration
├── templates/         # HTML templates
├── static/            # Static files (CSS, JS, images)
├── docs/              # Documentation
└── manage.py          # Django management script
```

## Key Management Commands

```bash
# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py loaddata initial_data.json

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

## Environment Variables

Key environment variables (see `.env.example`):

```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=secure-password
```

## Shopping Cart & Orders

### Customer Flow
1. Browse products at `/products/`
2. Search/filter within categories
3. Add items to cart with custom quantities
4. View/edit cart at `/cart/`
5. Login and checkout at `/cart/checkout/`
6. View order history at `/my-orders/`

### Key URLs
- `/products/` - Product catalog
- `/cart/` - Shopping cart
- `/cart/checkout/` - Checkout (requires login)
- `/my-orders/` - Order history (requires login)
- `/my-orders/{id}/` - Order details

### Email Notifications
Orders automatically trigger email notifications to the configured admin email (mpbenti@gmail.com).

**Gmail Setup:**
Gmail no longer supports app passwords for new applications. Use Gmail API instead:
1. See `docs/EMAIL_TESTING.md` for complete Gmail API setup instructions
2. One-time OAuth authentication creates a `token.json` file that persists
3. Token automatically refreshes - no repeated login required

## Support

For deployment issues or questions, refer to the documentation in the `docs/` folder.

## License

Proprietary - All rights reserved

