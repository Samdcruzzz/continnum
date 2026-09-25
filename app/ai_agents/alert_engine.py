"""
Real-Time Alert Engine

Provides WebSocket-based live alert streaming for:
- New clinical alerts as they're generated
- Alert status updates (acknowledged, resolved)
- Dashboard push notifications
- Clinical workflow integration

This engine monitors patient records and clinical agents for alerts,
streaming them to connected WebSocket clients in real-time.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Callable, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from app.models import Patient, MedicalRecord, CaregiverObservation
from app.ai_agents.orchestrator import HealthMemoryOrchestrator


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertCategory(str, Enum):
    """Alert categories"""
    DRUG_INTERACTION = "drug_interaction"
    DRUG_DISEASE = "drug_disease"
    DOSING = "dosing"
    FALL_RISK = "fall_risk"
    COGNITIVE_DECLINE = "cognitive_decline"
    MEDICATION_COUNT = "medication_count"
    ADHERENCE = "adherence"
    LAB_ABNORMAL = "lab_abnormal"
    POLYPHARMACY = "polypharmacy"
    FUNCTIONAL_DECLINE = "functional_decline"
    CONTRAINDICATION = "contraindication"


@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    patient_id: int
    severity: AlertSeverity
    category: AlertCategory
    message: str
    action: str
    timestamp: str
    source_agent: str  # which agent generated this
    acknowledged: bool = False
    resolved: bool = False
    data: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert alert to JSON"""
        return json.dumps(asdict(self))


class AlertStream:
    """Manages active alert subscriptions for WebSocket clients"""

    def __init__(self):
        self.subscribers: Dict[int, Set[Callable]] = {}  # patient_id -> set of callbacks
        self.alert_history: Dict[int, List[Alert]] = {}  # patient_id -> alert list
        self.max_history_per_patient = 100

    def subscribe(self, patient_id: int, callback: Callable) -> None:
        """Subscribe to alerts for a patient"""
        if patient_id not in self.subscribers:
            self.subscribers[patient_id] = set()
            self.alert_history[patient_id] = []
        self.subscribers[patient_id].add(callback)

    def unsubscribe(self, patient_id: int, callback: Callable) -> None:
        """Unsubscribe from patient alerts"""
        if patient_id in self.subscribers:
            self.subscribers[patient_id].discard(callback)
            if not self.subscribers[patient_id]:
                del self.subscribers[patient_id]

    async def publish_alert(self, alert: Alert) -> None:
        """Publish alert to all subscribers"""
        # Store in history
        if alert.patient_id not in self.alert_history:
            self.alert_history[alert.patient_id] = []

        self.alert_history[alert.patient_id].append(alert)

        # Trim history if too large
        if (
            len(self.alert_history[alert.patient_id])
            > self.max_history_per_patient
        ):
            self.alert_history[alert.patient_id] = self.alert_history[
                alert.patient_id
            ][-self.max_history_per_patient :]

        # Send to all subscribers
        if alert.patient_id in self.subscribers:
            tasks = []
            for callback in self.subscribers[alert.patient_id]:
                tasks.append(callback(alert))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    def get_alert_history(
        self, patient_id: int, limit: int = 50
    ) -> List[Alert]:
        """Get alert history for patient"""
        if patient_id not in self.alert_history:
            return []
        return self.alert_history[patient_id][-limit:]


