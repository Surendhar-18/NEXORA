# NEXORA — System Architecture

**Document ID:** DOC-006  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. System Context Diagram

```mermaid
C4Context
    title NEXORA System Context
    
    Person(operator, "Safety Operator", "Uploads video, reviews events, manages incidents")
    Person(commander, "Operations Commander", "Reviews dashboards, oversees response")
    
    System(nexora, "NEXORA Platform", "AI-powered crowd safety intelligence and emergency response coordination")
    
    System_Ext(osm, "OpenStreetMap", "Background map tile provider")
    System_Ext(yolo_repo, "Ultralytics Hub", "YOLO model weight repository")
    System_Ext(browser, "Web Browser", "Chrome/Firefox/Edge")
    
    Rel(operator, nexora, "Uses via browser", "HTTPS")
    Rel(commander, nexora, "Views dashboards via browser", "HTTPS")
    Rel(nexora, osm, "Fetches map tiles", "HTTPS")
    Rel(nexora, yolo_repo, "Downloads model weights (one-time)", "HTTPS")
    Rel(operator, browser, "Interacts through")
    Rel(browser, nexora, "API requests", "HTTP/JSON")
```

## 2. High-Level Component Diagram

```mermaid
graph TB
    subgraph "Client (Browser)"
        FE[React Frontend<br/>TypeScript + Vite]
        MAP[Leaflet Map Component]
        CHARTS[Recharts Visualisations]
    end
    
    subgraph "Backend Server (FastAPI)"
        API[API Layer<br/>FastAPI Routers]
        
        subgraph "Application Modules"
            VM[Video Module]
            DM[Detection Module<br/>VisionX Engine]
            EM[Event Module]
            RM[Routing Module]
            IM[Incident Module]
            RES[Resource Module]
            AM[Audit Module]
            AN[Analytics Module]
        end
        
        subgraph "Infrastructure"
            DB_LAYER[Database Layer<br/>SQLAlchemy ORM]
            FILE_STORE[File Storage<br/>Local Filesystem]
            CONFIG[Configuration<br/>Environment Variables]
        end
        
        subgraph "AI/ML Engine"
            CV[OpenCV<br/>Frame Extraction]
            YOLO[YOLO Detector<br/>Ultralytics]
            RULES[Crowd Rules<br/>Engine]
        end
        
        subgraph "GIS Engine"
            NX[NetworkX<br/>Graph & Routing]
            VENUE[Venue Configuration<br/>Loader]
        end
    end
    
    subgraph "Storage"
        SQLITE[(SQLite Database)]
        VID_FS[Video File Storage]
        EVD_FS[Evidence Image Storage]
        VENUE_DATA[Venue Data Files<br/>JSON Configuration]
    end
    
    subgraph "External"
        OSM_TILES[OpenStreetMap Tiles]
        YOLO_WEIGHTS[YOLO Model Weights]
    end
    
    FE -->|REST API| API
    MAP -->|Tile Requests| OSM_TILES
    
    API --> VM
    API --> EM
    API --> RM
    API --> IM
    API --> RES
    API --> AM
    API --> AN
    
    VM --> DM
    DM --> CV
    DM --> YOLO
    DM --> RULES
    RULES --> EM
    
    RM --> NX
    RM --> VENUE
    
    VM --> DB_LAYER
    DM --> DB_LAYER
    EM --> DB_LAYER
    RM --> DB_LAYER
    IM --> DB_LAYER
    RES --> DB_LAYER
    AM --> DB_LAYER
    AN --> DB_LAYER
    
    VM --> FILE_STORE
    DM --> FILE_STORE
    
    DB_LAYER --> SQLITE
    FILE_STORE --> VID_FS
    FILE_STORE --> EVD_FS
    VENUE --> VENUE_DATA
    YOLO -.->|One-time download| YOLO_WEIGHTS
```

## 3. Module Responsibilities

### 3.1 Frontend (React + TypeScript)

