# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
  - Technical: Deploy trên AWS ap-southeast-1 (Singapore) hoặc on-premise VN datacenter
  - Enforce via: Terraform region constraints + OPA policy kiểm tra destination_country
- [x] Backup cũng phải ở trong lãnh thổ VN
  - Technical: S3 bucket replication chỉ trong VN region, RDS automated backups với same-region constraint
- [x] Log việc transfer data ra ngoài nếu có
  - Technical: CloudTrail logging + custom Lambda function alert khi detect cross-region transfer

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
  - Technical: Consent management table trong PostgreSQL với columns: patient_id, consent_type, timestamp, ip_address
  - UI: Checkbox trong patient registration form với clear language về AI usage
- [x] Có mechanism để user rút consent (Right to Erasure)
  - Technical: DELETE /api/patients/{id} endpoint (admin only) + soft delete flag
  - Process: Xóa khỏi training dataset trong vòng 30 ngày, log deletion event
- [x] Lưu consent record với timestamp
  - Technical: consent_records table với created_at, updated_at, consent_version fields

## C. Breach Notification (72h)
- [x] Có incident response plan
  - Document: incident_response_playbook.md với escalation matrix
  - Team: Security team on-call rotation, DPO contact info
- [x] Alert tự động khi phát hiện breach
  - Technical: Prometheus alerting rules cho anomalous access patterns
  - Integration: PagerDuty webhook + Slack #security-incidents channel
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h
  - Process: Automated email template tới Cục An toàn thông tin (Ministry of Information and Communications)
  - Tracking: Jira ticket với SLA 72h, auto-escalate sau 48h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
  - Name: Nguyễn Văn An
  - Email: dpo@medviet.vn
  - Phone: +84-xxx-xxx-xxx
- [x] DPO có thể liên hệ tại: dpo@medviet.vn
  - Public contact form: https://medviet.vn/privacy-contact
  - Office hours: Mon-Fri 9AM-6PM ICT

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) với detection rate >95% | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) với 4 roles: admin, ml_engineer, data_analyst, intern | ✅ Done | Platform Team |
| Encryption | AES-256-GCM envelope encryption (KEK + DEK pattern), TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | FastAPI access logs + Prometheus metrics + CloudTrail for AWS API calls | ✅ Done | Platform Team |
| Breach detection | Prometheus anomaly detection rules: failed auth >10/min, unusual data export volume >1GB/hour | ✅ Done | Security Team |

## F. Additional Technical Controls Implemented

### 1. PII Detection & Anonymization
- **Tool**: Presidio Analyzer + Anonymizer
- **Entities**: VN_CCCD (12 digits), VN_PHONE (0[3|5|7|8|9]xxxxxxxx), EMAIL_ADDRESS, PERSON
- **Strategies**: Replace (fake data), Mask (partial), Hash (SHA-256)
- **Validation**: Detection rate ≥95% on test dataset

### 2. Role-Based Access Control (RBAC)
- **Framework**: Casbin with CSV policy file
- **Roles**:
  - `admin`: Full access to patient_data, model_artifacts (read/write/delete)
  - `ml_engineer`: Access to training_data, model_artifacts (read/write only)
  - `data_analyst`: Access to aggregated_metrics, reports (read only)
  - `intern`: Access to sandbox_data only (read/write)
- **Authentication**: Bearer token (mock implementation, production uses JWT + OAuth2)

### 3. Data Quality Validation
- **Framework**: Great Expectations
- **Checks**:
  - CCCD length = 12 characters
  - Test results in range [0, 50]
  - Disease values in allowed set
  - Email format validation
  - No duplicate patient_id
  - No null values in critical columns

### 4. Security Scanning
- **Pre-commit hooks**: Secret detection (regex patterns), Bandit SAST, pip-audit CVE check
- **Patterns blocked**: API keys, passwords, private keys, tokens
- **CI/CD integration**: Automated security scans on every PR

### 5. Encryption at Rest
- **Pattern**: Envelope encryption (KEK encrypts DEK, DEK encrypts data)
- **Algorithm**: AES-256-GCM with 12-byte nonce
- **Key management**: KEK stored in .vault_key file (production: AWS KMS or HashiCorp Vault)
- **Scope**: Sensitive columns (CCCD, medical records) encrypted before storage

### 6. API Security
- **Framework**: FastAPI with dependency injection
- **Endpoints**:
  - GET /api/patients/raw (admin only)
  - GET /api/patients/anonymized (ml_engineer, admin)
  - GET /api/metrics/aggregated (data_analyst, ml_engineer, admin)
  - DELETE /api/patients/{id} (admin only)
- **Error handling**: 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error

### 7. Monitoring & Observability
- **Stack**: Prometheus + Grafana + MLflow
- **Metrics tracked**:
  - API request latency (p50, p95, p99)
  - Authentication failures
  - Data access patterns
  - Model training metrics
- **Alerts**: PagerDuty integration for critical incidents

## G. Compliance Gaps & Remediation Plan

| Gap | Risk Level | Remediation | Timeline |
|-----|-----------|-------------|----------|
| KEK stored in file (not HSM) | High | Migrate to AWS KMS or HashiCorp Vault | Q2 2026 |
| Mock authentication (no real JWT) | High | Implement OAuth2 + JWT with refresh tokens | Q1 2026 |
| No data retention policy | Medium | Implement automated data deletion after 7 years | Q2 2026 |
| No penetration testing | Medium | Hire external security firm for pentest | Q3 2026 |
| No GDPR compliance (for EU patients) | Low | Add GDPR consent flow if expanding to EU | Future |

## H. Audit Trail

| Date | Change | Approver | Notes |
|------|--------|----------|-------|
| 2026-05-12 | Initial compliance checklist created | AI Team Lead | Based on NĐ13/2023 requirements |
| 2026-05-12 | Technical controls implemented | Platform Team | PII detection, RBAC, encryption |
| 2026-05-12 | Security scanning setup | Security Team | Pre-commit hooks, Bandit, pip-audit |

## I. Next Steps

1. **Legal Review**: Have legal team review consent forms and privacy policy
2. **DPO Training**: Ensure DPO is trained on NĐ13/2023 requirements
3. **Incident Response Drill**: Run tabletop exercise for breach scenario
4. **Third-party Audit**: Schedule external audit for ISO 27001 certification
5. **Documentation**: Create user-facing privacy policy and data processing agreement
