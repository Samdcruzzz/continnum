"""
API Routers Package

Contains all FastAPI route handlers organized by domain.

Currently includes:
- patients: Patient management, medical records, timeline
"""

from app.routers import patients

__all__ = [
    "patients",
]
