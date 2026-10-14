# NEXORA — Software Requirements Specification (SRS)

**Document ID:** DOC-003  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification defines the functional and non-functional requirements for NEXORA — AI-Powered Crowd Safety Intelligence and Emergency Response Coordination. It serves as the authoritative reference for development, testing, and validation of the hackathon prototype.

### 1.2 Scope
NEXORA is a web-based decision-support prototype comprising two integrated modules:
- **VisionX:** AI-powered crowd detection from prerecorded video using OpenCV and YOLO.
- **NEXORA Operations:** GIS-based venue visualisation, route comparison, incident management, and resource coordination.

The system is designed for local development deployment with SQLite storage, targeting a single-operator demonstration workflow.

### 1.3 Intended Audience
- Development team
- Hackathon judges
- QA reviewers
- Future maintainers

## 2. Definitions and Abbreviations

| Abbreviation | Meaning |
|-------------|---------|
| API | Application Programming Interface |
| CORS | Cross-Origin Resource Sharing |
| CRUD | Create, Read, Update, Delete |
| CSV | Comma-Separated Values |
| FPS | Frames Per Second |
| FR | Functional Requirement |
| GIS | Geographic Information System |
| HTTP | Hypertext Transfer Protocol |
| JSON | JavaScript Object Notation |
| JWT | JSON Web Token |
| MP4 | MPEG-4 Part 14 video format |
| MVP | Minimum Viable Product |
| NFR | Non-Functional Requirement |
| OSM | OpenStreetMap |
| REST | Representational State Transfer |
| SRS | Software Requirements Specification |
| UUID | Universally Unique Identifier |
| YOLO | You Only Look Once (object detection model) |

## 3. Overall System Description

### 3.1 System Context
NEXORA operates as a two-tier web application:
- **Frontend:** React SPA running in the operator's browser.
- **Backend:** FastAPI server providing REST APIs, running AI processing, graph routing, and database management.

External dependencies:
- OpenStreetMap tile server (map background tiles)
- Ultralytics YOLO model weights (downloaded once)

### 3.2 System Boundaries
The system boundary encompasses:
- The React frontend application
- The FastAPI backend server
- The SQLite database
- Local file storage (uploaded videos, evidence images)

External to the system:
- Map tile providers
- YOLO model weight repositories
- The operator's browser
- The operator's local filesystem

### 3.3 User Classes and Permissions

| User Class | Description | Permission Level |
|-----------|-------------|-----------------|
| **Operator** | Primary user — uploads video, reviews events, manages incidents | Full access to all features |
| **Commander** | Supervisory user — reviews dashboards and incident history | Read access + incident management |
| **System** | Automated processes — video processing, event generation | Internal process execution |

**Note:** For the MVP prototype, authentication is simulated. All users have operator-level access. Role-based access control is deferred to post-MVP (see ADR on this topic).

### 3.4 Operating Environment

| Component | Requirement |
|-----------|-------------|
| Server OS | Windows 10/11, macOS 12+, or Ubuntu 20.04+ |
| Python | 3.10 or later |
| Node.js | 18 or later |
| Browser | Chrome 100+, Firefox 100+, Edge 100+ |
| RAM | Minimum 8 GB (16 GB recommended for video processing) |
| Disk | At least 2 GB free for application, models, and uploaded videos |
| Network | Required for initial setup (model weights, npm packages, map tiles) |
| GPU | Optional — CUDA-compatible GPU accelerates YOLO inference but is not required |

## 4. Functional Requirements

### 4.1 Video Upload and Validation

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-001 | The system shall accept video file uploads through a web interface. | P0 | Video file selectable and uploadable via browser form. | Manual test + API test |
| FR-002 | The system shall validate uploaded file type against an allowed list (MP4, AVI, MOV, MKV). | P0 | Files with disallowed extensions are rejected with error message. | Unit test with invalid file types |
| FR-003 | The system shall enforce a maximum upload file size (configurable, default 500 MB). | P0 | Files exceeding the limit are rejected before full upload. | Unit test with oversized payload |
| FR-004 | The system shall generate a unique identifier (UUID) for each uploaded video. | P0 | Each upload receives a distinct UUID. | Unit test verifying uniqueness |
| FR-005 | The system shall store uploaded video files in a configurable server directory outside the web root. | P0 | Video files are saved to the configured path, not accessible via direct URL. | Integration test + path inspection |
| FR-006 | The system shall sanitise uploaded filenames to prevent path traversal attacks. | P0 | Filenames with "../", special characters, or excessive length are sanitised. | Security test with malicious filenames |

