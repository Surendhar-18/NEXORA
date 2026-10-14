# NEXORA — Requirement Traceability Matrix

**Document ID:** DOC-014  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. Product Goals → User Stories Mapping

| Product Goal | User Stories |
|-------------|-------------|
| PG-01: End-to-end workflow | US-001 through US-025 (complete workflow) |
| PG-02: Actionable crowd density info | US-005, US-006, US-007, US-008 |
| PG-03: Informed route decisions | US-013, US-014, US-015, US-016, US-017, US-018 |
| PG-04: Structured incident response | US-019, US-020, US-021, US-022, US-023 |
| PG-05: Transparency and accountability | US-011, US-022, US-023, US-024 |
| PG-06: Responsible AI use | US-009, US-010, US-011, US-012 |

## 2. User Stories → Functional Requirements

| User Story | Functional Requirements |
|-----------|------------------------|
| US-001 (Upload video) | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006 |
| US-002 (Processing status) | FR-007, FR-008, FR-009, FR-010, FR-012 |
| US-003 (Invalid upload rejection) | FR-002, FR-003, FR-006 |
| US-004 (Frame sampling config) | FR-013 |
| US-005 (Detection results) | FR-013, FR-014, FR-015, FR-016, FR-017 |
| US-006 (Evidence images) | FR-018, FR-019 |
| US-007 (Confidence scores) | FR-016, FR-017 |
| US-008 (Confidence filtering) | FR-016 |
| US-009 (Event generation) | FR-021, FR-022, FR-024, FR-025 |
| US-010 (Event review) | FR-026, FR-027 |
| US-011 (Event actions) | FR-028, FR-029, FR-030, FR-031 |
| US-012 (Sustained count) | FR-023 |
| US-013 (GIS map) | FR-032, FR-033, FR-034, FR-035, FR-036, FR-037 |
| US-014 (Route comparison) | FR-038, FR-039, FR-040, FR-041 |
| US-015 (Block walkway) | FR-042, FR-044 |
| US-016 (Reopen walkway) | FR-043, FR-044 |
| US-017 (No route message) | FR-045 |
| US-018 (Multiple routes) | FR-046 |
| US-019 (Create incident) | FR-047, FR-048 |
| US-020 (Assign resource) | FR-050, FR-054, FR-055, FR-056 |
| US-021 (Update status) | FR-049, FR-051 |
| US-022 (Incident history) | FR-051, FR-052 |
| US-023 (Audit trail) | FR-057, FR-058, FR-059 |
| US-024 (Dashboard) | FR-060, FR-061, FR-062 |
| US-025 (Analytics) | FR-063 |

## 3. Functional Requirements → UI Screens

| FR ID | UI Screen(s) |
|-------|-------------|
| FR-001 to FR-006 | Screen 2: VisionX Video Upload |
| FR-007 to FR-012 | Screen 3: Video Processing Details |
| FR-013 to FR-020 | Screen 4: Detection Timeline & Evidence |
| FR-021 to FR-025 | (Backend processing — no direct screen) |
| FR-026 to FR-027 | Screen 5: Event Review Queue, Screen 6: Event Details |
| FR-028 to FR-031 | Screen 6: Event Details |
| FR-032 to FR-037 | Screen 7: GIS Operations Map |
| FR-038 to FR-041 | Screen 8: Route Comparison Panel |
| FR-042 to FR-046 | Screen 8: Route Comparison Panel |
| FR-047 to FR-053 | Screen 9: Incident Management, Screen 10: Incident Details |
| FR-054 to FR-056 | Screen 11: Resource Management |
| FR-057 to FR-059 | Audit Trail view |
| FR-060 to FR-063 | Screen 1: Dashboard, Screen 12: Analytics |

## 4. Functional Requirements → API Endpoints

