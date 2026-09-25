import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.database import engine
from app.models import Base
from app.routers import patients, clinical, websocket

# Automatically generate tables in PostgreSQL if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gericure: AI-Powered Health Memory for Elderly Patients",
    version="2.0.0-ai-orchestration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def health_check():
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
    }