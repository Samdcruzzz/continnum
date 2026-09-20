# Railway Deployment Guide

Complete step-by-step instructions to deploy Gericure Demo to Railway.

---

## ⚡ Quick Deploy (5 Minutes)

### Step 1: Sign Up to Railway

1. Go to [railway.app](https://railway.app)
2. Click **"Start Free"**
3. Click **"Deploy with GitHub"**
4. Authorize Railway to access your GitHub account
5. Done! Railway is connected

### Step 2: Create New Project

1. In Railway Dashboard, click **"New Project"**
2. Click **"Deploy from GitHub Repo"**
3. Search for: `gericure-demo`
4. Click to select the repository
5. Click **"Deploy"**

### Step 3: Add PostgreSQL Database

1. In your new Railway project, click **"+ New"** button (top right)
2. Click **"Database"** → **"PostgreSQL"**
3. Railway will:
   - Provision PostgreSQL database
   - Set `DATABASE_URL` environment variable
   - Start the deployment

### Step 4: Wait for Deployment

Railway will:
1. Detect Python application
2. Install dependencies from `requirements.txt`
3. Build Docker container
4. Start FastAPI server
5. Verify health check
6. Auto-assign domain name

**Estimated time:** 2-3 minutes

### Step 5: Get Your URL

In Railway Dashboard:
1. Click your "web" service
2. Go to **"Settings"** tab
3. Under **"Domains"** section
4. Copy the generated domain: `https://your-project-xxxxx.up.railway.app`

### Step 6: Test the Deployment

```bash
# Health check
curl https://your-domain.up.railway.app/health

# View API docs
# Open in browser: https://your-domain.up.railway.app/docs
```

**✅ Done!** Your backend is live on Railway! 🎉

---

## 📊 Seed Demo Data

After deployment, add the demo patient with 5 timeline events:

### Option 1: Via Railway CLI

```bash
# Install Railway CLI (if not already)
npm install -g @railway/cli

# Login to Railway
railway login

# Navigate to project directory
cd gericure-demo

# Link to Railway project
railway link

# Run seed script
railway run python seed_demo.py
```

### Option 2: Via Railway Dashboard

1. Open Railway Dashboard
2. Click your project
3. Click "web" service
4. Click **"Deployments"** tab
5. Select latest deployment
6. Look for **"Execute command"** section
7. Run: `python seed_demo.py`

### Option 3: Manual via SSH (Advanced)

```bash
railway connect  # Opens SSH connection to container
python seed_demo.py
exit
```

---

## 🔍 Verify Deployment

### Check Health Status

```bash
curl https://your-domain.up.railway.app/health
```

**Expected Response:**
```json
{"status": "healthy", "service": "Gericure Demo Backend", "version": "1.0.0"}
```

### View API Documentation

Open in browser:
```
https://your-domain.up.railway.app/docs
```

This opens **Swagger UI** with all endpoints.

### Test Patient Endpoint (After Seeding)

```bash
curl https://your-domain.up.railway.app/api/patients/1 | jq '.'
```

**Expected Response:**
```json
{
  "id": 1,
  "first_name": "Nagarajan",
  "last_name": "...",
  ...
}
```

### Test Timeline (NEW)

```bash
curl https://your-domain.up.railway.app/api/patients/1/timeline | jq '.total_events'
```

**Expected Response:** `5`

---

## 🔧 Environment Configuration

Railway automatically handles:
- `DATABASE_URL` - PostgreSQL connection (auto-set)
- `PORT` - Server port (auto-set)

### Optional Environment Variables

To add custom variables:

1. In Railway Dashboard
2. Click your "web" service
3. Go to **"Variables"** tab
4. Click **"+ New Variable"**
5. Add key-value pair

Examples:
```
ENV = production
DEBUG = false
CORS_ORIGINS = https://frontend-domain.com
```

---

## 📊 Monitoring & Logs

### View Logs

1. Railway Dashboard → Your Service → **"Logs"** tab
2. See real-time application output
3. Scroll to see deployment history

### View Metrics

1. Railway Dashboard → Your Service → **"Metrics"** tab
2. See CPU, memory, disk usage
3. Monitor performance

### Set Up Alerts (Optional)

1. Dashboard → Project Settings
2. Enable notifications
3. Get alerts on deployment failures

---

## 🔐 Secrets & Environment Variables

### Adding Sensitive Data

**IMPORTANT:** Never commit `.env` file to GitHub!

To add secrets safely:

1. Railway Dashboard → Your Service
2. Go to **"Variables"** tab
3. Click **"New Variable"**
4. Paste sensitive data (API keys, passwords, etc.)
5. **Do NOT use `.env` file in production!**

### Database Credentials

Railway auto-manages PostgreSQL credentials:
- You don't need to set `DATABASE_URL` manually
- It's automatically created when you add PostgreSQL
- Available to your app automatically

---

## ❌ Troubleshooting

### "Deployment Failed"

**Check logs:**
1. Go to Railway Dashboard
2. Click your service
3. Go to "Logs" tab
4. Look for error messages

**Common issues:**
- `ModuleNotFoundError` - Missing dependency in `requirements.txt`
- `Cannot connect to database` - PostgreSQL not linked
- `Port error` - App not respecting `$PORT` variable

### "Health Check Failed"

Your app might not be starting correctly.

**Check:**
1. Logs show any startup errors?
2. Is `/health` endpoint accessible?
3. Is PostgreSQL connected?

### "Cannot Connect to Database"

1. Verify PostgreSQL service exists in Railway
2. Check `DATABASE_URL` is set in variables
3. Review logs for connection errors

**Fix:**
1. Go to Railway Dashboard
2. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
3. This sets `DATABASE_URL` automatically

### "App keeps restarting"

Usually means crashes in startup.

**Check logs for:**
- Python import errors
- Missing environment variables
- Database connection issues

---

## 🚀 Auto-Deployment

Every push to `main` branch auto-deploys:

```bash
git push origin main
```

Railway will:
1. Detect changes
2. Rebuild container
3. Run tests (if configured)
4. Deploy new version
5. Perform health check
6. Redirect traffic (if healthy)

If deployment fails:
- Previous version keeps running
- Check logs for error messages
- Fix and push again

---

## 🔗 Custom Domain (Optional)

### Connect Your Domain

1. Railway Dashboard → Your Service → **"Settings"**
2. Under "Domains" section
3. Click **"+ Add Domain"**
4. Enter your domain (e.g., `api.example.com`)
5. Railway provides DNS settings
6. Update your domain's DNS records

**Note:** Free Railway includes 1 free domain

---

## 📈 Scaling (Optional)

If you need more resources:

1. Railway Dashboard → Your Service
2. Go to **"Settings"**
3. Under "Resources" section
4. Adjust:
   - CPU allocation
   - Memory allocation
   - Storage (if persistent)

**Note:** Paid plans have higher limits

---

## 🧹 Cleanup

### Stop Service (Keep Project)

1. Railway Dashboard → Your Service
2. Click **"..."** menu → **"Remove"**
3. Service stops, but project remains
4. Can redeploy later

### Delete Entire Project

1. Railway Dashboard → Project Settings
2. Scroll down → **"Delete Project"**
3. Confirm deletion
4. All services and databases removed

---

## 📞 Getting Help

### Railway Support

- [Railway Docs](https://docs.railway.app/)
- [Railway Community Discord](https://discord.gg/railway)
- [GitHub Issues](https://github.com/railwayapp/railway/issues)

### Gericure Demo Support

- Check `/docs` endpoint (Swagger UI)
- Review application logs
- Check `README.md` for architecture info

---

## ✅ Deployment Checklist

- [ ] Signed up for Railway account
- [ ] Connected GitHub repository
- [ ] Created new Railway project
- [ ] Added PostgreSQL database
- [ ] Deployment completed successfully
- [ ] Health check endpoint works
- [ ] Can access Swagger UI at `/docs`
- [ ] Seeded demo data (optional)
- [ ] Timeline endpoint returns 5 events
- [ ] All endpoints responding correctly

---

## 🎉 You're Done!

Your Gericure Demo backend is now:
- ✅ **Live** on Railway
- ✅ **Auto-deploying** on code changes
- ✅ **Monitored** with health checks
- ✅ **Scalable** with one-click upgrades
- ✅ **Secure** with automatic SSL/TLS

---

**Deployment complete! Your backend is ready for production.** 🚀

Next: 
1. Seed demo data with `railway run python seed_demo.py`
2. Build frontend (P1 phase)
3. Connect frontend to your Railway domain

---

Last updated: September 20, 2026