| FR ID | API Endpoint |
|-------|-------------|
| FR-001 to FR-006 | `POST /api/v1/videos/upload` |
| FR-007, FR-008, FR-010, FR-011 | `GET /api/v1/videos/jobs/{id}` |
| FR-009 | (Background processing — no direct endpoint) |
| FR-012 | `GET /api/v1/videos/jobs` |
| FR-013 to FR-020 | `GET /api/v1/videos/jobs/{id}/detections`, `GET /api/v1/evidence/...` |
| FR-021 to FR-025 | (Internal processing during job completion) |
| FR-026 | `GET /api/v1/events` |
| FR-027 | `GET /api/v1/events/{id}` |
| FR-028 to FR-031 | `PUT /api/v1/events/{id}/review` |
| FR-032 to FR-037 | `GET /api/v1/venue` |
| FR-038, FR-039, FR-041, FR-044, FR-045, FR-046 | `GET /api/v1/routes/compare` |
| FR-040 | (Frontend map rendering) |
| FR-042 | `PUT /api/v1/venue/edges/{id}/block` |
| FR-043 | `PUT /api/v1/venue/edges/{id}/reopen` |
| FR-047, FR-048 | `POST /api/v1/incidents` |
| FR-049, FR-051 | `PUT /api/v1/incidents/{id}/status` |
| FR-050 | `POST /api/v1/incidents/{id}/assign` |
| FR-052, FR-053 | `GET /api/v1/incidents/{id}`, `GET /api/v1/incidents` |
| FR-054 to FR-056 | `GET /api/v1/resources`, `POST /api/v1/incidents/{id}/assign` |
| FR-057 to FR-059 | `GET /api/v1/audit` |
| FR-060 to FR-062 | `GET /api/v1/dashboard/metrics` |
| FR-063 | `GET /api/v1/analytics` |

## 5. Functional Requirements → Database Entities

| FR ID | Database Table(s) |
|-------|------------------|
| FR-001 to FR-006 | `video_jobs` |
| FR-007 to FR-012 | `video_jobs` |
| FR-013 to FR-020 | `detection_results` |
| FR-021 to FR-025 | `crowd_events`, `detection_results` |
| FR-026 to FR-031 | `crowd_events`, `audit_log` |
| FR-032 to FR-037 | `venue_nodes`, `venue_edges` |
| FR-038 to FR-046 | `venue_nodes`, `venue_edges`, `audit_log` |
| FR-047 to FR-053 | `incidents`, `incident_history`, `audit_log` |
| FR-054 to FR-056 | `resources` |
| FR-057 to FR-059 | `audit_log` |
| FR-060 to FR-063 | (Aggregation across all tables) |

## 6. Functional Requirements → Implementation Modules

| FR ID | Backend Module | Frontend Module |
|-------|---------------|----------------|
| FR-001 to FR-006 | `routers/videos.py`, `services/video_service.py` | `pages/Upload.tsx` |
| FR-007 to FR-012 | `routers/videos.py`, `services/video_service.py` | `pages/JobDetail.tsx` |
| FR-013 to FR-020 | `visionx/frame_extractor.py`, `visionx/detector.py` | `pages/DetectionTimeline.tsx` |
| FR-021 to FR-025 | `visionx/crowd_rules.py`, `services/event_service.py` | — |
| FR-026 to FR-031 | `routers/events.py`, `services/event_service.py` | `pages/EventQueue.tsx`, `pages/EventDetail.tsx` |
| FR-032 to FR-037 | `routers/venue.py` | `pages/GISMap.tsx` |
| FR-038 to FR-046 | `routers/routes.py`, `services/routing_service.py` | `pages/RouteComparison.tsx` |
| FR-047 to FR-053 | `routers/incidents.py`, `services/incident_service.py` | `pages/IncidentList.tsx`, `pages/IncidentDetail.tsx` |
| FR-054 to FR-056 | `routers/resources.py` | `pages/Resources.tsx` |
| FR-057 to FR-059 | `routers/audit.py`, `services/audit_service.py` | `pages/AuditTrail.tsx` |
| FR-060 to FR-063 | `routers/analytics.py` | `pages/Dashboard.tsx`, `pages/Analytics.tsx` |

## 7. Functional Requirements → Test Cases