| Responsibility | Description |
|---------------|-------------|
| UI rendering | React components with design system |
| State management | React context/state for UI state; server state via API calls |
| Routing | React Router for page navigation |
| Map rendering | Leaflet integration for GIS display |
| Chart rendering | Recharts for data visualisation |
| API communication | Fetch/Axios for REST API calls |
| File upload | File selection and upload handling |
| Form validation | Client-side validation before submission |

**Not responsible for:** AI processing, route calculation, data persistence, business rule evaluation.

### 3.2 Backend — API Layer (FastAPI)

| Responsibility | Description |
|---------------|-------------|
| Request routing | HTTP method + path → handler function |
| Request validation | Pydantic model validation |
| Response serialisation | JSON response formatting |
| Error handling | Consistent error response format |
| CORS management | Cross-origin request configuration |
| Static file serving | Evidence images and (optionally) frontend build |

### 3.3 Backend — Video Module

| Responsibility | Description |
|---------------|-------------|
| Upload handling | Receive, validate, and store video files |
| Job management | Create, track, and update processing jobs |
| Background processing | Initiate and manage background tasks |
| File cleanup | Remove orphaned files on deletion |

### 3.4 Backend — Detection Module (VisionX Engine)

| Responsibility | Description |
|---------------|-------------|
| Frame extraction | OpenCV-based sampling from video |
| Object detection | YOLO inference on extracted frames |
| Class filtering | Person-class isolation from detections |
| Confidence filtering | Threshold-based detection filtering |
| Evidence generation | Annotated image creation with bounding boxes |
| Result storage | Persist detection records to database |

### 3.5 Backend — Event Module

| Responsibility | Description |
|---------------|-------------|
| Rule evaluation | Apply crowd-count rules to detection results |
| Event creation | Generate events from triggered rules |
| Event review | Process operator review actions |
| Status management | Track event state transitions |

### 3.6 Backend — Routing Module (GIS Engine)

| Responsibility | Description |
|---------------|-------------|
| Venue data management | Load and serve venue configuration |
| Graph management | Maintain NetworkX graph of venue |
| Route calculation | Shortest path and alternative routes |
| Edge management | Block/reopen walkways |
| Cost calculation | Apply cost formula to routes |

### 3.7 Backend — Incident Module

| Responsibility | Description |
|---------------|-------------|
| Incident CRUD | Create, read, update incidents |
| Status transitions | Validate and apply state machine |
| Resource assignment | Link resources to incidents |
| History tracking | Record all incident changes |

### 3.8 Backend — Resource Module

| Responsibility | Description |
|---------------|-------------|
| Resource listing | Retrieve available resources |
| Status tracking | Manage resource availability |
| Assignment validation | Prevent double-assignment |

### 3.9 Backend — Audit Module

| Responsibility | Description |
|---------------|-------------|
| Action logging | Record all operator actions |
| Log retrieval | Query and filter audit entries |
| Entity linking | Associate logs with target entities |

### 3.10 Backend — Analytics Module

| Responsibility | Description |
|---------------|-------------|
| Metric calculation | Aggregate metrics from database |
| Chart data preparation | Format data for frontend charts |
| Dashboard data | Compute dashboard summary values |

## 4. Data Flow

### 4.1 Video-to-Event Data Flow

```mermaid
flowchart LR
    A[Video File] -->|Upload| B[File Storage]
    A -->|Metadata| C[VideoJob Record]
    B -->|Read frames| D[OpenCV Extractor]
    D -->|Frames| E[YOLO Detector]
    E -->|Detections| F[DetectionResult Records]
    E -->|Annotated frames| G[Evidence Image Storage]
    F -->|Person counts| H[Crowd Rules Engine]
    H -->|Triggered rules| I[CrowdEvent Records]
    I -->|Operator review| J[AuditLog Records]
```

### 4.2 Event-to-Incident Data Flow

