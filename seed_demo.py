"""
P0 DEMO SEEDING SCRIPT - Nagarajan Patient Timeline
Configured to match the Frontend UI inputs (continuum.html) and timeline visualization.

Kept in sync with continuum.html's `seedData` + `SHARED_PORTAL_PASSWORD`:
  - Patient phone:     9486508579
  - Doctor email:      doc@gmail.com
  - Shared password:   demo123   (used by BOTH the Caregiver portal and the
                        Doctor portal login forms in continuum.html)

New in this version:
  - Added the 17-Feb-2024 Angioplasty (PTCA to RCA) operation record, sourced
    from the Dr. Jeyasekharan Medical Trust operation report. This is now the
    EARLIEST event in the timeline (it predates the Sept-2024 diabetes
    diagnosis), performed by an external cardiologist rather than Dr. Ramesh.
"""

from datetime import datetime
from app.database import SessionLocal, engine
from app.models import Base, Patient, Doctor, MedicalRecord, Medicine, CaregiverObservation, Consent

# ======================================================
# SHARED DEMO CREDENTIALS
# Mirrors the SHARED_PORTAL_PASSWORD constant in continuum.html.
# Caregiver and Doctor portals sign in with this same password.
# ======================================================
SHARED_PORTAL_PASSWORD = "demo123"
DOCTOR_LOGIN_EMAIL = "doc@gmail.com"


def set_if_has(obj, attr, value):
    """
    Set an attribute only if the SQLAlchemy model actually defines it.
    Keeps this script resilient to schema differences (e.g. if `password`,
    `blood_group`, `license_number`, etc. haven't been added to the models
    yet) instead of blowing up with an AttributeError/TypeError.
    """
    if hasattr(obj, attr):
        setattr(obj, attr, value)


# Create tables if they do not exist
Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("=" * 60)
print("SEEDING DEMO PATIENT: Nagarajan S. (Frontend Integration)")
print("=" * 60)

# Clear existing demo patient/doctor to allow clean rewrites
existing_patients = db.query(Patient).filter(
    (Patient.phone == "9486508579") |
    (Patient.phone == "+1 (555) 890-1234") |
    (Patient.email == "nagarajan.demo@example.com")
).all()

if existing_patients:
    for p in existing_patients:
        db.query(Consent).filter(Consent.patient_id == p.id).delete()
        db.query(Medicine).filter(Medicine.patient_id == p.id).delete()
        db.query(MedicalRecord).filter(MedicalRecord.patient_id == p.id).delete()
        db.query(CaregiverObservation).filter(CaregiverObservation.patient_id == p.id).delete()
        db.delete(p)
    db.commit()
    print("✓ Cleared prior demo patient records for fresh sync")

existing_doctors = db.query(Doctor).filter(
    (Doctor.email == DOCTOR_LOGIN_EMAIL) |
    (Doctor.email == "dr.ramesh.demo@hospital.com")
).all()
if existing_doctors:
    for d in existing_doctors:
        db.delete(d)
    db.commit()
    print("✓ Cleared prior demo doctor records for fresh sync")

# ============ CREATE DEMO PATIENT ============
# Phone/email configured to match continuum.html's seedData.patient
demo_patient = Patient(
    first_name="Nagarajan",
    last_name="S.",
    date_of_birth="1966-05-23",
    gender="M",
    phone="9486508579",  # Also supports +1 (555) 890-1234 via query aliases
    email="nagarajan.demo@example.com",
    address="42 Elderly Care Lane, Chennai, TN 600001",
    emergency_contact="Thanu Shree N (Daughter)"
)
# Optional fields present in continuum.html's seedData.patient — set only if
# the schema supports them, so this script never breaks on older models.
set_if_has(demo_patient, "blood_group", "O+")
set_if_has(demo_patient, "allergies", "Penicillin, Peanuts")
set_if_has(demo_patient, "insurance_provider", "Star Health Insurance")
set_if_has(demo_patient, "insurance_policy_number", "SH-2024-88291")
set_if_has(demo_patient, "insurance_valid_till", "2026-12-31")
set_if_has(demo_patient, "emergency_contact_name", "Thanu Shree N")
set_if_has(demo_patient, "emergency_contact_relation", "Daughter")
set_if_has(demo_patient, "emergency_contact_phone", "9876543210")
set_if_has(demo_patient, "emergency_contact_email", "thanu.shree@email.com")
set_if_has(demo_patient, "caregiving_since", "2024-06-01")
# Caregiver portal login (continuum.html checks name + SHARED_PORTAL_PASSWORD)
set_if_has(demo_patient, "caregiver_password", SHARED_PORTAL_PASSWORD)

