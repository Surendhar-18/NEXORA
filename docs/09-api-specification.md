# NEXORA — API Specification

**Document ID:** DOC-009  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. API Overview

**Base URL:** `http://localhost:8000/api/v1`  
**Content Type:** `application/json` (except file uploads: `multipart/form-data`)  
**Authentication:** Simulated (not enforced in MVP). `X-Operator` header used for audit attribution.  
**Error Format:** Consistent JSON error responses (see Section 3).

## 2. Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | `application/json` or `multipart/form-data` |
| `X-Operator` | No | Operator identifier for audit logging (default: "operator") |

## 3. Error Response Format

All error responses follow this structure:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human-readable error description",
        "details": [
            {
                "field": "file_size",
                "message": "File exceeds maximum size of 500 MB"
            }
        ]
    }
}
```

### Standard Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | BAD_REQUEST | Invalid request format |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | State conflict (e.g., resource already assigned) |
| 413 | PAYLOAD_TOO_LARGE | File exceeds size limit |
| 415 | UNSUPPORTED_MEDIA_TYPE | Invalid file type |
| 422 | VALIDATION_ERROR | Pydantic validation failure |
| 500 | INTERNAL_ERROR | Unexpected server error (details logged, not exposed) |

---

## 4. Endpoints

### 4.1 Health Check

#### `GET /api/v1/health`

**Purpose:** Verify the API server is running and dependencies are accessible.  
**Permission:** Public.  
**Persistence:** None.

**Response 200:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected",
    "model_available": true,
    "timestamp": "2026-10-09T14:30:00Z"
}
```

---

### 4.2 Video Upload

#### `POST /api/v1/videos/upload`

**Purpose:** Upload a prerecorded video file for crowd analysis.  
**Permission:** Operator.  
**Content-Type:** `multipart/form-data`  
**Persistence:** Creates `video_jobs` record; saves file to storage.

**Request:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `file` | File | Yes | MP4, AVI, MOV, MKV; ≤500 MB |
| `zone_id` | string | No | Must match configured zone ID |
| `sampling_interval` | float | No | 0.5–30.0 (default: 2.0) |
| `confidence_threshold` | float | No | 0.1–1.0 (default: 0.5) |

**Response 201:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "original_filename": "festival_main_gate.mp4",
    "file_size_bytes": 47185920,
    "file_type": "mp4",
    "zone_id": "zone_main_gate",
    "status": "queued",
    "sampling_interval_sec": 2.0,
    "confidence_threshold": 0.5,
    "created_at": "2026-10-09T14:30:00Z",
    "message": "Video uploaded successfully. Processing will begin shortly."
}
```

**Error Responses:**
- `413` — File exceeds 500 MB limit.
- `415` — Unsupported file type.
- `422` — Invalid sampling_interval or confidence_threshold.

---

### 4.3 Job Listing

#### `GET /api/v1/videos/jobs`

**Purpose:** List all video processing jobs with optional filtering.  
**Permission:** Operator.  
**Persistence:** None (read-only).

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: queued, processing, completed, failed |
| `zone_id` | string | No | Filter by zone |
| `limit` | int | No | Max results (default: 50, max: 100) |
| `offset` | int | No | Pagination offset (default: 0) |

**Response 200:**
```json
{
    "jobs": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "original_filename": "festival_main_gate.mp4",
            "zone_id": "zone_main_gate",
            "status": "completed",
            "total_frames_extracted": 150,
            "max_person_count": 78,
            "created_at": "2026-10-09T14:30:00Z",
            "completed_at": "2026-10-09T14:31:15Z"
        }
    ],
    "total": 5,
    "limit": 50,
    "offset": 0
}
```

---

### 4.4 Job Details

#### `GET /api/v1/videos/jobs/{job_id}`

**Purpose:** Get detailed information about a specific job.  
**Permission:** Operator.  
**Persistence:** None.

**Response 200:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "original_filename": "festival_main_gate.mp4",
    "file_size_bytes": 47185920,
    "file_type": "mp4",
    "zone_id": "zone_main_gate",
    "status": "completed",
    "sampling_interval_sec": 2.0,
    "confidence_threshold": 0.5,
    "model_name": "yolov8n",
    "total_frames_extracted": 150,
    "total_persons_detected": 4250,
    "max_person_count": 78,
    "avg_person_count": 28.3,
    "processing_duration_sec": 45.2,
    "error_message": null,
    "created_at": "2026-10-09T14:30:00Z",
    "started_at": "2026-10-09T14:30:01Z",
    "completed_at": "2026-10-09T14:31:15Z",
    "events_generated": 2
}
```

