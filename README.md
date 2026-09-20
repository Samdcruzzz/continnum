# Gericure Demo - AI Health Memory System

FastAPI backend for patient health records with AI-powered insights, privacy enforcement, and chronological timeline tracking.

**Status:** ✅ Production Ready | ⚡ Deployed on Railway

---

## 🚀 Quick Deploy to Railway

### Step 1: Connect GitHub to Railway

1. Go to [railway.app](https://railway.app)
2. Sign up / Login with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Authorize Railway to access your GitHub account
6. Select this repository: `Samdcruzzz/gericure-demo`

### Step 2: Add Database

In Railway Dashboard:
1. Click **"+ New"** button
2. Select **"PostgreSQL"**
3. Railway will auto-configure `DATABASE_URL`

### Step 3: Configure Environment

Railway auto-detects and deploys! That's it. 🎉

**Auto-configured by Railway:**
- Python 3.11 environment
- PostgreSQL database connection
- Automatic port assignment (via `$PORT`)
- Health checks
- Auto-restarts on failure

---

## 📋 Features

✅ **Patient Management**
- Create, read, update patient records
- Full medical history tracking
- Multiple data categories (diagnoses, procedures, labs, vitals)

✅ **Chronological Timeline** (NEW)
- `GET /api/patients/{patient_id}/timeline`
- Events sorted by date
- Medication changes with notes
- Complete audit trail with record_id

✅ **Privacy Enforcement**
- Consent expiry checking at database layer
- Expired consent blocks data access
- Cannot be bypassed by prompts
- Fine-grained access control (categories)

✅ **Record Traceability**
- Every record includes `record_id`
- Audit trail for compliance
- Full chain of custody

✅ **Medication Tracking**
- `change_note` field for dosage/formula changes
- Track "why" medication changed
- Complete medication history

✅ **API Documentation**
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Interactive endpoint testing

---

## 🏗️ Project Structure

```
gericure-demo/
├── main.py                      # FastAPI entry point
├── seed_demo.py                 # Demo data seeding
├── requirements.txt             # Python dependencies
├── .env.local                   # Local environment (Railway uses secrets)
├── Dockerfile                   # Container configuration
├── railway.toml                 # Railway deployment config
│
├── app/
│   ├── __init__.py
│   ├── database.py              # PostgreSQL connection
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic validation schemas
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── patients.py          # Patient endpoints
│   │
│   └── ai_agents/
│       ├── __init__.py
│       ├── consent_agent.py     # Privacy enforcement
│       └── records_adapter.py   # Data adaptation layer
```

---

## 🔌 API Endpoints

### Patient Management
```
POST   /api/patients/                      Create patient
GET    /api/patients/                      List patients
GET    /api/patients/{patient_id}          Get patient
GET    /api/patients/{patient_id}/timeline Get timeline (NEW)
```

### Health & Status
```
GET    /health                             Health check
GET    /                                   API info
GET    /docs                               Swagger UI
GET    /redoc                              ReDoc
```

---

## 📊 Database Schema

### Tables

**patients** - Patient records  
**doctors** - Healthcare providers  
**medicines** - Prescriptions (with `change_note`)  
**medical_records** - Diagnoses, procedures, vitals, labs  
**caregiver_observations** - Family/caregiver notes  
**consents** - Privacy/access control with expiry dates  

---

## 🔑 Environment Variables

Railway automatically sets:
- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Server port (default 8000)

Optional:
- `ENV` - Environment mode (development/production)
- `DEBUG` - Debug logging (true/false)

---

## 🧪 Testing After Deployment

### Health Check
```bash
curl https://your-railway-domain.up.railway.app/health
```

### Get Demo Patient
```bash
curl https://your-railway-domain.up.railway.app/api/patients/1
```

### Timeline (NEW P0 Feature)
```bash
curl https://your-railway-domain.up.railway.app/api/patients/1/timeline
```

### Swagger UI
Open in browser:
```
https://your-railway-domain.up.railway.app/docs
```

---

## 🌱 Seed Demo Data

After deployment, seed the demo patient (Nagarajan) with 5-event timeline:

```bash
railway run python seed_demo.py
```

Or via Railway dashboard:
1. Open project
2. Click your service
3. Go to "Deployments" tab
4. Select latest deployment
5. Click "..." menu → "View Logs" or run command in console

---

## 🔐 Security Notes

### Secrets Management

Railway handles secrets safely:
1. Create variables in Railway dashboard
2. Never add `.env` to git
3. `.env.local` is git-ignored

### Environment Variables (Railway Dashboard)

Add these in Railway Variables section:
```
DATABASE_URL = postgresql://user:pass@host:port/dbname
# Railway auto-generates this when you add PostgreSQL
```

---

## 📈 Monitoring

### View Logs
Railway dashboard → Your Service → "Logs" tab

### Performance Metrics
Railway dashboard → Your Service → "Metrics" tab

### Health Status
```bash
curl https://your-domain/health
```

---

## 🚀 Deployment Pipeline

Every push to main branch:
1. Railway detects changes
2. Builds Python 3.11 environment
3. Installs dependencies from `requirements.txt`
4. Runs `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Performs health check
6. Redirects traffic to new deployment (if healthy)

---

## 🛠️ Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.local .env
# Edit .env with PostgreSQL credentials

# Run locally
python main.py
```

### Database Setup (Local)

```bash
# Create PostgreSQL database
createdb gericure_demo

# Or via psql:
psql -U postgres
CREATE DATABASE gericure_demo;
\q

# Seed demo data
python seed_demo.py
```

---

## 📚 Documentation

- **[Complete Audit](./docs/PROJECT_AUDIT.md)** - Technical architecture
- **[Installation Guide](./docs/INSTALLATION_STEPS.md)** - Local setup
- **[Command Reference](./docs/START_COMMANDS.txt)** - Quick commands
- **[Missing Files Report](./docs/MISSING_FILES_REPORT.md)** - What was generated

---

## 🤝 Contributing

1. Clone repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes
4. Commit: `git commit -m "Add amazing feature"`
5. Push: `git push origin feature/amazing-feature`
6. Open Pull Request

All pushes to `main` auto-deploy to Railway.

---

## 📝 Technologies

- **Framework:** FastAPI 0.104.1
- **Server:** Uvicorn 0.24.0
- **Database:** PostgreSQL 12+
- **ORM:** SQLAlchemy 2.0.23
- **Validation:** Pydantic 2.5.0
- **Deployment:** Railway
- **Container:** Docker
- **Python:** 3.11

---

## 📞 Support

For issues or questions:
1. Check `/docs` endpoint (Swagger UI)
2. Review logs in Railway dashboard
3. Check GitHub Issues
4. Email: ktmsjsam@gmail.com

---

## 📄 License

This project is part of the Gericure Demo - AI Health Memory System

---

## 🎯 P0 Features

✅ Chronological patient timeline  
✅ Medication change tracking (`change_note`)  
✅ Privacy enforcement with consent expiry  
✅ Record traceability via `record_id`  
✅ Demo patient (Nagarajan) with 5-event timeline  
✅ PostgreSQL integration  
✅ Production-ready code  

---

**Deployed with ❤️ on [Railway](https://railway.app)**

Updated: September 20, 2026
