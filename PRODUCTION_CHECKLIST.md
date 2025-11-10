# Django Production Readiness Checklist

## ✅ Current Status

Your Django app is **mostly production-ready**, but needs a few critical configurations before Railway deployment.

---

## 🔴 CRITICAL - Must Fix Before Deployment

### 1. Security Settings Issues

#### ❌ Issue: Default SECRET_KEY fallback
**Location:** `core/settings.py:11`
```python
SECRET_KEY = env("SECRET_KEY", default="dev-secret-change-me")
```

**Problem:** If `SECRET_KEY` is not set, it falls back to a public default value - major security risk!

**Fix Required:**
```python
SECRET_KEY = env("SECRET_KEY")  # Remove default - force it to be set
```

#### ⚠️  Issue: ALLOWED_HOSTS wildcard default
**Location:** `core/settings.py:15`
```python
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
```

**Problem:** Allows any host in production if not configured (Host Header injection vulnerability)

**Fix Required:**
```python
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
```

#### ⚠️  Issue: CSRF_COOKIE_SECURE and SESSION_COOKIE_SECURE
**Location:** `core/settings.py:28-29`
```python
CSRF_COOKIE_SECURE = False  # Set to False since internal traffic is HTTP
SESSION_COOKIE_SECURE = False  # Set to False since internal traffic is HTTP
```

**Current Status:** These are set to `False` for double-proxy setups (Proxmox Nginx → Docker)

**For Railway:** Should be `True` since Railway handles HTTPS directly

**Fix Required for Railway:**
```python
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

    # Railway: Set to True since Railway handles HTTPS
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
```

---

## 🟡 RECOMMENDED - Should Configure

### 2. Additional Security Headers

**Missing settings:**
- `SECURE_HSTS_SECONDS` - HTTP Strict Transport Security
- `SECURE_CONTENT_TYPE_NOSNIFF` - Prevent MIME type sniffing
- `X_FRAME_OPTIONS` - Already set via middleware, but good to verify

**Recommended additions to settings.py:**
```python
if not DEBUG:
    # Existing settings...

    # Additional security headers
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
```

### 3. Session Security

**Current:** Using default Django session settings

**Recommended additions:**
```python
# Session security
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

### 4. Logging Configuration

**Missing:** No logging configured for production debugging

**Recommended:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## ✅ Already Configured Correctly

### Good Settings:
- ✅ `DEBUG` defaults to `False` (safe for production)
- ✅ WhiteNoise for static file serving
- ✅ Compressed static files (`CompressedManifestStaticFilesStorage`)
- ✅ Password validators enabled
- ✅ SQLite with WAL mode for concurrency
- ✅ CSRF protection enabled
- ✅ Clickjacking protection
- ✅ Timezone set to Australia/Sydney
- ✅ django-environ for environment variable management

---

## 📦 Initial Data Situation

### What You Have:

**File:** `initial_data.json` (4,672 lines)

**Contents:**
- 📁 **8 categories** (Cheese, Smallgoods, etc.)
- 🛒 **252 products** with pricing and images
- 👤 **2 users** (likely test users - **SECURITY RISK**)
- ⚙️  **1 site settings** record

### ⚠️  SECURITY CONCERN: User Data in Fixtures

**Problem:** The fixture includes 2 user accounts with potentially weak/known passwords

**Action Required:**
1. Check what users are included
2. Remove them from fixture OR change passwords immediately after loading

**Check the users:**
```bash
python3 -c "import json; users=[d for d in json.load(open('initial_data.json')) if d['model']=='auth.user']; print(json.dumps(users, indent=2))"
```

### Recommended Initial Data Strategy:

**Option 1: Load Everything (Quick Start)**
```bash
# After Railway deployment
railway run python manage.py loaddata initial_data.json
```

Then immediately:
- Delete or change passwords for the 2 included users
- Or delete them and create new ones

**Option 2: Selective Loading (Safer)**
1. Extract just categories and products to a new fixture
2. Don't include users in fixture
3. Create users manually via management commands

**Create new fixture without users:**
```bash
python3 -c "
import json
data = json.load(open('initial_data.json'))
# Filter out users
filtered = [d for d in data if d['model'] != 'auth.user']
with open('initial_data_no_users.json', 'w') as f:
    json.dump(filtered, f, indent=2)
