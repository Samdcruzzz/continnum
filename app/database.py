"""
Database Connection and Session Management

Provides:
- SQLAlchemy engine (PostgreSQL connection)
- SessionLocal (database session factory)
- get_db (FastAPI dependency for injecting sessions into routes)

Environment Variables:
- DATABASE_URL (preferred) or
- DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Get database configuration from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Build from individual components
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_name = os.getenv("DATABASE_NAME", "gericure_demo")
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_password = os.getenv("DATABASE_PASSWORD", "password")

    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create SQLAlchemy engine
# echo=True logs all SQL statements (disable in production)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging
    pool_pre_ping=True,  # Test connection before using it
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions in FastAPI routes.

    Usage in route:
        @app.get("/patients/")
        def list_patients(db: Session = Depends(get_db)):
            return db.query(Patient).all()

    Guarantees:
    - Session is created fresh for each request
    - Session is closed after request completes
    - Errors don't leave connections hanging
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
