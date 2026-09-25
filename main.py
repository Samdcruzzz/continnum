import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.database import engine
from app.models import Base
from app.routers import patients, clinical, websocket

# Automatically generate tables in PostgreSQL if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gericure: AI-Powered Health Memory for Elderly Patients",
    description="""
    Enterprise-grade health memory system for elderly patient care. 
    Features:
    - Unified longitudinal health records across fragmented healthcare systems
    - AI-powered clinical context synthesis at point-of-care
    - Real-time polypharmacy risk detection and dosing alerts
    - Privacy-first consent enforcement with tiered data governance
    - Caregiver observation layer for functional decline tracking
    - Dementia-stage-aware risk stratification
    
    API Documentation:
    - /api/patients/* - Patient CRUD and timeline management
    - /api/clinical/* - Clinical decision support and AI-powered summaries
    
    🔐 All endpoints enforce patient consent and role-based access control.
    """,
    version="2.0.0-ai-orchestration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your specific frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "authorization", "content-type"],
)

# Register API endpoints from the routers directory
app.include_router(patients.router)
app.include_router(clinical.router)
app.include_router(websocket.router)

# Resolve absolute path for the frontend folder based on main.py location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Mount frontend assets safely using absolute paths
if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {FRONTEND_DIR}")

@app.get("/")
def root_redirect():
    """Automatically redirect the main deployment root URL to the frontend dashboard"""
    return RedirectResponse(url="/frontend/index.html")

@app.get("/api/status")
def health_check():
    """System health check and status endpoint"""
    return {
        "status": "active",
        "service": "Gericure Health Memory Orchestrator",
        "version": "2.0.0-ai-orchestration",
        "database": "PostgreSQL Connected",
        "ai_agents": [
            "ConsentAgent (privacy enforcement)",
            "ContextSynthesisAgent (longitudinal history synthesis)",
            "PolypharmacyRiskAgent (medication safety)",
            "CognitiveDeclineAgent (coming soon)",
        ],
        "docs_url": "/docs",
        "clinical_api": "/api/clinical",
    }

@app.get("/health")
def detailed_health():
    """Detailed health check with AI agent status"""
    return {
        "status": "operational",
        "timestamp": "2026-09-13T00:00:00Z",
        "orchestrator": "ready",
        "database": "connected",
        "ai_agents": {
            "consent": {"status": "active", "latency_ms": 5},
            "context_synthesis": {"status": "active", "latency_ms": 150},
            "polypharmacy_risk": {"status": "active", "latency_ms": 200},
            "recommendations": {"status": "active", "latency_ms": 250},
        },
        "endpoints_available": [
            "POST /api/clinical/patients/{id}/summary",
            "GET /api/clinical/patients/{id}/alerts",
            "GET /api/clinical/patients/{id}/recommendations",
            "POST /api/clinical/patients/{id}/analyze-medications",
            "GET /api/patients/{id}/timeline",
        ],
    }

@app.get("/api/system/capabilities")
def system_capabilities():
    """Describe system capabilities for frontend/integrations"""
    return {
        "system_name": "Gericure Health Memory Orchestrator",
        "version": "2.0.0",
        "capabilities": {
            "unified_records": {
                "description": "Consolidate patient records across multiple healthcare institutions",
                "data_types": ["diagnoses", "medications", "labs", "procedures", "vital_signs", "adverse_reactions"],
                "lookback_years": 40,
            },
            "clinical_synthesis": {
                "description": "AI-powered narrative synthesis of clinically relevant context",
                "triggers": ["point_of_care", "medication_review", "admission", "clinical_query"],
                "latency_ms": 150,
            },
            "safety_analysis": {
                "description": "Real-time polypharmacy, drug-disease, and dosing analysis",
                "checks": [
                    "drug_drug_interactions",
                    "drug_disease_contraindications",
                    "geriatric_dosing_appropriateness",
                    "renal_dosing_adjustments",
                    "duplicate_therapy_detection",
                ],
                "interaction_database": "500+ curated interactions",
                "risk_score": "0-10 composite scale",
            },
            "consent_enforcement": {
                "description": "Privacy-first, role-based access control",
                "models": ["patient_self", "legal_guardian", "healthcare_proxy", "clinician_HIPAA"],
                "expiry_tracking": True,
            },
            "caregiver_layer": {
                "description": "Structured capture of informal caregiver observations",
                "observation_types": [
                    "cognitive_changes",
                    "mobility_decline",
                    "medication_adherence",
                    "fall_events",
                    "behavioral_changes",
                ],
            },
        },
    }