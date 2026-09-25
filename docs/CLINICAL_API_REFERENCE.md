# Clinical API Reference
**AI-Powered Clinical Decision Support Endpoints**

---

## Base URL
```
http://localhost:8000/api/clinical
```

All endpoints require:
- `requester_id` (query param) - ID of clinician/guardian making request
- `requester_role` (query param, default="clinician") - Role: clinician, guardian, caregiver

---

## Endpoints

### 1. Clinical Summary
Get comprehensive clinical context for point-of-care decision-making.

**Request**
```
POST /patients/{patient_id}/summary
```

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| requester_id | int | required | ID of requesting user |
| requester_role | string | "clinician" | clinician, guardian, caregiver |
| clinical_query | string | null | Specific question (e.g., "prescribing metformin") |

**Example Request**
```bash
curl -X POST "http://localhost:8000/api/clinical/patients/1/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "requester_id": 5,
    "requester_role": "clinician",
    "clinical_query": "prescribing metformin"
  }'

# Or as query params:
curl "http://localhost:8000/api/clinical/patients/1/summary?requester_id=5&requester_role=clinician&clinical_query=prescribing%20metformin"
```

**Example Response (Success)**
```json
{
  "patient": {
    "id": 1,
    "name": "Nagarajan Raman",
    "age": 78,
    "date_of_birth": "1948-06-15"
  },
  "clinical_query": "prescribing metformin",
  "synthesis": {
    "narrative": "Nagarajan is a 78-year-old patient with active conditions including hypertension, type 2 diabetes mellitus, and chronic kidney disease (Stage 3b, GFR 35)...",
    "key_diagnoses": [
      {
        "name": "Type 2 Diabetes Mellitus",
        "date": "2018-06-01",
        "status": "active"
      },
      {
        "name": "Chronic Kidney Disease Stage 3b",
        "date": "2020-03-15",
        "status": "active"
      }
    ],
    "current_medications": {
      "current": [
        {
          "name": "Lisinopril",
          "dose": "10mg",
          "frequency": "once daily",
          "start_date": "2020-01-10"
        },
        {
          "name": "Atorvastatin",
          "dose": "20mg",
          "frequency": "once daily",
          "start_date": "2019-05-22"
        }
      ],
      "discontinued": []
    },
    "functional_status": {
      "trend": "declining",
      "mobility_issues": 2,
      "cognitive_issues": 1,
      "recent_events": [
        {
          "date": "2026-09-10",
          "observation": "Patient having difficulty walking distances greater than 50 meters"
        }
      ]
    }
  },
  "safety": {
    "medication_count": 8,
    "overall_risk_score": 6.2,
    "risk_category": "HIGH",
    "drug_drug_interactions": [
      {
        "drug_a": "lisinopril",
        "drug_b": "potassium_supplement",
        "severity": "moderate",
        "mechanism": "Hyperkalemia risk with ACE inhibitors",
        "recommendation": "Monitor K+; check renal function monthly"
      }
    ],
    "drug_disease_conflicts": [
      {
        "drug": "metformin",
        "disease": "renal_disease",
        "severity": "high",
        "threshold": "GFR < 45",
        "recommendation": "CONTRAINDICATED - GFR is 35. Use SGLT2 inhibitor (empagliflozin) instead"
      }
    ],
    "duplicate_therapies": [],
    "dosing_issues": []
  },
  "alerts": [
    {
      "severity": "HIGH",
      "category": "drug_disease",
      "message": "Metformin contraindicated with GFR < 45",
      "action": "AVOID metformin; consider SGLT2 inhibitor or DPP4 inhibitor"
    },
    {
      "severity": "HIGH",
      "category": "safety",
      "message": "Prior adverse reaction: ACE inhibitor cough (2015)",
      "action": "Review before prescribing ACE inhibitors; patient has history of intolerance"
    },
    {
      "severity": "MEDIUM",
      "category": "functional_status",
      "message": "Functional decline detected: mobility issues",
      "action": "Consider geriatric assessment and fall prevention interventions"
    }
  ],
  "timeline": [
    {
      "date": "2026-09-10",
      "event_type": "observation",
      "description": "Fall risk assessment - patient had one near-fall event",
      "category": "safety"
    },
    {
      "date": "2026-08-15",
      "event_type": "lab",
      "description": "Serum Creatinine: 2.1 mg/dL, eGFR: 35 mL/min/1.73m2",
      "category": "lab_result"
    }
  ],
  "recommendations": [
    {
      "category": "drug_disease",
      "priority": "high",
      "message": "Do NOT prescribe metformin - contraindicated",
      "action": "Use SGLT2 inhibitor (empagliflozin 10mg daily) or GLP-1 agonist instead"
    },
    {
      "category": "dosing",
      "priority": "high",
      "message": "Current lisinopril dose may be appropriate for renal function",
      "action": "Verify eGFR monthly given declining renal function"
    },
    {
      "category": "deprescribing",
      "priority": "medium",
      "message": "Consider deprescribing redundant antihypertensives",
      "action": "Patient may be overmedicated for BP control"
    }
  ],
  "metadata": {
    "generated_at": "2026-09-13T10:30:45Z",
    "consent_verified": true,
    "confidence_scores": {
      "synthesis": 0.92,
      "safety": 0.87
    }
  },
  "access_log": {
    "requester_id": 5,
    "requester_role": "clinician",
    "accessed_at": "2026-09-13T10:30:45Z",
    "data_categories": ["timeline", "synthesis", "safety", "recommendations"]
  }
}
```