```mermaid
flowchart LR
    A[CrowdEvent<br/>reviewed] -->|Create incident| B[Incident Record]
    B -->|Assign resource| C[Resource Assignment]
    B -->|Status change| D[IncidentHistory Record]
    C -->|Log| E[AuditLog]
    D -->|Log| E
    B -->|Metrics| F[Dashboard Analytics]
```

### 4.3 Route Calculation Data Flow

```mermaid
flowchart LR
    A[Venue Config<br/>JSON] -->|Load| B[NetworkX Graph]
    C[Operator] -->|Select nodes| D[API Request]
    D -->|Query| B
    B -->|Calculate| E[Route Results]
    E -->|Format| F[API Response]
    
    C -->|Block walkway| G[Edge Update]
    G -->|Modify graph| B
    G -->|Log| H[AuditLog]
```

## 5. Deployment Architecture

### 5.1 Local Development (Primary Target)

```mermaid
graph TB
    subgraph "Developer Machine"
        subgraph "Process 1: Frontend Dev Server"
            VITE[Vite Dev Server<br/>Port 5173]
        end
        
        subgraph "Process 2: Backend Server"
            UVICORN[Uvicorn<br/>Port 8000]
            FASTAPI[FastAPI Application]
        end
        
        subgraph "Storage"
            SQLITE[(SQLite File<br/>nexora.db)]
            UPLOADS[uploads/]
            EVIDENCE[evidence/]
        end
        
        subgraph "External Downloads"
            YOLO_W[YOLO Weights<br/>~/.cache/ultralytics/]
        end
    end
    
    BROWSER[Browser] -->|http://localhost:5173| VITE
    VITE -->|Proxy /api → :8000| UVICORN
    UVICORN --> FASTAPI
    FASTAPI --> SQLITE
    FASTAPI --> UPLOADS
    FASTAPI --> EVIDENCE
    BROWSER -->|Map tiles| OSM[OpenStreetMap CDN]
```

### 5.2 Production Build (Optional)

```mermaid
graph TB
    subgraph "Server"
        UVICORN[Uvicorn/Gunicorn<br/>Port 8000]
        FASTAPI[FastAPI Application]
        STATIC[Static Files<br/>Frontend Build]
    end
    
    BROWSER[Browser] -->|https://host:8000| UVICORN
    UVICORN --> FASTAPI
    FASTAPI --> STATIC
```

In production mode, the FastAPI server serves the built frontend assets as static files, eliminating the need for a separate frontend server.

## 6. External Dependencies

| Dependency | Purpose | Availability Risk | Mitigation |
|-----------|---------|------------------|------------|
| OpenStreetMap tiles | Map background | Low (highly available) | Functional without tiles (venue overlay still works) |
| YOLO model weights | Person detection | Low (cached after first download) | Pre-download during setup; cache locally |
| npm registry | Frontend packages | Low | lock file ensures reproducibility |
| PyPI | Python packages | Low | requirements.txt ensures reproducibility |

## 7. Trust Boundaries

```mermaid
graph TB
    subgraph "Untrusted"
        UPLOAD[User File Uploads]
        USER_INPUT[User Form Inputs]
    end
    
    subgraph "Trust Boundary"
        VALIDATION[Input Validation Layer]
        FILE_VAL[File Validation]
    end
    
    subgraph "Trusted"
        APP[Application Logic]
        DB[Database]
        FS[File Storage]
    end
    
    UPLOAD -->|Validate type, size, name| FILE_VAL
    USER_INPUT -->|Pydantic validation| VALIDATION
    FILE_VAL -->|Sanitised| FS
    VALIDATION -->|Validated| APP
    APP --> DB
```

**Trust boundary rules:**
1. All user input crosses a trust boundary and must be validated.
2. Uploaded files are treated as untrusted binary data.
3. Database queries use parameterised statements (via SQLAlchemy).
4. File paths are constructed server-side, never from user input.
5. Error messages crossing the trust boundary outward are sanitised.

