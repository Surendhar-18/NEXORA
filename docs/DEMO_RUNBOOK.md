# NEXORA — Hackathon Demonstration Runbook
**Theme 11: Disaster Mitigation & Resilience**  
**Document Version:** 1.0.0  
**Target Audience:** Judges, Evaluators, Operators, and Technical Reviewers  

---

## A. System Prerequisites & Environment Setup

### 1. Hardware & System Requirements
- **Operating System:** Windows 10/11, macOS, or Linux.
- **RAM:** Minimum 8 GB recommended (16 GB optimal for YOLO inference).
- **Disk Space:** ~2 GB free disk space for Python virtual environment, Node modules, and test assets.

### 2. Runtime Environments
- **Python:** Python 3.12 (verified: 3.12.5).
- **Node.js:** Node.js 20+ (verified: Node 24+ / npm 10+).

### 3. Model Weights & Data Directory
- **Detector Weights:** `data/models/yolov8n.pt` (Ultralytics YOLOv8 nano person detection weights).
- **Venue Specification:** `data/venue/demo_venue.json` (Triveni Festival Grounds map, 6 zones, 12 nodes, 16 walkways).
- **Database:** `data/nexora.db` (SQLite in WAL mode).

### 4. Dependency Installation
If setting up a fresh machine:
```powershell
# Backend Dependencies
pip install -r backend/requirements.txt

# Frontend Dependencies
cd frontend
npm install
cd ..
```

---

## B. Starting the Application

NEXORA operates as a decoupled architecture: FastAPI on the backend and Vite React on the frontend.

### Step 1: Start the Backend Service
Open Terminal 1:
```powershell
# From the repository root
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected Output:*
```text
INFO:     Started server process [pid]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 2: Verify Backend Health
```powershell
curl http://127.0.0.1:8000/api/v1/health
```
*Expected Output:*
```json
{"status":"healthy","database":"connected","models":{"detector":"loaded"},"version":"1.0.0"}
```

### Step 3: Start the Frontend Interface
Open Terminal 2:
```powershell
cd frontend
npm run dev
```
*Expected Output:*
```text
  VITE v8.3.4  ready in 420 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Network: use --host to expose
```

Open your browser to: **`http://127.0.0.1:5173/`**

---

## C. Preparing & Resetting Demo Data

NEXORA includes non-destructive demo automation scripts.

### 1. Prepare / Refresh Demo State
To populate the database with a predictable demonstration baseline:
```powershell
python scripts/prepare_demo.py
```
*This command is completely idempotent and safe to run multiple times.* It ensures:
- Default venue `venue_triveni` is loaded with all 16 walkways set to open.
- Default crowd-count rules are active.
- 8 simulated response units are seeded and marked `available`.
- 1 demo video & job record (`video-demo-north-plaza`).
- 1 demo crowd surge event pending operator review (`EVT-DEMO-001`).
- 1 active operational incident (`INC-DEMO-001`).
- 1 historical resolved incident with resolution notes (`INC-DEMO-002`).

### 2. Resetting the Demo Environment Safely
To clear demo-labeled records and return all resources and corridors to an available state:
```powershell
python scripts/reset_demo.py --force
```
*Safety Guarantee:* This script **never drops database tables** and **never deletes user uploaded videos**. It only removes records with `[DEMO]` identifiers, unblocks walkways, and releases resource locks.

---

## D. Guided 14-Step Demonstration Sequence

Follow this sequence for an engaging, cohesive 5–7 minute walkthrough.

### Stage 1: Overview Dashboard (`/`)
1. **Show Executive KPI Cards:** Point to `Active Incidents`, `Pending Events`, `Simulated Units Available`, and `Blocked Walkways`.
2. **Review Attention Queue:** Point out the prioritized alert card showing high/critical priority items requiring attention.
3. **Inspect Real-Time Activity Feed:** Explain that audit events are chronologically tracked in SQLite WAL mode.

### Stage 2: Video Ingestion & VisionX Analysis (`/videos`)
4. **Inspect Upload Interface:** Show the upload zone supporting `.mp4`/`.avi`/`.mov` with strict MIME and magic-byte validation.
5. **Demonstrate Uploaded Feeds:** Select `video-demo-north-plaza` (or upload an authorized test clip).
6. **Inspect Job Progress & Evidence:** Click on the completed job to inspect the detected person count timeline, sampling rate (2.0s), and the peak evidence bounding-box frame.

### Stage 3: Human Event Review & Triage (`/events`)
7. **Examine Pending Review Triage:** Show `EVT-DEMO-001` (`SURGE_INGRESS_OVERFLOW` at North Plaza, peak count: 26).
8. **Explain Human-in-the-Loop Philosophy:** Explain that AI does not trigger autonomous evacuations; it alerts human operators for decision verification.
9. **Acknowledge Event:** Click **"Acknowledge"** and enter operator notes ("Verified crowd density spike near Entry Gate 1").