### 4.2 Video Processing Job Management

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-007 | The system shall create a processing job record when a video upload is validated. | P0 | Database record created with job ID, video reference, and "queued" status. | Integration test |
| FR-008 | The system shall track job status through defined states: queued, processing, completed, failed. | P0 | Job status transitions are persisted and retrievable via API. | State transition test |
| FR-009 | The system shall process video jobs in the background without blocking the API. | P0 | API remains responsive during video processing. | Concurrent request test |
| FR-010 | The system shall record job start time, end time, and processing duration. | P0 | Timestamps recorded and visible in job details. | Integration test |
| FR-011 | The system shall record error details when a job fails. | P0 | Failed jobs have an error message in the database. | Error injection test |
| FR-012 | The system shall allow retrieval of all jobs with their current status. | P0 | GET endpoint returns list of jobs with status. | API test |

### 4.3 Frame Extraction and Detection

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-013 | The system shall extract frames from uploaded video using OpenCV at a configurable sampling interval (default: every 2 seconds). | P0 | Frames extracted at specified intervals, count matches expected. | Unit test with known video |
| FR-014 | The system shall use a pretrained YOLO model (via Ultralytics) to detect people in extracted frames. | P0 | Person detections returned with bounding boxes and confidence scores. | Detection test with sample image |
| FR-015 | The system shall filter YOLO detections to include only the "person" class. | P0 | Only person-class detections are stored; other classes are discarded. | Unit test verifying class filter |
| FR-016 | The system shall apply a configurable minimum confidence threshold (default: 0.5) to filter detections. | P0 | Detections below the threshold are excluded from counts. | Unit test with varied confidence |
| FR-017 | The system shall store per-frame detection results: frame index, timestamp, person count, average confidence, and individual bounding boxes. | P0 | Detection records persisted in database with all fields. | Database verification test |
| FR-018 | The system shall generate annotated evidence images with bounding boxes drawn on detected frames. | P0 | Evidence images saved as JPEG/PNG files with visible bounding boxes. | Visual inspection + file existence test |
| FR-019 | The system shall store evidence image file paths in the detection results. | P0 | Evidence path field populated and file exists at the path. | Integration test |
| FR-020 | The system shall handle frames with zero detections gracefully (store count as 0, optionally skip evidence image). | P0 | Zero-detection frames recorded with count 0, no crash. | Unit test with empty frame |

### 4.4 Crowd Events and Rules

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-021 | The system shall apply configurable crowd-count rules after video processing completes. | P0 | Rules evaluated against detection results; matching conditions trigger events. | Rule evaluation test |
| FR-022 | The system shall support a threshold rule: if person count in any sampled frame exceeds a configured value, generate an event. | P0 | Event created when count > threshold. No event when count ≤ threshold. | Boundary test |
| FR-023 | The system shall optionally support a sustained-count rule: if person count exceeds a threshold for N or more consecutive sampled frames, generate a flagged event. | P1 | Sustained event created only when condition persists across N frames. | Multi-frame rule test |
| FR-024 | The system shall create events with status "pending_review" and link them to the originating video, zone, frame timestamp, and person count. | P0 | Event record contains all required references. | Database verification |
| FR-025 | The system shall not automatically claim that high person counts indicate panic, violence, stampede, or imminent disaster. | P0 | Event descriptions use neutral language (e.g., "High person count detected"). | Content review |