**Example Response (Access Denied)**
```json
{
  "error": "ACCESS_DENIED",
  "message": "Patient consent expired on 2026-08-01; cannot access records",
  "patient_id": 1
}
```

**HTTP Status Codes**
- `200 OK` - Success
- `403 Forbidden` - Consent denied or access not authorized
- `404 Not Found` - Patient not found
- `500 Internal Server Error` - Orchestration failed

---

### 2. Clinical Alerts (Dashboard)
Get high-priority alerts for dashboard/notification systems.

**Request**
```
GET /patients/{patient_id}/alerts
```

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| requester_id | int | required | ID of requesting user |
| requester_role | string | "clinician" | User role |
| min_severity | string | "MEDIUM" | HIGH, MEDIUM, LOW |

**Example Request**
```bash
curl "http://localhost:8000/api/clinical/patients/1/alerts?requester_id=5&min_severity=HIGH"
```

**Example Response**
```json
{
  "patient_id": 1,
  "alert_count": 5,
  "urgent_count": 2,
  "risk_score": 7.2,
  "risk_category": "HIGH",
  "alerts": [
    {
      "severity": "HIGH",
      "category": "drug_disease",
      "message": "Metformin contraindicated - GFR < 45",
      "action": "CONTRAINDICATED - use SGLT2 inhibitor instead"
    },
    {
      "severity": "HIGH",
      "category": "fall_risk",
      "message": "Fall events documented in recent observations",
      "action": "Review medications (benzodiazepines, opioids); assess home safety"
    },
    {
      "severity": "MEDIUM",
      "category": "drug_interaction",
      "message": "Moderate interaction: Lisinopril + Potassium supplement",
      "action": "Monitor K+ levels; check renal function"
    }
  ],
  "generated_at": "2026-09-13T10:35:22Z"
}
```

**Use Cases**
- Dashboard widget updated every 5 minutes
- Mobile notifications
- Clinical workflow alerts at patient check-in

---

### 3. Patient Recommendations
Get actionable clinical recommendations prioritized by importance.

**Request**
```
GET /patients/{patient_id}/recommendations
```

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| requester_id | int | required | ID of requesting user |
| requester_role | string | "clinician" | User role |
| category | string | null | Filter: deprescribing, drug_interaction, drug_disease, dosing |

**Example Request**
```bash
# Get all recommendations
curl "http://localhost:8000/api/clinical/patients/1/recommendations?requester_id=5"

# Get only deprescribing recommendations
curl "http://localhost:8000/api/clinical/patients/1/recommendations?requester_id=5&category=deprescribing"
```

