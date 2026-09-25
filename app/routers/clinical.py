"""
Clinical API Routes

Exposes the full power of the Health Memory Orchestrator through REST endpoints:
- /api/clinical/summary - Comprehensive clinical context
- /api/clinical/alerts - Real-time alerts dashboard
- /api/clinical/recommendations - Actionable recommendations
- /api/clinical/timeline - Chronological event view (inherited)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.ai_agents.orchestrator import HealthMemoryOrchestrator
from app.schemas import PatientResponse

router = APIRouter(prefix="/api/clinical", tags=["Clinical Intelligence"])


# Dependency: Get orchestrator
def get_orchestrator(db: Session = Depends(get_db)) -> HealthMemoryOrchestrator:
    return HealthMemoryOrchestrator(db)


@router.post("/patients/{patient_id}/summary")
async def get_clinical_summary(
    patient_id: int,
    requester_id: int = Query(..., description="ID of clinician/guardian making request"),
    requester_role: str = Query("clinician", description="Role: clinician, guardian, caregiver"),
    clinical_query: Optional[str] = Query(
        None, description="Specific question (e.g., 'prescribing metformin')"
    ),
    orchestrator: HealthMemoryOrchestrator = Depends(get_orchestrator),
):
    """
    Get comprehensive clinical summary for point-of-care decision-making.

    **Response includes:**
    - Clinical synthesis (narrative summary of relevant context)
    - Alerts (ranked by severity)
    - Timeline (all events, chronologically)
    - Safety analysis (drug interactions, disease conflicts, dosing)
    - Recommendations (actionable)
    - Metadata (consent verification, confidence scores)

    **Example requests:**
    ```
    POST /api/clinical/patients/1/summary?requester_id=5&requester_role=clinician
      → Full summary
    POST /api/clinical/patients/1/summary?requester_id=5&clinical_query=prescribing%20metformin
      → Summary focused on metformin considerations
    ```
    """
    result = orchestrator.get_clinical_summary(
        patient_id=patient_id,
        requester_id=requester_id,
        requester_role=requester_role,
        clinical_query=clinical_query,
    )

    if "error" in result:
        raise HTTPException(
            status_code=403 if result["error"] == "ACCESS_DENIED" else 404,
            detail=result.get("message", "Error generating clinical summary"),
        )

    return result


@router.get("/patients/{patient_id}/alerts")
async def get_clinical_alerts(
    patient_id: int,
    requester_id: int = Query(..., description="ID of requester"),
    requester_role: str = Query("clinician", description="Role: clinician, guardian, caregiver"),
    min_severity: str = Query("MEDIUM", description="Minimum severity: HIGH, MEDIUM, LOW"),
    orchestrator: HealthMemoryOrchestrator = Depends(get_orchestrator),
):
    """
    Get high-priority alerts for dashboard/notifications.

    **Response:**
    ```json
    {
      "patient_id": 1,
      "alert_count": 5,
      "urgent_count": 2,
      "risk_score": 7.2,
      "risk_category": "HIGH",
      "alerts": [
        {
          "severity": "HIGH",
          "category": "drug_interaction",
          "message": "Severe interaction: Warfarin + Aspirin",
          "action": "Avoid combination; use apixaban instead"
        },
        ...
      ]
    }
    ```

    **Use cases:**
    - Dashboard alert widget (every 5 mins)
    - Mobile notification trigger
    - Clinical workflow integration
    """
    result = orchestrator.get_clinical_alerts(
        patient_id=patient_id,
        requester_id=requester_id,
        requester_role=requester_role,
    )

    if "error" in result:
        raise HTTPException(
            status_code=403 if result["error"] == "ACCESS_DENIED" else 404,
            detail=result.get("message", "Error retrieving alerts"),
        )

    # Filter by severity if requested
    if min_severity in ["HIGH", "MEDIUM", "LOW"]:
        severity_levels = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}
        min_level = severity_levels.get(min_severity, 0)
        result["alerts"] = [
            a
            for a in result.get("alerts", [])
            if severity_levels.get(a.get("severity", "LOW"), 0) >= min_level
        ]

    return result


@router.get("/patients/{patient_id}/recommendations")
async def get_recommendations(
    patient_id: int,
    requester_id: int = Query(..., description="ID of requester"),
    requester_role: str = Query("clinician", description="Role: clinician, guardian, caregiver"),
    category: Optional[str] = Query(
        None, description="Filter by category: deprescribing, drug_interaction, drug_disease, dosing"
    ),
    orchestrator: HealthMemoryOrchestrator = Depends(get_orchestrator),
):
    """
    Get actionable clinical recommendations.

    **Response:**
    ```json
    {
      "patient_id": 1,
      "recommendation_count": 8,
      "high_priority_count": 3,
      "recommendations": [
        {
          "category": "drug_interaction",
          "priority": "high",
          "message": "Warfarin + Aspirin interaction detected",
          "action": "Review with patient; consider switching Aspirin to acetaminophen"
        },
        {
          "category": "deprescribing",
          "priority": "medium",
          "message": "Patient on two beta-blockers",
          "action": "Consider deprescribing one; typically only one needed"
        },
        ...
      ]
    }
    ```

    **Categories:**
    - `deprescribing`: Remove unnecessary medications
    - `drug_interaction`: Resolve DDI
    - `drug_disease`: Resolve drug-disease conflicts
    - `dosing`: Adjust doses for age/renal function
    """
    result = orchestrator.get_patient_recommendations(
        patient_id=patient_id,
        requester_id=requester_id,
        requester_role=requester_role,
    )

    if "error" in result:
        raise HTTPException(
            status_code=403 if result["error"] == "ACCESS_DENIED" else 404,
            detail=result.get("message", "Error retrieving recommendations"),
        )

    # Filter by category if requested
    if category:
        result["recommendations"] = [
            r for r in result.get("recommendations", [])
            if r.get("category") == category
        ]

    return result


@router.post("/patients/{patient_id}/analyze-medications")
async def analyze_medications(
    patient_id: int,
    requester_id: int = Query(..., description="ID of requester"),
    requester_role: str = Query("clinician"),
    orchestrator: HealthMemoryOrchestrator = Depends(get_orchestrator),
):
    """
    Deep-dive medication analysis (polypharmacy focus).

    Returns detailed interaction matrix, dosing appropriateness, adherence concerns.
    """
    from app.ai_agents.polypharmacy_risk_agent import PolypharmacyRiskAgent

    # Check consent first
    summary = orchestrator.get_clinical_summary(
        patient_id=patient_id,
        requester_id=requester_id,
        requester_role=requester_role,
    )
    if "error" in summary:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get detailed pharmacy analysis
    db = Depends(get_db)
    pharmacy_agent = PolypharmacyRiskAgent(next(db))
    analysis = pharmacy_agent.analyze(patient_id)

    return analysis


@router.get("/patients/{patient_id}/clinical-context")
async def get_clinical_context(
    patient_id: int,
    requester_id: int = Query(...),
    requester_role: str = Query("clinician"),
    context_type: str = Query(
        "full", description="full, synthesis, medications, safety, timeline"
    ),
    orchestrator: HealthMemoryOrchestrator = Depends(get_orchestrator),
):
    """
    Get specific clinical context (flexible endpoint for different views).

    **context_type options:**
    - `full`: Complete summary (default)
    - `synthesis`: Narrative summary only
    - `medications`: Current meds + history
    - `safety`: Drug interactions + warnings
    - `timeline`: Chronological events
    """
    summary = orchestrator.get_clinical_summary(
        patient_id=patient_id,
        requester_id=requester_id,
        requester_role=requester_role,
    )

    if "error" in summary:
        raise HTTPException(status_code=403, detail="Access denied")

    # Return filtered by type
    if context_type == "synthesis":
        return {"patient": summary.get("patient"), "synthesis": summary.get("synthesis")}
    elif context_type == "medications":
        return {
            "patient": summary.get("patient"),
            "medications": summary.get("synthesis", {}).get("current_medications", {}),
        }
    elif context_type == "safety":
        return {"patient": summary.get("patient"), "safety": summary.get("safety")}
    elif context_type == "timeline":
        return {
            "patient": summary.get("patient"),
            "timeline": summary.get("timeline"),
            "alert_count": len(summary.get("alerts", [])),
        }
    else:
        return summary


# WebSocket endpoint for live alerts (stub - implement in main.py)
# @router.websocket("/ws/patients/{patient_id}/live-alerts")
# async def websocket_alerts(websocket: WebSocket, patient_id: int):
#     """
#     WebSocket endpoint for real-time alert streaming.
#     Streams new alerts as they're generated (new labs, observations, etc.)
#     """
#     await websocket.accept()
#     try:
#         while True:
#             # Poll for new alerts
#             alerts = orchestrator.get_clinical_alerts(patient_id)
#             await websocket.send_json(alerts)
#             # Sleep before next poll
#             await asyncio.sleep(5)
#     except Exception as e:
#         await websocket.close(code=1001)
