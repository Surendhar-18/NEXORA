# NEXORA — Project Charter

**Document ID:** DOC-001  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. Project Title

**NEXORA — AI-Powered Crowd Safety Intelligence and Emergency Response Coordination**

With its AI video-analysis module: **VisionX**

## 2. Project Summary

NEXORA is a web-based decision-support prototype designed for hackathon demonstration. It integrates AI-powered crowd detection from prerecorded video footage with GIS-based venue operations, emergency coordination, and incident management. The system enables authorised operators to upload video, detect and count people using computer vision, review crowd-density events, examine venue routes, manage incidents, and coordinate simulated response resources — all through a unified command-centre interface.

## 3. Hackathon Theme

**Disaster Mitigation & Resilience**

## 4. Problem Statement

Large public gatherings — festivals, pilgrimages, railway events, and events like the Kumbh Mela — pose significant crowd-safety challenges. Organisers and safety personnel lack integrated tools that combine:

- **Crowd awareness:** Understanding how many people are present in different zones at different times.
- **Spatial intelligence:** Knowing venue layout, available routes, and exit capacities.
- **Coordinated response:** Managing incidents, assigning resources, and tracking actions in a unified system.

Current approaches often rely on fragmented systems: manual headcounts, disconnected communication channels, paper-based logs, and delayed decision-making. This fragmentation increases the risk of delayed responses during high-density situations.

## 5. Problem Significance

- **Scale:** Events like Kumbh Mela attract tens of millions of visitors. Even smaller festivals routinely involve crowds of tens of thousands.
- **Consequences:** Crowd crushes and stampedes at large gatherings have historically resulted in significant loss of life. The 2022 Itaewon crowd crush (159 deaths), the 2015 Mina stampede (over 2,400 deaths), and multiple incidents at Indian religious gatherings underscore the severity.
- **Gap:** There is a documented need for integrated situational awareness tools that combine video-based crowd monitoring with spatial analysis and coordinated incident response.
- **Timeliness:** Advances in computer vision (YOLO-based detection) and open-source GIS tools make it feasible to prototype such systems at hackathon scale.

## 6. Proposed Solution

NEXORA provides a two-module integrated prototype:

### Module A: VisionX — AI Crowd Safety Intelligence
- Accepts prerecorded, authorised video uploads from operators.
- Processes video using OpenCV for frame extraction and Ultralytics YOLO for person detection.
- Generates frame-by-frame person counts with evidence images.
- Applies configurable crowd-count rules to flag sustained high-density situations.
- Creates reviewable events that require human operator assessment.

### Module B: NEXORA Operations — GIS and Emergency Coordination
- Displays a configured demonstration venue on an interactive map.
- Represents zones, cameras, junctions, walkways, and exits.
- Maintains an explicit venue routing graph for path calculation.
- Allows operators to block/reopen walkways and recalculate routes.
- Supports incident creation from reviewed events with resource assignment.
- Provides dashboard metrics derived from actual application data.

**Key principle:** All automated alerts require human review before action. The system supports decision-making; it does not replace human judgement.

## 7. Project Objectives

| ID | Objective | Measurable Criterion |
|----|-----------|---------------------|
| OBJ-01 | Demonstrate end-to-end video-to-incident workflow | Complete workflow executable in demo within 5 minutes |
| OBJ-02 | Perform actual person detection on uploaded video | YOLO detections with bounding boxes and confidence scores visible |
| OBJ-03 | Generate reviewable crowd events from detection data | At least one event auto-generated from processed video in demo |
| OBJ-04 | Provide interactive GIS venue visualisation | Map displays zones, cameras, walkways, exits with interaction |
| OBJ-05 | Calculate and compare venue routes | At least two route alternatives displayed with cost breakdown |
| OBJ-06 | Support incident lifecycle management | Incident created, resource assigned, status updated, history preserved |
| OBJ-07 | Maintain complete audit trail | All operator actions logged with timestamps and retrievable |
| OBJ-08 | Present dashboard with real data | All dashboard metrics derived from persisted application records |

## 8. Target Users and Stakeholder Groups

### Primary Users
| User | Role | Interaction Level |
|------|------|-------------------|
| **Venue Safety Operator** | Uploads video, reviews events, manages incidents | High — primary daily user |
| **Operations Commander** | Reviews dashboard, oversees incident response | Medium — supervisory role |

### Secondary Stakeholders
| Stakeholder | Interest |
|-------------|----------|
| Hackathon Judges | Evaluate prototype innovation, feasibility, and completeness |
| Development Team | Build and maintain the prototype |
| Venue Administrators | Configure venue layout and zones (simulated) |
| Emergency Coordinators | Coordinate response resources (simulated) |

### Out-of-Scope Users
- General public (no public-facing interface)
- Real emergency services (no real dispatch)
- Law enforcement (no surveillance or identification features)

## 9. Project Scope

### In Scope
- Web-based single-page application with React frontend
- Python FastAPI backend with SQLite database
- Video upload with file validation (type, size)
- OpenCV frame extraction with configurable sampling
- YOLO-based person detection using Ultralytics
- Detection results storage with evidence images
- Configurable crowd-count threshold rules
- Event generation and operator review workflow
- Interactive Leaflet-based GIS map
- Configured demo venue with zones, cameras, walkways, exits
- NetworkX-based routing with explicit venue graph
- Walkway blocking/reopening with route recalculation
- Incident creation, resource assignment, status tracking
- Audit trail for operator actions
- Dashboard with metrics from persisted data
- Responsive UI for desktop and tablet
- Local development deployment
- Demo scenario with sample data

