# NEXORA — Deployment and Operations Guide

**Document ID:** DOC-016  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. Supported Environments and Hardware Requirements

NEXORA is engineered as a local developer-first web application prototype designed to run reliably on modern personal workstations during hackathon judging and live demonstrations.

### Target Host Environments
| Operating System | Support Level | Notes |
|------------------|---------------|-------|
| **Windows 10 / 11 (64-bit)** | Tier 1 (Primary) | Direct PowerShell support; tested host OS |
| **Ubuntu 22.04+ / Debian 12** | Tier 1 (Full) | Native Linux environment, standard apt packages |
| **macOS 13+ (Apple Silicon)** | Tier 1 (Full) | Metal acceleration supported by PyTorch |

### Hardware Specifications
| Resource | Minimum Requirement | Recommended (Optimal Demo) |
|----------|---------------------|----------------------------|
| **CPU** | 4 physical cores (e.g. Intel Core i5 / AMD Ryzen 5) | 8 cores (Intel Core i7/i9, AMD Ryzen 7/9) |
| **Memory (RAM)** | 8 GB total | 16 GB+ total (ensures smooth OpenCV decoding) |
| **GPU** | Not required (CPU inference supported) | NVIDIA GPU with CUDA 11.8+ (accelerates YOLO) |
| **Disk Storage** | 5 GB free SSD space | 20 GB free SSD space (for video and evidence storage) |
| **Network** | Offline supported after asset download | Internet connection for OSM map tiles & first model download |

---

## 2. Software Prerequisites

Before starting installation, ensure the following core runtimes are installed on the host machine:

1. **Python 3.10, 3.11, or 3.12 (64-bit)**
   - Check version: `python --version`
   - Windows users: Ensure "Add Python to PATH" was checked during installation.
2. **Node.js 18.x LTS or 20.x LTS with npm 9+**
   - Check version: `node --version && npm --version`
3. **Git (for version control)**
   - Check version: `git --version`
4. **C++ Redistributable (Windows only)**
   - OpenCV requires MS Visual C++ Redistributable 2015–2022 (`vc_redist.x64.exe`).

---

## 3. Local Development Setup

### 3.1 Backend Setup (Python / FastAPI)

1. **Navigate to the backend directory:**
   ```powershell
   # In PowerShell / Windows:
   cd c:\Users\ssure\OneDrive\Documents\nexora!\backend
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   # (On Linux / macOS: source venv/bin/activate)
   ```

3. **Install backend dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
   *Core dependencies included:*
   - `fastapi>=0.110.0`
   - `uvicorn[standard]>=0.28.0`
   - `pydantic>=2.6.0`
   - `sqlalchemy>=2.0.28`
   - `alembic>=1.13.1`
   - `opencv-python-headless>=4.9.0`
   - `ultralytics>=8.1.0`
   - `networkx>=3.2.1`
   - `python-multipart>=0.0.9`
   - `pytest>=8.1.0`

4. **Initialize environment configuration:**
   Copy `.env.example` to `.env` in the backend root:
   ```powershell
   Copy-Item .env.example .env
   ```

### 3.2 Frontend Setup (React / Vite)

1. **Navigate to the frontend directory:**
   ```powershell
   cd c:\Users\ssure\OneDrive\Documents\nexora!\frontend
   ```

2. **Install frontend packages:**
   ```powershell
   npm install
   ```
   *Core dependencies included:*
   - `react`, `react-dom` (^18.2.0)
   - `leaflet` (^1.9.4)
   - `react-leaflet` (^4.2.1)
   - `lucide-react` (icon set)
   - `vite` (^5.1.0)

---

## 4. Environment Configuration (`.env`)

A comprehensive `.env` configuration template governs application parameters:

