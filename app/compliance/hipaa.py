"""
HIPAA Compliance Module (Phase 3)
Implements encryption, audit logging, access controls, and data retention policies
Covers: Technical safeguards, administrative safeguards, physical safeguards
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
import logging
from cryptography.fernet import Fernet
from dataclasses import dataclass, asdict
import sqlite3

logger = logging.getLogger(__name__)

# ============================================================================
# HIPAA CONFIGURATION
# ============================================================================

class HIPAALevel(str, Enum):
    """HIPAA compliance levels"""
    BASIC = "basic"           # Encryption + audit logging
    STANDARD = "standard"     # + Access controls + retention policies
    ADVANCED = "advanced"     # + Risk analysis + breach notification
    ENTERPRISE = "enterprise" # + Full compliance + monitoring


class DataClassification(str, Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"               # Non-sensitive
    INTERNAL = "internal"           # Internal use only
    CONFIDENTIAL = "confidential"   # Sensitive business data
    PHI = "phi"                     # Protected Health Information
    EPIC_PHI = "epic_phi"           # Extremely Protected Health Information


@dataclass
class HIPAAConfig:
    """HIPAA compliance configuration"""
    level: HIPAALevel = HIPAALevel.ADVANCED
    encryption_enabled: bool = True
    audit_logging_enabled: bool = True
    access_control_enabled: bool = True
    data_retention_days: int = 2555  # 7 years as per HIPAA
    breach_notification_enabled: bool = True
    risk_analysis_interval_days: int = 365
    encryption_key: Optional[str] = None
    audit_db_path: str = "audit_logs.db"


# ============================================================================
# ENCRYPTION MODULE
# ============================================================================

class DataEncryption:
    """Handles encryption and decryption of PHI"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize encryption with key"""
        if encryption_key is None:
            # Generate from environment or use default (not for production!)
            encryption_key = os.getenv("GERICURE_ENCRYPTION_KEY", "default-key-not-secure")
        
        # Derive key from password using proper KDF
        derived_key = hashlib.pbkdf2_hmac('sha256', encryption_key.encode(), b'gericure-salt', 100000)
        # Fernet requires base64 encoded 32-byte key
        import base64
        self.cipher_suite = Fernet(base64.urlsafe_b64encode(derived_key[:32]))
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt data"""
        try:
            ciphertext = self.cipher_suite.encrypt(plaintext.encode())
            return ciphertext.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt data"""
        try:
            plaintext = self.cipher_suite.decrypt(ciphertext.encode())
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_json(self, data: Dict) -> str:
        """Encrypt JSON data"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_json(self, ciphertext: str) -> Dict:
        """Decrypt JSON data"""
        plaintext = self.decrypt(ciphertext)
        return json.loads(plaintext)


# ============================================================================
# AUDIT LOGGING MODULE
# ============================================================================

@dataclass
class AuditLog:
    """Audit log entry"""
    timestamp: datetime
    event_type: str  # READ, WRITE, DELETE, ACCESS_DENIED, LOGIN, LOGOUT
    user_id: int
    user_role: str
    resource_type: str  # patient, record, consent, etc.
    resource_id: int
    action: str  # create, read, update, delete, export
    status: str  # success, failure
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogger:
    """Handles HIPAA-compliant audit logging"""
    
    def __init__(self, db_path: str = "audit_logs.db"):
        """Initialize audit logger with SQLite database"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for audit logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    user_role TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resource ON audit_logs(resource_type, resource_id)
            """)
            conn.commit()
    
    def log(self, audit_entry: AuditLog):
        """Log audit entry"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_logs 
                (timestamp, event_type, user_id, user_role, resource_type, resource_id, 
                 action, status, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_entry.timestamp.isoformat(),
                audit_entry.event_type,
                audit_entry.user_id,
                audit_entry.user_role,
                audit_entry.resource_type,
                audit_entry.resource_id,
                audit_entry.action,
                audit_entry.status,
                audit_entry.details,
                audit_entry.ip_address,
                audit_entry.user_agent
            ))
            conn.commit()
        
        logger.info(f"Audit: {audit_entry.event_type} - {audit_entry.action} on {audit_entry.resource_type}#{audit_entry.resource_id} by user#{audit_entry.user_id}")
    
    def get_logs(self, 
                 user_id: Optional[int] = None,
                 resource_type: Optional[str] = None,
                 resource_id: Optional[int] = None,
                 days: int = 30) -> List[AuditLog]:
        """Query audit logs with filters"""
        query = "SELECT * FROM audit_logs WHERE timestamp >= ?"
        params = [(datetime.utcnow() - timedelta(days=days)).isoformat()]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
        
        if resource_id:
            query += " AND resource_id = ?"
            params.append(resource_id)
        
        query += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # Convert to AuditLog objects
        logs = []
        for row in rows:
            logs.append(AuditLog(
                timestamp=datetime.fromisoformat(row[1]),
                event_type=row[2],
                user_id=row[3],
                user_role=row[4],
                resource_type=row[5],
                resource_id=row[6],
                action=row[7],
                status=row[8],
                details=row[9],
                ip_address=row[10],
                user_agent=row[11]
            ))
        
        return logs
    
    def cleanup_old_logs(self, retention_days: int = 2555):
        """Delete logs older than retention period (HIPAA requires 6 years)"""
        cutoff_date = (datetime.utcnow() - timedelta(days=retention_days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM audit_logs WHERE timestamp < ?",
                (cutoff_date,)
            )
            conn.commit()
            deleted_count = cursor.rowcount
        
        logger.info(f"Cleaned up {deleted_count} audit logs older than {retention_days} days")


# ============================================================================
# ACCESS CONTROL MODULE
# ============================================================================

class AccessControl:
    """Implements access control policies"""
    
    # Access control rules by role
    ACCESS_RULES = {
        "clinician": {
            "patient": ["read", "update"],
            "record": ["read", "update"],
            "consent": ["read"],
            "alert": ["read", "acknowledge"],
        },
        "guardian": {
            "patient": ["read"],
            "consent": ["read", "update", "manage"],
            "observation": ["create", "read", "update"],
            "alert": ["read"],
        },
        "caregiver": {
            "patient": ["read"],
            "observation": ["create", "read"],
            "activity": ["create", "read", "update"],
        },
        "admin": {
            "patient": ["read", "update", "delete"],
            "record": ["read", "update", "delete"],
            "consent": ["read", "update", "manage"],
            "user": ["read", "create", "update", "delete"],
            "audit": ["read"],
        }
    }
    
    @staticmethod
    def check_access(user_role: str, resource_type: str, action: str) -> bool:
        """Check if user can perform action on resource"""
        rules = AccessControl.ACCESS_RULES.get(user_role, {})
        allowed_actions = rules.get(resource_type, [])
        return action in allowed_actions


# ============================================================================
# DATA RETENTION POLICY
# ============================================================================

class DataRetentionPolicy:
    """Implements HIPAA data retention policies"""
    
    # Retention periods by data type (in days)
    RETENTION_PERIODS = {
        "patient_record": 2555,      # 7 years
        "lab_results": 2555,         # 7 years
        "medications": 2555,         # 7 years
        "audit_log": 2555,           # 7 years
        "consent": 3650,             # 10 years
        "alerts": 365,               # 1 year
        "temporary_file": 30,        # 30 days
    }
    
    @staticmethod
    def should_delete(data_type: str, created_date: datetime) -> bool:
        """Check if data should be deleted based on retention policy"""
        retention_days = DataRetentionPolicy.RETENTION_PERIODS.get(data_type, 365)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return created_date < cutoff_date
    
    @staticmethod
    def get_retention_days(data_type: str) -> int:
        """Get retention period for data type"""
        return DataRetentionPolicy.RETENTION_PERIODS.get(data_type, 365)


# ============================================================================
# BREACH NOTIFICATION
# ============================================================================

@dataclass
class BreachNotification:
    """Breach notification record"""
    breach_id: str
    detected_date: datetime
    discovery_date: datetime
    affected_patients: int
    description: str
    remediation_steps: List[str]
    notification_status: str  # pending, sent, documented


class BreachDetection:
    """Handles breach detection and notification"""
    
    def __init__(self):
        self.breaches: List[BreachNotification] = []
    
    def detect_suspicious_activity(self, 
                                   user_id: int,
                                   event_type: str,
                                   frequency_threshold: int = 100) -> Optional[str]:
        """
        Detect suspicious access patterns
        Returns breach_id if suspicious activity detected
        """
        # Placeholder for anomaly detection logic
        # In production, use ML-based anomaly detection
        return None
    
    def create_breach_notification(self, 
                                  affected_patients: List[int],
                                  description: str) -> BreachNotification:
        """Create breach notification record"""
        import uuid
        breach_id = str(uuid.uuid4())
        
        notification = BreachNotification(
            breach_id=breach_id,
            detected_date=datetime.utcnow(),
            discovery_date=datetime.utcnow(),
            affected_patients=len(affected_patients),
            description=description,
            remediation_steps=[],
            notification_status="pending"
        )
        
        self.breaches.append(notification)
        logger.warning(f"Breach created: {breach_id} - {description} - {len(affected_patients)} patients affected")
        
        return notification


# ============================================================================
# RISK ASSESSMENT
# ============================================================================

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    assessment_date: datetime
    risk_level: str  # low, medium, high, critical
    findings: List[str]
    recommendations: List[str]
    score: float  # 0-100


class RiskAnalyzer:
    """Performs HIPAA risk analysis"""
    
    @staticmethod
    def analyze_access_patterns(audit_logs: List[AuditLog]) -> RiskAssessment:
        """Analyze access patterns for risks"""
        findings = []
        recommendations = []
        risk_score = 0.0
        
        # Check for unusual access times
        night_accesses = [log for log in audit_logs if log.timestamp.hour >= 22 or log.timestamp.hour <= 6]
        if len(night_accesses) > len(audit_logs) * 0.1:
            findings.append(f"High number of night-time accesses ({len(night_accesses)})")
            recommendations.append("Investigate after-hours access")
            risk_score += 15
        
        # Check for bulk data access
        bulk_accesses = [log for log in audit_logs if "export" in log.action.lower()]
        if bulk_accesses:
            findings.append(f"Bulk data access detected ({len(bulk_accesses)} times)")
            recommendations.append("Review bulk access requests and implement controls")
            risk_score += 20
        
        # Check for failed access attempts
        failed_attempts = [log for log in audit_logs if log.status == "failure"]
        if len(failed_attempts) > 10:
            findings.append(f"Multiple failed access attempts ({len(failed_attempts)})")
            recommendations.append("Review access control policies")
            risk_score += 10
        
        # Check for admin access
        admin_accesses = [log for log in audit_logs if log.user_role == "admin"]
        if len(admin_accesses) > len(audit_logs) * 0.05:
            findings.append("Significant admin access detected")
            recommendations.append("Verify admin access is necessary and authorized")
            risk_score += 10
        
        risk_level = "low" if risk_score < 25 else "medium" if risk_score < 50 else "high" if risk_score < 75 else "critical"
        
        return RiskAssessment(
            assessment_date=datetime.utcnow(),
            risk_level=risk_level,
            findings=findings,
            recommendations=recommendations,
            score=risk_score
        )


# ============================================================================
# HIPAA COMPLIANCE MANAGER
# ============================================================================

class HIPAACompliance:
    """Main HIPAA compliance manager"""
    
    def __init__(self, config: Optional[HIPAAConfig] = None):
        """Initialize compliance manager"""
        self.config = config or HIPAAConfig()
        self.encryption = DataEncryption(self.config.encryption_key)
        self.audit_logger = AuditLogger(self.config.audit_db_path)
        self.breach_detection = BreachDetection()
        self.risk_analyzer = RiskAnalyzer()
    
    def log_access(self, 
                   user_id: int,
                   user_role: str,
                   resource_type: str,
                   resource_id: int,
                   action: str,
                   status: str = "success",
                   ip_address: Optional[str] = None):
        """Log access for audit trail"""
        if self.config.audit_logging_enabled:
            audit_entry = AuditLog(
                timestamp=datetime.utcnow(),
                event_type="ACCESS",
                user_id=user_id,
                user_role=user_role,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                status=status,
                ip_address=ip_address
            )
            self.audit_logger.log(audit_entry)
    
    def check_access(self, user_role: str, resource_type: str, action: str) -> bool:
        """Check if access is allowed"""
        if self.config.access_control_enabled:
            return AccessControl.check_access(user_role, resource_type, action)
        return True
    
    def encrypt_phi(self, phi_data: Dict) -> str:
        """Encrypt PHI data"""
        if self.config.encryption_enabled:
            return self.encryption.encrypt_json(phi_data)
        return json.dumps(phi_data)
    
    def decrypt_phi(self, encrypted_data: str) -> Dict:
        """Decrypt PHI data"""
        if self.config.encryption_enabled:
            return self.encryption.decrypt_json(encrypted_data)
        return json.loads(encrypted_data)
    
    def run_risk_analysis(self, days: int = 30) -> RiskAssessment:
        """Run risk analysis on recent activity"""
        logs = self.audit_logger.get_logs(days=days)
        return self.risk_analyzer.analyze_access_patterns(logs)


# ============================================================================
# COMPLIANCE REPORT
# ============================================================================

@dataclass
class ComplianceReport:
    """HIPAA compliance report"""
    report_date: datetime
    compliance_level: HIPAALevel
    encryption_status: str
    audit_logging_status: str
    access_control_status: str
    data_retention_status: str
    risk_assessment: RiskAssessment
    findings: List[str]
    recommendations: List[str]


def generate_compliance_report(compliance_manager: HIPAACompliance) -> ComplianceReport:
    """Generate HIPAA compliance report"""
    risk_assessment = compliance_manager.run_risk_analysis()
    
    return ComplianceReport(
        report_date=datetime.utcnow(),
        compliance_level=compliance_manager.config.level,
        encryption_status="enabled" if compliance_manager.config.encryption_enabled else "disabled",
        audit_logging_status="enabled" if compliance_manager.config.audit_logging_enabled else "disabled",
        access_control_status="enabled" if compliance_manager.config.access_control_enabled else "disabled",
        data_retention_status=f"retention period: {compliance_manager.config.data_retention_days} days",
        risk_assessment=risk_assessment,
        findings=[
            f"Compliance Level: {compliance_manager.config.level.value}",
            f"Encryption: {'Enabled' if compliance_manager.config.encryption_enabled else 'Disabled'}",
            f"Audit Logging: {'Enabled' if compliance_manager.config.audit_logging_enabled else 'Disabled'}",
        ],
        recommendations=[
            "Enable all security controls for production",
            "Review and update access control policies quarterly",
            "Schedule regular risk assessments",
            "Maintain audit logs for minimum 7 years",
            "Implement encryption for all PHI data",
        ]
    )
