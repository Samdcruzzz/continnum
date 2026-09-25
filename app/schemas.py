from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ============ PATIENT SCHEMAS ============
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    gender: Optional[str] = None
    phone: str
    email: EmailStr
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class PatientResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ DOCTOR SCHEMAS ============
class DoctorCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    hospital: Optional[str] = None
    specialization: Optional[str] = None

class DoctorResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    specialization: Optional[str] = None
    hospital: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ MEDICAL RECORD SCHEMAS ============
class MedicalRecordCreate(BaseModel):
    category: str
    document_type: str
    description: str
    date_of_record: str
    source: str

class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: int
    category: str
    document_type: str
    description: str
    date_of_record: str
    source: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ MEDICINE SCHEMAS ============
class MedicineCreate(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str
    prescribed_date: str
    stop_date: Optional[str] = None
    prescribed_by: Optional[str] = None
    indication: Optional[str] = None
    change_note: Optional[str] = None  # P0: NEW FIELD - e.g., "dosage increased from 500mg to 750mg"

class MedicineResponse(BaseModel):
    id: int
    patient_id: int
    medicine_name: str
    dosage: str
    frequency: str
    prescribed_date: str
    stop_date: Optional[str] = None
    is_current: bool
    indication: Optional[str] = None
    change_note: Optional[str] = None  # P0: NEW FIELD
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ CAREGIVER OBSERVATION SCHEMAS ============
class ObservationCreate(BaseModel):
    caregiver_name: str
    observation_text: str
    category: str
    date_of_observation: str
    severity: Optional[str] = None

class ObservationResponse(BaseModel):
    id: int
    patient_id: int
    caregiver_name: str
    observation_text: str
    category: str
    date_of_observation: str
    severity: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ CONSENT SCHEMAS ============
class ConsentCreate(BaseModel):
    doctor_id: int
    allowed_categories: str
    expiry_date: Optional[str] = None

class ConsentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    allowed_categories: str
    status: str
    expiry_date: Optional[str] = None
    requested_date: datetime
    decided_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============ TIMELINE EVENT SCHEMA ============
class TimelineEventResponse(BaseModel):
    """Single event in patient's longitudinal timeline"""
    record_id: int
    event_type: str  # "medication", "diagnosis", "observation", "procedure", etc.
    date: str
    title: str
    description: str
    category: str
    source: str
    
    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    """Full patient timeline - events sorted chronologically"""
    patient_id: int
    total_events: int
    events: list[TimelineEventResponse]
    
    class Config:
        from_attributes = True
