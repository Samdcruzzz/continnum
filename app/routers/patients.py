from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Patient, MedicalRecord, Medicine, CaregiverObservation
from app.schemas import PatientCreate, PatientResponse, TimelineResponse, TimelineEventResponse

router = APIRouter(prefix="/api/patients", tags=["patients"])

# CREATE PATIENT
@router.post("/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient record"""
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# GET PATIENT BY ID
@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Retrieve patient details by ID"""
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

# GET ALL PATIENTS
@router.get("/")
def list_patients(db: Session = Depends(get_db)):
    """List all patients"""
    patients = db.query(Patient).all()
    return patients


# P0: NEW ENDPOINT - LONGITUDINAL TIMELINE
@router.get("/{patient_id}/timeline", response_model=TimelineResponse)
def get_patient_timeline(patient_id: int, db: Session = Depends(get_db)):
    """
    GET /api/patients/{patient_id}/timeline
    
    Returns complete patient timeline - all medical events chronologically sorted.
    Includes: medications, diagnoses, procedures, observations, lab results, vitals.
    
    Each event includes:
    - record_id: Database ID for traceability to source record
    - event_type: medication, diagnosis, procedure, observation, lab, vitals
    - date: When event occurred (YYYY-MM-DD format)
    - title: Short summary
    - description: Full details
    - category: Normalized category for consent filtering
    - source: Where record came from (prescription, caregiver, manual, etc.)
    
    Events are sorted by date ascending (oldest first).
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    events: list[TimelineEventResponse] = []
    
    # P0: MEDICAL RECORDS (diagnosis, procedure, lab, vitals)
    for record in db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all():
        doc_type = (record.document_type or "").strip().lower()
        if doc_type in {"diagnosis", "procedure", "lab", "vitals"}:
            event_type = doc_type
        else:
            event_type = "diagnosis"  # default
        
        events.append(TimelineEventResponse(
            record_id=record.id,
            event_type=event_type,
            date=record.date_of_record,
            title=f"{event_type.capitalize()}: {record.description[:50]}",
            description=record.description or "",
            category=(record.category or "").strip().lower(),
            source=record.source or "medical_record",
        ))
    
    # P0: MEDICATIONS
    for med in db.query(Medicine).filter(Medicine.patient_id == patient_id).all():
        # Include both prescribed and stopped medications in timeline
        title = f"Medication: {med.medicine_name} {med.dosage}"
        if not med.is_current:
            title += " [STOPPED]"
        
        description = f"{med.medicine_name} {med.dosage} {med.frequency}"
        if med.indication:
            description += f" - Indication: {med.indication}"
        if med.change_note:
            description += f" - Change: {med.change_note}"
        if med.stop_date:
            description += f" - Stopped on: {med.stop_date}"
        
        events.append(TimelineEventResponse(
            record_id=med.id,
            event_type="medication",
            date=med.prescribed_date,
            title=title,
            description=description,
            category="medicines",
            source=med.prescribed_by or "prescription",
        ))
    
    # P0: CAREGIVER OBSERVATIONS
    for obs in db.query(CaregiverObservation).filter(CaregiverObservation.patient_id == patient_id).all():
        events.append(TimelineEventResponse(
            record_id=obs.id,
            event_type="observation",
            date=obs.date_of_observation,
            title=f"Observation: {obs.observation_text[:50]}",
            description=f"{obs.observation_text} [Caregiver: {obs.caregiver_name}]",
            category=(obs.category or "").strip().lower(),
            source="caregiver",
        ))
    
    # Sort chronologically by date (oldest first)
    def parse_date(event):
        try:
            return datetime.strptime(event.date, "%Y-%m-%d")
        except:
            return datetime.min
    
    events.sort(key=parse_date)
    
    return TimelineResponse(
        patient_id=patient_id,
        total_events=len(events),
        events=events,
    )