db.add(demo_patient)
db.commit()
db.refresh(demo_patient)
print(f"✓ Patient created: {demo_patient.first_name} {demo_patient.last_name} (ID: {demo_patient.id})")

# ============ CREATE DEMO DOCTOR ============
demo_doctor = Doctor(
    first_name="Dr.",
    last_name="Ramesh",
    email=DOCTOR_LOGIN_EMAIL,  # matches continuum.html sign-in hint: doc@gmail.com
    phone="555-1234",
    hospital="CMC Hospital, Chennai",
    specialization="Internal Medicine"
)
set_if_has(demo_doctor, "license_number", "TNMC-88213")
set_if_has(demo_doctor, "years_experience", 14)
# Doctor portal login (continuum.html checks email + SHARED_PORTAL_PASSWORD)
set_if_has(demo_doctor, "password", SHARED_PORTAL_PASSWORD)

db.add(demo_doctor)
db.commit()
db.refresh(demo_doctor)
print(f"✓ Doctor created: {demo_doctor.first_name} {demo_doctor.last_name} <{demo_doctor.email}> (ID: {demo_doctor.id})")

# ============ TIMELINE EVENT 0: Feb 2024 (earliest event) ============
# Source: Dr. Jeyasekharan Medical Trust — Dept. of Cardiology
# Angioplasty Report / Operation Record, OP No BK 7679, Cath No 202413482
procedure1 = MedicalRecord(
    patient_id=demo_patient.id,
    category="procedure",
    document_type="cardiology_procedure",
    description=(
        "Coronary Angioplasty (PTCA) with stent deployment to the RCA "
        "(Right Coronary Artery). Pre-diagnosis: PTCA to RCA. Post-diagnosis: "
        "PTCA done to RCA. RCA engaged with 6fr JR SH 3 guiding catheter; "
        "lesion crossed with .014\" Runthrough guide wire; pre-dilated with "
        "2mm x 10mm balloon @ 8 ATM x 30s. Stent: Boston Scientific Promus "
        "Premier 3.5mm x 24mm deployed at 8-11 ATM. Post-dilated with 4mm x "
        "12mm NC balloon @ 11-14 ATM x 30s. Post-procedure angiogram showed "
        "no residual stenosis / no flap. Patient hemodynamically stable "
        "throughout. Heart rate 76/min. Approach: RRA (right radial artery). "
        "Anaesthesia: LA/MAC."
    ),
    date_of_record="2024-02-17",
    source="external_hospital_record"
)
set_if_has(procedure1, "performing_doctor", "Dr. Chandrakumar Immanuel, MD, DM, FACC (Cardiologist, Reg. No: 54110)")
set_if_has(procedure1, "hospital_name", "Dr. Jeyasekharan Hospital & Nursing Home, Nagercoil")
set_if_has(procedure1, "reference_number", "OP No: BK 7679 | IP No: BC 7700 | Cath No: 202413482")
db.add(procedure1)

# ============ TIMELINE EVENT 1: Sept 2024 ============
diag1 = MedicalRecord(
    patient_id=demo_patient.id,
    category="diagnosis",
    document_type="diagnosis",
    description="Type 2 Diabetes Mellitus confirmed. HbA1c: 8.2%",
    date_of_record="2024-09-10",
    source="hospital_lab"
)
db.add(diag1)

med1 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Metformin",
    dosage="500mg",
    frequency="Twice daily",
    prescribed_date="2024-09-10",
    prescribed_by="Dr. Ramesh",
    indication="Type 2 Diabetes Mellitus",
    change_note="Initial therapy - baseline for diabetes control",
    is_current=False
)
db.add(med1)

