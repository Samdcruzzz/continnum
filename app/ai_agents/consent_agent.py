from sqlalchemy.orm import Session
from app.models import Consent
from datetime import datetime

class ConsentAgent:
    """
    Consent Agent - real DB-backed version with expiry enforcement.
    """
    @staticmethod
    def filter_by_consent(doctor_id: int, patient_id: int, records: list, db: Session) -> dict:
        """Looks up the most recent APPROVED consent this doctor has for this
        patient, then returns only the record categories it covers.
        
        P0: NOW CHECKS EXPIRY DATE. If consent is expired, access is denied.
        """
        consent = (
            db.query(Consent)
            .filter(
                Consent.patient_id == patient_id,
                Consent.doctor_id == doctor_id,
                Consent.status == "approved",
            )
            .order_by(Consent.decided_date.desc().nullslast())
            .first()
        )

        if not consent:
            return {
                "access_granted": False,
                "records": [],
                "message": f"Access denied: no approved consent for doctor '{doctor_id}' on this patient.",
            }

        # P0: CHECK EXPIRY DATE
        if consent.expiry_date:
            try:
                expiry = datetime.strptime(consent.expiry_date, "%Y-%m-%d")
                today = datetime.now()
                
                if today > expiry:
                    return {
                        "access_granted": False,
                        "records": [],
                        "message": f"Access denied: consent expired on {consent.expiry_date}. Doctor must request new consent.",
                    }
            except ValueError:
                pass

        allowed_categories = [
            c.strip().lower() for c in (consent.allowed_categories or "").split(",") if c.strip()
        ]

        filtered = [r for r in records if r["category"] in allowed_categories]

        return {
            "access_granted": True,
            "allowed_categories": allowed_categories,
            "records": filtered,
            "records_hidden_count": len(records) - len(filtered),
        }
