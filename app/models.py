from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ============ PATIENT TABLE ============
class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(String, nullable=False)
    gender = Column(String(10))
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    address = Column(Text)
    emergency_contact = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    medicines = relationship("Medicine", back_populates="patient", cascade="all, delete-orphan")
    observations = relationship("CaregiverObservation", back_populates="patient", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="patient", cascade="all, delete-orphan")


# ============ DOCTOR TABLE ============
class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    hospital = Column(String(150))
    specialization = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    consents = relationship("Consent", back_populates="doctor", cascade="all, delete-orphan")


# ============ MEDICAL RECORD TABLE ============
class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    category = Column(String(50), nullable=False)
    document_type = Column(String(50), nullable=False)
    raw_text = Column(Text)
    structured_data = Column(Text)
    description = Column(Text)
    date_of_record = Column(String, nullable=False)
    source = Column(String(100))
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="medical_records")


# ============ MEDICINE TABLE ============
class Medicine(Base):
    __tablename__ = "medicines"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medicine_name = Column(String(150), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    prescribed_date = Column(String, nullable=False)
    stop_date = Column(String)
    prescribed_by = Column(String(150))
    indication = Column(Text)
    change_note = Column(Text)  # P0: NEW COLUMN - tracks medication changes (e.g., "dosage increased from 500mg to 750mg")
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="medicines")


# ============ CAREGIVER OBSERVATION TABLE ============
class CaregiverObservation(Base):
    __tablename__ = "caregiver_observations"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    caregiver_name = Column(String(150), nullable=False)
    observation_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    date_of_observation = Column(String, nullable=False)
    severity = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("Patient", back_populates="observations")


# ============ CONSENT TABLE ============
class Consent(Base):
    __tablename__ = "consents"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    allowed_categories = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    expiry_date = Column(String)
    requested_date = Column(DateTime, default=datetime.utcnow)
    decided_date = Column(DateTime)
    
    patient = relationship("Patient", back_populates="consents")
    doctor = relationship("Doctor", back_populates="consents")
