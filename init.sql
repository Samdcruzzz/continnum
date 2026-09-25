-- Database Initialization Script (Phase 3)
-- PostgreSQL initialization with HIPAA-compliant schema

-- ============================================================================
-- CREATE SCHEMAS
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'clinician',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT valid_role CHECK (role IN ('clinician', 'guardian', 'caregiver', 'admin'))
);

CREATE INDEX idx_users_username ON public.users(username);
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_role ON public.users(role);

-- ============================================================================
-- PATIENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.patients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(50),
    mrn VARCHAR(255) UNIQUE,
    ssn_encrypted VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patients_mrn ON public.patients(mrn);
CREATE INDEX idx_patients_name ON public.patients(last_name, first_name);

-- ============================================================================
-- MEDICAL RECORDS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.medical_records (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES public.patients(id),
    record_type VARCHAR(100) NOT NULL,
    record_date DATE NOT NULL,
    data_encrypted TEXT NOT NULL,
    source VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_record_type CHECK (record_type IN ('diagnosis', 'medication', 'lab_result', 'vital', 'note', 'procedure'))
);

CREATE INDEX idx_records_patient ON public.medical_records(patient_id);
CREATE INDEX idx_records_date ON public.medical_records(record_date);
CREATE INDEX idx_records_type ON public.medical_records(record_type);