### 4.5 Event Review

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-026 | The system shall display a list of events with filtering by status (pending_review, acknowledged, dismissed, escalated). | P0 | Event list shows filtered results with correct counts. | UI + API test |
| FR-027 | The system shall display event details including evidence image, person count, confidence, timestamp, zone, and originating video. | P0 | All event detail fields populated and displayed. | Integration test |
| FR-028 | The system shall allow an operator to acknowledge an event, changing its status to "acknowledged". | P0 | Status change persisted, audit log entry created. | Workflow test |
| FR-029 | The system shall allow an operator to dismiss an event, changing its status to "dismissed". | P0 | Status change persisted, audit log entry created. | Workflow test |
| FR-030 | The system shall allow an operator to escalate an event, changing its status to "escalated". | P0 | Status change persisted, audit log entry created. | Workflow test |
| FR-031 | The system shall record all event review actions in the audit trail with operator identifier, action, and timestamp. | P0 | Audit records created for each review action. | Audit log verification |

### 4.6 GIS Venue Display

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-032 | The system shall display a configured demonstration venue on an interactive Leaflet map. | P0 | Map renders with venue overlay at configured coordinates. | Visual inspection |
| FR-033 | The system shall display venue zones as labelled, coloured polygons on the map. | P0 | Zones visible with names and distinct colours. | Visual inspection |
| FR-034 | The system shall display camera locations as icons on the map, associated with their zones. | P0 | Camera markers visible at configured positions. | Visual inspection |
| FR-035 | The system shall display exits, junctions, and walkways as map elements. | P0 | All venue graph elements visible on the map. | Visual inspection |
| FR-036 | The system shall allow the operator to click on zones, cameras, and nodes for details. | P0 | Click interaction shows popup or panel with element details. | UI interaction test |
| FR-037 | The system shall display event indicators on the map at their associated zone locations. | P0 | Active events shown as markers/badges on their zones. | Integration test |

### 4.7 Route Calculation and Comparison

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-038 | The system shall maintain a venue routing graph with nodes (junctions, exits) and edges (walkways) using NetworkX. | P0 | Graph loaded from configuration with correct node and edge count. | Unit test |
| FR-039 | The system shall calculate the shortest route between two selected nodes using a documented cost formula. | P0 | Route returned with total cost matching manual calculation. | Calculation verification test |
| FR-040 | The system shall display calculated routes as highlighted paths on the GIS map. | P0 | Route polyline visible on map between selected points. | Visual inspection |
| FR-041 | The system shall display route cost breakdown (distance, congestion penalty, hazard penalty). | P0 | Cost components shown for each route. | API response verification |
| FR-042 | The system shall allow an operator to block a walkway, removing it from route eligibility. | P0 | Blocked walkway excluded from all subsequent route calculations. | Routing test after block |
| FR-043 | The system shall allow an operator to reopen a blocked walkway, restoring it to route eligibility. | P0 | Reopened walkway included in subsequent route calculations. | Routing test after reopen |
| FR-044 | The system shall recalculate routes when walkway availability changes. | P0 | New route calculation reflects current walkway status. | Integration test |
| FR-045 | The system shall display a clear message when no valid route exists between selected points. | P0 | "No valid route found" message displayed with explanation. | Disconnected graph test |
| FR-046 | The system shall calculate and display multiple route alternatives (up to 3) when available. | P1 | Multiple routes shown with comparative costs. | Multi-path test |

### 4.8 Incident Management

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-047 | The system shall allow creating an incident from a reviewed (acknowledged or escalated) event. | P0 | Incident created with reference to source event. | Workflow test |
| FR-048 | The system shall record incident properties: ID, title, description, location (zone), priority (low/medium/high/critical), status, related event ID, created timestamp. | P0 | All fields persisted and retrievable. | Database test |
| FR-049 | The system shall support incident status transitions: open → responding → resolved → closed. | P0 | Valid transitions succeed; invalid transitions are rejected. | State machine test |
| FR-050 | The system shall allow assigning a simulated response resource to an incident. | P0 | Resource assignment recorded with timestamp. | Integration test |
| FR-051 | The system shall track incident status changes with timestamps in an incident history. | P0 | History entries created for each status change. | History verification |
| FR-052 | The system shall display incident details including history, assignments, and linked event. | P0 | Incident detail view shows all related information. | UI test |
| FR-053 | The system shall allow listing all incidents with filtering by status and priority. | P0 | Filtered list returns correct results. | API test |