```ini
# ==============================================================================
# NEXORA Core Configuration
# ==============================================================================
ENVIRONMENT=development
DEBUG=True
APP_NAME="NEXORA Intelligence Platform"
API_V1_PREFIX=/api/v1
HOST=127.0.0.1
PORT=8000
FRONTEND_ORIGIN=http://localhost:5173

# ==============================================================================
# Database & Storage
# ==============================================================================
DATABASE_URL=sqlite:///./data/nexora.db
UPLOAD_DIR=./data/uploads
EVIDENCE_DIR=./data/evidence
VENUE_CONFIG_PATH=./data/venue/demo_venue.json
MAX_UPLOAD_SIZE_MB=500

# ==============================================================================
# VisionX Engine & AI Detection
# ==============================================================================
YOLO_MODEL_NAME=yolov8n.pt
YOLO_MODEL_DIR=./data/models
DETECTION_CONFIDENCE_THRESHOLD=0.35
DEFAULT_SAMPLING_INTERVAL_SEC=2.0
SUSTAINED_FRAMES_THRESHOLD=3
HIGH_DENSITY_THRESHOLD=15

# ==============================================================================
# GIS & Routing Engine
# ==============================================================================
ROUTING_SPEED_MPS=1.2
HIGH_DENSITY_COST_PENALTY=2.5
BLOCKED_WALKWAY_PENALTY=999999.0
```

---

## 5. Database Initialization and Seed Data

NEXORA utilizes SQLite with write-ahead logging (WAL) for seamless local persistence.

1. **Ensure the data directories exist:**
   ```powershell
   python -c "import os; [os.makedirs(d, exist_ok=True) for d in ['data/uploads', 'data/evidence', 'data/models', 'data/venue']]"
   ```

2. **Run database table creation & seed demo venue:**
   ```powershell
   cd backend
   python -m app.database_init
   ```
   This executes:
   - DDL creation for `videos`, `jobs`, `detections`, `events`, `incidents`, `resources`, `audit_logs`.
   - Ingestion of `demo_venue.json` into SQLite tables.
   - Creation of 6 initial simulated emergency response units (2 Medical, 3 Security, 1 Fire Warden).

---

## 6. Running the Application Locally

For live operation and testing, start both the backend server and frontend development server in separate terminal windows:

### Terminal 1: Backend Service
```powershell
cd c:\Users\ssure\OneDrive\Documents\nexora!\backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API root: `http://localhost:8000/api/v1`
- Interactive OpenAPI Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

### Terminal 2: Frontend Client
```powershell
cd c:\Users\ssure\OneDrive\Documents\nexora!\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
- Application Web UI: `http://localhost:5173`

---

## 7. Model Download and Cache Behaviour

- **Model Download Source:** The Ultralytics YOLOv8n model (`yolov8n.pt`, ~6.2 MB) automatically downloads from official GitHub releases on the first inference pass if not present locally.
- **Cache Location:** The weights are cached into `./data/models/yolov8n.pt` or the standard Ultralytics cache directory (`%APPDATA%\Ultralytics` on Windows, `~/.config/Ultralytics` on Linux).
- **Offline / Air-Gapped Operation:**
  For environments with restricted Internet, download `yolov8n.pt` beforehand and place it into `backend/data/models/yolov8n.pt`. The backend inspects this folder prior to attempting any remote network download.

---

## 8. External Map Tile Dependency and Fallbacks