### Stage 4: Incident Escalation & Response Coordination (`/incidents`)
10. **Escalate to Operational Incident:** Click **"Escalate to Incident"** on the acknowledged event. Notice the unique tracking ID (`INC-...`).
11. **Assign Simulated Emergency Resource:** Open the incident detail view. In the resource assignment dropdown, select `MEDIC-1` (Medical Team Alpha) and click **"Assign Resource"**.
    - Notice incident status transitions to `in_progress`.
    - Point out that `MEDIC-1` is now locked; attempting to assign it elsewhere triggers a 409 Conflict.

### Stage 5: GIS Venue Operations & Dynamic Rerouting (`/gis`)
12. **Explore Venue Graph:** View the interactive Leaflet map of Triveni Festival Grounds with 6 zones, gates, and 16 connecting walkways.
13. **Simulate Corridor Blockage & Rerouting:**
    - In Route Alternatives, select Origin: `Main Entrance Gate` and Destination: `North Exit Gate`. Observe the primary shortest path.
    - Click **"Block Walkway"** on the central connecting corridor (e.g., `walk_1_2`) with reason: "Crowd density overflow diversion".
    - Click **"Recalculate Routes"**: Observe that the routing engine automatically excludes the blocked corridor and computes an alternative detour path.

### Stage 6: Incident Resolution & Resource Release (`/incidents`)
14. **Resolve the Incident:**
    - Return to the incident view. Click **"Resolve Incident"**.
    - Try submitting with empty notes: notice the system requires a mandatory resolution summary note.
    - Enter resolution notes: "Crowd safely diverted via Alternate Corridor. Density returned to baseline."
    - Submit resolution: Observe the incident status transitions to `resolved`, and `MEDIC-1` is **automatically released** back to `available`.

### Stage 7: Reporting, Audit & Verification (`/reports`)
15. **Generate Multi-Format Reports:**
    - Switch to **Reports & Audit**. Select report type: `Operational Summary` or `Incident Management`.
    - Click **"Generate Preview"** to inspect tabulated metrics and incident histories.
    - Click **"Export PDF"**: Open the downloaded clean, publication-ready ReportLab document.
    - Click **"Export CSV"**: Open the spreadsheet; highlight the formula-injection defense (cells with `=`, `+` are sanitized).
16. **Verify Audit Trail:** Show that every action (event review, incident escalation, resource dispatch, walkway blockage, reopen) is permanently audited.

---

## E. Honest Narration Notes (What NEXORA Does vs Does Not Claim)

When presenting to evaluators, maintain high technical credibility by stating these boundaries clearly:

1. **Recorded Video vs. Continuous Live CCTV:**
   - *What it is:* A reliable asynchronous analysis pipeline that ingests video recordings, extracts sampled frames, and runs person detection.
   - *What it is not:* NEXORA does not claim to ingest hundreds of concurrent real-time 4K RTSP cameras without dedicated GPU streaming clusters.

2. **Sampled-Frame Person Detections vs. Unique Attendee Census:**
   - *What it is:* VisionX records person bounding boxes at discrete sampled intervals (e.g., every 2.0s) to gauge density trends.
   - *What it is not:* It does not track unique individuals, re-identify faces across cameras, or compute exact biometric counts.

3. **Decision-Support Rules vs. Autonomous Behavior Recognition:**
   - *What it is:* Deterministic threshold and sustained-presence rules that surface objective crowd surges for human triage.
   - *What it is not:* It does not claim "AI panic detection", emotion recognition, or automated stampede forecasting.

4. **GIS Route Alternatives vs. Guaranteed-Safe Evacuations:**
   - *What it is:* Graph-based shortest-path and detour alternatives that respect operator-reported walkway blockages.
   - *What it is not:* It is a decision-support guidance tool, not a certified physical life-safety guarantee.

5. **Simulated Response Resources vs. Live 911 Dispatch:**
   - *What it is:* A simulated fleet allocation engine modeling unit availability, zone positioning, and double-booking prevention.
   - *What it is not:* It is not interfaced to government Computer-Aided Dispatch (CAD) or municipal radio networks.

---

## F. Troubleshooting Guide

| Issue | Likely Cause | Verified Resolution |
|---|---|---|
| **Backend fails on port 8000** | Port 8000 already in use by another service | Run `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess \| Stop-Process` or use `--port 8001` |
| **Frontend fails to reach backend** | Backend not running or wrong port | Verify `http://127.0.0.1:8000/api/v1/health` responds; check Vite proxy in `vite.config.ts` |
| **Missing Model Weights error** | `yolov8n.pt` not found in `data/models/` | The detector automatically downloads `yolov8n.pt` from Ultralytics on first run if internet is available; or verify `data/models/yolov8n.pt` exists |
| **Upload rejected (400 Bad Request)** | File is not valid MP4/AVI/MOV or header is invalid | Use an authorized MP4 video clip with standard container headers |
| **Map tiles appear blank** | Internet disconnected for OpenStreetMap tiles | Leaflet requires network access for external OSM tile downloads; vector venue polygons and nodes render locally regardless |
| **Resource assignment 409 Conflict** | Resource is already assigned to another active incident | Resolve the prior incident or manually select an available resource |
| **Incident resolution fails with 422** | Resolution notes field is empty | Enter a non-empty summary explaining how the situation was resolved |
