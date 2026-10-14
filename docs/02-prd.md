# NEXORA — Product Requirements Document (PRD)

**Document ID:** DOC-002  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. Product Vision

NEXORA envisions a unified decision-support platform where crowd safety operators can analyse recorded video footage for crowd density, review automated alerts with full evidence, examine venue routes and spatial context, and coordinate incident response — all within a single, integrated command-centre interface.

The product bridges the gap between fragmented crowd monitoring tools and emergency coordination systems, providing a transparent, auditable, and human-centred workflow from video analysis to incident resolution.

## 2. User Personas

### Persona 1: Venue Safety Operator — "Ananya"

| Attribute | Detail |
|-----------|--------|
| **Role** | On-site safety coordinator at a large festival venue |
| **Age** | 32 |
| **Technical Proficiency** | Moderate — comfortable with web applications and basic data review |
| **Responsibilities** | Monitor crowd conditions, review alerts, coordinate with response teams |
| **Goals** | Quickly identify high-density situations, make informed routing decisions, create and track incidents |
| **Frustrations** | Disconnected tools, manual counting, delayed information, no evidence trail |
| **Usage Pattern** | Active during event hours, reviews video footage after collection, manages incidents through resolution |
| **Key Need** | A single interface that connects video analysis results to spatial context and response coordination |

### Persona 2: Operations Commander — "Rajesh"

| Attribute | Detail |
|-----------|--------|
| **Role** | Senior operations manager overseeing multiple venue zones |
| **Age** | 48 |
| **Technical Proficiency** | Low-to-moderate — prefers high-level dashboards over technical interfaces |
| **Responsibilities** | Overall situational awareness, resource allocation decisions, escalation handling |
| **Goals** | See aggregated venue status at a glance, understand incident trends, verify response actions |
| **Frustrations** | Lack of overview dashboards, no historical data, reliance on verbal reports |
| **Usage Pattern** | Periodic dashboard review, incident escalation handling |
| **Key Need** | Dashboard with real metrics, incident history, and audit trail for accountability |

## 3. User Needs and Pain Points

| ID | Need | Pain Point | NEXORA Solution |
|----|------|-----------|----------------|
| UN-01 | Understand crowd density in venue zones | Manual headcounts are slow, inaccurate, and unscalable | VisionX automated person detection from video |
| UN-02 | Review evidence for crowd alerts | Alerts without evidence are not actionable | Evidence images with bounding boxes and counts |
| UN-03 | Assess available routes under current conditions | No spatial awareness tool for temporary venues | Interactive GIS map with route comparison |
| UN-04 | Respond to walkway blockages | No dynamic rerouting capability | Walkway block/reopen with automatic route recalculation |
| UN-05 | Coordinate incident response | Paper logs, radio communication, no tracking | Incident management with assignment and status tracking |
| UN-06 | Maintain accountability | No audit trail for decisions | Complete audit log of operator actions |
| UN-07 | See overall venue status | Fragmented data across multiple systems | Unified dashboard with real metrics |
| UN-08 | Handle uncertainty in AI detections | Blind trust in automated alerts leads to errors | Human review required for all system-generated events |

## 4. Product Goals

| ID | Goal | Metric |
|----|------|--------|
| PG-01 | Demonstrate feasibility of integrated video-to-incident workflow | End-to-end workflow completable in demo |
| PG-02 | Provide actionable crowd-density information | Person counts with evidence viewable per zone |
| PG-03 | Enable informed route decisions | Route comparison with cost breakdown available |
| PG-04 | Support structured incident response | Incident lifecycle fully trackable |
| PG-05 | Ensure transparency and accountability | All actions auditable |
| PG-06 | Maintain responsible AI use | All automated outputs subject to human review |

## 5. Core Features and User Benefits

| Feature | User Benefit |
|---------|-------------|
| Video upload and processing | Automated crowd analysis without manual counting |
| Person detection with evidence | Verifiable detection results with visual proof |
| Crowd-count event rules | Proactive alerting based on configurable thresholds |
| Event review workflow | Structured assessment with acknowledge/dismiss/escalate options |
| Interactive GIS map | Spatial context for decision-making |
| Route comparison | Informed routing decisions with cost transparency |
| Walkway management | Dynamic response to venue condition changes |
| Incident management | Structured coordination from detection to resolution |
| Resource assignment | Simulated dispatch with tracking |
| Audit trail | Accountability and post-event review |
| Dashboard | At-a-glance situational awareness with real data |