- **Primary Map Tiles:** OpenStreetMap standard tile servers (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`).
- **Network Dependency:** Leaflet downloads vector/raster tiles dynamically via the browser client.
- **Offline Fallback Strategy:** If tile loading fails due to restricted hackathon Wi-Fi or offline usage:
  - Leaflet map gracefully renders the venue geometry, zone polygons, walkways, and camera markers against a dark canvas backdrop (`#101010` background matching theme).
  - The routing algorithm and spatial coordinates remain 100% operational because calculations run purely on geometric coordinates via NetworkX on the backend, completely independent of tile raster downloads.

---

## 9. Testing and Verification Commands

Execute the test suites to verify system integrity:

```powershell
# In backend virtual environment:
pytest -v -s tests/

# Execute individual test categories:
pytest tests/test_api_endpoints.py -v       # Endpoint contract tests
pytest tests/test_visionx_pipeline.py -v    # Frame extraction & YOLO tests
pytest tests/test_routing_engine.py -v      # NetworkX route cost & blockage tests
pytest tests/test_security_bounds.py -v     # Path traversal & upload rejection tests
```

---

## 10. Production Build and Packaging

To package NEXORA for production evaluation or local static serving:

1. **Build the frontend bundle:**
   ```powershell
   cd frontend
   npm run build
   ```
   Outputs optimized HTML/JS/CSS assets into `frontend/dist/`.

2. **Mount frontend in FastAPI (Single-binary mode):**
   FastAPI can serve the static build directly using `StaticFiles`:
   ```python
   app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
   ```
3. **Run Production Server:**
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

---

## 11. Deployment Constraints and Cloud Reality

> [!WARNING]
> **Cloud Platform Limitations for Video & Computer Vision:**
> Many free or micro-tier cloud PaaS platforms (e.g. Free Render, Vercel Serverless, Heroku Free, PythonAnywhere) are **unsuitable** for video analysis workloads:
> - **Filesystem Ephemerality:** Serverless platforms discard local storage upon execution completion.
> - **CPU Throttling:** Multi-frame OpenCV decoding and YOLO inference quickly exceed 1-vCPU memory/execution limits, causing process termination (OOM kill).
> - **Execution Timeout:** Video processing of 30-second clips requires 15–40 seconds on standard CPU, exceeding 10-second serverless gateway timeouts.

### Recommended Deployment Options
1. **Local Workstation (Preferred for Hackathon):** Fast, zero latency, predictable GPU/CPU, and immediate file access.
2. **Dedicated Cloud VM (AWS EC2 t3.xlarge / GCP n2-standard-4):**
   - 4 vCPUs, 16 GB RAM, persistent EBS SSD storage.
   - Install Docker & Docker Compose to containerize FastAPI + Nginx + persistent volume mounts.

---

## 12. Logging, Monitoring and Troubleshooting

### Log Locations
- **Backend logs:** Standard output (stdout/stderr) formatted with timestamps, module names, and severity levels. Optionally redirected to `logs/nexora_backend.log`.
- **Database logs:** SQLite audit log stored directly in table `audit_logs`.

### Common Troubleshooting Scenarios

| Issue | Root Cause | Solution |
|-------|------------|----------|
| `ImportError: DLL load failed while importing cv2` | Missing Windows Visual C++ runtime | Install MS Visual C++ Redistributable 2015–2022 x64 |
| `sqlite3.OperationalError: database is locked` | SQLite write concurrency in WAL mode | Ensure connection timeout is set to 30.0s in SQLAlchemy engine |
| `Upload 413: Entity Too Large` | Video file exceeds size limit | Upload clip under 500 MB or adjust `MAX_UPLOAD_SIZE_MB` in `.env` |
| `Map tiles not rendering (grey background)` | Blocked internet access to OSM | Geometry and routes continue working; verify browser network tab |
| `Out of memory during YOLO inference` | Large video frame resolution | Configure engine to resize input frames to 640x640 prior to inference |

---

## 13. Data Backup, Retention and Demo Reset Procedure

### Backup Procedure
To back up the application state before a demonstration:
```powershell
Copy-Item data/nexora.db data/nexora_backup.db
```

### Clean Demo Reset Procedure
To reset the system to pristine demo-ready condition:
```powershell
# Run the reset utility script:
python scripts/reset_demo_state.py
```
This script:
1. Clears temporary video uploads in `data/uploads/` (preserving demo fixture clips).
2. Clears generated frame crops in `data/evidence/`.
3. Truncates tables `videos`, `jobs`, `detections`, `events`, `incidents`, and `audit_logs`.
4. Resets `resources` to `available` status and unblocks all walkways.
5. Re-seeds the baseline demo venue geometry.

---

*End of Document 16 — Deployment and Operations Guide*
