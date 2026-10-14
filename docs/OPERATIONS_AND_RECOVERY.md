# NEXORA — Operations, Deployment & Disaster Recovery Runbook

**Version:** 1.0.0 (Phase 10 Production Hardening)  
**Target Environment:** Windows 10 / 11 Development & Staging  
**Application:** NEXORA Decision-Support Monolith  

---

## 1. Startup & Runtime Commands

### Prerequisites
- Python 3.12+ (64-bit) with `pip`
- Node.js 20+ with `npm`
- Windows PowerShell or Command Prompt

### Environment Initialization
Ensure your `.env` configuration file exists in the repository root:
```powershell
Copy-Item .env.example .env
```

### Backend Startup
From the repository root or `backend` folder:
```powershell
cd c:\Users\ssure\OneDrive\Documents\nexora!\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Startup
From the `frontend` folder:
```powershell
cd c:\Users\ssure\OneDrive\Documents\nexora!\frontend
npm run dev
```
Access the operational dashboard at: `http://localhost:5173`

---

## 2. Administrator Account Initialization (Bootstrap)

NEXORA enforces safe, idempotent administrative bootstrapping. The bootstrap command creates the primary system administrator only if no administrator exists in the database.

### Method A: CLI Tool (Recommended)
Run the automated bootstrap script:
```powershell
python scripts/bootstrap_admin.py --username sys_admin --email admin@nexora.internal --password "YourStrongPassword123!"
```
*Note: If an administrator already exists, the script halts safely with an error message and will never overwrite existing credentials.*

### Method B: REST API Endpoint
Send a bootstrap request to the API:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/bootstrap" -Method Post -ContentType "application/json" -Body '{"username":"sys_admin","email":"admin@nexora.internal","password":"YourStrongPassword123!"}'
```

---

## 3. Database Maintenance, Backup & Recovery

NEXORA persists all operational records in an embedded SQLite database using Write-Ahead Logging (WAL) for concurrency resilience.

### Database Location
- Primary DB: `data/nexora.db`
- WAL Log: `data/nexora.db-wal`
- Shared Memory: `data/nexora.db-shm`

### Creating a Consistent Backup
To create a transactionally safe live snapshot without stopping the server:
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "data\backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
python -c "import sqlite3; con = sqlite3.connect('data/nexora.db'); bck = sqlite3.connect('$backupDir/nexora_backup_$timestamp.db'); con.backup(bck); bck.close(); con.close(); print('Backup complete.')"
```

### Restoring from Backup
1. Terminate the backend service.
2. Replace `data/nexora.db` with the designated snapshot file.
3. Remove any residual `data/nexora.db-wal` and `data/nexora.db-shm` files.
4. Restart the backend service.

---

## 4. Background Job Recovery & Restart Behavior

### Automatic Startup Sweep
If the backend process is abruptly interrupted while video analysis jobs are actively executing (`status = "processing"`):
1. Upon application restart, the FastAPI `lifespan` hook automatically queries the database for orphaned `processing` or `queued` jobs.
2. Orphaned jobs are safely marked as `failed` with the diagnostic message:
   `"Processing interrupted by application restart. Re-submission required."`
3. Database locks are released and temporary OpenCV capture handles are unblocked.
4. Operators can re-submit analysis jobs from the **Video Analysis** module.

---

## 5. System Health Probes & Troubleshooting

### Operational Probes
- **Liveness Probe:** `GET /api/v1/health/liveness`  
  Returns HTTP 200 `{"status": "alive"}` indicating the process is responsive.
- **Readiness Probe:** `GET /api/v1/health/readiness`  
  Verifies database connectivity, storage write capability, and YOLO model weight presence. Returns HTTP 200 when ready, or HTTP 503 if critical dependencies fail.

### Common Troubleshooting Scenarios

| Issue | Cause | Corrective Action |
|---|---|---|
| HTTP 401 Unauthorized | Missing or expired JWT Bearer token | Re-authenticate via UI Login or obtain fresh token via `POST /api/v1/auth/login`. |
| HTTP 403 Forbidden | Authenticated user lacks required role (e.g., Observer attempting action) | Ensure operator has `operator` or `admin` role assigned. |
| HTTP 429 Too Many Requests | Exceeded 5 login attempts per minute | Wait 60 seconds for sliding-window rate limit to reset. |
| YOLO Weights Missing | `models/yolov8n.pt` absent from disk | Verify `models/` directory contains `yolov8n.pt`. Pre-download weights before running offline demos. |
| SQLite Database Locked | Lingering process holding exclusive locks | Ensure no secondary SQLite process has exclusive locks; SQLite WAL mode handles multi-reader concurrency. |