## 6. Feature Priorities

### P0 — Must Have (MVP)

| ID | Feature | Rationale |
|----|---------|-----------|
| P0-01 | Video upload with validation | Entry point for the entire workflow |
| P0-02 | Video processing job management | Track processing status |
| P0-03 | OpenCV frame extraction | Required for detection pipeline |
| P0-04 | YOLO person detection | Core AI capability |
| P0-05 | Detection results storage | Persist counts, confidence, timestamps |
| P0-06 | Evidence image generation | Visual proof of detections |
| P0-07 | Detection timeline view | Frame-by-frame count visualisation |
| P0-08 | Crowd-count threshold rules | Event generation trigger |
| P0-09 | Event creation from rules | Automated alert generation |
| P0-10 | Event review workflow | Operator assessment (acknowledge/dismiss/escalate) |
| P0-11 | GIS map with venue display | Spatial context for zones and cameras |
| P0-12 | Venue routing graph | Nodes and edges for path calculation |
| P0-13 | Route calculation and comparison | Compare alternatives with costs |
| P0-14 | Walkway block/reopen | Dynamic route management |
| P0-15 | Incident creation from events | Connect detection to response |
| P0-16 | Incident status management | Track incident lifecycle |
| P0-17 | Resource assignment to incidents | Simulated dispatch |
| P0-18 | Audit trail | Operator action logging |
| P0-19 | Dashboard with real metrics | Overview from persisted data |
| P0-20 | Responsive UI shell | Command-centre interface |

### P1 — Should Have (Enhanced MVP)

| ID | Feature | Rationale |
|----|---------|-----------|
| P1-01 | Sustained high-count detection | More sophisticated alerting |
| P1-02 | Configurable frame sampling interval | Operator control over processing |
| P1-03 | Multiple route alternatives display | Better decision support |
| P1-04 | Incident history timeline | Detailed tracking view |
| P1-05 | Resource availability management | Resource lifecycle tracking |
| P1-06 | Export incident reports | Documentation capability |
| P1-07 | Venue configuration interface | Manage zones and cameras |
| P1-08 | Processing progress indicators | Better user experience during long jobs |
| P1-09 | Detection confidence filtering | Adjustable detection sensitivity |

### P2 — Nice to Have (Post-MVP)

| ID | Feature | Rationale |
|----|---------|-----------|
| P2-01 | Multi-video batch processing | Scale handling |
| P2-02 | Historical analytics and trends | Long-term pattern analysis |
| P2-03 | Role-based access control | Multi-user support |
| P2-04 | Notification system (in-app) | Proactive alerting |
| P2-05 | Video playback with overlay | Enhanced evidence review |
| P2-06 | Heatmap visualisation | Density distribution view |
| P2-07 | PDF report generation | Formal reporting |
| P2-08 | Dark/light theme toggle | User preference |
| P2-09 | Keyboard shortcuts | Power user efficiency |

## 7. User Stories

### Video Upload and Processing

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|-------------------|
| US-001 | As an operator, I want to upload a prerecorded video file so that I can analyse it for crowd density. | P0 | Given a valid MP4/AVI/MOV file under 500 MB, when I upload it, then the system creates a processing job and shows upload confirmation. |
| US-002 | As an operator, I want to see the processing status of my uploaded video so that I know when results are available. | P0 | Given a submitted job, when I view the job list, then I see status (queued/processing/completed/failed) with progress indication. |
| US-003 | As an operator, I want invalid uploads to be rejected with clear error messages so that I don't wait for broken processing. | P0 | Given an invalid file (wrong type, too large, corrupt), when I attempt upload, then the system rejects it with a specific error message. |
| US-004 | As an operator, I want to configure the frame sampling interval before processing so that I can balance speed and detail. | P1 | Given a video upload form, when I set the sampling interval (e.g., 1–10 seconds), then the system uses that interval for frame extraction. |

