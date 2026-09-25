"""
Bridges the real Postgres-backed models (Patient/MedicalRecord/Medicine/
CaregiverObservation) to the plain record-dict format the AI agents
(medication_agent, trend_agent, context_agent) were written against.

P0 ENHANCEMENT: Each record now includes record_id for full traceability
from AI responses back to the source database record.
"""

from sqlalchemy.orm import Session
from app.models import MedicalRecord, Medicine, CaregiverObservation

# Document types recognized as "trend-able" clinical readings vs plain notes.
_TREND_TYPES = {"vitals", "lab"}
_EVENT_TYPES = {"diagnosis", "procedure"}


def _normalize_category(category: str) -> str:
    return (category or "").strip().lower()


class RecordsAdapter:
    """
    Records Adapter agent wrapper for handling medical record formats and sources.
    """

    @staticmethod
    def build_patient_records(patient_id: int, db: Session) -> list[dict]:
        """Pulls every record the platform has for a patient and returns it in
        the flat dict shape the AI agents understand. Consent filtering happens
        AFTER this - this function itself does not enforce access control.
        
        P0: Each record includes record_id for full traceability.
        """
        records: list[dict] = []

        # P0: MEDICAL RECORDS - now includes record_id
        for r in db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all():
            doc_type = (r.document_type or "").strip().lower()
            rtype = doc_type if doc_type in (_TREND_TYPES | _EVENT_TYPES) else "diagnosis"
            records.append({
                "type": rtype,
                "category": _normalize_category(r.category),
                "date": r.date_of_record,
                "condition": r.description,
                "value": r.description,
                "source": r.source,
                "record_id": r.id,  # P0: NEW - traceability
            })

        # P0: MEDICINES - now uses real change_note column instead of indication fallback
        for m in db.query(Medicine).filter(Medicine.patient_id == patient_id).all():
            records.append({
                "type": "medication",
                "category": _normalize_category("medicines"),
                "date": m.prescribed_date,
                "medicine_name": m.medicine_name,
                "dose": m.dosage,
                "frequency": m.frequency,
                "prescribed_by": m.prescribed_by,
                "indication": m.indication,
                "change_note": m.change_note or "",  # P0: NOW USES REAL COLUMN
                "is_current": m.is_current,
                "source": "prescription",
                "record_id": m.id,  # P0: NEW - traceability
            })

        # P0: CAREGIVER OBSERVATIONS - now includes record_id
        for o in db.query(CaregiverObservation).filter(CaregiverObservation.patient_id == patient_id).all():
            records.append({
                "type": "observation",
                "category": _normalize_category(o.category),
                "date": o.date_of_observation,
                "value": o.observation_text,
                "caregiver_name": o.caregiver_name,
                "severity": o.severity,
                "source": "caregiver",
                "record_id": o.id,  # P0: NEW - traceability
            })

        return records