"
```

Then load:
```bash
railway run python manage.py loaddata initial_data_no_users.json
```

---

## 🚀 Pre-Deployment Steps

### Step 1: Fix Critical Security Issues

Apply the security fixes mentioned above to `core/settings.py`

### Step 2: Generate Secure SECRET_KEY

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Save this for Railway environment variables.

### Step 3: Review Initial Data

Decide on data loading strategy (see above).

### Step 4: Set Railway Environment Variables

**Required:**
```bash
SECRET_KEY=<generated-secret-key>
DEBUG=False
ALLOWED_HOSTS=*.railway.app,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://your-app-name.railway.app,https://yourdomain.com
DATABASE_URL=sqlite:////app/data/db.sqlite3
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@mpbenti.com.au
DJANGO_SUPERUSER_PASSWORD=<strong-password-here>
```

**Optional but recommended:**
```bash
DJANGO_SETTINGS_MODULE=core.settings
PYTHONUNBUFFERED=1
```

### Step 5: Create Railway Volume

- Volume name: `db_volume`
- Mount path: `/app/data`
- Ensures database persists across deployments

---

## 📋 Post-Deployment Steps

### 1. Initial Deployment
Railway will automatically:
- ✅ Run migrations
- ✅ Create superuser (from env vars)
- ✅ Collect static files

### 2. Load Initial Data

**Option A: Load all data**
```bash
railway run python manage.py loaddata initial_data.json
```

Then check and secure the included users:
```bash
railway run python manage.py shell < check_staff_users.py
```

**Option B: Load filtered data (no users)**
```bash
railway run python manage.py loaddata initial_data_no_users.json
```

### 3. Verify Deployment

- [ ] Visit `https://your-app.railway.app`
- [ ] Check homepage loads
- [ ] Login to admin: `https://your-app.railway.app/admin`
- [ ] Verify products are visible in catalogue
- [ ] Test placing an order
- [ ] Access dashboard: `https://your-app.railway.app/dashboard`

### 4. Create Additional Staff Users

```bash
railway run python manage.py make_staff username
```

### 5. Configure Site Settings

Login to dashboard and configure:
- Price visibility settings
- Any other site-wide preferences

---

## 🔍 Testing Production Configuration Locally

Before deploying, test with production-like settings:

**1. Create `.env` file:**
```bash
cp .env.example .env
```

**2. Edit `.env` with production-like values:**
```env
SECRET_KEY=<generated-key>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@test.com
DJANGO_SUPERUSER_PASSWORD=testpass123
```

**3. Test locally:**
```bash
python manage.py migrate
python manage.py createsuperuser --noinput
python manage.py loaddata initial_data.json
python manage.py collectstatic --noinput
python manage.py runserver
```

**4. Verify:**
- Static files load correctly
- No errors in console
- Can login and access dashboard

---

## 📊 Production Monitoring

After deployment, monitor:

### Railway Dashboard
- CPU and memory usage
- Request logs
- Error rates

### Django Admin
- Check `/admin/` for any errors
- Monitor user activity

### Database
- SQLite file size (in `/app/data/`)
- Regular backups

### Security
- Review Railway logs for suspicious activity
- Monitor failed login attempts

---

## 🔐 Security Best Practices

1. **Never commit secrets** to git
   - ✅ Already using `.env` files
   - ✅ `.env` is in `.gitignore`

2. **Strong passwords**
   - Use strong superuser password
   - Enforce for all staff users

3. **Regular updates**
   - Keep Django and dependencies updated
   - Monitor security advisories

4. **Database backups**
   - Set up automated backups (see RAILWAY_DEPLOY.md)
   - Test restore process

5. **User audit**
   - Regularly review staff users
   - Remove inactive accounts

---

## 📝 Summary

### Must Do Before Deployment:
1. ❌ Fix SECRET_KEY to not have default fallback
2. ⚠️  Fix ALLOWED_HOSTS to not default to wildcard
3. ⚠️  Update CSRF/SESSION cookie settings for Railway
4. 🔑 Generate secure SECRET_KEY
5. 🗑️  Remove or secure users in initial_data.json

### Your Starting Data:
- 8 product categories
- 252 products
- 1 site settings record
- (2 users - review and secure)

### Deployment Flow:
1. Apply security fixes
2. Push to GitHub
3. Deploy to Railway
4. Railway auto-runs migrations and creates superuser
5. Load initial data via Railway CLI
6. Verify everything works
7. Start using the platform!

---

## 🆘 Need Help?

See `RAILWAY_DEPLOY.md` for detailed deployment instructions.
See `STAFF_ACCESS_FIX.md` for user management.
