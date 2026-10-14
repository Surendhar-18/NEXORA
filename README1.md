# NEXORA — AI-Powered Crowd Safety Intelligence and Emergency Response Coordination

> **Hackathon Theme:** Disaster Mitigation & Resilience  
> **Module A:** VisionX — AI Crowd Safety Intelligence  
> **Module B:** NEXORA — GIS Operations & Emergency Coordination  
> **Design Theme:** Dark Terminal Control Surface (Obsidian Canvas `#101010`, Carbon Lift `#1d1a18`, Signal Orange `#ee6018`, Metric Green `#a0ca92`)

---

## 1. Project Overview

**NEXORA** is a unified, web-based decision-support platform designed to protect lives at high-density public gatherings such as religious festivals (e.g. Kumbh Mela), pilgrimages, and railway hubs.

The platform bridges automated computer-vision crowd density detection with interactive spatial intelligence and incident dispatch:
- **VisionX AI:** Ingests operator-provided video footage, extracts frames at configured intervals using OpenCV, detects people with Ultralytics YOLOv8, and presents visual evidence bounding boxes without facial surveillance.
- **GIS & NetworkX Routing:** Dynamically computes safe evacuation and navigation paths through internal venue walkways, factoring in density impedance and dynamic walkway blockages.
- **Incident Coordination:** Enforces human-in-the-loop alert triage, coordinates simulated emergency teams (medical, security, wardens), and logs every operator action to an unalterable audit trail.

---

## 2. Complete Planning & Architecture Documentation Suite

The complete engineering specification is documented across 18 authoritative deliverables in the [`docs/`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs) directory:

| Document ID | Title | File Path | Focus Area |
|:-----------:|-------|-----------|------------|
| **DOC-001** | Project Charter | [`docs/01-project-charter.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/01-project-charter.md) | Vision, problem scope, business case, assumptions & constraints |
| **DOC-002** | Product Requirements Document (PRD) | [`docs/02-prd.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/02-prd.md) | User personas, 25 user stories (US-001–025), MVP boundaries |
| **DOC-003** | Software Requirements Specification (SRS) | [`docs/03-srs.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/03-srs.md) | 63 functional requirements (FR-001–063), 20 non-functional requirements |
| **DOC-004** | User Journeys & Application Flow | [`docs/04-user-journeys-and-app-flow.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/04-user-journeys-and-app-flow.md) | Persona journeys, workflow state machines, decision branches |
| **DOC-005** | UI/UX Design Specification | [`docs/05-ui-ux-design.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/05-ui-ux-design.md) | 8 wireframe screens, design tokens, component hierarchy, accessibility |
| **DOC-006** | System Architecture | [`docs/06-system-architecture.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/06-system-architecture.md) | C4 architectural diagrams, data flow, modular monolith boundaries |
| **DOC-007** | Technical Design & Technology Decisions | [`docs/07-technical-design.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/07-technical-design.md) | Tech stack evaluation, library versions, concurrency & caching |
| **DOC-008** | Database Design | [`docs/08-database-design.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/08-database-design.md) | Entity relationship diagrams (ERD), SQLite DDL schema, indexes |
| **DOC-009** | API Specification | [`docs/09-api-specification.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/09-api-specification.md) | 22 REST endpoints, Pydantic schemas, validation rules, error codes |
| **DOC-010** | GIS and Routing Design | [`docs/10-gis-and-routing-design.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/10-gis-and-routing-design.md) | Venue topological model, cost formula, NetworkX rerouting, demo venue |
| **DOC-011** | VisionX AI & Computer Vision Design | [`docs/11-visionx-ai-design.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/11-visionx-ai-design.md) | OpenCV extraction, YOLO pipeline, crowd rules engine, responsible AI |
| **DOC-012** | Security, Privacy & Responsible-Use Plan | [`docs/12-security-and-privacy.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/12-security-and-privacy.md) | Threat modeling, path traversal defense, privacy by design, ethics |
| **DOC-013** | Test Strategy and Test Cases | [`docs/13-test-plan.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/13-test-plan.md) | 30 test cases (TC-001–030) spanning backend, AI, GIS, and security |
| **DOC-014** | Requirement Traceability Matrix | [`docs/14-requirement-traceability.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/14-requirement-traceability.md) | Full bidirectional traceability: Goals → Stories → FRs → API → Tests |
| **DOC-015** | Development Roadmap | [`docs/15-development-roadmap.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/15-development-roadmap.md) | Phases 0 through 10, dependency graph, critical path analysis |
| **DOC-016** | Deployment and Operations Guide | [`docs/16-deployment-and-operations.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/16-deployment-and-operations.md) | Local setup, environment config, startup commands, demo reset |
| **DOC-017** | Hackathon Demo & Presentation Plan | [`docs/17-hackathon-demo-plan.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/17-hackathon-demo-plan.md) | 5-minute walkthrough script, contingencies, judge Q&A preparation |
| **DOC-018** | Architecture Decision Records (ADRs) | [`docs/18-architecture-decision-records.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/18-architecture-decision-records.md) | ADR Register linking ADR-0001 through ADR-0007 in [`docs/adr/`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/adr) |