**Error:** `404` — Job not found.

---

### 4.5 Detection Results

#### `GET /api/v1/videos/jobs/{job_id}/detections`

**Purpose:** Get frame-by-frame detection results for a job.  
**Permission:** Operator.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `min_count` | int | No | Only frames with count ≥ value |
| `limit` | int | No | Max results (default: 200) |
| `offset` | int | No | Pagination offset |

**Response 200:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440001",
    "total_frames": 150,
    "summary": {
        "max_count": 78,
        "min_count": 5,
        "avg_count": 28.3,
        "total_detections": 4250
    },
    "detections": [
        {
            "id": "det-001",
            "frame_index": 0,
            "timestamp_sec": 0.0,
            "person_count": 23,
            "avg_confidence": 0.78,
            "evidence_image_url": "/api/v1/evidence/550e8400-.../frame_000000.jpg"
        }
    ],
    "limit": 200,
    "offset": 0
}
```

---

### 4.6 Evidence Image

#### `GET /api/v1/evidence/{job_id}/{filename}`

**Purpose:** Serve an annotated evidence image.  
**Permission:** Operator.  
**Content-Type:** `image/jpeg`

**Validation:** Job must exist. Filename must match pattern `frame_\d{6}\.(jpg|png)`.

**Response 200:** Binary image data.  
**Error:** `404` — Image not found or job does not exist.

---

### 4.7 Event Listing

#### `GET /api/v1/events`

**Purpose:** List crowd events with optional filtering.  
**Permission:** Operator.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | pending_review, acknowledged, dismissed, escalated |
| `zone_id` | string | No | Filter by zone |
| `severity` | string | No | low, medium, high, critical |
| `limit` | int | No | Default: 50 |
| `offset` | int | No | Default: 0 |

**Response 200:**
```json
{
    "events": [
        {
            "id": "evt-001",
            "job_id": "550e8400-...",
            "zone_id": "zone_main_gate",
            "rule_type": "threshold",
            "person_count": 78,
            "severity": "high",
            "status": "pending_review",
            "description": "High person count detected: 78 persons (threshold: 50)",
            "frame_timestamp_sec": 64.0,
            "evidence_image_url": "/api/v1/evidence/550e8400-.../frame_000032.jpg",
            "created_at": "2026-10-09T14:31:15Z"
        }
    ],
    "total": 3,
    "limit": 50,
    "offset": 0
}
```

---

### 4.8 Event Details

#### `GET /api/v1/events/{event_id}`

**Purpose:** Get detailed information about a specific event.  
**Permission:** Operator.

**Response 200:**
```json
{
    "id": "evt-001",
    "job_id": "550e8400-...",
    "detection_id": "det-032",
    "zone_id": "zone_main_gate",
    "rule_type": "sustained",
    "person_count": 78,
    "threshold_value": 50,
    "sustained_frames": 5,
    "severity": "high",
    "status": "pending_review",
    "description": "Sustained high person count: 78 persons over 5 consecutive frames (threshold: 50)",
    "evidence_image_url": "/api/v1/evidence/550e8400-.../frame_000032.jpg",
    "frame_timestamp_sec": 64.0,
    "reviewed_by": null,
    "reviewed_at": null,
    "review_notes": null,
    "created_at": "2026-10-09T14:31:15Z",
    "video_filename": "festival_main_gate.mp4",
    "has_incident": false
}
```

---

### 4.9 Event Review

#### `PUT /api/v1/events/{event_id}/review`

**Purpose:** Record an operator's review decision on an event.  
**Permission:** Operator.  
**Persistence:** Updates `crowd_events` status; creates `audit_log` entry.

**Request:**
```json
{
    "action": "acknowledge",
    "notes": "Verified — crowd is dense but moving steadily."
}
```

**Validation:**
- `action`: Required. One of: `acknowledge`, `dismiss`, `escalate`.
- `notes`: Optional string.
- Event must be in `pending_review` status.

**Response 200:**
```json
{
    "id": "evt-001",
    "status": "acknowledged",
    "reviewed_by": "operator",
    "reviewed_at": "2026-10-09T14:35:00Z",
    "review_notes": "Verified — crowd is dense but moving steadily.",
    "message": "Event acknowledged successfully."
}
```

**Error:**
- `404` — Event not found.
- `409` — Event already reviewed (not in pending_review status).
- `422` — Invalid action value.

---

### 4.10 Venue Retrieval

#### `GET /api/v1/venue`

**Purpose:** Get the complete venue configuration (zones, nodes, edges, cameras).  
**Permission:** Operator.

**Response 200:**
```json
{
    "venue_name": "Demo Festival Grounds",
    "center": { "latitude": 25.4358, "longitude": 81.8463 },
    "zoom_level": 16,
    "zones": [
        {
            "id": "zone_main_gate",
            "name": "Main Gate Area",
            "polygon": [[25.436, 81.846], [25.437, 81.846], [25.437, 81.847], [25.436, 81.847]],
            "color": "#3B82F6",
            "cameras": ["cam_01", "cam_02"]
        }
    ],
    "nodes": [
        {
            "id": "junction_1",
            "name": "Main Junction",
            "type": "junction",
            "latitude": 25.4362,
            "longitude": 81.8465
        }
    ],
    "edges": [
        {
            "id": "walk_1_2",
            "from_node": "junction_1",
            "to_node": "junction_2",
            "name": "Main Walkway",
            "distance_meters": 120.0,
            "is_blocked": false,
            "congestion_penalty": 0,
            "hazard_penalty": 0
        }
    ],
    "cameras": [
        {
            "id": "cam_01",
            "name": "Camera 1 — Main Gate",
            "latitude": 25.4361,
            "longitude": 81.8464,
            "zone_id": "zone_main_gate"
        }
    ]
}
```

---

### 4.11 Route Comparison

#### `GET /api/v1/routes/compare`

**Purpose:** Calculate and compare routes between two venue nodes.  
**Permission:** Operator.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_node` | string | Yes | Source node ID |
| `to_node` | string | Yes | Destination node ID |
| `max_routes` | int | No | Maximum alternatives (default: 3) |

