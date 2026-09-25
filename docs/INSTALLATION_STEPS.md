# GERICURE DEMO - INSTALLATION STEPS

**Complete setup guide for the Gericure Demo FastAPI backend**

---

## PREREQUISITES

### System Requirements
- Python 3.9+ (check with: `python --version`)
- PostgreSQL 12+ (check with: `psql --version`)
- pip (Python package manager)
- Git (for version control)

### Check Prerequisites
```bash
python --version      # Should be 3.9+
pip --version         # Should be present
psql --version        # Should be 12+
```

---

## STEP 1: SET UP POSTGRESQL DATABASE

### Option A: PostgreSQL Already Running Locally

```bash
# Connect to PostgreSQL as superuser (usually 'postgres')
psql -U postgres

# In psql prompt, create database:
CREATE DATABASE gericure_demo;

# Exit psql
\q
```

### Option B: PostgreSQL Not Running

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
createdb gericure_demo
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb gericure_demo
```

**Windows:**
- Download PostgreSQL installer from https://www.postgresql.org/download/windows/
- Run installer, note the password you set for 'postgres' user
- Open pgAdmin (comes with installer)
- Create new database named 'gericure_demo'

**Docker (Optional):**
```bash
docker run --name gericure-postgres -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=gericure_demo -p 5432:5432 -d postgres:15
```

### Verify Database Created
```bash
psql -U postgres -l | grep gericure_demo
# Should show: gericure_demo | postgres | ...
```

---

## STEP 2: PREPARE PROJECT DIRECTORY

```bash
# Navigate to your Gericure_demo project
cd /path/to/Gericure_demo

# Verify project structure (from P0 handoff)
ls -la app/
# Should show: models.py, schemas.py, routers/, ai_agents/

ls -la app/routers/
# Should show: patients.py

ls -la app/ai_agents/
# Should show: consent_agent.py, records_adapter.py

ls -la
# Should show: seed_demo.py
```

---

## STEP 3: INSTALL GENERATED FILES

### 3a. Copy Generated Python Files

From the audit output folder (`FINAL_PROJECT_FIX/GENERATED_FILES/`), copy these files:

```bash
# Copy main.py to project root
cp FINAL_PROJECT_FIX/GENERATED_FILES/main.py ./

# Copy database.py to app/
cp FINAL_PROJECT_FIX/GENERATED_FILES/app_database.py ./app/database.py

# Copy __init__.py files to packages
cp FINAL_PROJECT_FIX/GENERATED_FILES/app__init__.py ./app/__init__.py
cp FINAL_PROJECT_FIX/GENERATED_FILES/app_routers__init__.py ./app/routers/__init__.py
cp FINAL_PROJECT_FIX/GENERATED_FILES/app_ai_agents__init__.py ./app/ai_agents/__init__.py
```

### 3b. Copy Configuration Files

```bash
# Copy environment template
cp FINAL_PROJECT_FIX/GENERATED_FILES/.env.example ./

# Copy dependency list
cp FINAL_PROJECT_FIX/GENERATED_FILES/requirements.txt ./
```

### 3c. Verify Files Copied

```bash
# Check Python files
ls -la main.py
ls -la app/database.py
ls -la app/__init__.py
ls -la app/routers/__init__.py
ls -la app/ai_agents/__init__.py

# Check config files
ls -la .env.example
ls -la requirements.txt
```

---

## STEP 4: CREATE PYTHON VIRTUAL ENVIRONMENT

```bash
# Create venv
python -m venv venv

# Activate venv
# On macOS/Linux:
source venv/bin/activate

# On Windows (CMD):
venv\Scripts\activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
```

### If Activation Fails

**macOS/Linux:**
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

**Windows PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

---

## STEP 5: INSTALL PYTHON DEPENDENCIES

```bash
# Upgrade pip first (recommended)
pip install --upgrade pip setuptools wheel

# Install from requirements.txt
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import sqlalchemy; print('✓ Dependencies OK')"
```

### If Installation Fails

```bash
# Try alternative installation method
pip install --upgrade --force-reinstall -r requirements.txt

# Check for specific errors
pip install -v -r requirements.txt  # Verbose mode

# If psycopg2-binary fails, try psycopg2 instead:
pip install psycopg2
```

---

## STEP 6: CONFIGURE ENVIRONMENT VARIABLES

### 6a. Create .env File

```bash
cp .env.example .env
```

### 6b. Edit .env with Your Database Credentials

Open `.env` in a text editor:

```bash
# macOS/Linux:
nano .env