**Example Response**
```json
{
  "patient_id": 1,
  "recommendation_count": 8,
  "high_priority_count": 3,
  "recommendations": [
    {
      "category": "drug_disease",
      "priority": "high",
      "message": "Metformin contraindicated with CKD Stage 3b",
      "action": "Switch to SGLT2 inhibitor (empagliflozin 10mg) or GLP-1 agonist"
    },
    {
      "category": "dosing",
      "priority": "high",
      "message": "Atorvastatin 20mg may be low-dose for secondary prevention",
      "action": "Consider increasing to 40-80mg based on lipid goals and tolerance"
    },
    {
      "category": "drug_interaction",
      "priority": "high",
      "message": "ACE inhibitor + NSAIDs increases AKI risk",
      "action": "Avoid NSAIDs; use acetaminophen for pain instead"
    },
    {
      "category": "deprescribing",
      "priority": "medium",
      "message": "Patient on two different blood pressure agents",
      "action": "Consider combining into single agent or dose optimization"
    }
  ],
  "generated_at": "2026-09-13T10:40:15Z"
}
```

---

### 4. Medication Analysis (Deep-Dive)
Comprehensive polypharmacy analysis for pharmacy reviews.

**Request**
```
POST /patients/{patient_id}/analyze-medications
```

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| requester_id | int | required | ID of requesting user |
| requester_role | string | "clinician" | User role |

**Example Response (Detailed)**
```json
{
  "patient_id": 1,
  "patient_name": "Nagarajan Raman",
  "patient_age": 78,
  "medication_count": 8,
  "renal_function_estimated": "GFR 35 mL/min/1.73m2",
  "overall_risk_score": 6.8,
  "risk_category": "HIGH",
  "interactions": {
    "drug_drug": [
      {
        "drug_a": "lisinopril",
        "drug_b": "potassium_supplement",
        "severity": "moderate",
        "mechanism": "Hyperkalemia risk",
        "recommendation": "Monitor K+ monthly"
      }
    ],
    "drug_disease": [
      {
        "drug": "metformin",
        "disease": "renal_disease",
        "severity": "high",
        "threshold": "GFR < 45",
        "recommendation": "CONTRAINDICATED"
      }
    ],
    "drug_allergy": []
  },
  "duplicate_therapies": [],
  "dosing_issues": [
    {
      "medication": "Atorvastatin",
      "current_dose": "20mg",
      "gfr": 35,
      "reason": "Reduced renal function",
      "recommendation": "May need dose adjustment; verify with pharmacist"
    }
  ],
  "adherence_concerns": [
    "High medication burden (8 drugs) - adherence risk"
  ],
  "medications_analyzed": [
    {
      "name": "Lisinopril",
      "dose": "10mg",
      "frequency": "once daily"
    }
  ],
  "recommendations": [
    {
      "category": "drug_disease",
      "priority": "high",
      "message": "Metformin + CKD Stage 3b",
      "action": "AVOID; switch to alternative"
    }
  ]
}
```

---

### 5. Flexible Clinical Context
Get specific types of clinical context based on use case.

**Request**
```
GET /patients/{patient_id}/clinical-context
```

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| requester_id | int | required | ID of requesting user |
| requester_role | string | "clinician" | User role |
| context_type | string | "full" | full, synthesis, medications, safety, timeline |

**Example Requests**

**Get synthesis only:**
```bash
curl "http://localhost:8000/api/clinical/patients/1/clinical-context?requester_id=5&context_type=synthesis"
```

**Response:**
```json
{
  "patient": {"id": 1, "name": "Nagarajan Raman", "age": 78},
  "synthesis": {
    "narrative": "78-year-old with hypertension, diabetes, CKD Stage 3b...",
    "key_diagnoses": [...],
    "current_medications": {...}
  }
}
```

**Get medications only:**
```bash
curl "http://localhost:8000/api/clinical/patients/1/clinical-context?requester_id=5&context_type=medications"
```

**Response:**
```json
{
  "patient": {"id": 1, "name": "Nagarajan Raman"},
  "medications": {
    "current": [
      {"name": "Lisinopril", "dose": "10mg", "frequency": "daily"}
    ],
    "discontinued": []
  }
}
```

**Get safety only:**
```bash
curl "http://localhost:8000/api/clinical/patients/1/clinical-context?requester_id=5&context_type=safety"
```

**Response:**
```json
{
  "patient": {"id": 1, "name": "Nagarajan Raman"},
  "safety": {
    "medication_count": 8,
    "overall_risk_score": 6.8,
    "risk_category": "HIGH",
    "drug_drug_interactions": [...],
    "drug_disease_conflicts": [...]
  }
}
```