**Response 200 (routes found):**
```json
{
    "from_node": "junction_1",
    "to_node": "exit_north",
    "routes_found": 2,
    "routes": [
        {
            "rank": 1,
            "is_best": true,
            "path": ["junction_1", "junction_3", "exit_north"],
            "total_cost": 450.0,
            "distance_meters": 420.0,
            "congestion_penalty": 20.0,
            "hazard_penalty": 10.0,
            "segments": [
                {
                    "from": "junction_1",
                    "to": "junction_3",
                    "edge_id": "walk_1_3",
                    "distance": 250.0,
                    "congestion": 10.0,
                    "hazard": 5.0
                },
                {
                    "from": "junction_3",
                    "to": "exit_north",
                    "edge_id": "walk_3_exit_n",
                    "distance": 170.0,
                    "congestion": 10.0,
                    "hazard": 5.0
                }
            ]
        },
        {
            "rank": 2,
            "is_best": false,
            "path": ["junction_1", "junction_2", "junction_4", "exit_north"],
            "total_cost": 570.0,
            "distance_meters": 520.0,
            "congestion_penalty": 30.0,
            "hazard_penalty": 20.0,
            "segments": []
        }
    ],
    "blocked_edges": ["walk_2_5"]
}
```

**Response 200 (no route found):**
```json
{
    "from_node": "junction_1",
    "to_node": "exit_south",
    "routes_found": 0,
    "routes": [],
    "blocked_edges": ["walk_1_5", "walk_3_7"],
    "message": "No valid route exists between junction_1 and exit_south. Some walkways may be blocked."
}
```

**Error:**
- `404` — Node not found.
- `422` — Missing or same from_node/to_node.

---

### 4.12 Walkway Block

#### `PUT /api/v1/venue/edges/{edge_id}/block`

**Purpose:** Block a walkway, removing it from route eligibility.  
**Permission:** Operator.  
**Persistence:** Updates `venue_edges` record; creates `audit_log` entry.

**Request:**
```json
{
    "reason": "Structural concern reported"
}
```

**Response 200:**
```json
{
    "id": "walk_1_2",
    "name": "Main Walkway",
    "is_blocked": true,
    "blocked_at": "2026-10-09T14:40:00Z",
    "blocked_by": "operator",
    "message": "Walkway blocked successfully. Route calculations will exclude this walkway."
}
```

**Error:**
- `404` — Edge not found.
- `409` — Edge already blocked.

---

### 4.13 Walkway Reopen

#### `PUT /api/v1/venue/edges/{edge_id}/reopen`

**Purpose:** Reopen a blocked walkway, restoring route eligibility.  
**Permission:** Operator.  
**Persistence:** Updates `venue_edges` record; creates `audit_log` entry.

**Response 200:**
```json
{
    "id": "walk_1_2",
    "name": "Main Walkway",
    "is_blocked": false,
    "message": "Walkway reopened successfully."
}
```

**Error:**
- `404` — Edge not found.
- `409` — Edge not currently blocked.

---

### 4.14 Incident Creation

#### `POST /api/v1/incidents`