### 4.9 Resource Management

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-054 | The system shall maintain a list of simulated response resources (e.g., medical teams, security patrols, fire units). | P0 | Resource list retrievable via API. | API test |
| FR-055 | The system shall track resource status: available, assigned, unavailable. | P0 | Status reflected correctly after assignment. | State test |
| FR-056 | The system shall prevent assigning an already-assigned resource to another incident without releasing it first. | P0 | Assignment rejected with appropriate error. | Validation test |

### 4.10 Audit and History

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-057 | The system shall log all operator actions (event reviews, incident changes, resource assignments, walkway changes) in an audit trail. | P0 | Audit entries created for all specified actions. | Comprehensive audit test |
| FR-058 | The system shall store audit entries with: action type, target entity, operator identifier, timestamp, and details. | P0 | All fields populated for each entry. | Schema verification |
| FR-059 | The system shall provide an API to retrieve audit entries with optional filtering by entity type and date range. | P0 | Filtered audit query returns correct results. | API test |

### 4.11 Dashboard and Analytics

| ID | Requirement | Priority | Acceptance Criteria | Verification |
|----|------------|----------|-------------------|-------------|
| FR-060 | The system shall display a dashboard with metrics derived from persisted application records. | P0 | Dashboard values match database query results. | Data accuracy test |
| FR-061 | The system shall display on the dashboard: total videos processed, active incidents, pending events, total detections, resource utilisation. | P0 | All specified metrics visible. | UI inspection |
| FR-062 | The system shall display a detection count chart showing person counts over time for recent processing jobs. | P0 | Chart renders with correct data points. | Data verification |
| FR-063 | The system shall provide an analytics view with incident trends and event statistics. | P1 | Analytics charts populated from real data. | Data verification |

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement | Target | Benchmark Method |
|----|------------|--------|-----------------|
| NFR-001 | API response time for non-processing endpoints | < 500ms for 95th percentile | Measure response times for 100 sequential requests |
| NFR-002 | Video upload initiation response | < 2 seconds for files up to 500 MB | Measure time from upload start to server acknowledgement |
| NFR-003 | Dashboard page load time | < 3 seconds initial load | Browser performance profiling |
| NFR-004 | Map rendering time | < 5 seconds for venue display | Browser performance profiling |
| NFR-005 | Route calculation time | < 2 seconds for a venue graph with up to 100 nodes | Benchmark with test graph |
| NFR-006 | Frame extraction throughput | Process at least 1 frame per second (CPU) | Measure processing time for sample video |

### 5.2 Reliability

| ID | Requirement | Acceptance Criteria |
|----|------------|-------------------|
| NFR-007 | The system shall not crash on corrupt or unreadable video files. | Error logged, job marked as failed, user notified. |
| NFR-008 | The system shall handle YOLO model weight download failures gracefully. | Clear error message, processing deferred until model available. |
| NFR-009 | The system shall handle map tile server unavailability. | Map renders with error overlay or cached tiles. |
| NFR-010 | The system shall recover from database connection errors. | SQLite file checked on startup, error reported if inaccessible. |
| NFR-011 | The system shall handle concurrent API requests without data corruption. | SQLite WAL mode enabled; API serialises writes where necessary. |

### 5.3 Security

| ID | Requirement | Acceptance Criteria |
|----|------------|-------------------|
| NFR-012 | The system shall validate all API inputs using Pydantic schemas. | Invalid requests return 422 with validation details. |
| NFR-013 | The system shall not expose server filesystem paths in API responses. | API responses use relative paths or resource URLs. |
| NFR-014 | The system shall configure CORS to restrict cross-origin access. | CORS configured for frontend origin only. |
| NFR-015 | The system shall not commit secrets, credentials, or model weights to version control. | .gitignore includes .env, model weights, uploaded files. |
| NFR-016 | The system shall use environment variables for all configuration secrets. | No hardcoded secrets in source code. |
| NFR-017 | The system shall sanitise error messages to avoid information leakage. | Internal errors return generic messages; details logged server-side. |