## 8. Failure Modes

| Failure | Impact | Detection | Recovery |
|---------|--------|-----------|----------|
| Video file corrupt | Processing job fails | OpenCV exception | Mark job failed, notify operator |
| YOLO model missing | Cannot process video | Model load exception | Error message, download instructions |
| SQLite locked | Write operations fail | Database exception | Retry with backoff (WAL mode mitigates) |
| Map tiles unavailable | No map background | Tile load error | Venue overlay renders without background |
| Disk full | Cannot save files | OS exception | Error message, cleanup suggestion |
| Background task crash | Job stuck in "processing" | Timeout detection | Periodic stale job check, mark failed |
| Invalid venue config | Routing errors | Config validation | Fallback to empty venue, error notification |
| Out of memory (YOLO) | Process crash | OS kill signal | Smaller model suggestion, frame skip |

## 9. Architecture Decisions

### Decision 1: Modular Monolith

**Context:** The application has multiple functional areas (video, detection, events, routing, incidents) that need to share data.

**Decision:** Use a modular monolith architecture — a single FastAPI application with well-defined module boundaries.

**Rationale:**
- Simplicity for hackathon prototype
- Shared database access without network overhead
- Easier debugging and deployment
- Modules can be extracted later if needed

**Rejected alternatives:** Microservices (excessive complexity), serverless (insufficient for video processing).

See ADR-002 for full record.

### Decision 2: Background Processing via Threading

**Context:** Video processing is CPU-intensive and must not block the API.

**Decision:** Use Python `concurrent.futures.ThreadPoolExecutor` or `BackgroundTasks` in FastAPI for video processing jobs.

**Rationale:**
- Simple to implement
- No external message broker needed
- Sufficient for single-user prototype
- Job status tracked in database

**Rejected alternatives:** Celery + Redis (over-engineered for prototype), multiprocessing (complex for shared state).

**Trade-off:** Limited to one concurrent processing job due to CPU constraints. GIL may limit true parallelism, but YOLO/OpenCV release the GIL for compute-heavy operations.

### Decision 3: File-Based Media Storage

**Context:** Uploaded videos and evidence images need persistent storage.

**Decision:** Store media files on the local filesystem with paths referenced in the database.

**Rationale:**
- Simple and performant for local development
- No blob storage service needed
- Files organised by job ID for easy cleanup

**Rejected alternatives:** Database BLOBs (performance issues), S3 (requires cloud account).

### Decision 4: Venue Graph as Configuration

**Context:** Route calculation needs an explicit venue walkway network.

**Decision:** Define the venue graph in JSON configuration files loaded at startup.

**Rationale:**
- Separates venue data from application code
- Easy to swap demo venues
- Deterministic for testing
- Clear boundary between OSM (visual tiles) and routing data

## 10. Modularity Without Microservices

The backend is structured as a single application with internal module boundaries:

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py             # Environment configuration
│   ├── database.py           # SQLAlchemy setup
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── routers/              # FastAPI route handlers
│   │   ├── videos.py
│   │   ├── events.py
│   │   ├── venue.py
│   │   ├── routes.py
│   │   ├── incidents.py
│   │   ├── resources.py
│   │   ├── audit.py
│   │   └── analytics.py
│   ├── services/             # Business logic
│   │   ├── video_service.py
│   │   ├── detection_service.py
│   │   ├── event_service.py
│   │   ├── routing_service.py
│   │   ├── incident_service.py
│   │   └── audit_service.py
│   └── visionx/              # AI/CV engine
│       ├── frame_extractor.py
│       ├── detector.py
│       └── crowd_rules.py
```

**Module interaction rules:**
- Routers depend on services (never on other routers)
- Services may depend on other services for cross-module operations
- All modules share the same database session factory
- VisionX is isolated and could be extracted to a separate process

---

*End of Document 06 — System Architecture*
