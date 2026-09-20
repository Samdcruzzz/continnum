"""
P0 DEMO SEEDING SCRIPT - Nagarajan Patient Timeline

Creates a complete demo patient record with 5 key events spanning
Sept 2024 -> Sept 2026, showing medication changes and clinical progression.

Timeline:
  1. Sept 2024: Initial diagnosis - Type 2 Diabetes, started on Metformin
  2. Jan 2025: Medication adjustment - Metformin increased to 750mg
  3. Apr 2025: New comorbidity - Hypertension diagnosed, Amlodipine started
  4. Aug 2025: Medication optimization - Amlodipine reduced (side effects)
  5. Sept 2026: Routine checkup - Stable condition, continuing current meds

This is the timeline the judge will see in the demo. It shows:
- Medication change tracking (change_note field usage)
- Chronological ordering
- Clinical decision making
- Patient stability over time

USAGE:
  python seed_demo.py  # Idempotent - safe to run multiple times
"""

from app.database import SessionLocal, engine
from app.models import Base, Patient, Doctor, MedicalRecord, Medicine, CaregiverObservation, Consent
from datetime import datetime

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("=" * 60)
print("P0 DEMO SEEDING: Patient Nagarajan Timeline")
print("=" * 60)

# Check if patient already exists (idempotent)
existing = db.query(Patient).filter(
    Patient.first_name == "Nagarajan",
    Patient.email == "nagarajan.demo@example.com"
).first()

if existing:
    print(f"\n✓ Demo patient already exists (ID: {existing.id})")
    print("  Skipping seeding (idempotent)")
    db.close()
    exit(0)

# ============ CREATE DEMO PATIENT ============
demo_patient = Patient(
    first_name="Nagarajan",
    last_name="S.",
    date_of_birth="1950-03-15",  # Age 74
    gender="M",
    phone="555-9999",
    email="nagarajan.demo@example.com",
    address="42 Elderly Care Lane, Chennai, TN 600001",
    emergency_contact="Priya Nagarajan (Daughter)"
)
db.add(demo_patient)
db.commit()
db.refresh(demo_patient)
print(f"\n✓ Patient created: {demo_patient.first_name} (ID: {demo_patient.id})")

# ============ CREATE DEMO DOCTOR ============
demo_doctor = Doctor(
    first_name="Dr.",
    last_name="Ramesh",
    email="dr.ramesh.demo@hospital.com",
    phone="555-1234",
    hospital="CMC Hospital, Chennai",
    specialization="Internal Medicine"
)
db.add(demo_doctor)
db.commit()
db.refresh(demo_doctor)
print(f"✓ Doctor created: Dr. {demo_doctor.last_name} (ID: {demo_doctor.id})")

# ============ TIMELINE EVENT 1: Sept 2024 - Diabetes Diagnosis ============
# Medical Record: Diagnosis
diag1 = MedicalRecord(
    patient_id=demo_patient.id,
    category="diagnosis",
    document_type="diagnosis",
    description="Type 2 Diabetes Mellitus confirmed. HbA1c: 8.2%",
    date_of_record="2024-09-10",
    source="hospital_lab"
)
db.add(diag1)

# Medicine: Initial Metformin prescription
med1 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Metformin",
    dosage="500mg",
    frequency="Twice daily",
    prescribed_date="2024-09-10",
    prescribed_by="Dr. Ramesh",
    indication="Type 2 Diabetes Mellitus",
    change_note="Initial therapy - baseline for diabetes control",
    is_current=False  # Will be superseded later
)
db.add(med1)
db.commit()
print("✓ Event 1 (Sept 2024): Diabetes diagnosis + Metformin 500mg started")

# ============ TIMELINE EVENT 2: Jan 2025 - Medication Increase ============
# Medicine: Metformin increased to 750mg
med2 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Metformin",
    dosage="750mg",
    frequency="Twice daily",
    prescribed_date="2025-01-15",
    stop_date=None,
    prescribed_by="Dr. Ramesh",
    indication="Type 2 Diabetes Mellitus",
    change_note="Dosage increased from 500mg to 750mg due to suboptimal glycemic control (HbA1c: 7.8%)",
    is_current=False  # Will be superseded
)
db.add(med2)

# Medical Record: Follow-up observation
obs1 = CaregiverObservation(
    patient_id=demo_patient.id,
    caregiver_name="Priya Nagarajan",
    observation_text="Father's energy levels improving after medication adjustment. Better appetite.",
    category="caregiver_observation",
    date_of_observation="2025-01-20",
    severity="mild"
)
db.add(obs1)
db.commit()
print("✓ Event 2 (Jan 2025): Metformin increased to 750mg + caregiver observation")

# ============ TIMELINE EVENT 3: Apr 2025 - Hypertension Diagnosis ============
# Medical Record: Hypertension diagnosis
diag2 = MedicalRecord(
    patient_id=demo_patient.id,
    category="diagnosis",
    document_type="diagnosis",
    description="Essential Hypertension (Stage 2). BP: 152/94 mmHg. Risk for cardiovascular complications.",
    date_of_record="2025-04-05",
    source="clinic_visit"
)
db.add(diag2)