---

## Authentication & Authorization

### Current State (Development)
- No authentication required
- Access control via `requester_role` parameter
- Consent verified via ConsentAgent database lookup

### Production Requirements (Phase 2)
- OAuth2 with Cognito/Auth0
- JWT token validation
- Role-based access control (RBAC) with granular permissions
- Multi-factor authentication (MFA) for sensitive data access

---

## Error Handling

### Common Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid patient_id: must be integer"
}
```

**403 Forbidden** (Consent denied)
```json
{
  "error": "ACCESS_DENIED",
  "message": "Consent expired on 2026-08-01; renewal required",
  "patient_id": 1
}
```

**404 Not Found**
```json
{
  "error": "PATIENT_NOT_FOUND",
  "message": "Patient 999 not found in system",
  "patient_id": 999
}
```

**500 Internal Server Error**
```json
{
  "error": "ORCHESTRATION_FAILED",
  "message": "Exception during context synthesis: database connection timeout",
  "patient_id": 1
}
```

---

## Performance Considerations

### Endpoint Latencies (Estimated)
| Endpoint | Typical Latency | Notes |
|----------|-----------------|-------|
| `/summary` | 200-400ms | Full synthesis + 4 agents |
| `/alerts` | 100-150ms | Fast-path, limited data |
| `/recommendations` | 150-250ms | Aggregation of recommendations |
| `/analyze-medications` | 300-500ms | Detailed interaction matrix |
| `/clinical-context` | 100-400ms | Depends on context_type |

### Optimization Tips
1. **For dashboards:** Use `/alerts` endpoint with 5-minute refresh
2. **For EHR integration:** Use `/clinical-context?context_type=medications` + filter results client-side
3. **For batch processing:** Call `/summary` with `clinical_query` parameter to reduce response size

---

## Rate Limiting (Future)

Not yet implemented, but recommended for production:
- **Clinical summary:** 100 req/min per user
- **Alerts:** 1000 req/min per user  
- **Batch operations:** 10 req/min per user

---

## Examples by Clinical Scenario

### Scenario: New Diabetes Patient - Considering Metformin

```bash
curl -X POST "http://localhost:8000/api/clinical/patients/42/summary" \
  -H "Content-Type: application/json" \
  -G \
  --data-urlencode "requester_id=7" \
  --data-urlencode "requester_role=clinician" \
  --data-urlencode "clinical_query=prescribing metformin for newly diagnosed diabetes"
```

**Key insight in response:** 
- If renal disease present: "CONTRAINDICATED - use SGLT2 inhibitor"
- If no contraindications: "Check GFR baseline; consider dose 500mg BID titrating upward"

---

### Scenario: Deprescribing Review for Elderly Patient

```bash
curl "http://localhost:8000/api/clinical/patients/78/recommendations?requester_id=3&category=deprescribing"
```

**Expected response:** List of redundant medications and deprescribing priorities

---

### Scenario: Mobile App Alert Notification

```bash
curl "http://localhost:8000/api/clinical/patients/23/alerts?requester_id=5&min_severity=HIGH" \
  -H "Accept: application/json"
```

**Use this for:** Push notifications, in-app alerts, clinical action items

---

## WebSocket Streaming (Planned, Phase 2)

```
WS /ws/patients/{patient_id}/live-alerts
```

Real-time alert streaming as new data arrives:
```json
{
  "event": "new_alert",
  "timestamp": "2026-09-13T11:00:45Z",
  "alert": {
    "severity": "HIGH",
    "category": "lab_result",
    "message": "Lab result: Potassium 5.8 (HIGH)",
    "action": "Review in context of ACE inhibitor use"
  }
}
```

---

## Support & Questions

For clinical questions about specific recommendations, consult:
- Beers Criteria 2023 (Potentially Inappropriate Medications)
- Clinical Pharmacology Resources (UpToDate, MicroMedex)
- Internal geriatrics team

For API issues:
- Check response `error` field and `message` field
- Review this documentation
- Check application logs at `/var/log/gericure/`

---

**Last Updated:** September 13, 2026
**API Version:** 2.0.0-ai-orchestration