### Out of Scope
- **Live/real-time CCTV or streaming video analysis**
- **Real emergency service dispatch or communication**
- **Certified or official evacuation guidance**
- **Facial recognition or individual identification**
- **Emotion detection, panic detection, or violence detection**
- **Stampede prediction or anomaly detection** (unless separately validated)
- **Multi-user authentication with real identity providers**
- **Production-grade deployment with cloud infrastructure**
- **Mobile native applications**
- **Real-time video streaming protocols (RTSP, WebRTC)**
- **Integration with external emergency management systems**
- **Validated safety improvement claims**
- **Multi-venue or multi-tenant support**
- **Internationalisation or localisation**

## 10. Expected Deliverables

| # | Deliverable | Type |
|---|------------|------|
| 1 | Complete project documentation (18 documents) | Documentation |
| 2 | Functional React frontend with command-centre UI | Software |
| 3 | FastAPI backend with all API endpoints | Software |
| 4 | VisionX video processing pipeline | Software |
| 5 | GIS venue display and routing engine | Software |
| 6 | Incident management module | Software |
| 7 | SQLite database with schema and seed data | Data |
| 8 | Demo venue configuration | Data |
| 9 | Test suite with documented results | Testing |
| 10 | Deployment and operations guide | Documentation |
| 11 | Hackathon demo script and presentation plan | Documentation |

## 11. Success Criteria

| ID | Criterion | Verification Method |
|----|-----------|-------------------|
| SC-01 | Operator can upload a video and see processing status | Manual demo walkthrough |
| SC-02 | YOLO detects people in uploaded video with visible results | Inspect detection results and evidence images |
| SC-03 | Crowd event is generated when configured thresholds are met | Process sample video and verify event creation |
| SC-04 | Operator can review, acknowledge, or dismiss an event | Execute review workflow in UI |
| SC-05 | GIS map displays configured venue with interactive elements | Visual inspection of map |
| SC-06 | Route comparison shows alternatives with cost breakdown | Request routes between two points and inspect results |
| SC-07 | Blocked walkway is excluded from route calculation | Block walkway, recalculate, verify exclusion |
| SC-08 | Incident can be created from a reviewed event | Create incident and verify persistence |
| SC-09 | Resources can be assigned to incidents | Assign resource and verify in incident history |
| SC-10 | Dashboard metrics reflect actual stored data | Compare dashboard values with database records |
| SC-11 | All operator actions are logged in audit trail | Review audit log after performing actions |
| SC-12 | System handles errors gracefully (corrupt video, missing routes) | Test with invalid inputs |

## 12. Assumptions and Constraints

### Assumptions
| ID | Assumption |
|----|-----------|
| A-01 | Development machine has at least 8 GB RAM and a modern multi-core CPU |
| A-02 | Python 3.10+ and Node.js 18+ are available |
| A-03 | Internet access is available for downloading YOLO model weights and map tiles |
| A-04 | Uploaded videos are prerecorded and authorised for analysis |
| A-05 | SQLite is sufficient for prototype-scale data volumes |
| A-06 | CPU-based YOLO inference is acceptable (GPU optional) |
| A-07 | OpenStreetMap tile servers are available for background map |
| A-08 | The demo venue is a configured fictional or simplified layout |
| A-09 | Single-operator usage is sufficient for the prototype |
| A-10 | Video files are in common formats (MP4, AVI, MOV) under 500 MB |

### Constraints
| ID | Constraint |
|----|-----------|
| C-01 | Hackathon time constraints limit scope to MVP features |
| C-02 | No GPU may be available — CPU inference must be supported |
| C-03 | No real emergency infrastructure or external system integration |
| C-04 | No production deployment infrastructure required |
| C-05 | YOLO model weights must be downloaded at first run (network dependency) |
| C-06 | Video processing is inherently CPU-intensive and time-consuming |
| C-07 | Map tile rendering depends on external tile server availability |
| C-08 | SQLite does not support concurrent writes well under heavy load |
| C-09 | No personally identifiable information should be processed or stored |

## 13. Definitions of Technical Terminology

| Term | Definition |
|------|-----------|
| **NEXORA** | The overall project name for the crowd safety and emergency coordination platform |
| **VisionX** | The AI video analysis module within NEXORA |
| **YOLO** | You Only Look Once — a family of real-time object detection models |
| **Ultralytics** | The organisation maintaining the YOLOv8/YOLOv11 model library |
| **OpenCV** | Open Source Computer Vision Library — used for video frame extraction |
| **GIS** | Geographic Information System — technology for spatial data management |
| **Leaflet** | An open-source JavaScript library for interactive maps |
| **NetworkX** | A Python library for graph-based network analysis and routing |
| **FastAPI** | A modern Python web framework for building APIs |
| **SQLite** | A self-contained, file-based relational database |
| **Frame sampling** | Extracting frames from video at a configured interval (e.g., every 2 seconds) |
| **Confidence score** | A value between 0 and 1 indicating the model's certainty in a detection |
| **Bounding box** | A rectangle drawn around a detected object in an image |
| **Evidence image** | An annotated frame with bounding boxes saved as proof of detection |
| **Crowd event** | A system-generated alert when crowd-count rules are triggered |
| **Venue graph** | An explicit network of nodes (junctions/exits) and edges (walkways) representing the venue layout |
| **Route cost** | A calculated metric combining distance and configured penalties for route comparison |
| **Incident** | A tracked event requiring response — created by an operator from a reviewed crowd event |
| **Resource** | A simulated response unit (e.g., medical team, security patrol) assignable to incidents |
| **Audit trail** | A chronological record of all operator actions and system events |
| **Modular monolith** | A single deployable application with well-defined internal module boundaries |
| **MVP** | Minimum Viable Product — the smallest set of features that demonstrates the core workflow |

---

*End of Document 01 — Project Charter*
