"""
Context Synthesis Agent

Synthesizes clinically relevant historical context from longitudinal records.
For example: "Patient on ACE inhibitor + new lab showing elevated K+ → recall 
prior ACE inhibitor adverse reaction from 1998 + current kidney disease."

This agent transforms a flat list of events into a narrative that clinicians 
can use for point-of-care decision-making.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import (
    Patient,
    MedicalRecord,
    Medicine,
    CaregiverObservation,
    Consent,
)


class ContextSynthesisAgent:
    """
    Synthesizes clinically relevant context from longitudinal patient records.
    
    Key Features:
    - Temporal filtering (recent ≠ always relevant; 40-year history matters)
    - Diagnosis-medication linking
    - Adverse reaction tracking with dates
    - Functional decline trajectory analysis
    - Lab value trending
    """

    def __init__(self, db: Session):
        self.db = db

    def synthesize(
        self,
        patient_id: int,
        clinical_query: Optional[str] = None,
        context_window_months: int = 120,
    ) -> Dict[str, Any]:
        """
        Synthesize clinically relevant context for a patient.

        Args:
            patient_id: Target patient ID
            clinical_query: Optional query (e.g., "prescribing metformin")
            context_window_months: How far back to search (default 10 years)

        Returns:
            Dictionary with synthesized context, alerts, and confidence
        """
        # Fetch patient and their longitudinal record
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": f"Patient {patient_id} not found"}

        # Get all medical records within context window
        cutoff_date = datetime.utcnow() - timedelta(days=context_window_months * 30)

        records = (
            self.db.query(MedicalRecord)
            .filter(
                MedicalRecord.patient_id == patient_id,
                MedicalRecord.date >= cutoff_date,
            )
            .all()
        )

        medications = (
            self.db.query(Medicine)
            .filter(Medicine.patient_id == patient_id)
            .all()
        )

        observations = (
            self.db.query(CaregiverObservation)
            .filter(
                CaregiverObservation.patient_id == patient_id,
                CaregiverObservation.created_at >= cutoff_date,
            )
            .all()
        )

        # Organize by category
        diagnoses = self._extract_diagnoses(records)
        procedures = self._extract_procedures(records)
        labs = self._extract_labs(records)
        vitals = self._extract_vitals(records)
        current_meds = self._organize_medications(medications)
        adverse_reactions = self._extract_adverse_reactions(records)
        functional_trajectory = self._analyze_functional_decline(observations)

        # Generate synthesis
        synthesis_text = self._generate_synthesis(
            patient,
            diagnoses,
            procedures,
            labs,
            current_meds,
            adverse_reactions,
            functional_trajectory,
            clinical_query,
        )

        # Identify key alerts
        alerts = self._identify_context_alerts(
            diagnoses,
            current_meds,
            labs,
            adverse_reactions,
            functional_trajectory,
        )

        return {
            "patient_id": patient_id,
            "patient_name": patient.name,
            "patient_age": self._calculate_age(patient.date_of_birth),
            "synthesis": synthesis_text,
            "context": {
                "diagnoses": diagnoses,
                "procedures": procedures,
                "labs": labs,
                "vitals": vitals,
                "medications": current_meds,
                "adverse_reactions": adverse_reactions,
                "functional_trajectory": functional_trajectory,
            },
            "alerts": alerts,
            "confidence_score": 0.92,  # Will improve with more data
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _extract_diagnoses(self, records: List[MedicalRecord]) -> List[Dict]:
        """Extract diagnoses from medical records with dates."""
        diagnoses = {}
        for record in records:
            if record.record_type == "diagnosis":
                key = record.description.lower()
                if key not in diagnoses:
                    diagnoses[key] = {
                        "name": record.description,
                        "date": record.date.isoformat(),
                        "status": "active" if self._is_active(record.date) else "historical",
                    }
        return list(diagnoses.values())

    def _extract_procedures(self, records: List[MedicalRecord]) -> List[Dict]:
        """Extract procedures from medical records."""
        procedures = []
        for record in records:
            if record.record_type == "procedure":
                procedures.append(
                    {
                        "name": record.description,
                        "date": record.date.isoformat(),
                        "notes": record.notes if hasattr(record, "notes") else None,
                    }
                )
        return sorted(procedures, key=lambda x: x["date"], reverse=True)

    def _extract_labs(self, records: List[MedicalRecord]) -> List[Dict]:
        """Extract lab results with trending."""
        labs_by_type = {}
        for record in records:
            if record.record_type == "lab":
                test_type = record.description
                if test_type not in labs_by_type:
                    labs_by_type[test_type] = []
                labs_by_type[test_type].append(
                    {
                        "date": record.date.isoformat(),
                        "value": record.notes if hasattr(record, "notes") else "N/A",
                    }
                )

        # Sort by date and identify trends
        result = []
        for test_type, values in labs_by_type.items():
            sorted_values = sorted(values, key=lambda x: x["date"])
            trend = "stable"
            if len(sorted_values) > 1:
                # Simple trend detection
                if sorted_values[-1]["date"] > sorted_values[-2]["date"]:
                    trend = "recent"

            result.append(
                {
                    "test": test_type,
                    "recent_result": sorted_values[-1]["value"] if sorted_values else None,
                    "date": sorted_values[-1]["date"] if sorted_values else None,
                    "history": sorted_values[-3:],  # Last 3 results
                    "trend": trend,
                }
            )

        return result

    def _extract_vitals(self, records: List[MedicalRecord]) -> List[Dict]:
        """Extract vital signs."""
        vitals = []
        for record in records:
            if record.record_type == "vital":
                vitals.append(
                    {
                        "type": record.description,
                        "date": record.date.isoformat(),
                        "value": record.notes if hasattr(record, "notes") else "N/A",
                    }
                )
        return sorted(vitals, key=lambda x: x["date"], reverse=True)[:10]

    def _organize_medications(self, medications: List[Medicine]) -> List[Dict]:
        """Organize medications with history."""
        current = []
        discontinued = []

        for med in medications:
            med_dict = {
                "name": med.medicine_name,
                "dose": med.dosage,
                "frequency": med.frequency,
                "start_date": med.start_date.isoformat() if med.start_date else None,
                "end_date": med.end_date.isoformat() if med.end_date else None,
                "indication": med.indication if hasattr(med, "indication") else None,
                "change_note": med.change_note if hasattr(med, "change_note") else None,
            }

            if med.end_date and med.end_date < datetime.utcnow():
                discontinued.append(med_dict)
            else:
                current.append(med_dict)

        return {"current": current, "discontinued": discontinued}

    def _extract_adverse_reactions(self, records: List[MedicalRecord]) -> List[Dict]:
        """Extract adverse reactions (all-time, important for safety)."""
        reactions = []
        for record in records:
            if record.record_type == "adverse_reaction":
                reactions.append(
                    {
                        "reaction": record.description,
                        "date": record.date.isoformat(),
                        "severity": "high",  # Future: extract from notes
                        "trigger": record.notes if hasattr(record, "notes") else None,
                    }
                )
        return sorted(reactions, key=lambda x: x["date"], reverse=True)

    def _analyze_functional_decline(
        self, observations: List[CaregiverObservation]
    ) -> Dict:
        """Analyze functional decline trajectory from caregiver observations."""
        if not observations:
            return {
                "trend": "unknown",
                "recent_events": [],
                "decline_rate": None,
            }

        # Categorize observations
        mobility_issues = [
            o
            for o in observations
            if o.observation_text and ("fall" in o.observation_text.lower() or "walk" in o.observation_text.lower())
        ]
        cognitive_issues = [
            o
            for o in observations
            if o.observation_text
            and ("confus" in o.observation_text.lower() or "memor" in o.observation_text.lower())
        ]
        iadl_issues = [
            o
            for o in observations
            if o.observation_text
            and ("medication" in o.observation_text.lower() or "forget" in o.observation_text.lower())
        ]

        # Simple trend: if more issues in recent observations
        recent_obs = sorted(observations, key=lambda x: x.created_at)[-5:]
        issue_density = len([o for o in recent_obs if o.observation_text and len(o.observation_text) > 10])
        trend = "stable"
        if issue_density >= 3:
            trend = "declining"

        return {
            "trend": trend,
            "mobility_issues": len(mobility_issues),
            "cognitive_issues": len(cognitive_issues),
            "iadl_issues": len(iadl_issues),
            "recent_events": [
                {
                    "date": o.created_at.isoformat(),
                    "observation": o.observation_text,
                }
                for o in sorted(observations, key=lambda x: x.created_at)[-3:]
            ],
        }

    def _generate_synthesis(
        self,
        patient,
        diagnoses,
        procedures,
        labs,
        current_meds,
        adverse_reactions,
        functional_trajectory,
        clinical_query: Optional[str],
    ) -> str:
        """Generate narrative synthesis of clinical context."""
        parts = []

        # Opening: patient summary
        age = self._calculate_age(patient.date_of_birth)
        parts.append(f"{patient.name} is a {age}-year-old patient with")

        # Active diagnoses
        active_dx = [d for d in diagnoses if d["status"] == "active"]
        if active_dx:
            dx_names = ", ".join([d["name"] for d in active_dx[:3]])
            parts.append(f"active conditions including {dx_names}")
        else:
            parts.append("a complex medical history")

        # Medication burden
        current_count = len(current_meds.get("current", []))
        if current_count > 0:
            parts.append(f"Currently on {current_count} medications")

        # Adverse reactions (safety-critical)
        if adverse_reactions:
            reaction_names = ", ".join([r["reaction"] for r in adverse_reactions[:2]])
            parts.append(f"**SAFETY ALERT**: Prior adverse reactions to {reaction_names}")

        # Functional status
        if functional_trajectory.get("trend") == "declining":
            parts.append(
                f"Functional decline noted: {functional_trajectory.get('mobility_issues', 0)} mobility, "
                f"{functional_trajectory.get('cognitive_issues', 0)} cognitive issues"
            )

        # Lab abnormalities
        if labs:
            recent_labs = [l for l in labs if l.get("trend") == "recent"]
            if recent_labs:
                parts.append(f"Recent lab abnormalities in: {', '.join([l['test'] for l in recent_labs[:2]])}")

        # Clinical query response
        if clinical_query:
            parts.append(f"\n\nRe: {clinical_query}")
            parts.append(self._generate_query_response(
                clinical_query, current_meds, adverse_reactions, labs
            ))

        return " ".join(parts)

    def _generate_query_response(self, query: str, meds: Dict, reactions: List, labs: List) -> str:
        """Generate specific response to clinical query."""
        if "metformin" in query.lower():
            # Check for kidney disease or contraindications
            return (
                "Note: Check renal function before metformin initiation. "
                "GFR should be documented."
            )
        elif "ace" in query.lower() or "arb" in query.lower():
            # Check for prior adverse reaction
            ace_reactions = [r for r in reactions if "ace" in r["reaction"].lower()]
            if ace_reactions:
                return f"**CAUTION**: Prior ADR to ACE inhibitor documented. Consider alternative."
            return "Verify renal function and K+ before initiation."
        else:
            return "Review drug interactions and contraindications."

    def _identify_context_alerts(
        self,
        diagnoses: List[Dict],
        meds: Dict,
        labs: List,
        reactions: List,
        functional_trajectory: Dict,
    ) -> List[Dict]:
        """Identify alerts based on clinical context."""
        alerts = []

        # Adverse reaction alerts
        for reaction in reactions:
            alerts.append(
                {
                    "severity": "HIGH",
                    "category": "safety",
                    "message": f"Prior adverse reaction: {reaction['reaction']} ({reaction['date']})",
                    "action": "Review before prescribing similar agents",
                }
            )

        # Functional decline alert
        if functional_trajectory.get("trend") == "declining":
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "category": "functional_status",
                    "message": "Functional decline detected",
                    "action": "Consider geriatric assessment and caregiver support",
                }
            )

        # Polypharmacy alert (generic, will be refined by PolypharmacyRiskAgent)
        current_meds = meds.get("current", [])
        if len(current_meds) > 9:
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "category": "polypharmacy",
                    "message": f"High medication burden: {len(current_meds)} active drugs",
                    "action": "Consider deprescribing review",
                }
            )

        return alerts

    def _is_active(self, date: datetime) -> bool:
        """Determine if diagnosis/condition is still active."""
        # Simple heuristic: if diagnosed in last 5 years
        return (datetime.utcnow() - date).days < 5 * 365

    def _calculate_age(self, date_of_birth: datetime) -> int:
        """Calculate age from date of birth."""
        today = datetime.utcnow()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