# Or use any editor:
vim .env      # vim
code .env     # VS Code
gedit .env    # GNOME Text Editor
```

**Fill in with your PostgreSQL credentials:**

```env
# For local PostgreSQL with default credentials:
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=gericure_demo
DATABASE_USER=postgres
DATABASE_PASSWORD=password

# Or use full URL:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/gericure_demo
```

### 6c. Verify Environment File

```bash
# Check .env exists and is readable
cat .env | grep DATABASE_HOST
# Should output your host
```

---

## STEP 7: TEST DATABASE CONNECTION

```bash
# Activate venv if not already
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Test connection
python -c "
from app.database import engine
try:
    connection = engine.connect()
    connection.close()
    print('✓ Database connection successful!')
except Exception as e:
    print(f'✗ Connection failed: {e}')
"
```

### If Connection Fails

**Check credentials:**
```bash
# Verify with psql
psql -U postgres -d gericure_demo -c "SELECT 1;"
```

**Check environment variables are loaded:**
```bash
python -c "import os; print(f'HOST: {os.getenv(\"DATABASE_HOST\")}')"
```

**Check .env syntax:**
```bash
grep "DATABASE_" .env
# Should show your values without quotes
```

---

## STEP 8: CREATE DATABASE TABLES

```bash
# Load environment
source .env  # or: export $(cat .env | xargs)

# Create tables
python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('✓ Database tables created successfully!')
"

# Verify tables created
psql -U postgres -d gericure_demo -c "\dt"
# Should show: patients, doctors, medicines, medical_records, caregiver_observations, consents
```

---

## STEP 9: VERIFY APPLICATION STARTUP

```bash
# Load environment if not already loaded
source .env  # or: export $(cat .env | xargs)

# Test import all modules
python -c "
from app import database, models, schemas, routers
from app.routers import patients
from app.ai_agents import consent_agent, records_adapter
print('✓ All modules import successfully!')
"
```

---

## STEP 10: START BACKEND SERVER

```bash
# Load environment
source .env  # or: export $(cat .env | xargs)

# Start with Python (recommended for development)
python main.py

# Alternative: Start with uvicorn directly
# uvicorn main:app --reload

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# Press CTRL+C to stop
```

### Server Started Successfully?
- You should see: `INFO: Uvicorn running on http://0.0.0.0:8000`
- Leave this terminal running

---

## STEP 11: TEST API ENDPOINTS (In Another Terminal)

### 11a. Open New Terminal
```bash
# Keep server running in first terminal
# Open new terminal, navigate to project
cd /path/to/Gericure_demo
source venv/bin/activate
```

### 11b. Test Basic Endpoints

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy",...}

# Root endpoint
curl http://localhost:8000/
# Expected: API information

# List patients (empty initially)
curl http://localhost:8000/api/patients/
# Expected: [] (empty array)
```

---

## STEP 12: SEED DEMO DATA

### 12a. Run Seed Script

```bash
# In new terminal with venv activated:
cd /path/to/Gericure_demo
source venv/bin/activate
source .env  # Load environment

python seed_demo.py
```

### Expected Output:
```
============================================================
P0 DEMO SEEDING: Patient Nagarajan Timeline
============================================================

✓ Patient created: Nagarajan (ID: 1)
✓ Doctor created: Dr. Ramesh (ID: 1)
✓ Event 1 (Sept 2024): Diabetes diagnosis + Metformin 500mg started
✓ Event 2 (Jan 2025): Metformin increased to 750mg + caregiver observation
✓ Event 3 (Apr 2025): Hypertension diagnosed + Amlodipine 5mg started
✓ Event 4 (Aug 2025): Amlodipine reduced to 2.5mg + vitals improving
✓ Event 5 (Sept 2026): Annual checkup - stable on current medications
✓ Consent created: Doctor has access to diagnosis, medicines, follow-up, vitals (Expires: 2027-09-08)

============================================================
DEMO SEEDING COMPLETE
============================================================
```

### If Seed Fails

```bash
# Check database connection
python -c "from app.database import SessionLocal; db = SessionLocal(); print('✓ Session OK'); db.close()"

# Check if patient already exists
python -c "from app.database import SessionLocal; from app.models import Patient; db = SessionLocal(); print(f'Patients: {db.query(Patient).count()}'); db.close()"

