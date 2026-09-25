"""
Cognitive Decline Agent

Analyzes caregiver observations and clinical records to:
- Detect functional and cognitive decline trajectories
- Estimate dementia stage (normal cognition → MCI → mild → moderate → severe)
- Identify stage-specific risks and safety concerns
- Generate targeted interventions and monitoring recommendations

This agent operates on structured caregiver observations + historical clinical data.
It's critical for elderly patients where cognitive status dramatically changes management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import Patient, MedicalRecord, CaregiverObservation


# Dementia stage criteria (simplified Montreal Cognitive Assessment mapping)
COGNITIVE_STAGES = {
    "normal": {
        "mmse_score_min": 24,
        "description": "No cognitive impairment",
        "characteristics": ["independent ADL", "normal memory", "normal orientation"],
    },
    "mild_cognitive_impairment": {
        "mmse_score_range": (18, 23),
        "description": "Mild cognitive impairment (MCI)",
        "characteristics": ["memory lapses", "difficulty complex tasks", "preserved independence"],
        "risk_level": "medium",
    },
    "mild_dementia": {
        "mmse_score_range": (12, 17),
        "description": "Mild dementia",
        "characteristics": ["frequent memory loss", "difficulty ADL", "behavioral changes"],
        "risk_level": "high",
    },
    "moderate_dementia": {
        "mmse_score_range": (8, 11),
        "description": "Moderate dementia",
        "characteristics": ["significant memory loss", "dependent ADL", "confusion", "wandering"],
        "risk_level": "very_high",
    },
    "severe_dementia": {
        "mmse_score_max": 7,
        "description": "Severe dementia",
        "characteristics": ["loss of communication", "total dependence", "behavioral disturbance"],
        "risk_level": "critical",
    },
}

# Stage-specific medication concerns
STAGE_SPECIFIC_DRUG_RISKS = {
    "mild_cognitive_impairment": [
        {
            "drug_class": "anticholinergic",
            "risk": "May accelerate cognitive decline",
            "drugs": ["diphenhydramine", "benztropine", "oxybutynin"],
        },
        {
            "drug_class": "benzodiazepine",
            "risk": "Falls, confusion",
            "alternative": "Consider buspirone or SSRI for anxiety",
        },
    ],
    "mild_dementia": [
        {
            "drug_class": "anticholinergic",
            "risk": "AVOID - accelerates decline",
            "severity": "high",
        },
        {
            "drug_class": "opioid",
            "risk": "AVOID - delirium risk",
            "severity": "high",
        },
        {
            "drug_class": "sedating_antihistamine",
            "risk": "AVOID - delirium risk",
            "severity": "high",
        },
    ],
    "moderate_dementia": [
        {
            "drug_class": "anticholinergic",
            "risk": "CONTRAINDICATED",
            "severity": "critical",
        },
        {
            "drug_class": "sedating_drug",
            "risk": "AVOID due to fall risk + aspiration risk",
            "severity": "critical",
        },
    ],
    "severe_dementia": [
        {
            "drug_class": "any_non_essential",
            "risk": "Deprescribing focus - comfort care priority",
            "recommendation": "Consider hospice care model; deprescribe aggressively",
        },
    ],
}

# Caregiver observation keywords for pattern detection
COGNITIVE_KEYWORDS = {
    "memory": ["forget", "memory", "reminisc", "recall", "lost"],
    "orientation": ["confus", "disoriented", "where am", "who are"],
    "communication": ["speak", "word", "language", "silent", "quiet"],
    "executive_function": ["decision", "planning", "organize", "complex"],
    "behavioral": ["wander", "aggress", "agitat", "sundown", "paranoid"],
}

FUNCTIONAL_KEYWORDS = {
    "iadl": ["medication", "bills", "shop", "cook", "clean", "phone"],
    "adl": ["dress", "bath", "toilet", "feed", "transfer", "walk"],
    "mobility": ["fall", "gait", "step", "walk", "balance", "trip"],
}


class CognitiveDeclineAgent:
    """
    Analyzes cognitive and functional decline trajectories.

    Key Features:
    - Detect cognitive stage from observations + clinical history
    - Track decline rate (stable, slow decline, rapid decline)
    - Identify stage-specific medication risks
    - Generate safety recommendations based on stage
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze(self, patient_id: int) -> Dict[str, Any]:
        """
        Comprehensive cognitive decline analysis.

        Args:
            patient_id: Target patient ID

        Returns:
            Dictionary with:
            - estimated_stage: current dementia stage
            - confidence: 0-1 confidence in stage assessment
            - trajectory: decline trend (stable/slow/rapid)
            - functional_summary: ADL/IADL status
            - stage_specific_risks: medication/safety concerns for this stage
            - recommendations: stage-appropriate interventions
        """
        # Fetch patient and records
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": f"Patient {patient_id} not found"}

        # Get observations (primary data source)
        observations = (
            self.db.query(CaregiverObservation)
            .filter(CaregiverObservation.patient_id == patient_id)
            .order_by(CaregiverObservation.created_at.desc())
            .all()
        )

        # Get cognitive assessment records if available
        cognitive_records = (
            self.db.query(MedicalRecord)
            .filter(
                MedicalRecord.patient_id == patient_id,
                MedicalRecord.record_type.in_(["assessment", "cognitive"]),
            )
            .all()
        )

        # Analyze observations for cognitive/functional patterns
        cognitive_analysis = self._analyze_observations(observations)
        functional_analysis = self._analyze_functional_status(observations)

        # Extract any MMSE/MoCA scores from records
        cognitive_scores = self._extract_cognitive_scores(cognitive_records)

        # Estimate cognitive stage
        estimated_stage = self._estimate_cognitive_stage(
            cognitive_analysis, functional_analysis, cognitive_scores
        )

        # Detect decline trajectory
        trajectory = self._detect_decline_trajectory(observations, estimated_stage)

        # Get stage-specific risks
        stage_risks = self._get_stage_specific_risks(estimated_stage)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            estimated_stage, trajectory, functional_analysis
        )

        return {
            "patient_id": patient_id,
            "patient_name": patient.name,
            "patient_age": self._calculate_age(patient.date_of_birth),
            "estimated_cognitive_stage": estimated_stage["stage"],
            "stage_description": estimated_stage["description"],
            "confidence_score": estimated_stage["confidence"],  # 0-1
            "cognitive_profile": cognitive_analysis,
            "functional_status": functional_analysis,
            "decline_trajectory": trajectory,
            "cognitive_scores": cognitive_scores,
            "stage_specific_risks": stage_risks,
            "safety_alerts": self._generate_safety_alerts(
                estimated_stage, functional_analysis
            ),
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ========== PRIVATE HELPERS ==========

    def _analyze_observations(self, observations: List[CaregiverObservation]) -> Dict:
        """Analyze observations for cognitive patterns."""
        if not observations:
            return {
                "trend": "unknown",
                "cognitive_events": [],
                "event_count": 0,
            }

        # Count occurrences of cognitive-related keywords
        cognitive_event_counts = {
            category: 0 for category in COGNITIVE_KEYWORDS.keys()
        }
        recent_events = []

        for obs in observations:
            if not obs.observation_text:
                continue

            text_lower = obs.observation_text.lower()

            # Match keywords
            for category, keywords in COGNITIVE_KEYWORDS.items():
                if any(kw in text_lower for kw in keywords):
                    cognitive_event_counts[category] += 1
                    recent_events.append(
                        {
                            "date": obs.created_at.isoformat(),
                            "category": category,
                            "observation": obs.observation_text[:100],
                        }
                    )

        # Detect trend
        recent_count = len(
            [o for o in observations if self._is_recent(o.created_at, days=30)]
        )
        older_count = len(
            [o for o in observations if not self._is_recent(o.created_at, days=30)]
        )

        trend = "stable"
        if recent_count > older_count * 1.5:
            trend = "declining"
        elif recent_count > 0 and older_count == 0:
            trend = "new_onset"

        return {
            "trend": trend,
            "event_count_total": len(observations),
            "cognitive_event_counts": cognitive_event_counts,
            "recent_cognitive_events": recent_events[-5:],  # Last 5
            "dominant_category": max(
                cognitive_event_counts.items(), key=lambda x: x[1]
            )[0]
            if cognitive_event_counts
            else None,
        }

    def _analyze_functional_status(
        self, observations: List[CaregiverObservation]
    ) -> Dict:
        """Analyze ADL/IADL functional status."""
        if not observations:
            return {"adl_status": "unknown", "iadl_status": "unknown"}

        adl_issues = []
        iadl_issues = []

        for obs in observations:
            if not obs.observation_text:
                continue

            text_lower = obs.observation_text.lower()

            for keyword in FUNCTIONAL_KEYWORDS.get("adl", []):
                if keyword in text_lower:
                    adl_issues.append(obs.observation_text[:80])

            for keyword in FUNCTIONAL_KEYWORDS.get("iadl", []):
                if keyword in text_lower:
                    iadl_issues.append(obs.observation_text[:80])

        # Categorize status
        def categorize_dependency(issues_count):
            if issues_count == 0:
                return "independent"
            elif issues_count <= 2:
                return "minimal_dependence"
            elif issues_count <= 5:
                return "moderate_dependence"
            else:
                return "severe_dependence"

        return {
            "adl_status": categorize_dependency(len(adl_issues)),
            "iadl_status": categorize_dependency(len(iadl_issues)),
            "adl_issues": adl_issues[:3],
            "iadl_issues": iadl_issues[:3],
            "fall_risk": any("fall" in o.observation_text.lower() for o in observations),
        }

    def _extract_cognitive_scores(
        self, records: List[MedicalRecord]
    ) -> Dict[str, Any]:
        """Extract MMSE/MoCA scores from clinical records."""
        scores = {}
        for record in records:
            if "mmse" in record.description.lower():
                # Try to parse score from notes
                if record.notes:
                    try:
                        score = int("".join(filter(str.isdigit, record.notes)))
                        scores["mmse"] = {
                            "score": score,
                            "date": record.date.isoformat(),
                        }
                    except:
                        pass

            if "moca" in record.description.lower():
                if record.notes:
                    try:
                        score = int("".join(filter(str.isdigit, record.notes)))
                        scores["moca"] = {"score": score, "date": record.date.isoformat()}
                    except:
                        pass

        return scores

    def _estimate_cognitive_stage(
        self, cognitive_analysis: Dict, functional_analysis: Dict, scores: Dict
    ) -> Dict[str, Any]:
        """Estimate cognitive stage based on available data."""
        confidence = 0.0
        stage = "unknown"
        description = "Insufficient data for cognitive staging"

        # If we have formal MMSE/MoCA score, use it (high confidence)
        if "mmse" in scores:
            mmse = scores["mmse"]["score"]
            confidence = 0.95

            if mmse >= 24:
                stage = "normal"
            elif 18 <= mmse <= 23:
                stage = "mild_cognitive_impairment"
            elif 12 <= mmse <= 17:
                stage = "mild_dementia"
            elif 8 <= mmse <= 11:
                stage = "moderate_dementia"
            else:
                stage = "severe_dementia"

        # Else, use observation-based heuristic (lower confidence)
        else:
            adl_status = functional_analysis.get("adl_status", "unknown")
            cognitive_trend = cognitive_analysis.get("trend", "stable")
            dominant_cog_category = cognitive_analysis.get("dominant_category")

            if cognitive_trend == "stable" and adl_status == "independent":
                stage = "normal"
                confidence = 0.6
            elif cognitive_trend == "declining" and adl_status == "minimal_dependence":
                stage = "mild_cognitive_impairment"
                confidence = 0.7
            elif adl_status == "moderate_dependence":
                stage = "mild_dementia"
                confidence = 0.65
            elif adl_status == "severe_dependence":
                stage = "moderate_dementia"
                confidence = 0.6
            else:
                stage = "unknown"
                confidence = 0.4

        # Get description
        description = COGNITIVE_STAGES.get(stage, {}).get(
            "description", "Unknown cognitive stage"
        )

        return {
            "stage": stage,
            "description": description,
            "confidence": confidence,
        }

    def _detect_decline_trajectory(
        self, observations: List[CaregiverObservation], estimated_stage: Dict
    ) -> Dict[str, Any]:
        """Detect decline trajectory: stable, slow, or rapid."""
        if len(observations) < 2:
            return {"trajectory": "unknown", "rate_per_month": 0}

        # Sort by date
        sorted_obs = sorted(observations, key=lambda x: x.created_at)

        # Count cognitive events in recent vs historical
        recent_cutoff = datetime.utcnow() - timedelta(days=90)
        recent_obs = [o for o in sorted_obs if o.created_at >= recent_cutoff]
        older_obs = [o for o in sorted_obs if o.created_at < recent_cutoff]

        recent_cognitive_count = sum(
            1
            for o in recent_obs
            if o.observation_text
            and any(
                kw in o.observation_text.lower()
                for kws in COGNITIVE_KEYWORDS.values()
                for kw in kws
            )
        )
        older_cognitive_count = sum(
            1
            for o in older_obs
            if o.observation_text
            and any(
                kw in o.observation_text.lower()
                for kws in COGNITIVE_KEYWORDS.values()
                for kw in kws
            )
        )

        # Estimate decline rate
        trajectory = "stable"
        rate_per_month = 0.0

        if len(recent_obs) > 0 and len(older_obs) > 0:
            # Simple heuristic: ratio of recent to older
            ratio = recent_cognitive_count / max(older_cognitive_count, 1)
            if ratio > 2.0:
                trajectory = "rapid_decline"
                rate_per_month = 1.0
            elif ratio > 1.2:
                trajectory = "slow_decline"
                rate_per_month = 0.3
            else:
                trajectory = "stable"
                rate_per_month = 0.0

        return {
            "trajectory": trajectory,
            "rate_per_month": rate_per_month,
            "recent_event_density": len(recent_obs),
            "interpretation": f"Patient showing {trajectory} cognitive/functional pattern",
        }

    def _get_stage_specific_risks(self, estimated_stage: Dict) -> List[Dict]:
        """Get medication and safety risks specific to this cognitive stage."""
        stage = estimated_stage["stage"]
        risks = STAGE_SPECIFIC_DRUG_RISKS.get(stage, [])

        return [
            {
                "drug_class": r["drug_class"],
                "risk": r["risk"],
                "severity": r.get("severity", "medium"),
                "affected_drugs": r.get("drugs", []),
                "alternative": r.get("alternative"),
            }
            for r in risks
        ]

    def _generate_safety_alerts(
        self, estimated_stage: Dict, functional_analysis: Dict
    ) -> List[Dict]:
        """Generate stage-specific safety alerts."""
        alerts = []
        stage = estimated_stage["stage"]

        # Dementia-specific alerts
        if stage in ["moderate_dementia", "severe_dementia"]:
            alerts.append(
                {
                    "severity": "HIGH",
                    "category": "cognitive_safety",
                    "message": f"Patient in {stage} - high safety risk",
                    "action": "Implement caregiver support, environmental modifications, medication review",
                }
            )

            # Swallowing/aspiration risk in moderate/severe dementia
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "category": "aspiration_risk",
                    "message": "Potential swallowing difficulty in advanced dementia",
                    "action": "Evaluate swallowing; consider diet modifications",
                }
            )

        # Fall risk
        if functional_analysis.get("fall_risk"):
            alerts.append(
                {
                    "severity": "HIGH",
                    "category": "fall_risk",
                    "message": "Fall events documented in caregiver observations",
                    "action": "Review medications (benzodiazepines, opioids); assess home safety",
                }
            )

        # ADL dependence alerts
        adl_status = functional_analysis.get("adl_status")
        if adl_status in ["severe_dependence"]:
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "category": "dependence",
                    "message": "Total ADL dependence - patient requires 24/7 care",
                    "action": "Ensure adequate caregiver resources; consider institutionalization",
                }
            )

        return alerts

    def _generate_recommendations(
        self, estimated_stage: Dict, trajectory: Dict, functional_analysis: Dict
    ) -> List[Dict]:
        """Generate stage-appropriate clinical recommendations."""
        recommendations = []
        stage = estimated_stage["stage"]

        # Cognitive monitoring
        if trajectory["trajectory"] in ["slow_decline", "rapid_decline"]:
            recommendations.append(
                {
                    "category": "monitoring",
                    "priority": "high",
                    "message": "Patient showing cognitive decline",
                    "action": f"Schedule cognitive re-assessment in 3 months; neuropsychology referral if rapid decline",
                }
            )

        # Medication optimization by stage
        if stage in ["mild_cognitive_impairment"]:
            recommendations.append(
                {
                    "category": "medications",
                    "priority": "high",
                    "message": "In MCI: avoid anticholinergics and benzodiazepines",
                    "action": "Review medications; consider cognitive enhancers (donepezil) if Alzheimer's",
                }
            )
        elif stage in ["mild_dementia", "moderate_dementia"]:
            recommendations.append(
                {
                    "category": "medications",
                    "priority": "high",
                    "message": f"In {stage}: aggressive deprescribing focus",
                    "action": "Eliminate non-essential drugs; prioritize comfort and safety",
                }
            )

        # ADL support
        adl_status = functional_analysis.get("adl_status")
        if adl_status != "independent":
            recommendations.append(
                {
                    "category": "functional_support",
                    "priority": "medium",
                    "message": f"ADL status: {adl_status}",
                    "action": f"Implement appropriate level of caregiver assistance; occupational therapy referral",
                }
            )

        # Caregiver burden
        recommendations.append(
            {
                "category": "caregiver_support",
                "priority": "medium",
                "message": "Caregiver support critical for cognitive decline management",
                "action": "Assess caregiver burden; provide respite care options, education, support groups",
            }
        )

        return recommendations

    def _is_recent(self, date: datetime, days: int = 30) -> bool:
        """Check if date is within N days of now."""
        return (datetime.utcnow() - date).days <= days

    def _calculate_age(self, date_of_birth: datetime) -> int:
        """Calculate age from date of birth."""
        today = datetime.utcnow()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