# Medicine: Amlodipine started
med3 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Amlodipine",
    dosage="5mg",
    frequency="Once daily",
    prescribed_date="2025-04-05",
    prescribed_by="Dr. Ramesh",
    indication="Essential Hypertension",
    change_note="New antihypertensive added to control BP. Target: <140/90 mmHg",
    is_current=False  # Will be modified later
)
db.add(med3)
db.commit()
print("✓ Event 3 (Apr 2025): Hypertension diagnosed + Amlodipine 5mg started")

# ============ TIMELINE EVENT 4: Aug 2025 - Medication Optimization ============
# Medicine: Amlodipine reduced due to side effects
med4 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Amlodipine",
    dosage="2.5mg",
    frequency="Once daily",
    prescribed_date="2025-08-12",
    stop_date=None,
    prescribed_by="Dr. Ramesh",
    indication="Essential Hypertension",
    change_note="Dosage reduced from 5mg to 2.5mg due to ankle edema side effects. BP now well-controlled at 138/88.",
    is_current=False  # Will be superseded
)
db.add(med4)

# Medical Record: Vital signs improvement
rec1 = MedicalRecord(
    patient_id=demo_patient.id,
    category="vitals",
    document_type="vitals",
    description="BP: 138/88 mmHg. HR: 72 bpm. Ankle edema resolving.",
    date_of_record="2025-08-15",
    source="clinic_visit"
)
db.add(rec1)
db.commit()
print("✓ Event 4 (Aug 2025): Amlodipine reduced to 2.5mg + vitals improving")

# ============ TIMELINE EVENT 5: Sept 2026 - Routine Checkup ============
# Current medications (mark previous as inactive)
# Metformin 750mg - CURRENT
med5_current_metformin = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Metformin",
    dosage="750mg",
    frequency="Twice daily",
    prescribed_date="2025-01-15",  # Established date (Event 2)
    stop_date=None,
    prescribed_by="Dr. Ramesh",
    indication="Type 2 Diabetes Mellitus",
    change_note="Current: dosage increase from 500mg effective since Jan 2025",
    is_current=True
)
db.add(med5_current_metformin)

# Amlodipine 2.5mg - CURRENT
med5_current_amlodipine = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Amlodipine",
    dosage="2.5mg",
    frequency="Once daily",
    prescribed_date="2025-08-12",  # Established date (Event 4)
    stop_date=None,
    prescribed_by="Dr. Ramesh",
    indication="Essential Hypertension",
    change_note="Current: well-tolerated at reduced dose, no side effects",
    is_current=True
)
db.add(med5_current_amlodipine)

# Medical Record: Latest checkup
rec2 = MedicalRecord(
    patient_id=demo_patient.id,
    category="follow-up",
    document_type="follow-up",
    description="Annual review: Patient stable on current regimen. HbA1c: 7.1% (improved). BP: 136/86 mmHg (well-controlled). No new complaints.",
    date_of_record="2026-09-08",
    source="clinic_visit"
)
db.add(rec2)
db.commit()
print("✓ Event 5 (Sept 2026): Annual checkup - stable on current medications")

# ============ CREATE CONSENT FOR DEMO ============
# Doctor has approved consent to access diabetes + hypertension records
consent = Consent(
    patient_id=demo_patient.id,
    doctor_id=demo_doctor.id,
    allowed_categories="diagnosis, medicines, follow-up, vitals",
    status="approved",
    expiry_date="2027-09-08",  # Valid for 1 year from latest checkup
    decided_date=datetime.utcnow()
)
db.add(consent)
db.commit()
print(f"✓ Consent created: Doctor has access to diagnosis, medicines, follow-up, vitals (Expires: 2027-09-08)")

# ============ FINAL SUMMARY ============
print("\n" + "=" * 60)
print("DEMO SEEDING COMPLETE")
print("=" * 60)
print(f"\nPatient: {demo_patient.first_name} (ID: {demo_patient.id})")
print(f"Doctor: Dr. {demo_doctor.last_name} (ID: {demo_doctor.id})")
print(f"\nTimeline Events: 5")
print("  1. Sept 2024: Type 2 Diabetes diagnosed → Metformin 500mg")
print("  2. Jan 2025:  Metformin increased to 750mg (HbA1c control)")
print("  3. Apr 2025:  Hypertension diagnosed → Amlodipine 5mg")
print("  4. Aug 2025:  Amlodipine reduced to 2.5mg (side effects)")
print("  5. Sept 2026: Annual checkup - stable, HbA1c 7.1%")
print(f"\nConsent: Approved (expires 2027-09-08)")
print(f"Accessible Categories: diagnosis, medicines, follow-up, vitals")

print("\nTesting Endpoints:")
print(f"  GET /api/patients/{demo_patient.id}")
print(f"  GET /api/patients/{demo_patient.id}/timeline")
print(f"  GET /api/patients/{demo_patient.id}/medicines")
print("\n✓ Demo is ready for judge walkthrough!")
print("=" * 60)

db.close()