### 5.4 Usability

| ID | Requirement | Acceptance Criteria |
|----|------------|-------------------|
| NFR-018 | The interface shall be responsive for desktop (1280px+) and tablet (768px+) viewports. | Layout adapts without horizontal scrolling. |
| NFR-019 | The system shall use accessible colour contrast ratios (WCAG AA). | Contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text. |
| NFR-020 | The system shall provide loading indicators for all asynchronous operations. | Spinners/progress bars visible during loading. |
| NFR-021 | The system shall display meaningful error messages for user-facing errors. | Errors include what happened and suggested action. |
| NFR-022 | The system shall provide confirmation dialogs for destructive or critical actions. | Confirmations required for incident creation, event escalation, walkway blocking. |
| NFR-023 | All interactive elements shall have accessible labels. | Buttons, inputs, and controls have aria-label or visible labels. |

### 5.5 Maintainability

| ID | Requirement | Acceptance Criteria |
|----|------------|-------------------|
| NFR-024 | The backend shall follow a modular architecture with clear module boundaries. | Modules (video, detection, events, routing, incidents) are independently testable. |
| NFR-025 | The frontend shall use reusable component architecture. | Shared components used across screens. |
| NFR-026 | The codebase shall include code comments for complex logic. | AI processing, routing algorithm, and rule evaluation documented in code. |

## 6. External Interface Requirements

### 6.1 User Interface
- Web browser (Chrome, Firefox, Edge)
- Mouse and keyboard input
- File upload dialog for video files
- Interactive map with click, zoom, pan controls

### 6.2 Software Interfaces

| Interface | Purpose | Protocol |
|-----------|---------|----------|
| OpenStreetMap Tile Server | Background map tiles | HTTPS (GET tile images) |
| Ultralytics Model Repository | YOLO model weight download | HTTPS (one-time download) |
| SQLite Database | Data persistence | File-based SQL |
| Local Filesystem | Video and evidence file storage | OS file I/O |

### 6.3 Communication Interfaces
- Frontend ↔ Backend: HTTP REST API (JSON)
- Backend ↔ Database: SQLAlchemy ORM
- Backend ↔ Filesystem: Python file I/O

## 7. Data Requirements

### 7.1 Data Entities
See Document 08 (Database Design) for complete schema.

Core entities: VideoJob, DetectionResult, CrowdEvent, VenueNode, VenueEdge, Incident, Resource, IncidentHistory, AuditLog.

### 7.2 Data Retention
- Uploaded videos: Retained until operator deletes or demo reset.
- Evidence images: Retained as long as associated detection results exist.
- Database records: Retained until demo reset.
- Audit logs: Never deleted during normal operation.

### 7.3 Data Integrity
- Foreign key constraints enforced.
- Cascade delete for evidence images when detection results are deleted.
- Orphan video files cleaned up on demo reset.

## 8. Constraints and Assumptions

### Constraints
1. SQLite single-writer limitation acceptable for prototype.
2. CPU-based YOLO inference may be slow for long videos (mitigation: configurable frame sampling).
3. Map tiles require external network access.
4. YOLO model weights require ~25 MB download on first run.
5. Video processing is a blocking CPU-intensive task per job.

### Assumptions
1. A single operator uses the system at a time.
2. Uploaded videos are under 500 MB and in supported formats.
3. The demonstration venue graph has fewer than 100 nodes.
4. Internet access is available during development and demo.
5. The development machine meets minimum hardware requirements.

## 9. Requirement Traceability

See Document 14 (Requirement Traceability Matrix) for complete mapping of:
- FR/NFR → PRD User Stories
- FR/NFR → UI Screens
- FR/NFR → API Endpoints
- FR/NFR → Database Entities
- FR/NFR → Test Cases

---

*End of Document 03 — Software Requirements Specification*
