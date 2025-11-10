# Railway Deployment Guide

This guide will help you deploy the MP Benti wholesale ordering platform to Railway.

## Prerequisites

1. A [Railway account](https://railway.app/) (free to start, ~$5-7 AUD/month for active usage)
2. A GitHub account (for connecting your repository)
3. Your code pushed to a GitHub repository

## Cost Estimate

With SQLite and low traffic (100 users, 1000 products):
- **Estimated cost**: $5-7 AUD/month (~$3-5 USD)
- Railway provides $5 USD monthly credit to start

## Deployment Steps

### 1. Push Your Code to GitHub

```bash
# If not already a git repository
git init
git add .
git commit -m "Initial commit - SQLite configuration"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/yourusername/mpbenti_site.git
git branch -M main
git push -u origin main
```

### 2. Create a New Project on Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select your `mpbenti_site` repository

### 3. Configure Environment Variables

In the Railway dashboard, go to your project → **Variables** tab and add:

```bash
# Required Variables
SECRET_KEY=your-super-secret-key-generate-with-openssl-rand-base64-32
DEBUG=False
ALLOWED_HOSTS=*.railway.app,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://your-app-name.railway.app

# Database (SQLite - Railway will use persistent volume)
DATABASE_URL=sqlite:////app/data/db.sqlite3

# Admin User (for first deployment)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@mpbenti.com.au
DJANGO_SUPERUSER_PASSWORD=your-secure-admin-password
```

**Generate a secure SECRET_KEY:**
```bash
openssl rand -base64 32
```

### 4. Add a Persistent Volume

Railway needs a persistent volume for your SQLite database:

1. In your Railway project, click **"+ New"** → **"Volume"**
2. Name it: `db_volume`
3. Mount path: `/app/data`
4. This ensures your database persists across deployments

### 5. Configure Custom Domain (Optional)

1. In Railway dashboard → **Settings** → **Domains**
2. Click **"Generate Domain"** for a free Railway subdomain
3. Or add your custom domain and update DNS records

### 6. Deploy

Railway will automatically:
- Build your Docker image
- Run migrations via `entrypoint.sh`
- Create the superuser
- Collect static files
- Start Gunicorn

Monitor the deployment in the **Deployments** tab.

### 7. Access Your Application

Once deployed:
- Visit your Railway URL: `https://your-app-name.railway.app`
- Admin panel: `https://your-app-name.railway.app/admin`
- Login with your configured superuser credentials

## Post-Deployment

### Load Initial Data (Products & Categories)

If you have the `initial_data.json` fixture:

```bash
# Using Railway CLI (install: npm i -g @railway/cli)
railway login
railway link  # Select your project
railway run python manage.py loaddata initial_data.json
```

Or via Railway dashboard shell:
1. Go to your service → **Terminal** tab
2. Run: `python manage.py loaddata initial_data.json`

### Database Backups

**Important**: SQLite is a single file, so regular backups are critical.

**Manual backup via Railway CLI:**
```bash
railway run python manage.py dumpdata > backup.json
```

**Automated backups**: Consider setting up:
- GitHub Actions to backup daily
- Railway cron job (requires addon)
- Or manually download `/app/data/db.sqlite3` periodically

### Monitoring

Railway provides:
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Alerts**: Set up notifications for downtime

## Scaling Considerations

### When to switch from SQLite:

If you experience:
- 100+ concurrent orders
- Database lock errors
- Need for horizontal scaling (multiple instances)

Then migrate to Railway's **PostgreSQL plugin**:
1. Add PostgreSQL service in Railway
2. Update `DATABASE_URL` to PostgreSQL connection string
3. Add `psycopg2-binary==2.9.9` to `requirements.txt`
4. Re-deploy

## Troubleshooting

### Deployment fails

Check Railway logs for errors. Common issues:
- Missing environment variables
- Volume not mounted correctly
- Build errors (check Dockerfile)

### Static files not loading

Ensure:
- `STATICFILES_STORAGE` is set correctly in `settings.py`
- Nginx configuration is correct (if using nginx service)
- Railway is serving static files via WhiteNoise

### Database not persisting

Verify:
- Volume is mounted to `/app/data`
- `DATABASE_URL` points to `/app/data/db.sqlite3`
- Volume is attached to your service

### Can't access admin panel

1. Verify superuser was created: Check deployment logs
2. Reset password if needed:
   ```bash
   railway run python manage.py changepassword admin
   ```

## Cost Optimization

To minimize costs:
- **Use Railway's free tier** as long as possible
- **Scale down workers**: Currently set to 2 workers (good for low traffic)
- **Monitor usage**: Railway dashboard shows your spend
- **Pause unused services**: If testing, pause when not in use

## Useful Railway CLI Commands

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link project
railway login
railway link

# View logs
railway logs

# Run Django management commands
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py collectstatic

# Open Railway dashboard
railway open

# SSH into your service
railway shell
```

## Support

- **Railway Docs**: https://docs.railway.app/
- **Railway Discord**: https://discord.gg/railway
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/

## Next Steps

1. Set up custom domain
2. Configure email backend for password resets
3. Set up regular database backups
4. Enable monitoring and alerts
5. Add your products and test ordering workflow
