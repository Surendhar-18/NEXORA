# NEXORA — Security Model & Access Control Architecture

**Document Version:** 1.0.0 (Phase 10 Hardened)  
**Classification:** Operational Security Reference  
**System:** NEXORA — AI-Powered Crowd Safety Intelligence and Emergency Response Coordination  
**Theme:** Theme 11 — Disaster Mitigation & Resilience  

---

## 1. System Trust Boundaries

The NEXORA architecture establishes clear trust perimeters between untrusted networks, the application gateway, processing pipelines, and persisted state.

```
+-------------------------------------------------------------------------+
| UNTRUSTED EXTERNAL ZONE                                                 |
| - Web Browsers (Operator Workstations)                                  |
| - Direct HTTP/REST Clients                                              |
+------------------------------------+------------------------------------+
                                     |  HTTPS / Credentialed CORS
                                     v
+-------------------------------------------------------------------------+
| EDGE & PERIMETER SECURITY GATEWAY (FastAPI / Starlette)                 |
| - Security Headers Middleware (CSP, X-Content-Type-Options, Frame-Deny)|
| - In-Memory Sliding-Window Rate Limiter (Brute-Force Protection)        |
| - OAuth2 Bearer Token Extraction & PyJWT Cryptographic Verification     |
+------------------------------------+------------------------------------+
                                     |  Validated Claims & User Principal
                                     v
+-------------------------------------------------------------------------+
| TRUSTED OPERATIONAL MONOLITH                                            |
| - RBAC Authorization Layer (require_admin, require_operator, observer)  |
| - API Routers (Videos, Events, GIS, Incidents, Reports, Users)          |
| - Native Bcrypt Hashing Primitive (Cost Factor 12)                      |
| - Verified Actor Audit Logging (No client spoofing)                     |
+------------------+----------------------------------+-------------------+
                   |                                  |
                   v                                  v
+------------------------------------+  +---------------------------------+
| BACKGROUND PROCESSING WORKER       |  | PERSISTENCE & STORAGE           |
| - In-Process Asynchronous Pipeline |  | - SQLite Database in WAL Mode   |
| - Frame Sampling & YOLO Inference  |  | - Private Uploads Directory     |
| - Lifespan Job Recovery Sweep      |  | - Protected Evidence Directory  |
+------------------------------------+  +---------------------------------+
```

---

## 2. Authentication Mechanism

### 2.1 Password Storage & Verification
- **Algorithm:** Native `bcrypt` (`bcrypt.hashpw` / `bcrypt.checkpw`).
- **Cost Factor:** 12 rounds with unique salt per credential.
- **Input Sanitization:** UTF-8 encoded with truncation to bcrypt's maximum 72-byte buffer length to prevent denial-of-service via oversized passwords.
- **Constant Time Verification:** All comparisons use timing-attack-resistant verification (`bcrypt.checkpw`).
- **Secret Disclosure:** Passwords and password hashes are never returned in responses, serialized in logs, or written to audit tables.

