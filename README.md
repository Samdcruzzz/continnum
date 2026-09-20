# Continuum — AI Health Memory Platform

A FastAPI + PostgreSQL backend for a longitudinal patient health record system, paired with a static frontend prototype ("Continuum — General Health Memory Platform"). 

## Project structure

```
continuum-health-memory/
├── main.py                      FastAPI entry point
├── seed_demo.py                 Idempotent demo-data seeding script (patient "Nagarajan")
├── requirements.txt             Python dependencies
├── .env.example                 Environment variable template (copy to .env)
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── database.py               SQLAlchemy engine/session (PostgreSQL, DATABASE_URL-driven)
│   ├── models.py                 SQLAlchemy models: Patient, Doctor, MedicalRecord,
│   │                              Medicine, CaregiverObservation, Consent
│   ├── schemas.py                Pydantic request/response schemas, incl. Timeline schemas
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── patients.py           Patient CRUD + GET /api/patients/{id}/timeline
│   │
│   └── ai_agents/
│       ├── __init__.py
│       ├── consent_agent.py      Consent + expiry enforcement (DB-layer, not prompt-bypassable)
│       └── records_adapter.py    Converts DB rows into the flat record format the AI agents use
│
├── frontend/
│   └── index.html                 Self-contained static UI prototype (Tailwind via CDN, no build step)
│
└── docs/
    ├── PROJECT_AUDIT.md           Original architecture/dependency audit
    ├── INSTALLATION_STEPS.md      Detailed step-by-step setup walkthrough
    ├── P0_CHANGES_MANIFEST.md     What changed in the P0 handoff and why
    └── IMPLEMENTATION_CHECKLIST.txt
```

## What was merged

This project previously existed as three disconnected pieces:

1. **`AI_Health_Memory_P0_Handoff`** — the real application logic:
   `models.py`, `schemas.py`, `routers/patients.py`, the two `ai_agents/`
   modules, and `seed_demo.py`.
2. **`FINAL_PROJECT_FIX`** — the infrastructure the app needs to actually
   run: `main.py`, `app/database.py`, the three `__init__.py` package
   markers, `requirements.txt`, and `.env.example`, plus a stack of audit
   docs.
3. **`index.html`** — a large, self-contained static frontend prototype
   (Tailwind CDN, vanilla JS, mock in-page data) that was never wired to
   the backend above.

Everything has been placed into one conventional Python package layout,
verified to import cleanly, and confirmed to expose the expected routes
(`/`, `/health`, `/api/patients/`, `/api/patients/{id}`,
`/api/patients/{id}/timeline`).

**Note on the frontend:** `frontend/index.html` is a UI prototype with
its own mock JavaScript data — it does not currently call the FastAPI
backend (no `fetch()` calls to `/api/...`). Wiring it up to the live API
is the natural next step and isn't done here, since it would mean writing
new integration code rather than reorganizing what already exists.

## Quick start

```bash
# 1. Install dependencies
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# edit .env with your PostgreSQL credentials (or see "Run without PostgreSQL" below)

# 3. Run the API
python main.py                  # or: uvicorn main:app --reload

# 4. In another terminal, seed demo data
python seed_demo.py

# 5. Try it
curl http://localhost:8000/api/patients/1/timeline
open http://localhost:8000/docs     # Swagger UI
```

### Run without PostgreSQL (quick local testing)

`app/database.py` reads `DATABASE_URL` from the environment. For a
zero-setup smoke test you can point it at SQLite instead:

```bash
export DATABASE_URL="sqlite:///./dev.db"
python main.py
```

### View the frontend prototype

`frontend/index.html` has no dependencies beyond a browser and internet
access (it pulls Tailwind and Google Fonts from CDNs). Just open it
directly:

```bash
open frontend/index.html            # macOS
# or: python -m http.server 5500 --directory frontend
```

## Key features

- **Longitudinal timeline** — `GET /api/patients/{id}/timeline` returns
  every medication, diagnosis, procedure, lab, vitals reading, and
  caregiver observation for a patient, chronologically sorted, each
  tagged with a `record_id` for traceability back to its source row.
- **Consent enforcement with expiry** — `consent_agent.py` checks
  `Consent.expiry_date` against the current date *before* any record is
  handed to an AI layer, so access can't be extended by prompting.
- **Medication change tracking** — `Medicine.change_note` records things
  like "dosage increased from 500mg to 750mg" and surfaces in both the
  timeline and the AI-facing record adapter.

## Further reading

See `docs/` for the original audit and setup documentation carried over
from the source packages.