### Detection and Evidence

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|-------------------|
| US-005 | As an operator, I want to see person detection results for each sampled frame so that I understand crowd density over time. | P0 | Given a completed processing job, when I view detection results, then I see a timeline of frame timestamps with person counts. |
| US-006 | As an operator, I want to view evidence images with bounding boxes so that I can verify detection accuracy. | P0 | Given a detection result, when I click on a frame, then I see the annotated image with bounding boxes around detected people. |
| US-007 | As an operator, I want to see confidence scores for detections so that I understand the reliability of counts. | P0 | Given detection results, when I view frame details, then I see average and per-detection confidence values. |
| US-008 | As an operator, I want to filter detections by confidence threshold so that I can exclude low-confidence results. | P1 | Given detection results, when I adjust the confidence slider, then counts are recalculated using only detections above the threshold. |

### Events and Review

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|-------------------|
| US-009 | As an operator, I want the system to create events when crowd counts exceed configured thresholds so that I am alerted to high-density situations. | P0 | Given a configured threshold (e.g., >50 people), when processing detects counts above this level, then an event is created with status "pending_review". |
| US-010 | As an operator, I want to review events with their evidence so that I can make informed decisions. | P0 | Given a pending event, when I open it, then I see the originating video, timestamp, zone, person count, and evidence image. |
| US-011 | As an operator, I want to acknowledge, dismiss, or escalate an event so that I can record my assessment. | P0 | Given a pending event, when I select an action, then the event status updates and my action is recorded in the audit trail. |
| US-012 | As an operator, I want events flagged only when high counts are sustained across multiple frames so that transient spikes don't generate false alerts. | P1 | Given a sustained-count rule (e.g., >50 people for 3+ consecutive frames), when this condition is met, then the event is flagged as sustained. |

### GIS and Routing

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|-------------------|
| US-013 | As an operator, I want to see the venue displayed on an interactive map so that I have spatial context for events and incidents. | P0 | Given the configured venue, when I open the GIS map, then I see zones, camera locations, junctions, walkways, and exits. |
| US-014 | As an operator, I want to compare routes between two points in the venue so that I can assess egress options. | P0 | Given two selected points, when I request route comparison, then I see at least one route with distance and cost. |
| US-015 | As an operator, I want to block a walkway so that I can simulate a blockage and see route impact. | P0 | Given an available walkway, when I block it, then it is excluded from subsequent route calculations. |
| US-016 | As an operator, I want to reopen a blocked walkway so that I can restore routing options. | P0 | Given a blocked walkway, when I reopen it, then it is included in subsequent route calculations. |
| US-017 | As an operator, I want to see a clear message when no valid route exists so that I understand the routing limitation. | P0 | Given a disconnected graph segment, when I request a route, then the system displays "No valid route found" with explanation. |
| US-018 | As an operator, I want to see multiple route alternatives with cost breakdowns so that I can choose the best option. | P1 | Given two points with multiple paths, when I request routes, then I see up to 3 alternatives with cost components. |

### Incident Management

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|-------------------|
| US-019 | As an operator, I want to create an incident from a reviewed event so that I can initiate a response. | P0 | Given a reviewed (acknowledged/escalated) event, when I create an incident, then it is linked to the event with location, description, and priority. |
| US-020 | As an operator, I want to assign a simulated response resource to an incident so that I can coordinate action. | P0 | Given an incident, when I assign a resource, then the assignment is recorded with timestamp. |
| US-021 | As an operator, I want to update incident status (open/responding/resolved/closed) so that I can track progress. | P0 | Given an incident, when I change status, then the change is recorded with timestamp and operator. |
| US-022 | As an operator, I want to view incident history so that I can review the complete response timeline. | P0 | Given an incident, when I view history, then I see all status changes, assignments, and actions chronologically. |
| US-023 | As an operator, I want to view the audit trail so that I can verify all operator actions taken. | P0 | Given the audit view, when I access it, then I see chronological entries with operator, action, target, and timestamp. |

### Dashboard and Analytics