**Purpose:** Create an incident from a reviewed event (or independently).  
**Permission:** Operator.  
**Persistence:** Creates `incidents`, `incident_history`, and `audit_log` records.

**Request:**
```json
{
    "title": "High crowd density at Main Gate",
    "description": "Sustained high person count detected. Visual verification confirms dense crowd.",
    "zone_id": "zone_main_gate",
    "event_id": "evt-001",
    "priority": "high"
}
```

**Validation:**
- `title`: Required, 5–200 characters.
- `priority`: Required. One of: low, medium, high, critical.
- `event_id`: Optional. If provided, must exist and be in acknowledged or escalated status.
- `zone_id`: Optional. Must match configured zone.

**Response 201:**
```json
{
    "id": "inc-001",
    "title": "High crowd density at Main Gate",
    "zone_id": "zone_main_gate",
    "event_id": "evt-001",
    "priority": "high",
    "status": "open",
    "created_by": "operator",
    "created_at": "2026-10-09T14:45:00Z",
    "message": "Incident created successfully."
}
```

**Error:**
- `409` — Event already has an associated incident.
- `422` — Validation failure.

---

### 4.15 Incident Listing

#### `GET /api/v1/incidents`

**Purpose:** List incidents with filtering.  
**Permission:** Operator.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | open, responding, resolved, closed |
| `priority` | string | No | low, medium, high, critical |
| `zone_id` | string | No | Filter by zone |
| `limit` | int | No | Default: 50 |
| `offset` | int | No | Default: 0 |

**Response 200:**
```json
{
    "incidents": [
        {
            "id": "inc-001",
            "title": "High crowd density at Main Gate",
            "zone_id": "zone_main_gate",
            "priority": "high",
            "status": "open",
            "event_id": "evt-001",
            "assigned_resource": null,
            "created_at": "2026-10-09T14:45:00Z",
            "updated_at": "2026-10-09T14:45:00Z"
        }
    ],
    "total": 2,
    "limit": 50,
    "offset": 0
}
```

---

### 4.16 Incident Details

#### `GET /api/v1/incidents/{incident_id}`

**Purpose:** Get full incident details with history and assignments.  
**Permission:** Operator.

**Response 200:**
```json
{
    "id": "inc-001",
    "title": "High crowd density at Main Gate",
    "description": "Sustained high person count detected...",
    "zone_id": "zone_main_gate",
    "event_id": "evt-001",
    "priority": "high",
    "status": "responding",
    "assigned_resource": {
        "id": "res-001",
        "name": "Medical Team Alpha",
        "type": "medical"
    },
    "created_by": "operator",
    "created_at": "2026-10-09T14:45:00Z",
    "updated_at": "2026-10-09T14:48:00Z",
    "resolved_at": null,
    "history": [
        {
            "id": "hist-001",
            "action": "created",
            "new_value": "open",
            "performed_by": "operator",
            "created_at": "2026-10-09T14:45:00Z"
        },
        {
            "id": "hist-002",
            "action": "resource_assigned",
            "new_value": "Medical Team Alpha",
            "performed_by": "operator",
            "created_at": "2026-10-09T14:46:00Z"
        },
        {
            "id": "hist-003",
            "action": "status_changed",
            "old_value": "open",
            "new_value": "responding",
            "performed_by": "operator",
            "created_at": "2026-10-09T14:48:00Z"
        }
    ]
}
```

---

### 4.17 Incident Status Update

#### `PUT /api/v1/incidents/{incident_id}/status`

**Purpose:** Update incident status.  
**Permission:** Operator.  
**Persistence:** Updates `incidents`, creates `incident_history` and `audit_log` entries.

**Request:**
```json
{
    "status": "responding",
    "notes": "Medical team dispatched to Main Gate."
}
```

**Validation:**
- Valid transitions: open→responding, responding→resolved, resolved→closed.
- Invalid transitions are rejected.

**Response 200:**
```json
{
    "id": "inc-001",
    "status": "responding",
    "updated_at": "2026-10-09T14:48:00Z",
    "message": "Incident status updated to responding."
}
```

**Error:**
- `409` — Invalid status transition (e.g., open→closed).

---

### 4.18 Resource Assignment

#### `POST /api/v1/incidents/{incident_id}/assign`

**Purpose:** Assign a resource to an incident.  
**Permission:** Operator.  
**Persistence:** Updates `resources` and `incidents`; creates `incident_history` and `audit_log`.

**Request:**
```json
{
    "resource_id": "res-001"
}
```

**Validation:**
- Resource must exist and be in "available" status.
- Incident must be in "open" or "responding" status.