# ============ TIMELINE EVENT 2: Jan 2025 ============
med2 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Metformin",
    dosage="750mg",
    frequency="Twice daily",
    prescribed_date="2025-01-15",
    prescribed_by="Dr. Ramesh",
    indication="Type 2 Diabetes Mellitus",
    change_note="Dosage increased from 500mg to 750mg due to suboptimal glycemic control (HbA1c: 7.8%)",
    is_current=False
)
db.add(med2)

obs1 = CaregiverObservation(
    patient_id=demo_patient.id,
    caregiver_name="Thanu Shree N",
    observation_text="Father's energy levels improving after medication adjustment. Better appetite.",
    category="caregiver_observation",
    date_of_observation="2025-01-20",
    severity="mild"
)
db.add(obs1)

# ============ TIMELINE EVENT 3: Apr 2025 ============
diag2 = MedicalRecord(
    patient_id=demo_patient.id,
    category="diagnosis",
    document_type="diagnosis",
    description="Essential Hypertension (Stage 2). BP: 152/94 mmHg. Risk for cardiovascular complications.",
    date_of_record="2025-04-05",
    source="clinic_visit"
)
db.add(diag2)

med3 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Amlodipine",
    dosage="5mg",
    frequency="Once daily",
    prescribed_date="2025-04-05",
    prescribed_by="Dr. Ramesh",
    indication="Essential Hypertension",
    change_note="New antihypertensive added to control BP. Target: <140/90 mmHg",
    is_current=False
)
db.add(med3)

# ============ TIMELINE EVENT 4: Aug 2025 ============
med4 = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Amlodipine",
    dosage="2.5mg",
    frequency="Once daily",
    prescribed_date="2025-08-12",
    prescribed_by="Dr. Ramesh",
    indication="Essential Hypertension",
    change_note="Dosage reduced from 5mg to 2.5mg due to ankle edema side effects. BP now well-controlled at 138/88.",
    is_current=False
)
db.add(med4)

rec1 = MedicalRecord(
    patient_id=demo_patient.id,
    category="vitals",
    document_type="vitals",
    description="BP: 138/88 mmHg. HR: 72 bpm. Ankle edema resolving.",
    date_of_record="2025-08-15",
    source="clinic_visit"
)
db.add(rec1)

# ============ TIMELINE EVENT 5: Sept 2026 ============
# Active Medicines for UI Active Medications section
current_metformin = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Metformin",
    dosage="750mg",
    frequency="Twice daily",
    prescribed_date="2025-01-15",
    prescribed_by="Dr. Ramesh",
    indication="Type 2 Diabetes Mellitus",
    change_note="Current: dosage increase from 500mg effective since Jan 2025",
    is_current=True
)
db.add(current_metformin)

current_amlodipine = Medicine(
    patient_id=demo_patient.id,
    medicine_name="Amlodipine",
    dosage="2.5mg",
    frequency="Once daily",
    prescribed_date="2025-08-12",
    prescribed_by="Dr. Ramesh",
    indication="Essential Hypertension",
    change_note="Current: well-tolerated at reduced dose, no side effects",
    is_current=True
)
db.add(current_amlodipine)

rec2 = MedicalRecord(
    patient_id=demo_patient.id,
    category="follow-up",
    document_type="follow-up",
    description="Annual review: Patient stable on current regimen. HbA1c: 7.1% (improved). BP: 136/86 mmHg (well-controlled).",
    date_of_record="2026-09-08",
    source="clinic_visit"
)
db.add(rec2)

# ============ CONSENT CONFIGURATION ============
consent = Consent(
    patient_id=demo_patient.id,
    doctor_id=demo_doctor.id,
    allowed_categories="diagnosis, medicines, follow-up, vitals, procedure",
    status="approved",
    expiry_date="2027-09-08",
    decided_date=datetime.utcnow()
)
db.add(consent)

db.commit()
db.close()

print("✓ 6 timeline milestones (incl. Feb 2024 angioplasty) + active medications seeded.")
print("✓ Ready for frontend login using:")
print(f"    Patient portal   -> phone: 9486508579")
print(f"    Caregiver portal -> name: Thanu Shree N / password: {SHARED_PORTAL_PASSWORD}")
print(f"    Doctor portal    -> email: {DOCTOR_LOGIN_EMAIL} / password: {SHARED_PORTAL_PASSWORD}")
print("=" * 60)