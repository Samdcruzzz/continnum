"""
Health Memory Orchestrator

Central service that coordinates all AI agents to deliver unified clinical context:
1. Consent enforcement (privacy-first)
2. Longitudinal record retrieval
3. Context synthesis (what's relevant)
4. Polypharmacy analysis (safety check)
5. Recommendations generation

This is the "brain" of the system - clinicians call the orchestrator to get
comprehensive, actionable clinical context for point-of-care decisions.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Patient, Consent
from app.ai_agents.consent_agent import ConsentAgent
from app.ai_agents.context_synthesis_agent import ContextSynthesisAgent
from app.ai_agents.polypharmacy_risk_agent import PolypharmacyRiskAgent
from app.ai_agents.records_adapter import RecordsAdapter


class HealthMemoryOrchestrator:
    """
    Central orchestration service for clinical context delivery.

    Workflow:
    1. Receive request (patient_id, guardian_id or clinician_id, clinical_query)
    2. Check consent (ConsentAgent) → verify access before proceeding
    3. Fetch longitudinal record (RecordsAdapter)
    4. Synthesize context (ContextSynthesisAgent)
    5. Analyze safety (PolypharmacyRiskAgent)
    6. Merge findings → unified clinical summary
    7. Return to point-of-care system
    """

    def __init__(self, db: Session):
        self.db = db
        self.consent_agent = ConsentAgent(db)
        self.context_agent = ContextSynthesisAgent(db)
        self.pharmacy_agent = PolypharmacyRiskAgent(db)
        self.records_adapter = RecordsAdapter(db)

    def get_clinical_summary(
        self,
        patient_id: int,
        requester_id: int,
        requester_role: str = "clinician",
        clinical_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive clinical summary with all context, safety checks, and recommendations.

        Args:
            patient_id: Target patient ID
            requester_id: Who's asking (clinician, guardian, etc.)
            requester_role: Role of requester (clinician, guardian, caregiver)
            clinical_query: Optional specific question (e.g., "prescribing metformin")

        Returns:
            Comprehensive clinical summary with synthesis, risks, and recommendations
            OR error dict if consent not granted
        """
        try:
            # STEP 1: Enforce consent (privacy-first principle)
            consent_check = self._check_access_permission(
                patient_id, requester_id, requester_role
            )
            if not consent_check["granted"]:
                return {
                    "error": "ACCESS_DENIED",
                    "message": consent_check["reason"],
                    "patient_id": patient_id,
                }

            # STEP 2: Fetch patient
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {
                    "error": "PATIENT_NOT_FOUND",
                    "message": f"Patient {patient_id} not found",
                }

            # STEP 3: Get longitudinal records (all categories, chronologically sorted)
            timeline = self.records_adapter.get_patient_timeline(patient_id)

            # STEP 4: Synthesize clinical context
            context_synthesis = self.context_agent.synthesize(
                patient_id, clinical_query=clinical_query
            )

            # STEP 5: Analyze medication safety
            pharma_analysis = self.pharmacy_agent.analyze(patient_id)

            # STEP 6: Merge findings into unified summary
            unified_summary = self._merge_findings(
                patient,
                context_synthesis,
                pharma_analysis,
                timeline,
                clinical_query,
                consent_check,
            )

            # Add audit trail (who accessed what when)
            unified_summary["access_log"] = {
                "requester_id": requester_id,
                "requester_role": requester_role,
                "accessed_at": datetime.utcnow().isoformat(),
                "data_categories": ["timeline", "synthesis", "safety", "recommendations"],
            }

            return unified_summary

        except Exception as e:
            return {
                "error": "ORCHESTRATION_FAILED",
                "message": str(e),
                "patient_id": patient_id,
            }

    def get_clinical_alerts(
        self, patient_id: int, requester_id: int, requester_role: str = "clinician"
    ) -> Dict[str, Any]:
        """
        Retrieve only high-priority alerts (faster endpoint for dashboard).

        Returns: { "alerts": [...], "risk_score": 7.8, "urgent_count": 2 }
        """
        # Check consent
        consent_check = self._check_access_permission(
            patient_id, requester_id, requester_role
        )
        if not consent_check["granted"]:
            return {
                "error": "ACCESS_DENIED",
                "message": consent_check["reason"],
            }

        # Get synthesis and pharmacy data
        context_synthesis = self.context_agent.synthesize(patient_id)
        pharma_analysis = self.pharmacy_agent.analyze(patient_id)

        # Extract high-priority alerts
        alerts = self._extract_high_priority_alerts(
            context_synthesis.get("alerts", []),
            pharma_analysis.get("interactions", {}).get("drug_drug", []),
            pharma_analysis.get("interactions", {}).get("drug_disease", []),
        )

        return {
            "patient_id": patient_id,
            "alert_count": len(alerts),
            "urgent_count": len([a for a in alerts if a.get("severity") == "HIGH"]),
            "risk_score": pharma_analysis.get("overall_risk_score", 0),
            "risk_category": pharma_analysis.get("risk_category", "UNKNOWN"),
            "alerts": sorted(alerts, key=lambda x: self._alert_priority(x), reverse=True),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_patient_recommendations(
        self, patient_id: int, requester_id: int, requester_role: str = "clinician"
    ) -> Dict[str, Any]:
        """
        Retrieve actionable clinical recommendations for the patient.

        Returns categorized, prioritized recommendations from all analysis modules.
        """
        # Check consent
        consent_check = self._check_access_permission(
            patient_id, requester_id, requester_role
        )
        if not consent_check["granted"]:
            return {"error": "ACCESS_DENIED", "message": consent_check["reason"]}

        # Get pharma recommendations (primary source)
        pharma_analysis = self.pharmacy_agent.analyze(patient_id)
        recommendations = pharma_analysis.get("recommendations", [])

        # Get context-based recommendations
        context_synthesis = self.context_agent.synthesize(patient_id)
        alerts = context_synthesis.get("alerts", [])

        # Convert alerts to recommendations
        for alert in alerts:
            recommendations.append(
                {
                    "category": alert.get("category", "general"),
                    "priority": "high" if alert["severity"] == "HIGH" else "medium",
                    "message": alert["message"],
                    "action": alert.get("action", "Review with clinician"),
                }
            )

        # Remove duplicates and sort by priority
        seen = set()
        unique_recs = []
        for rec in recommendations:
            key = (rec.get("message"), rec.get("action"))
            if key not in seen:
                seen.add(key)
                unique_recs.append(rec)

        unique_recs = sorted(
            unique_recs,
            key=lambda x: 0 if x["priority"] == "high" else 1
        )

        return {
            "patient_id": patient_id,
            "recommendation_count": len(unique_recs),
            "high_priority_count": len([r for r in unique_recs if r["priority"] == "high"]),
            "recommendations": unique_recs[:15],  # Top 15
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ========== PRIVATE HELPERS ==========

    def _check_access_permission(
        self, patient_id: int, requester_id: int, requester_role: str
    ) -> Dict[str, Any]:
        """
        Delegate to ConsentAgent to verify access permission.

        Returns: { "granted": bool, "reason": str }
        """
        try:
            result = self.consent_agent.check_consent(
                patient_id, requester_id, requester_role
            )
            return result
        except Exception as e:
            return {
                "granted": False,
                "reason": f"Consent check failed: {str(e)}",
            }

    def _merge_findings(
        self,
        patient,
        context_synthesis,
        pharma_analysis,
        timeline,
        clinical_query,
        consent_check,
    ) -> Dict[str, Any]:
        """
        Merge all analysis results into unified clinical summary.

        Structure:
        - Patient demographics
        - High-level synthesis
        - Alerts (ranked by severity)
        - Timeline (structured events)
        - Medication safety (DDI, DDD, dosing)
        - Recommendations (actionable)
        """
        return {
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": self._calculate_age(patient.date_of_birth),
                "date_of_birth": patient.date_of_birth.isoformat(),
            },
            "clinical_query": clinical_query,
            "synthesis": {
                "narrative": context_synthesis.get("synthesis"),
                "key_diagnoses": context_synthesis.get("context", {}).get("diagnoses", []),
                "current_medications": context_synthesis.get("context", {}).get("medications", {}),
                "functional_status": context_synthesis.get("context", {}).get("functional_trajectory", {}),
            },
            "safety": {
                "medication_count": pharma_analysis.get("medication_count", 0),
                "overall_risk_score": pharma_analysis.get("overall_risk_score", 0),
                "risk_category": pharma_analysis.get("risk_category", "UNKNOWN"),
                "drug_drug_interactions": pharma_analysis.get("interactions", {}).get("drug_drug", [])[:5],  # Top 5
                "drug_disease_conflicts": pharma_analysis.get("interactions", {}).get("drug_disease", [])[:3],  # Top 3
                "duplicate_therapies": pharma_analysis.get("duplicate_therapies", []),
                "dosing_issues": pharma_analysis.get("dosing_issues", [])[:3],
            },
            "alerts": self._rank_alerts(
                context_synthesis.get("alerts", []) + 
                self._pharma_alerts_to_format(pharma_analysis.get("interactions", {}))
            ),
            "timeline": timeline,
            "recommendations": pharma_analysis.get("recommendations", [])[:10],  # Top 10
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "consent_verified": consent_check["granted"],
                "confidence_scores": {
                    "synthesis": context_synthesis.get("confidence_score", 0.9),
                    "safety": pharma_analysis.get("overall_risk_score", 0) / 10.0,
                },
            },
        }

    def _extract_high_priority_alerts(
        self, context_alerts: List, ddi_alerts: List, ddi_disease: List
    ) -> List[Dict]:
        """Extract and format high-priority alerts."""
        alerts = []

        # Add context alerts
        for alert in context_alerts:
            if alert.get("severity") in ["HIGH", "MEDIUM"]:
                alerts.append(alert)

        # Add severe DDI
        for interaction in ddi_alerts:
            if interaction.get("severity") == "severe":
                alerts.append(
                    {
                        "severity": "HIGH",
                        "category": "drug_interaction",
                        "message": f"Severe interaction: {interaction['drug_a']} + {interaction['drug_b']}",
                        "action": interaction["recommendation"],
                    }
                )

        # Add high-severity DDD
        for conflict in ddi_disease:
            if conflict.get("severity") == "high":
                alerts.append(
                    {
                        "severity": "HIGH",
                        "category": "drug_disease",
                        "message": f"{conflict['drug']} contraindicated with {conflict['disease']}",
                        "action": conflict["recommendation"],
                    }
                )

        return alerts

    def _pharma_alerts_to_format(self, interactions: Dict) -> List[Dict]:
        """Convert pharmacy interactions to alert format."""
        alerts = []
        for ddi in interactions.get("drug_drug", []):
            alerts.append(
                {
                    "severity": "HIGH" if ddi.get("severity") == "severe" else "MEDIUM",
                    "category": "drug_interaction",
                    "message": ddi.get("mechanism"),
                    "action": ddi.get("recommendation"),
                }
            )
        return alerts

    def _rank_alerts(self, alerts: List[Dict]) -> List[Dict]:
        """Rank alerts by severity and return top ones."""
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_alerts = sorted(
            alerts,
            key=lambda x: severity_order.get(x.get("severity", "LOW"), 3)
        )
        return sorted_alerts[:10]  # Top 10 alerts

    def _alert_priority(self, alert: Dict) -> int:
        """Numeric priority for sorting."""
        severity_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return severity_map.get(alert.get("severity"), 0)

    def _calculate_age(self, date_of_birth: datetime) -> int:
        """Calculate age."""
        today = datetime.utcnow()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
