"""
AI Agents Package

Contains privacy enforcement and data adaptation layers.

Modules:
- consent_agent: Privacy enforcement with expiry checking
- records_adapter: Bridge DB models to AI agent record format
"""

from app.ai_agents import consent_agent
from app.ai_agents import records_adapter

__all__ = [
    "consent_agent",
    "records_adapter",
]