-- ============================================================================
-- MEDICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.medications (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES public.patients(id),
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE,
    prescriber_id INTEGER REFERENCES public.users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_medications_patient ON public.medications(patient_id);
CREATE INDEX idx_medications_active ON public.medications(end_date) WHERE end_date IS NULL;

-- ============================================================================
-- LAB RESULTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.lab_results (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES public.patients(id),
    test_name VARCHAR(255) NOT NULL,
    result_value VARCHAR(255),
    unit VARCHAR(50),
    reference_range VARCHAR(100),
    result_date DATE NOT NULL,
    abnormal_flag VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_labs_patient ON public.lab_results(patient_id);
CREATE INDEX idx_labs_date ON public.lab_results(result_date);

-- ============================================================================
-- CONSENT & PERMISSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.consents (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES public.patients(id),
    guardian_id INTEGER REFERENCES public.users(id),
    scope VARCHAR(100) NOT NULL,
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    granted_date TIMESTAMP,
    expiration_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_consents_patient ON public.consents(patient_id);
CREATE INDEX idx_consents_guardian ON public.consents(guardian_id);
CREATE INDEX idx_consents_scope ON public.consents(scope);

-- ============================================================================
-- ALERTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.alerts (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES public.patients(id),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES public.users(id),
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMP,
    CONSTRAINT valid_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX idx_alerts_patient ON public.alerts(patient_id);
CREATE INDEX idx_alerts_type ON public.alerts(alert_type);
CREATE INDEX idx_alerts_severity ON public.alerts(severity);
CREATE INDEX idx_alerts_generated ON public.alerts(generated_at DESC);
CREATE INDEX idx_alerts_acknowledged ON public.alerts(acknowledged) WHERE acknowledged = FALSE;

-- ============================================================================
-- CAREGIVER OBSERVATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.observations (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES public.patients(id),
    caregiver_id INTEGER NOT NULL REFERENCES public.users(id),
    observation_type VARCHAR(100) NOT NULL,
    details TEXT NOT NULL,
    severity VARCHAR(50),
    observation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_observation_type CHECK (observation_type IN (
        'cognitive_changes', 'mobility_issues', 'medication_side_effects',
        'appetite_changes', 'sleep_changes', 'behavioral_changes', 'other'
    ))
);

CREATE INDEX idx_observations_patient ON public.observations(patient_id);
CREATE INDEX idx_observations_caregiver ON public.observations(caregiver_id);
CREATE INDEX idx_observations_date ON public.observations(observation_date DESC);

-- ============================================================================
-- AUDIT LOGGING (HIPAA COMPLIANCE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit.access_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100) NOT NULL,
    user_id INTEGER,
    user_role VARCHAR(50),
    resource_type VARCHAR(100) NOT NULL,
    resource_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    CONSTRAINT valid_event_type CHECK (event_type IN ('ACCESS', 'MODIFY', 'DELETE', 'LOGIN', 'LOGOUT', 'ERROR'))
);

CREATE INDEX idx_audit_timestamp ON audit.access_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit.access_logs(user_id);
CREATE INDEX idx_audit_resource ON audit.access_logs(resource_type, resource_id);
CREATE INDEX idx_audit_event ON audit.access_logs(event_type);

-- ============================================================================
-- MONITORING & METRICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS monitoring.metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    labels JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_name ON monitoring.metrics(metric_name);
CREATE INDEX idx_metrics_timestamp ON monitoring.metrics(timestamp DESC);
CREATE INDEX idx_metrics_labels ON monitoring.metrics USING GIN(labels);

-- ============================================================================
-- HEALTH CHECKS
-- ============================================================================

CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    checks JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_health_service ON monitoring.health_checks(service_name);
CREATE INDEX idx_health_timestamp ON monitoring.health_checks(timestamp DESC);

-- ============================================================================
-- SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id),
    token_jti VARCHAR(255) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_sessions_user ON public.sessions(user_id);
CREATE INDEX idx_sessions_expiry ON public.sessions(expires_at);
CREATE INDEX idx_sessions_revoked ON public.sessions(revoked);

-- ============================================================================
-- DATA ENCRYPTION KEYS (for key rotation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.encryption_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(255) UNIQUE NOT NULL,
    key_version INTEGER NOT NULL,
    key_hash VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rotated_at TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_keys_name ON public.encryption_keys(key_name);
CREATE INDEX idx_keys_active ON public.encryption_keys(active);

-- ============================================================================
-- COMPLIANCE TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit.compliance_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    severity VARCHAR(50),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMP,
    CONSTRAINT valid_compliance_type CHECK (event_type IN (
        'breach', 'unauthorized_access', 'policy_violation', 'audit_failure'
    ))
);

CREATE INDEX idx_compliance_date ON audit.compliance_events(event_date DESC);
CREATE INDEX idx_compliance_resolved ON audit.compliance_events(resolved);

-- ============================================================================
-- VIEWS (for common queries)
-- ============================================================================

CREATE OR REPLACE VIEW public.active_alerts AS
SELECT 
    a.id,
    a.patient_id,
    p.first_name,
    p.last_name,
    a.alert_type,
    a.severity,
    a.description,
    a.generated_at,
    a.acknowledged
FROM public.alerts a
JOIN public.patients p ON a.patient_id = p.id
WHERE a.resolved = FALSE
ORDER BY a.severity DESC, a.generated_at DESC;

CREATE OR REPLACE VIEW public.active_medications AS
SELECT 
    m.id,
    m.patient_id,
    p.first_name,
    p.last_name,
    m.medication_name,
    m.dosage,
    m.frequency,
    m.start_date
FROM public.medications m
JOIN public.patients p ON m.patient_id = p.id
WHERE m.end_date IS NULL
ORDER BY m.start_date DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to get patient age
CREATE OR REPLACE FUNCTION public.get_patient_age(dob DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(dob))::INTEGER;
END;
$$ LANGUAGE plpgsql;

-- Function to update timestamp
CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER trigger_update_users_timestamp
BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

CREATE TRIGGER trigger_update_patients_timestamp
BEFORE UPDATE ON public.patients
FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

CREATE TRIGGER trigger_update_consents_timestamp
BEFORE UPDATE ON public.consents
FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

-- ============================================================================
-- GRANTS (for application user)
-- ============================================================================

GRANT USAGE ON SCHEMA public TO gericure_user;
GRANT USAGE ON SCHEMA audit TO gericure_user;
GRANT USAGE ON SCHEMA monitoring TO gericure_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gericure_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO gericure_user;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA monitoring TO gericure_user;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gericure_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO gericure_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA monitoring TO gericure_user;

-- ============================================================================
-- INITIALIZATION DATA
-- ============================================================================

-- Demo users (Note: passwords should be hashed in production)
INSERT INTO public.users (username, email, full_name, hashed_password, role, is_active) VALUES
('dr_johnson', 'dr.johnson@hospital.com', 'Dr. Johnson', '$2b$12$...', 'clinician', TRUE),
('guardian_sarah', 'sarah@family.com', 'Sarah Guardian', '$2b$12$...', 'guardian', TRUE),
('caregiver_mary', 'mary@careservice.com', 'Mary Caregiver', '$2b$12$...', 'caregiver', TRUE),
('admin_root', 'admin@gericure.com', 'Administrator', '$2b$12$...', 'admin', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Demo patient
INSERT INTO public.patients (first_name, last_name, date_of_birth, gender, mrn) VALUES
('John', 'Doe', '1942-05-15', 'M', 'MRN-001')
ON CONFLICT (mrn) DO NOTHING;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE public.users IS 'System users with roles (clinician, guardian, caregiver, admin)';
COMMENT ON TABLE public.patients IS 'Patient demographic information (PII/PHI)';
COMMENT ON TABLE public.medications IS 'Current and historical medications for patients';
COMMENT ON TABLE public.alerts IS 'AI-generated clinical alerts and warnings';
COMMENT ON TABLE public.observations IS 'Caregiver observations about patient behavior and status';
COMMENT ON TABLE audit.access_logs IS 'HIPAA audit trail of all data access and modifications';
COMMENT ON TABLE public.consents IS 'Patient/Guardian consents for data access and use';

-- ============================================================================
-- EOF
-- ============================================================================
