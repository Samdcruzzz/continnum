# 🩺 Continuum (Gericure) — AI Health Memory Platform for Elderly Care

An **AI-orchestrated, longitudinal health memory system** for elderly patients — built to unify fragmented medical records, surface clinically relevant context at the point of care, and catch the risks that fall through the cracks in geriatric care: polypharmacy, cognitive decline, and functional deterioration.

🔗 **Live Demo:** [continnum-production.up.railway.app/frontend/index.html](https://continnum-production.up.railway.app/frontend/index.html)

---

## 🎯 The Problem

Elderly patients typically see multiple doctors across multiple institutions, with no single source of truth for their history. Critical signals — a slow cognitive decline reported only by a caregiver, a new drug interacting badly with five others already prescribed, a consent that quietly expired — get lost between systems. **Continuum** exists to stitch that fragmented record back together and let AI agents watch for the things a rushed clinician doesn't have time to cross-reference.

---

## ✨ Key Features

- **Unified longitudinal timeline** — every diagnosis, medication, procedure, lab, vital, and caregiver observation for a patient, merged chronologically with full traceability back to its source record
- **AI-powered clinical context synthesis** — turns a flat list of clinical events into a narrative summary at the point of care, with functional-decline trend analysis and confidence scoring
- **Real-time polypharmacy & dosing risk detection** — drug–drug interactions, drug–disease contraindications, geriatric/renal dosing checks, and duplicate-therapy detection against a curated interaction database, producing a 0–10 composite risk score
- **Cognitive decline tracking** — a dedicated agent for dementia-stage-aware risk stratification from longitudinal and caregiver-reported signals
- **Real-time alert engine + WebSocket streaming** — clinically significant findings are pushed live to connected dashboards instead of waiting for a manual chart review
- **Privacy-first consent enforcement** — consent (and its expiry) is checked at the database layer *before* any record reaches an AI agent, so access can't be extended by prompting the model
- **Caregiver observation layer** — structured capture of informal caregiver input (cognitive changes, mobility decline, medication adherence, falls, behavioral changes) that feeds directly into the AI agents
- **HIPAA-aligned compliance layer** — PHI encryption, audit logging, and access-control enforcement
- **JWT-based authentication** with role-based access control (clinician, caregiver, legal guardian, healthcare proxy)
- **Observability** — Prometheus metrics for HTTP, database, and AI-agent execution performance, with a Docker Compose stack for Grafana/Kibana/Elasticsearch dashboards

---

## 🤖 AI Agent Architecture

Rather than one monolithic model, Continuum runs a small **orchestrated team of specialist agents**, each owning one clinical concern:

| Agent | File | Responsibility |
|---|---|---|
| **Orchestrator** | `app/ai_agents/orchestrator.py` | Coordinates the agents below and assembles the final clinical response |
| **Consent Agent** | `app/ai_agents/consent_agent.py` | Enforces consent + expiry at the DB layer before any record reaches an AI agent |
| **Context Synthesis Agent** | `app/ai_agents/context_synthesis_agent.py` | Builds a narrative clinical summary from the patient's longitudinal history (10-year default window, diagnosis–medication linking, lab trending) |
| **Polypharmacy Risk Agent** | `app/ai_agents/polypharmacy_risk_agent.py` | Detects drug–drug/drug–disease risk, geriatric dosing issues, and duplicate therapy |
| **Cognitive Decline Agent** | `app/ai_agents/cognitive_decline_agent.py` | Dementia-stage-aware risk stratification from clinical + caregiver signals |
| **Alert Engine** | `app/ai_agents/alert_engine.py` | Generates and streams real-time clinical alerts over WebSocket |
| **Records Adapter** | `app/ai_agents/records_adapter.py` | Converts raw DB rows into the flat record format the agents consume |

---

## 🏗️ Architecture

```
Client (Web / Mobile / Third-party)
            │
   Authentication Layer (JWT / OAuth2 — app/routers/auth.py)
            │
   HIPAA Compliance & Security Layer (app/compliance/hipaa.py)
   — PHI encryption · audit logging · access control
            │
   API Layer (FastAPI)
   ┌─────────────────────────┬───────────────────────────┐
   │ Patients API             │ Clinical API               │
   │ (app/routers/patients.py)│ (app/routers/clinical.py)  │
   │ — CRUD + timeline        │ — summary, alerts,         │
   │                          │   recommendations,         │
   │                          │   medication analysis      │
   └─────────────────────────┴───────────────────────────┘
            │                              │
   WebSocket Streaming            AI Agent Orchestrator
   (app/routers/websocket.py)     (app/ai_agents/*)
            │                              │
            └──────────────┬───────────────┘
                            │
   Monitoring (Prometheus metrics — app/monitoring/metrics.py)
                            │
   Data Layer: PostgreSQL · Redis (cache/sessions) · Elasticsearch (logs/audit)
   Visualization: Grafana · Kibana · PgAdmin (via docker-compose.yml)
```

---

## 📁 Repository Structure

```
continuum/
├── main.py                       FastAPI entry point, app metadata, mounted routers
├── seed_demo.py                  Idempotent demo-data seeding script
├── requirements.txt              Python dependencies
├── Dockerfile / docker-compose.yml   Full production stack (Postgres, Redis, Elasticsearch,
│                                      Grafana, Kibana, PgAdmin, Prometheus)
├── init.sql                      DB initialization script
│
├── app/
│   ├── database.py                SQLAlchemy engine/session (DATABASE_URL-driven)
│   ├── models.py                  Patient, Doctor, MedicalRecord, Medicine,
│   │                               CaregiverObservation, Consent
│   ├── schemas.py                 Pydantic request/response schemas
│   │
│   ├── routers/
│   │   ├── patients.py            Patient CRUD + GET /api/patients/{id}/timeline
│   │   ├── clinical.py            AI-powered summaries, alerts, recommendations,
│   │   │                          medication analysis, clinical context
│   │   ├── auth.py                JWT auth: register, login, refresh, roles, logout
│   │   └── websocket.py           Real-time alert streaming + alert history/ack/resolve
│   │
│   ├── ai_agents/                 See "AI Agent Architecture" above
│   │
│   ├── compliance/
│   │   └── hipaa.py               PHI encryption, audit trail, access control
│   │
│   └── monitoring/
│       └── metrics.py             Prometheus metrics for requests, DB, and agents
│
├── frontend/
│   ├── index.html                 Main dashboard UI (Tailwind via CDN, no build step)
│   └── consent-dashboard.html     Guardian/consent management UI
│
├── monitoring/
│   ├── prometheus.yml             Prometheus scrape config
│   └── logstash.conf              Log pipeline config
│
├── tests/
│   └── test_comprehensive.py      Test suite (pytest)
│
└── docs/                          Design audits, phase completion reports, API reference,
                                    installation walkthrough
```

> **Note:** `app/routers/auth.py` exists in the codebase but is not currently wired into `main.py`'s `include_router()` calls — only `patients`, `clinical`, and `websocket` are mounted. Registering the auth router is a straightforward next step for anyone picking this up.

---

## 🚀 Getting Started

### Option 1 — Full stack with Docker Compose (recommended)

```bash
git clone https://github.com/<your-org>/continuum.git
cd continuum
docker-compose up -d
```

This brings up the app alongside PostgreSQL, Redis, Elasticsearch, Prometheus, Grafana, Kibana, and PgAdmin.

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Frontend dashboard | http://localhost:8000/frontend/index.html |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |
| Kibana | http://localhost:5601 |
| PgAdmin | http://localhost:5050 |

### Option 2 — Run locally with Python

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env            # configure DATABASE_URL and secrets
python main.py                  # or: uvicorn main:app --reload

python seed_demo.py             # seed demo patient data
```

**Quick local testing without PostgreSQL** — `app/database.py` reads `DATABASE_URL` from the environment, so you can point it at SQLite instead:

```bash
export DATABASE_URL="sqlite:///./dev.db"
python main.py
```

Then visit:
```bash
curl http://localhost:8000/api/patients/1/timeline
open http://localhost:8000/docs
open http://localhost:8000/frontend/index.html
```

### Running tests

```bash
pytest tests/ -v --cov=app
```

---

## 📡 API Overview

| Area | Endpoint | Method | Purpose |
|---|---|---|---|
| Patients | `/api/patients/` | GET/POST | List / create patients |
| Patients | `/api/patients/{id}` | GET | Patient details |
| Patients | `/api/patients/{id}/timeline` | GET | Full longitudinal record timeline |
| Clinical | `/api/clinical/patients/{id}/summary` | POST | AI-synthesized clinical summary |
| Clinical | `/api/clinical/patients/{id}/alerts` | GET | Active clinical alerts |
| Clinical | `/api/clinical/patients/{id}/recommendations` | GET | AI recommendations |
| Clinical | `/api/clinical/patients/{id}/analyze-medications` | POST | Polypharmacy / dosing risk analysis |
| Clinical | `/api/clinical/patients/{id}/clinical-context` | GET | Raw synthesized clinical context |
| Auth | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`, `/auth/logout` | — | JWT auth (see note above re: wiring) |
| Alerts | `/api/alerts/patients/{id}/history` | GET | Historical alert log |
| Alerts | `/api/alerts/patients/{id}/acknowledge/{alert_id}` | POST | Acknowledge an alert |
| Alerts | `/api/alerts/patients/{id}/resolve/{alert_id}` | POST | Resolve an alert |
| System | `/api/status`, `/health`, `/api/system/capabilities` | GET | Service health & capabilities |

Full request/response examples are in [`docs/CLINICAL_API_REFERENCE.md`](docs/CLINICAL_API_REFERENCE.md).

---

## 🔐 Security & Compliance

- **JWT/OAuth2 authentication** with role-based access control and refresh tokens
- **Consent enforcement at the data layer** — expiry checked before records reach any AI agent, so a prompt can't extend access
- **PHI encryption** (Fernet) and **audit trail logging** via `app/compliance/hipaa.py`
- **Tiered consent models** — patient self, legal guardian, healthcare proxy, HIPAA-covered clinician

---

## 🛣️ Roadmap

- Wire `frontend/index.html` to live API calls (currently a UI prototype with mock in-page data)
- Mount `auth.py` into `main.py` and enforce auth across the clinical/patients routers
- Guardian consent UI workflows
- Additional AI agents for broader risk stratification

See `docs/PHASE2_COMPLETION.md` and `docs/PHASE3_COMPLETION.md` for a full history of what's shipped, and `docs/PROJECT_AUDIT.md` for the original architecture audit.

---

## 👥 Team

| Member | GitHub |
|---|---|
| Team Leader | [Samdcruzzz](https://github.com/Samdcruzzz) |
| Team Member | [ThanuShree99](https://github.com/ThanuShree99) |
| Team Member | [sudhamanikandan206](https://github.com/sudhamanikandan206) |
| Team Member | [Shakthipriya0305](https://github.com/Shakthipriya0305) |

---

## 🔗 Links

- **Live Demo:** [continnum-production.up.railway.app/frontend/index.html](https://continnum-production.up.railway.app/frontend/index.html)
- **API Docs (Swagger):** `/docs` on the deployed instance
- **Full documentation:** see the [`docs/`](docs) folder

---

*Continuum exists so that no elderly patient's history — or the caregiver who noticed something was wrong first — gets lost between appointments.*
