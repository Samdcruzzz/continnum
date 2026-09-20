# 🚀 DEPLOY NOW - Quick Start

**Everything is ready. Deploy to Railway in 3 steps (5 minutes total).**

---

## ⚡ The 3 Steps

### Step 1: Create GitHub Repository (2 minutes)

Go to [github.com/new](https://github.com/new):

```
Repository name: gericure-demo
Description: AI-powered patient health record system
Visibility: Public
Skip initializing README (you have one)
Click "Create repository"
```

### Step 2: Push Code to GitHub (1 minute)

```bash
cd /home/claude/gericure-demo-github

git remote add origin https://github.com/Samdcruzzz/gericure-demo.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Railway (2 minutes)

Go to [railway.app](https://railway.app):

```
Click "New Project"
Click "Deploy from GitHub Repo"
Search for: gericure-demo
Click to select
Click "Deploy"
Wait 2-3 minutes...
```

**That's it!** ✅

---

## 🗄️ Add Database (1 minute)

In Railway Dashboard:

```
Click "+ New" (top right)
Click "Database" → "PostgreSQL"
Wait 30 seconds...
Done!
```

---

## ✅ Verify It Works (1 minute)

In Railway Dashboard:
1. Go to "web" service
2. Go to "Settings"
3. Copy domain under "Domains"
4. Test: `curl https://your-domain/health`

Should return: `{"status": "healthy", ...}`

---

## 🌱 Seed Demo Data (Optional, 1 minute)

```bash
cd /home/claude/gericure-demo-github
railway login
railway link  # Link to your project
railway run python seed_demo.py
```

---

## 📊 Verify Demo Data (1 minute)

```bash
# Get patient Nagarajan
curl https://your-domain/api/patients/1

# Get 5-event timeline
curl https://your-domain/api/patients/1/timeline | jq '.total_events'
# Should return: 5

# View API docs
# Open in browser: https://your-domain/docs
```

---

## 📋 Full Checklist

```
☐ Created GitHub repository at github.com/Samdcruzzz/gericure-demo
☐ Pushed code: git push -u origin main
☐ Created Railway project at railway.app
☐ Added PostgreSQL database
☐ Deployment completed (check "Logs" tab)
☐ Health check works: curl /health
☐ Can access Swagger UI: /docs
☐ Seeded demo data: railway run python seed_demo.py
☐ Timeline returns 5 events: /api/patients/1/timeline
```

---

## 🎯 Your Live URLs

After deployment, you'll have:

```
API Base: https://your-project-xxxxx.up.railway.app
Health:   https://your-project-xxxxx.up.railway.app/health
API Docs: https://your-project-xxxxx.up.railway.app/docs
Patient:  https://your-project-xxxxx.up.railway.app/api/patients/1
Timeline: https://your-project-xxxxx.up.railway.app/api/patients/1/timeline
```

Replace `your-project-xxxxx` with your actual Railway domain.

---

## 🔑 Auto-Deployment on Push

After first deployment, every push auto-deploys:

```bash
# Make changes
vim app/routers/patients.py

# Push to GitHub
git add .
git commit -m "Your message"
git push origin main

# Railway automatically redeploys! ✅
```

---

## 🆘 If Something Goes Wrong

### Check logs:
```bash
railway logs
```

### Common issues:
- **Build failed** → Check Python syntax, requirements.txt
- **Cannot connect to DB** → Make sure PostgreSQL is added
- **Health check fails** → Check logs, restart deployment

### Need help?
- Check RAILWAY_DEPLOY.md (detailed guide)
- Check README.md (architecture)
- Check GITHUB_SETUP.md (GitHub integration)

---

## 📞 Support

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- GitHub Issues: https://github.com/Samdcruzzz/gericure-demo/issues

---

## 🎉 That's All!

Your backend is live in 5 minutes!

Next: Build frontend and connect to your Railway domain.

---

**Ready? Start with Step 1 above!** 🚀

---

All files are ready:
- ✅ main.py (FastAPI app)
- ✅ app/ (all modules)
- ✅ requirements.txt (dependencies)
- ✅ Dockerfile (container config)
- ✅ railway.toml (Railway config)
- ✅ .gitignore (security)
- ✅ seed_demo.py (demo data)
- ✅ README.md (documentation)

Just push to GitHub and Railway handles the rest!
