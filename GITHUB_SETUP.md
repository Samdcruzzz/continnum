# GitHub Setup & Deployment Instructions

Everything is ready to push to GitHub and auto-deploy to Railway!

---

## 📋 What You Have

✅ Complete git repository with all code  
✅ All 7 generated files (main.py, database.py, etc.)  
✅ All P0 handoff files (models, schemas, routers, agents)  
✅ Railway configuration (railway.toml, Dockerfile)  
✅ .gitignore for security  
✅ Comprehensive documentation  

---

## 🚀 Step 1: Create GitHub Repository

### Option A: Using GitHub Web Interface (Easy)

1. Go to [github.com/new](https://github.com/new)
2. **Repository name:** `gericure-demo`
3. **Description:** `AI-powered patient health record system with privacy enforcement`
4. **Visibility:** Public (or Private if preferred)
5. **Skip initializing with README** (you already have one)
6. Click **"Create repository"**

### Option B: Using GitHub CLI (Faster)

```bash
gh repo create gericure-demo --public --source=. --remote=origin --push
```

---

## 🔗 Step 2: Add Remote & Push

### If you created repo via web:

```bash
# Navigate to your repo directory
cd /home/claude/gericure-demo-github

# Add remote origin
git remote add origin https://github.com/Samdcruzzz/gericure-demo.git

# Verify remote
git remote -v
# Should show:
# origin  https://github.com/Samdcruzzz/gericure-demo.git (fetch)
# origin  https://github.com/Samdcruzzz/gericure-demo.git (push)

# Push to GitHub
git branch -M main
git push -u origin main
```

### If you used GitHub CLI:

```bash
# Push is already done! Just verify:
git remote -v
git log --oneline | head -3
```

---

## ✅ Verify on GitHub

1. Go to [github.com/Samdcruzzz/gericure-demo](https://github.com/Samdcruzzz/gericure-demo)
2. You should see:
   - ✅ README.md with project description
   - ✅ main.py in root
   - ✅ app/ folder with all subfolders
   - ✅ requirements.txt
   - ✅ railway.toml
   - ✅ Dockerfile
   - ✅ All 17 files committed

---

## 🚂 Step 3: Deploy to Railway

### Option A: Railway Dashboard (Easiest)

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Click **"Deploy from GitHub Repo"**
4. Search for: `gericure-demo`
5. Select the repository
6. Click **"Deploy"**
7. Wait 2-3 minutes

Railway will:
- Detect Python application
- Install dependencies
- Build Docker container
- Auto-assign domain
- Start server

### Option B: Railway CLI (Faster)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# In your repo directory
cd /home/claude/gericure-demo-github

# Create new project and deploy
railway init

# Railway will prompt:
# 1. Project name: gericure-demo
# 2. Add PostgreSQL? Yes
# 3. Deploy? Yes

# Push code
git push

# That's it! Auto-deployed!
```

---

## 🗄️ Step 4: Add PostgreSQL Database

In Railway Dashboard:

1. Click your project
2. Click **"+ New"** button (top right)
3. Select **"Database"** → **"PostgreSQL"**
4. Railway auto-creates:
   - PostgreSQL instance
   - Sets `DATABASE_URL` variable
   - Configures connection pooling

**Status:** Ready! Your backend is live!

---

## 🧪 Step 5: Test the Deployment

Once Railway finishes deployment (2-3 minutes):

### Get Your Domain

1. Railway Dashboard → Your Service
2. Go to **"Settings"**
3. Copy domain from **"Domains"** section
4. Format: `https://your-project-xxxxx.up.railway.app`

### Test Health Check

```bash
curl https://your-domain.up.railway.app/health
```

**Expected:**
```json
{"status": "healthy", "service": "Gericure Demo Backend", "version": "1.0.0"}
```

### View Swagger UI

Open in browser:
```
https://your-domain.up.railway.app/docs
```

### List Patients (After Seeding)

```bash
curl https://your-domain.up.railway.app/api/patients/
```

---

## 🌱 Step 6: Seed Demo Data (Optional)

### Via Railway CLI

```bash
cd /home/claude/gericure-demo-github
railway run python seed_demo.py
```

### Via Railway Dashboard

1. Railway Dashboard → Your Service
2. Click **"Deployments"**
3. Select latest deployment
4. Look for **"Execute command"** section
5. Run: `python seed_demo.py`

**Expected output:**
```
✓ Patient created: Nagarajan (ID: 1)
✓ Doctor created: Dr. Ramesh (ID: 1)
✓ Event 1-5 created...
✓ Consent created...
DEMO SEEDING COMPLETE
```

---

## 🔄 Auto-Deployment Setup

After pushing to GitHub, every change auto-deploys:

```bash
# Make code changes
vim app/routers/patients.py

# Commit and push
git add .
git commit -m "Add new endpoint"
git push origin main

# Railway automatically:
# 1. Detects changes
# 2. Rebuilds container
# 3. Runs tests
# 4. Deploys new version
# 5. Performs health check
# 6. Updates live service
```

---

## 🔐 Environment Variables

Railway auto-manages:
- `DATABASE_URL` ✅ Auto-set when PostgreSQL added
- `PORT` ✅ Auto-set (usually 8000)

Optional (via Railway Dashboard):
- `ENV=production`
- `DEBUG=false`
- `CORS_ORIGINS=https://your-frontend.com`

---

## 📊 Verify Everything

### Checklist

- [ ] GitHub repository created
- [ ] Code pushed to main branch
- [ ] Railway project created
- [ ] PostgreSQL database added
- [ ] Deployment successful (2-3 min)
- [ ] Health check works
- [ ] Swagger UI accessible at `/docs`
- [ ] Demo data seeded (optional)
- [ ] Timeline endpoint returns 5 events
- [ ] All endpoints responding

---

## 🆘 Troubleshooting

### Deployment Failed

**Check logs:**
```bash
railway logs
# or via Dashboard → Logs tab
```

**Common issues:**
- Missing dependency → Add to `requirements.txt`
- Import error → Check `__init__.py` files
- Database error → Verify PostgreSQL is linked

### Health Check Failing

**Check:**
1. Application starts? `railway logs`
2. Does `/health` endpoint exist? (It does!)
3. Is PostgreSQL connected? Check logs

### Cannot Connect to Database

**Fix:**
1. Railway Dashboard → Your Service → Variables
2. Verify `DATABASE_URL` exists
3. If missing, add PostgreSQL:
   - Click **"+ New"** → **"Database"** → **"PostgreSQL"**

---

## 📈 Next Steps

### After Successful Deployment:

1. **Test thoroughly**
   - All endpoints working?
   - Swagger UI responsive?
   - Demo patient showing?

2. **Monitor logs**
   - Railway Dashboard → Logs tab
   - Watch for errors in production

3. **Build frontend (P1 phase)**
   - React/Vue connecting to `/docs`
   - Use your Railway domain as backend API

4. **Set up custom domain (optional)**
   - Railway Dashboard → Settings → Domains
   - Point your domain to Railway

5. **Enable monitoring (optional)**
   - Railway Dashboard → Alerts
   - Get notified of deployment failures

---

## 📞 Support Resources

- **Railway Docs:** https://docs.railway.app/
- **Railway Discord:** https://discord.gg/railway
- **Gericure Demo README:** In repo root
- **RAILWAY_DEPLOY.md:** Detailed deployment guide

---

## 🎉 You're Done!

Your Gericure Demo backend is:
- ✅ **On GitHub** (version controlled, shareable)
- ✅ **On Railway** (live, auto-deploying)
- ✅ **Production Ready** (health checks, monitoring)
- ✅ **Scalable** (one-click upgrades)
- ✅ **Secure** (auto SSL/TLS)

---

**Backend live! Next: Build your frontend and connect it to your Railway domain.** 🚀

---

Quick Links:
- GitHub: https://github.com/Samdcruzzz/gericure-demo
- Railway: https://railway.app
- Documentation: See RAILWAY_DEPLOY.md

Last updated: September 20, 2026