class RealTimeAlertEngine:
    """
    Real-time alert generation and streaming engine.

    Monitors clinical data and generates alerts based on:
    - AI agent assessments (polypharmacy, cognition, context)
    - Lab value changes
    - New caregiver observations
    - Medication changes
    - Patient condition monitoring
    """

    def __init__(self, db: Session, orchestrator: HealthMemoryOrchestrator):
        self.db = db
        self.orchestrator = orchestrator
        self.alert_stream = AlertStream()
        self.monitoring_tasks: Dict[int, asyncio.Task] = {}

    def subscribe_patient_alerts(
        self, patient_id: int, callback: Callable
    ) -> None:
        """Subscribe to real-time alerts for a patient"""
        self.alert_stream.subscribe(patient_id, callback)
        # Start monitoring this patient if not already
        if patient_id not in self.monitoring_tasks:
            self.monitoring_tasks[patient_id] = asyncio.create_task(
                self._monitor_patient(patient_id)
            )

    def unsubscribe_patient_alerts(
        self, patient_id: int, callback: Callable
    ) -> None:
        """Unsubscribe from patient alerts"""
        self.alert_stream.unsubscribe(patient_id, callback)
        # Stop monitoring if no more subscribers
        if patient_id not in self.alert_stream.subscribers:
            if patient_id in self.monitoring_tasks:
                self.monitoring_tasks[patient_id].cancel()
                del self.monitoring_tasks[patient_id]

    async def _monitor_patient(self, patient_id: int) -> None:
        """
        Continuously monitor patient for new alerts.
        Runs while there are active subscribers.
        """
        last_check = datetime.utcnow()
        check_interval = 30  # seconds

        try:
            while patient_id in self.alert_stream.subscribers:
                await asyncio.sleep(check_interval)

                # Get current clinical alerts
                try:
                    alerts = await self._generate_alerts(
                        patient_id, since=last_check
                    )

                    for alert in alerts:
                        await self.alert_stream.publish_alert(alert)

                    last_check = datetime.utcnow()

                except Exception as e:
                    print(f"Error generating alerts for patient {patient_id}: {e}")
                    # Continue monitoring despite errors

        except asyncio.CancelledError:
            pass

    async def _generate_alerts(
        self, patient_id: int, since: datetime
    ) -> List[Alert]:
        """Generate new alerts for patient since last check"""
        alerts = []
        alert_id_counter = 0

        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return alerts

        # CHECK 1: Polypharmacy Risk
        try:
            summary = self.orchestrator.get_clinical_summary(
                patient_id=patient_id,
                requester_id=1,  # system user
                requester_role="system",
                clinical_query="medication safety check",
            )

            if "safety" in summary:
                safety = summary["safety"]
                risk_score = safety.get("overall_risk_score", 0)

                if risk_score >= 7:
                    alerts.append(
                        Alert(
                            alert_id=f"POLY-{patient_id}-{alert_id_counter}",
                            patient_id=patient_id,
                            severity=AlertSeverity.HIGH,
                            category=AlertCategory.POLYPHARMACY,
                            message=f"HIGH polypharmacy risk score: {risk_score}/10",
                            action="Conduct medication review; consider deprescribing",
                            timestamp=datetime.utcnow().isoformat(),
                            source_agent="PolypharmacyRiskAgent",
                            data={"risk_score": risk_score},
                        )
                    )
                    alert_id_counter += 1

                # CHECK 2: Drug-Drug Interactions
                ddi_list = safety.get("drug_drug_interactions", [])
                for ddi in ddi_list:
                    if ddi.get("severity") in ["severe", "high"]:
                        alerts.append(
                            Alert(
                                alert_id=f"DDI-{patient_id}-{alert_id_counter}",
                                patient_id=patient_id,
                                severity=AlertSeverity.HIGH,
                                category=AlertCategory.DRUG_INTERACTION,
                                message=f"Drug interaction: {ddi['drug_a']} + {ddi['drug_b']}",
                                action=ddi.get(
                                    "recommendation",
                                    "Review interaction; consider alternative",
                                ),
                                timestamp=datetime.utcnow().isoformat(),
                                source_agent="PolypharmacyRiskAgent",
                                data=ddi,
                            )
                        )
                        alert_id_counter += 1

                # CHECK 3: Drug-Disease Conflicts
                ddc_list = safety.get("drug_disease_conflicts", [])
                for ddc in ddc_list:
                    if ddc.get("severity") in ["high", "critical"]:
                        alerts.append(
                            Alert(
                                alert_id=f"DDC-{patient_id}-{alert_id_counter}",
                                patient_id=patient_id,
                                severity=AlertSeverity.CRITICAL
                                if ddc.get("severity") == "critical"
                                else AlertSeverity.HIGH,
                                category=AlertCategory.DRUG_DISEASE,
                                message=f"Contraindication: {ddc['drug']} + {ddc['disease']}",
                                action=ddc.get(
                                    "recommendation", "AVOID; use alternative"
                                ),
                                timestamp=datetime.utcnow().isoformat(),
                                source_agent="PolypharmacyRiskAgent",
                                data=ddc,
                            )
                        )
                        alert_id_counter += 1

        except Exception as e:
            print(f"Error checking polypharmacy for {patient_id}: {e}")

        # CHECK 4: Cognitive Decline & Fall Risk
        try:
            from app.ai_agents.cognitive_decline_agent import (
                CognitiveDeclineAgent,
            )

            cog_agent = CognitiveDeclineAgent(self.db)
            cog_analysis = cog_agent.analyze(patient_id)

            if cog_analysis.get("safety_alerts"):
                for safety_alert in cog_analysis["safety_alerts"]:
                    alerts.append(
                        Alert(
                            alert_id=f"COG-{patient_id}-{alert_id_counter}",
                            patient_id=patient_id,
                            severity=AlertSeverity[safety_alert.get("severity", "MEDIUM")],
                            category=AlertCategory[
                                safety_alert.get("category", "COGNITIVE_DECLINE").upper()
                            ],
                            message=safety_alert.get("message"),
                            action=safety_alert.get("action"),
                            timestamp=datetime.utcnow().isoformat(),
                            source_agent="CognitiveDeclineAgent",
                            data=safety_alert,
                        )
                    )
                    alert_id_counter += 1

        except Exception as e:
            print(f"Error checking cognitive status for {patient_id}: {e}")

        # CHECK 5: New Lab Results (abnormal values)
        try:
            new_records = (
                self.db.query(MedicalRecord)
                .filter(
                    MedicalRecord.patient_id == patient_id,
                    MedicalRecord.date >= since,
                    MedicalRecord.record_type.in_(["lab", "vital"]),
                )
                .all()
            )

            for record in new_records:
                if self._is_abnormal_lab(record):
                    alerts.append(
                        Alert(
                            alert_id=f"LAB-{patient_id}-{alert_id_counter}",
                            patient_id=patient_id,
                            severity=AlertSeverity.MEDIUM,
                            category=AlertCategory.LAB_ABNORMAL,
                            message=f"Abnormal lab: {record.description}",
                            action="Review result; consider clinical implications",
                            timestamp=datetime.utcnow().isoformat(),
                            source_agent="LabMonitor",
                            data={
                                "lab_type": record.record_type,
                                "description": record.description,
                                "date": record.date.isoformat(),
                            },
                        )
                    )
                    alert_id_counter += 1

        except Exception as e:
            print(f"Error checking labs for {patient_id}: {e}")

        # CHECK 6: New Caregiver Observations (decline indicators)
        try:
            new_observations = (
                self.db.query(CaregiverObservation)
                .filter(
                    CaregiverObservation.patient_id == patient_id,
                    CaregiverObservation.created_at >= since,
                )
                .all()
            )

            for obs in new_observations:
                severity, message, action = self._analyze_observation(obs)
                if severity and message:
                    alerts.append(
                        Alert(
                            alert_id=f"OBS-{patient_id}-{alert_id_counter}",
                            patient_id=patient_id,
                            severity=AlertSeverity[severity],
                            category=AlertCategory.FUNCTIONAL_DECLINE,
                            message=message,
                            action=action,
                            timestamp=datetime.utcnow().isoformat(),
                            source_agent="CaregiverObservationMonitor",
                            data={"observation": obs.observation_text[:200]},
                        )
                    )
                    alert_id_counter += 1

        except Exception as e:
            print(f"Error checking observations for {patient_id}: {e}")

        return alerts

    def _is_abnormal_lab(self, record: MedicalRecord) -> bool:
        """Check if lab result is abnormal"""
        description = record.description.lower()
        notes = (record.notes or "").lower()

        # Keywords indicating abnormal results
        abnormal_keywords = [
            "high",
            "low",
            "elevated",
            "critical",
            "abnormal",
            "positive",
            "negative",
        ]

        return any(kw in description or kw in notes for kw in abnormal_keywords)

    def _analyze_observation(
        self, obs: CaregiverObservation
    ) -> tuple[Optional[str], Optional[str], str]:
        """Analyze caregiver observation for alerts"""
        text = (obs.observation_text or "").lower()

        # Fall-related
        if any(w in text for w in ["fall", "fell", "tripped", "stumble"]):
            return (
                "HIGH",
                "Fall event reported by caregiver",
                "Assess for injuries; review fall risk factors; consider PT/OT",
            )

        # Memory/confusion
        if any(
            w in text for w in ["memory", "forgot", "confus", "disoriented", "lost"]
        ):
            return (
                "MEDIUM",
                "Cognitive concern reported: memory/orientation issue",
                "Cognitive assessment; monitor for decline",
            )

        # Behavioral changes
        if any(
            w in text
            for w in ["agitat", "wander", "aggress", "paranoid", "angry", "mood"]
        ):
            return (
                "MEDIUM",
                "Behavioral change reported",
                "Psychiatric evaluation; medication review",
            )

        # Mobility issues
        if any(w in text for w in ["mobility", "walk", "gait", "transfer", "bed"]):
            return (
                "MEDIUM",
                "Mobility decline reported",
                "Physical therapy referral; home safety assessment",
            )

        # Medication adherence
        if any(
            w in text
            for w in ["forgot", "missed", "skip", "took", "medication", "pills"]
        ):
            return (
                "MEDIUM",
                "Medication adherence concern",
                "Simplify regimen; consider pill organizer or medication management",
            )

        return None, None, ""

    def get_alert_history(self, patient_id: int, limit: int = 50) -> List[Dict]:
        """Get historical alerts for a patient"""
        alerts = self.alert_stream.get_alert_history(patient_id, limit)
        return [asdict(alert) for alert in alerts]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged"""
        for patient_alerts in self.alert_stream.alert_history.values():
            for alert in patient_alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved"""
        for patient_alerts in self.alert_stream.alert_history.values():
            for alert in patient_alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    return True
        return False