---

## 3. Technology Stack

- **Backend:** FastAPI (Python 3.10+), SQLAlchemy 2.0, Pydantic v2, Uvicorn
- **Computer Vision & AI:** OpenCV (`opencv-python-headless`), Ultralytics YOLOv8 (`yolov8n.pt`), PyTorch
- **GIS & Network Routing:** NetworkX, Leaflet.js (`react-leaflet`), GeoJSON
- **Database:** SQLite 3 with Write-Ahead Logging (WAL)
- **Frontend:** React 18, Vite, Vanilla CSS adhering to [`DESIGN.md`](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/DESIGN.md) dark terminal tokens
- **Testing:** Pytest, pytest-asyncio, HTTPX

---

## 4. Repository Structure

```
nexora/
├── .env.example                          # Environment configuration template
├── .gitignore                            # Python, Node, media & model ignore rules
├── DESIGN.md                             # UI/UX design tokens and style reference
├── README.md                             # Project overview and documentation index
├── docs/                                 # Authoritative documentation suite
│   ├── 01-project-charter.md
│   ├── 02-prd.md
│   ├── 03-srs.md
│   ├── 04-user-journeys-and-app-flow.md
│   ├── 05-ui-ux-design.md
│   ├── 06-system-architecture.md
│   ├── 07-technical-design.md
│   ├── 08-database-design.md
│   ├── 09-api-specification.md
│   ├── 10-gis-and-routing-design.md
│   ├── 11-visionx-ai-design.md
│   ├── 12-security-and-privacy.md
│   ├── 13-test-plan.md
│   ├── 14-requirement-traceability.md
│   ├── 15-development-roadmap.md
│   ├── 16-deployment-and-operations.md
│   ├── 17-hackathon-demo-plan.md
│   ├── 18-architecture-decision-records.md
│   └── adr/                              # Individual ADR markdown files
│       ├── 0001-react-and-fastapi.md
│       ├── 0002-modular-monolith.md
│       ├── 0003-sqlite-for-local-prototype.md
│       ├── 0004-prerecorded-video-analysis-scope.md
│       ├── 0005-explicit-venue-routing-graph.md
│       ├── 0006-human-in-the-loop-alert-review.md
│       └── 0007-simulated-resource-assignment.md
└── [Application Directories — Scheduled for Phase 1 Implementation]
    ├── backend/
    ├── frontend/
    ├── data/
    │   ├── uploads/
    │   ├── evidence/
    │   ├── models/
    │   └── venue/
    ├── demo_scenarios/
    └── tests/
```

---

## 5. Next Steps

The planning, requirements engineering, architectural modeling, and documentation phase is complete. Implementation will proceed according to the [Development Roadmap](file:///c:/Users/ssure/OneDrive/Documents/nexora%21/docs/15-development-roadmap.md) starting with **Phase 0 & Phase 1** upon user approval.
