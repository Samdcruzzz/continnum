"""
Gericure Demo Application Package

Main package for the health record system backend.
Exports core modules for clean imports.
"""

# Make key modules easily importable
from app import database
from app import models
from app import schemas
from app import routers

__all__ = [
    "database",
    "models",
    "schemas",
    "routers",
]