# Manually check with psql
psql -U postgres -d gericure_demo -c "SELECT COUNT(*) FROM patients;"
```

---

## STEP 13: TEST DEMO PATIENT API

```bash
# Test patient retrieval
curl http://localhost:8000/api/patients/1
# Expected: {"id":1,"first_name":"Nagarajan",...}

# Test timeline endpoint (new P0 feature)
curl http://localhost:8000/api/patients/1/timeline
# Expected: {"patient_id":1,"total_events":5,"events":[...]}

# Check timeline events
curl http://localhost:8000/api/patients/1/timeline | jq '.events | length'
# Expected: 5

# Check timeline is chronological
curl http://localhost:8000/api/patients/1/timeline | jq '.events | map(.date)'
# Expected: ["2024-09-10", "2025-01-15", "2025-04-05", "2025-08-12", "2026-09-08"]

# Check medications have change_note
curl http://localhost:8000/api/patients/1/timeline | jq '.events[] | select(.event_type=="medication") | .description' | head -1
# Expected: Should include "Change:" information
```

---

## STEP 14: VIEW API DOCUMENTATION

Open in browser:
```
http://localhost:8000/docs
```

This opens the **Swagger UI** with interactive API testing.

You can:
- See all available endpoints
- Read descriptions and schemas
- Make test requests with "Try it out"
- View request/response examples

---

## FINAL VERIFICATION CHECKLIST

✅ Python 3.9+ installed  
✅ PostgreSQL running with gericure_demo database  
✅ All 7 generated files copied to correct locations  
✅ Virtual environment created and activated  
✅ Dependencies installed (pip install -r requirements.txt)  
✅ .env file created and configured with DB credentials  
✅ Database tables created successfully  
✅ All modules import without errors  
✅ Server starts with python main.py  
✅ Health check endpoint responds  
✅ Demo patient seeded with python seed_demo.py  
✅ Timeline endpoint returns 5 events  
✅ Events are chronologically sorted  
✅ Swagger UI accessible at /docs  

---

## TROUBLESHOOTING

### "ModuleNotFoundError: No module named 'app'"
- Verify you're in the correct directory
- Check venv is activated: `which python` should show venv path
- Try: `python -m pip install -e .`

### "psycopg2 error" or "Cannot connect to database"
- Check PostgreSQL is running: `psql -U postgres`
- Check credentials in .env match your setup
- Test with: `psql -U postgres -d gericure_demo`

### "main.py not found"
- Verify it was copied to project root
- Check with: `ls -la main.py`

### Timeline endpoint returns empty
- Check seed_demo.py ran successfully
- Verify with: `psql -U postgres -d gericure_demo -c "SELECT COUNT(*) FROM patients;"`
- Re-run seed_demo.py if needed

### Change_note column not found
- SQLAlchemy auto-creates columns
- If stuck, manually: `ALTER TABLE medicines ADD COLUMN change_note TEXT;`

### Port 8000 already in use
- Use different port: `python -m uvicorn main:app --port 8001`
- Or kill process using port 8000

---

## NEXT STEPS

1. **Verify all tests pass** (see checklist above)
2. **Test AI agents** (consent_agent, records_adapter)
3. **Test consent expiry** (see README_P0_HANDOFF.md)
4. **Demo walkthrough** (show judge the timeline)
5. **Frontend integration** (P1 phase)

---

## QUICK REFERENCE COMMANDS

```bash
# Activate environment
source venv/bin/activate

# Load environment variables
source .env

# Start server
python main.py

# Seed demo data (new terminal)
python seed_demo.py

# Test API
curl http://localhost:8000/api/patients/1/timeline | jq '.'

# View Swagger UI
# Open browser: http://localhost:8000/docs

# Database inspection
psql -U postgres -d gericure_demo
  SELECT COUNT(*) FROM patients;
  SELECT * FROM consents;
  \d medicines  -- show table schema
  \q -- exit

# Stop server
# Press CTRL+C in server terminal

# Deactivate environment
deactivate

# Delete venv (to start fresh)
rm -rf venv
```

---

## SUPPORT

For issues:
1. Check Troubleshooting section above
2. Review PROJECT_AUDIT.md for architecture
3. Review README_P0_HANDOFF.md for P0 requirements
4. Check server logs (main.py output)
5. Verify database state with psql

---

**Installation complete!** Your Gericure Demo backend is now ready to run.
