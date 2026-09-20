"""
Gericure Demo - FastAPI Backend Application

Entry point for the AI Health Memory system.

This application provides:
- Patient management APIs
- Medical records tracking
- Medication history with change notes
- Chronological timeline endpoint
- Privacy enforcement (consent with expiry)
- Record traceability (record_id in all responses)

Start with: python main.py
Or with uvicorn: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.models import Base
from app.routers import patients

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Gericure Demo - AI Health Memory",
    description="AI-powered patient health record system with privacy enforcement",
    version="1.0.0",
)

# Configure CORS (allow frontend to make requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients.router)


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for deployment/monitoring."""
    return {
        "status": "healthy",
        "service": "Gericure Demo Backend",
        "version": "1.0.0",
    }


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Gericure Demo - AI Health Memory System",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/health",
        "endpoints": {
            "patients": {
                "list": "GET /api/patients/",
                "create": "POST /api/patients/",
                "get": "GET /api/patients/{patient_id}",
                "timeline": "GET /api/patients/{patient_id}/timeline",
            }
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