**Response 200:**
```json
{
    "incident_id": "inc-001",
    "resource_id": "res-001",
    "resource_name": "Medical Team Alpha",
    "message": "Resource assigned successfully."
}
```

**Error:**
- `409` — Resource already assigned to another incident.
- `404` — Resource or incident not found.

---

### 4.19 Resource Listing

#### `GET /api/v1/resources`

**Purpose:** List all response resources.  
**Permission:** Operator.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | available, assigned, unavailable |
| `type` | string | No | medical, security, fire, logistics |

**Response 200:**
```json
{
    "resources": [
        {
            "id": "res-001",
            "name": "Medical Team Alpha",
            "resource_type": "medical",
            "status": "assigned",
            "assigned_incident_id": "inc-001",
            "description": "First-aid team with stretcher and defibrillator"
        }
    ],
    "total": 8,
    "available": 5,
    "assigned": 2,
    "unavailable": 1
}
```

---

### 4.20 Audit Trail

#### `GET /api/v1/audit`

**Purpose:** Retrieve audit log entries.  
**Permission:** Operator.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | No | video_job, event, incident, edge, resource |
| `entity_id` | string | No | Specific entity ID |
| `action` | string | No | Specific action type |
| `from_date` | string | No | ISO 8601 start date |
| `to_date` | string | No | ISO 8601 end date |
| `limit` | int | No | Default: 100 |
| `offset` | int | No | Default: 0 |

**Response 200:**
```json
{
    "entries": [
        {
            "id": "aud-001",
            "action": "video_uploaded",
            "entity_type": "video_job",
            "entity_id": "550e8400-...",
            "operator": "operator",
            "details": {"filename": "festival_main_gate.mp4", "zone": "zone_main_gate"},
            "created_at": "2026-10-09T14:30:00Z"
        }
    ],
    "total": 25,
    "limit": 100,
    "offset": 0
}
```

---

### 4.21 Dashboard Metrics

#### `GET /api/v1/dashboard/metrics`

**Purpose:** Get aggregated dashboard metrics from persisted data.  
**Permission:** Operator.

**Response 200:**
```json
{
    "videos_processed": 5,
    "videos_processing": 1,
    "active_incidents": 2,
    "pending_events": 3,
    "total_detections": 12500,
    "resources_available": 5,
    "resources_assigned": 2,
    "recent_events": [
        {
            "id": "evt-001",
            "zone_id": "zone_main_gate",
            "severity": "high",
            "status": "pending_review",
            "person_count": 78,
            "created_at": "2026-10-09T14:31:15Z"
        }
    ],
    "detection_timeline": [
        {"timestamp": "2026-10-09T14:30:02Z", "count": 23},
        {"timestamp": "2026-10-09T14:30:04Z", "count": 31}
    ],
    "incident_summary": {
        "open": 1,
        "responding": 1,
        "resolved": 2,
        "closed": 3
    },
    "computed_at": "2026-10-09T14:55:00Z"
}
```

**Note:** All values are computed from database queries at request time. No values are hardcoded.

---

### 4.22 Analytics

#### `GET /api/v1/analytics`

**Purpose:** Get detailed analytics data for charts and reports.  
**Permission:** Operator.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_date` | string | No | ISO 8601 start date |
| `to_date` | string | No | ISO 8601 end date |

**Response 200:**
```json
{
    "period": {
        "from": "2026-10-09T00:00:00Z",
        "to": "2026-10-09T23:59:59Z"
    },
    "processing_summary": {
        "total_jobs": 6,
        "completed": 5,
        "failed": 1,
        "total_frames": 750,
        "total_detections": 12500
    },
    "events_by_status": {
        "pending_review": 3,
        "acknowledged": 5,
        "dismissed": 2,
        "escalated": 2
    },
    "events_by_severity": {
        "low": 1,
        "medium": 4,
        "high": 5,
        "critical": 2
    },
    "incidents_by_priority": {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 1
    },
    "detection_counts_over_time": [
        {"timestamp": "2026-10-09T14:30:00Z", "count": 23, "job_id": "..."}
    ]
}
```

---

## 5. API Consistency Notes

- All list endpoints support `limit`/`offset` pagination.
- All timestamps are ISO 8601 in UTC.
- All IDs are UUIDs (string format) or configured identifiers (venue nodes/edges).
- All mutation endpoints create corresponding `audit_log` entries.
- All error responses use the standard error format.
- Evidence image URLs are relative API paths, not filesystem paths.
- The `X-Operator` header is used for audit attribution in all mutation endpoints.

---

*End of Document 09 — API Specification*
