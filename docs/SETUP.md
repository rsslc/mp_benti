# PythonAnywhere Deployment - Quick Start

Welcome! This guide will get your MP Benti application deployed to PythonAnywhere in about 30 minutes.

## 📚 Documentation Overview

We've created comprehensive documentation for PythonAnywhere deployment:

1. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete step-by-step deployment guide (START HERE)
2. **[archive/PYTHONANYWHERE_QUICKREF.md](archive/PYTHONANYWHERE_QUICKREF.md)** - Quick reference for daily operations
3. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete PythonAnywhere deployment guide
4. **[README.md](README.md)** - Project overview (updated with PythonAnywhere instructions)

## 🚀 Quick Start (5 Steps)

### 1. Sign Up
Create account at [PythonAnywhere.com](https://www.pythonanywhere.com/)
- **Free tier**: For testing
- **Hacker plan ($5/mo)**: For production with custom domain

### 2. Clone & Setup (in Bash console)
```bash
git clone https://github.com/yourusername/mpbenti_site.git
cd mpbenti_site
mkvirtualenv mpbenti --python=/usr/bin/python3.11
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.pythonanywhere.example .env
nano .env  # Update with your settings
```

Generate SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 5. Configure Web App
- Go to **Web** tab → **Add a new web app**
- Choose **Manual configuration** → **Python 3.11**
- Set **Source code**: `/home/yourusername/mpbenti_site`
- Set **Virtualenv**: `/home/yourusername/.virtualenvs/mpbenti`
- Edit **WSGI file** (copy from `pythonanywhere_wsgi.py`)
- Add **Static files mapping**: `/static/` → `/home/yourusername/mpbenti_site/staticfiles`
- Add **Static files mapping**: `/media/` → `/home/yourusername/mpbenti_site/media`
- Click **Reload**

**Done!** Visit `https://yourusername.pythonanywhere.com` 🎉

## 📋 Files Included

### Configuration Files
- `.env.pythonanywhere.example` - Environment variables template
- `pythonanywhere_wsgi.py` - WSGI configuration example

### Scripts
- `deploy_pythonanywhere.sh` - Automated deployment script

### Documentation
- `DEPLOYMENT.md` - Full deployment guide
- `archive/PYTHONANYWHERE_QUICKREF.md` - Command reference
- `DEPLOYMENT.md` - Complete deployment guide

## 🔧 Daily Operations

### Deploy Updates
```bash
cd ~/mpbenti_site
workon mpbenti
./deploy_pythonanywhere.sh
# Then click Reload in Web tab
```

### View Logs
Go to **Web** tab → Click **error log** or **server log**

### Database Backup
```bash
cp ~/mpbenti_site/db.sqlite3 ~/backups/db_backup_$(date +%Y%m%d).sqlite3
```

## 💰 Pricing

| Plan | Price | Features |
|------|-------|----------|
| **Beginner** | Free | Basic, no custom domain |
| **Hacker** | $5/month | Custom domain, MySQL |
| **Web Developer** | $12/month | More power, multiple sites |

**Recommended**: Hacker plan for production

## 🆘 Need Help?

1. **Deployment Issues**: See [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
2. **Command Reference**: See [archive/PYTHONANYWHERE_QUICKREF.md](archive/PYTHONANYWHERE_QUICKREF.md)
3. **PythonAnywhere Help**: https://help.pythonanywhere.com/
4. **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/

## ✅ Deployment Checklist

Before going live:

- [ ] Sign up for PythonAnywhere (Hacker plan or higher)
- [ ] Clone repository to PythonAnywhere
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Create and configure `.env` file with secure SECRET_KEY
- [ ] Configure email settings (for order notifications)
- [ ] Run database migrations
- [ ] Create superuser
- [ ] Collect static files
- [ ] Configure web app in Web tab
- [ ] Set up WSGI configuration
- [ ] Add static file mappings
- [ ] Test the site loads correctly
- [ ] Test admin panel login
- [ ] Test shopping cart (add/remove items)
- [ ] Test checkout flow
- [ ] Test order email notification
- [ ] Test order history page
- [ ] Set up custom domain (optional)
- [ ] Configure database backups
- [ ] Enable HTTPS (Force HTTPS in Web tab)
- [ ] Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`

## 🔐 Security Checklist

- [ ] `DEBUG=False` in `.env`
- [ ] Strong `SECRET_KEY` generated
- [ ] Strong admin password
- [ ] `ALLOWED_HOSTS` correctly configured
- [ ] `CSRF_TRUSTED_ORIGINS` includes your domain(s)
- [ ] HTTPS enabled (Force HTTPS)
- [ ] `.env` file not committed to git
- [ ] Database backup scheduled

## 🎯 Next Steps

1. **Read the full guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Deploy your site**: Follow the steps above
3. **Bookmark the reference**: [archive/PYTHONANYWHERE_QUICKREF.md](archive/PYTHONANYWHERE_QUICKREF.md)
4. **Set up backups**: Schedule daily database backups
5. **Go live**: Configure your custom domain

---

**Ready to deploy?** Start with [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Questions?** Check [archive/PYTHONANYWHERE_QUICKREF.md](archive/PYTHONANYWHERE_QUICKREF.md) for common tasks and troubleshooting.