| ID | Story | Priority | Acceptance Criteria |
|----|-------|----------|-------------------|
| US-024 | As a commander, I want to see a dashboard overview so that I understand the current venue situation. | P0 | Given persisted data, when I view the dashboard, then I see active incidents, pending events, processing jobs, and resource status — all from real data. |
| US-025 | As a commander, I want to see analytics on detection and incident trends so that I can review patterns. | P1 | Given historical data, when I view analytics, then I see charts of detections over time, incidents by priority, and response times. |

## 8. MVP Definition

The MVP includes all P0 features. It demonstrates the complete end-to-end workflow:

**Video Upload → Processing → Detection → Event Generation → Event Review → GIS Context → Route Analysis → Incident Creation → Resource Assignment → Dashboard Reflection**

The MVP must be:
- Functional end-to-end (not just UI mockups)
- Using real YOLO detection (not simulated results)
- Using real route calculation (not hardcoded routes)
- Persisting all data to SQLite
- Displaying real metrics on the dashboard
- Recording all operator actions in audit trail

## 9. Non-Goals

The following are explicitly **not** goals for this product:

- Real-time live video streaming analysis
- Facial recognition or individual identification
- Emotion, panic, violence, or stampede detection
- Integration with real emergency dispatch systems
- Certified evacuation route guidance
- Production-scale deployment
- Mobile native applications
- Multi-tenant or multi-venue support
- Validated claims of safety improvement
- Crowd behaviour prediction or anomaly detection (without separately validated models)

## 10. Competitive Differentiation

### Proposed Differentiators
NEXORA's primary differentiation for the hackathon context is its **integrated workflow** — connecting AI-based video analysis directly to GIS-based spatial awareness and structured incident management in a single application. Many existing approaches treat these as separate systems.

### Honest Positioning
- **We do not claim** this is the first crowd monitoring tool — commercial solutions exist (e.g., Crowd Dynamics, NVIDIA Metropolis).
- **We do not claim** production-grade accuracy — the prototype uses standard YOLO models without custom training.
- **We do claim** a transparent, auditable, human-centred approach to crowd safety tooling at hackathon prototype scale.
- **We do claim** integration of video analysis, GIS operations, and incident management in a demonstrable workflow.

### Innovation for Hackathon Context
1. **End-to-end integration:** Video analysis → event → spatial context → incident → response in one system.
2. **Transparency:** Every detection is backed by evidence images; every action is audited.
3. **Human-centred design:** All automated alerts require human review — no autonomous action.
4. **Configurable rules:** Crowd-count thresholds and routing costs are transparent and adjustable.

## 11. Product Success Metrics

| Metric | How Measured | Target |
|--------|-------------|--------|
| Workflow completeness | Count of P0 features implemented and functional | 100% of P0 features |
| Detection accuracy (demo) | Manual comparison of YOLO detections vs. visible people in sample video | Reasonable detection of visible, unoccluded people |
| Processing completion | Percentage of valid videos successfully processed | 100% for valid test videos |
| Incident lifecycle coverage | Confirm all status transitions are functional | All statuses reachable |
| Route calculation correctness | Verify route costs match expected calculations | Correct for demo venue graph |
| Dashboard data accuracy | Compare dashboard metrics with database queries | 100% match |
| Audit trail completeness | Perform operator actions and verify all are logged | All P0 actions logged |
| Demo readiness | End-to-end demo executable without failures | Clean demo run |

**Note:** These are verification metrics for the prototype, not validated outcome measurements.

## 12. Future Roadmap

| Phase | Capability | Prerequisite |
|-------|-----------|-------------|
| Post-MVP 1 | Role-based access control with authentication | Security review |
| Post-MVP 2 | Real-time video stream support | Streaming infrastructure |
| Post-MVP 3 | Custom YOLO model fine-tuned for dense crowds | Training data and compute |
| Post-MVP 4 | Notification and alerting system | User preferences |
| Post-MVP 5 | Historical trend analytics | Sufficient data accumulation |
| Post-MVP 6 | Multi-venue support | Database schema extension |
| Post-MVP 7 | Mobile-responsive progressive web app | UI refactoring |
| Post-MVP 8 | Integration with external emergency systems | API partnerships |

---

*End of Document 02 — Product Requirements Document*