### 2.2 Token Management
- **Standard:** JSON Web Tokens (JWT) conforming to RFC 7519, transmitted via standard HTTP `Authorization: Bearer <token>` headers.
- **Signature Algorithm:** HMAC-SHA256 (`HS256`).
- **Key Requirement:** Minimum 256-bit entropy (64+ hexadecimal characters), configured via `JWT_SECRET_KEY`.
- **Token Claims:**
  - `sub`: Unique principal identifier (User ID or Username).
  - `role`: Assigned role at time of token issuance (`admin`, `operator`, `observer`).
  - `iss`: Issuer identifier (`NEXORA`).
  - `iat`: Timestamp of issuance (UTC).
  - `exp`: Expiration timestamp (default 120 minutes, configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

### 2.3 Account Lifecycle & Invariants
- **Deactivation:** Deactivated accounts (`is_active = False`) are rejected at the authentication gateway (HTTP 403 Forbidden).
- **Last Administrator Protection:** The system strictly prohibits deleting or deactivating the last remaining active administrator account, preventing unrecoverable operational lockouts.

---

## 3. Role-Based Access Control (RBAC) Matrix

NEXORA defines three discrete operational roles with least-privilege scoping:

| Endpoint / Operation | HTTP Method | Administrator (`admin`) | Operator (`operator`) | Read-Only Observer (`observer`) | Unauthenticated |
|---|:---:|:---:|:---:|:---:|:---:|
| **Authentication: Login** | `POST` | ALLOW | ALLOW | ALLOW | ALLOW (Rate Limited) |
| **Authentication: Current Profile (`/auth/me`)** | `GET` | ALLOW | ALLOW | ALLOW | DENY (401) |
| **System Liveness (`/health/liveness`)** | `GET` | ALLOW | ALLOW | ALLOW | ALLOW (Minimal JSON) |
| **System Readiness (`/health/readiness`)** | `GET` | ALLOW | ALLOW | ALLOW | ALLOW (Non-sensitive) |
| **Admin Bootstrap (`/auth/bootstrap`)** | `POST` | First Run Only | First Run Only | First Run Only | First Run Only (409 once configured) |
| **Account Management (`/auth/users/*`)** | `*` | **ALLOW** | DENY (403) | DENY (403) | DENY (401) |
| **Video Upload** | `POST` | ALLOW | **ALLOW** | DENY (403) | DENY (401) |
| **Video & Job Querying** | `GET` | ALLOW | ALLOW | ALLOW | DENY (401) |
| **Evidence Frame Retrieval** | `GET` | ALLOW | ALLOW | ALLOW | DENY (401) |
| **Crowd Rule Modification** | `POST` / `PUT` | ALLOW | **ALLOW** | DENY (403) | DENY (401) |
| **Crowd Event Review / Dismissal** | `POST` | ALLOW | **ALLOW** | DENY (403) | DENY (401) |
| **Venue Querying & Routing** | `GET` | ALLOW | ALLOW | ALLOW | DENY (401) |
| **Walkway Blocking / Reopening** | `PUT` | ALLOW | **ALLOW** | DENY (403) | DENY (401) |
| **Incident Escalation & Lifecycle** | `POST` / `PUT` | ALLOW | **ALLOW** | DENY (403) | DENY (401) |
| **Simulated Resource Assignment** | `POST` / `DELETE`| ALLOW | **ALLOW** | DENY (403) | DENY (401) |
| **Analytics & Operational KPIs** | `GET` | ALLOW | ALLOW | ALLOW | DENY (401) |
| **Operational Report Previews** | `GET` / `POST` | ALLOW | ALLOW | ALLOW | DENY (401) |
| **PDF & CSV Report Export** | `POST` | ALLOW | ALLOW | ALLOW | DENY (401) |
| **Comprehensive Audit Log Export**| `POST` | ALLOW | **ALLOW** | DENY (403) | DENY (401) |

---

## 4. API & Filesystem Isolation

1. **Private Storage Roots:** Uploaded video containers and extracted evidence JPEG frames reside strictly in `data/uploads` and `data/evidence`, isolated from the frontend static bundle.
2. **Path Traversal Defense:** All evidence file requests sanitize input paths, stripping directory traversal tokens (`..`, `/`, `\`) and verifying that resolved paths remain strictly within `settings.EVIDENCE_DIR`.
3. **MIME & Header Verification:** Uploaded videos require valid magic bytes (e.g., MP4 `ftyp` box header) and are constrained to `MAX_UPLOAD_SIZE_BYTES` (default 500MB).
4. **Information Leakage Defense:** File downloads set `Content-Disposition: attachment; filename="<sanitized>"` and mask absolute filesystem paths from responses.

---

## 5. Audit Trail Integrity & Non-Repudiation

1. **Principal Attribution:** All audit records (`AuditLog` entity) derive `actor_id` and `actor_role` directly from the authenticated JWT principal verified by the server. Any client-provided operator strings are ignored.
2. **Sensitive Exclusions:** Audit log payload dictionaries exclude passwords, raw video bytes, and authentication tokens.
3. **Deterministic Chronology:** Audit entries record UTC timestamps and autoincrement sequence IDs, preventing reordering during analytical exports.

---

## 6. HTTP Defense-in-Depth & Security Headers

Every HTTP response dispatched by the NEXORA backend attaches standard security headers:

- **`X-Content-Type-Options: nosniff`**: Prevents MIME-type sniffing.
- **`X-Frame-Options: DENY`**: Mitigates clickjacking attacks.
- **`Referrer-Policy: strict-origin-when-cross-origin`**: Restricts sensitive path leakage across origins.
- **`Content-Security-Policy`**: Restricts script execution to same-origin while supporting Leaflet tile rendering.
- **`Permissions-Policy: camera=(), microphone=(), geolocation=()`**: Restricts browser device capabilities.