| FR ID | Test Case(s) |
|-------|-------------|
| FR-001 | TC-001 |
| FR-002 | TC-002, TC-004 |
| FR-003 | TC-003 |
| FR-004 | TC-023 |
| FR-005 | TC-001, TC-025 |
| FR-006 | TC-004 |
| FR-007, FR-008 | TC-005, TC-023 |
| FR-009 | TC-001 (background processing verified) |
| FR-010, FR-011 | TC-005 |
| FR-012 | TC-027 (health check verifies API) |
| FR-013 | TC-007 |
| FR-014 | TC-007 |
| FR-015 | TC-007, TC-008 |
| FR-016 | TC-008 |
| FR-017 | TC-023, TC-025 |
| FR-018, FR-019 | TC-025 |
| FR-020 | TC-006 |
| FR-021, FR-022 | TC-009, TC-010, TC-011 |
| FR-023 | TC-012 |
| FR-024 | TC-010 |
| FR-025 | (Content review — manual) |
| FR-026, FR-027 | TC-013 |
| FR-028, FR-029, FR-030 | TC-013, TC-014 |
| FR-031 | TC-024 |
| FR-032 to FR-037 | (Visual inspection — manual) |
| FR-038, FR-039 | TC-015 |
| FR-040, FR-041 | TC-015 (API portion) |
| FR-042 | TC-016 |
| FR-043 | TC-017 |
| FR-044 | TC-016, TC-017 |
| FR-045 | TC-018 |
| FR-046 | TC-015 |
| FR-047, FR-048 | TC-019 |
| FR-049 | TC-020, TC-021 |
| FR-050 | TC-022 |
| FR-051, FR-052 | TC-020 |
| FR-053 | TC-019 |
| FR-054, FR-055 | TC-022 |
| FR-056 | TC-022 |
| FR-057, FR-058, FR-059 | TC-024 |
| FR-060, FR-061, FR-062 | TC-026 |
| FR-063 | TC-026 (analytics portion) |

## 8. P0 Requirements — Complete Traceability

Every P0 requirement has:

| P0 Feature | PRD Story | SRS FR | UI Screen | API Endpoint | DB Table | Test Case | Status |
|-----------|----------|--------|-----------|-------------|----------|-----------|--------|
| Video upload | US-001 | FR-001 | Screen 2 | POST /videos/upload | video_jobs | TC-001 | Planned |
| Upload validation | US-003 | FR-002,003 | Screen 2 | POST /videos/upload | — | TC-002,003 | Planned |
| Job management | US-002 | FR-007,008 | Screen 3 | GET /videos/jobs/{id} | video_jobs | TC-005 | Planned |
| Frame extraction | US-005 | FR-013 | Screen 4 | GET /jobs/{id}/detections | detection_results | TC-007 | Planned |
| YOLO detection | US-005 | FR-014,015 | Screen 4 | GET /jobs/{id}/detections | detection_results | TC-007 | Planned |
| Evidence images | US-006 | FR-018,019 | Screen 4 | GET /evidence/... | detection_results | TC-025 | Planned |
| Threshold rules | US-009 | FR-021,022 | — | — | crowd_events | TC-009,010,011 | Planned |
| Event review | US-011 | FR-028-031 | Screen 6 | PUT /events/{id}/review | crowd_events, audit_log | TC-013,014 | Planned |
| GIS map | US-013 | FR-032-037 | Screen 7 | GET /venue | venue_nodes, venue_edges | Manual | Planned |
| Route calc | US-014 | FR-038-041 | Screen 8 | GET /routes/compare | venue_nodes, venue_edges | TC-015 | Planned |
| Block walkway | US-015 | FR-042 | Screen 8 | PUT /edges/{id}/block | venue_edges, audit_log | TC-016 | Planned |
| Reopen walkway | US-016 | FR-043 | Screen 8 | PUT /edges/{id}/reopen | venue_edges, audit_log | TC-017 | Planned |
| No route | US-017 | FR-045 | Screen 8 | GET /routes/compare | — | TC-018 | Planned |
| Create incident | US-019 | FR-047,048 | Screen 9 | POST /incidents | incidents, history, audit | TC-019 | Planned |
| Assign resource | US-020 | FR-050,054-056 | Screen 10 | POST /incidents/{id}/assign | resources, incidents | TC-022 | Planned |
| Update status | US-021 | FR-049 | Screen 10 | PUT /incidents/{id}/status | incidents, history | TC-020,021 | Planned |
| Incident history | US-022 | FR-051,052 | Screen 10 | GET /incidents/{id} | incident_history | TC-020 | Planned |
| Audit trail | US-023 | FR-057-059 | Audit view | GET /audit | audit_log | TC-024 | Planned |
| Dashboard | US-024 | FR-060-062 | Screen 1 | GET /dashboard/metrics | All tables | TC-026 | Planned |

---

*End of Document 14 — Requirement Traceability Matrix*
