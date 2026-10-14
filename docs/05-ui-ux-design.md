# NEXORA — UI/UX Design Specification

**Document ID:** DOC-005  
**Version:** 1.0  
**Status:** Draft  
**Created:** 2026-10-09  
**Last Updated:** 2026-10-09  

---

## 1. Design Philosophy

NEXORA's interface follows a **command-centre design paradigm** — a professional, information-dense dashboard suitable for emergency operations contexts. The design prioritises:

- **Clarity:** Critical information visible at a glance without cognitive overload.
- **Trust:** Consistent status indicators, evidence-backed data, and explicit confirmation dialogs.
- **Efficiency:** Minimal clicks from alert to action; cross-linked navigation between modules.
- **Professionalism:** Clean, modern aesthetics appropriate for a safety-critical context.

## 2. Design System

### 2.1 Colour Tokens

#### Core Palette
| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#1E3A5F` | Primary navy — sidebar, headers |
| `--color-primary-light` | `#2A5080` | Primary hover states |
| `--color-primary-dark` | `#142A45` | Primary active/pressed states |
| `--color-secondary` | `#00B4D8` | Accent cyan — highlights, links, active indicators |
| `--color-secondary-light` | `#48CAE4` | Secondary hover |
| `--color-bg-primary` | `#F8F9FA` | Main background (light grey) |
| `--color-bg-surface` | `#FFFFFF` | Card/panel surfaces |
| `--color-bg-sidebar` | `#0F1B2D` | Sidebar dark background |
| `--color-text-primary` | `#1A1A2E` | Primary body text |
| `--color-text-secondary` | `#6C757D` | Secondary/muted text |
| `--color-text-inverse` | `#FFFFFF` | Text on dark backgrounds |
| `--color-border` | `#DEE2E6` | Default borders |
| `--color-border-focus` | `#00B4D8` | Focus ring colour |

#### Status Colours
| Token | Value | Usage |
|-------|-------|-------|
| `--color-status-critical` | `#DC2626` | Critical severity, errors |
| `--color-status-high` | `#EA580C` | High severity, warnings |
| `--color-status-medium` | `#D97706` | Medium severity |
| `--color-status-low` | `#2563EB` | Low severity, info |
| `--color-status-success` | `#16A34A` | Success states, resolved |
| `--color-status-pending` | `#9333EA` | Pending/awaiting review |
| `--color-status-processing` | `#0891B2` | In-progress states |
| `--color-status-neutral` | `#6B7280` | Inactive, closed, dismissed |

#### Map Colours
| Token | Value | Usage |
|-------|-------|-------|
| `--color-zone-default` | `#3B82F6` with 20% opacity | Default zone fill |
| `--color-zone-alert` | `#EF4444` with 30% opacity | Zone with active event |
| `--color-route-primary` | `#16A34A` | Best route |
| `--color-route-alt` | `#D97706` | Alternative route |
| `--color-walkway-open` | `#6B7280` | Open walkway |
| `--color-walkway-blocked` | `#DC2626` | Blocked walkway (dashed) |
| `--color-exit` | `#16A34A` | Exit markers |
| `--color-camera` | `#8B5CF6` | Camera markers |

### 2.2 Typography

| Token | Font | Weight | Size | Line Height | Usage |
|-------|------|--------|------|-------------|-------|
| `--font-family` | `'Inter', system-ui, sans-serif` | — | — | — | All text |
| `--text-display` | Inter | 700 | 28px | 1.2 | Page titles |
| `--text-heading-1` | Inter | 600 | 22px | 1.3 | Section headings |
| `--text-heading-2` | Inter | 600 | 18px | 1.3 | Card titles |
| `--text-heading-3` | Inter | 500 | 16px | 1.4 | Subsection titles |
| `--text-body` | Inter | 400 | 14px | 1.5 | Body text |
| `--text-body-sm` | Inter | 400 | 13px | 1.5 | Secondary text, captions |
| `--text-caption` | Inter | 400 | 12px | 1.4 | Labels, metadata |
| `--text-code` | `'JetBrains Mono', monospace` | 400 | 13px | 1.5 | IDs, technical values |

### 2.3 Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight internal padding |
| `--space-2` | 8px | Compact spacing |
| `--space-3` | 12px | Default internal padding |
| `--space-4` | 16px | Standard padding |
| `--space-5` | 20px | Section spacing |
| `--space-6` | 24px | Card padding |
| `--space-8` | 32px | Page section gaps |
| `--space-10` | 40px | Major section separation |
| `--space-12` | 48px | Page margins |

### 2.4 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Small elements (badges, chips) |
| `--radius-md` | 8px | Cards, panels, inputs |
| `--radius-lg` | 12px | Modal windows, large panels |
| `--radius-full` | 9999px | Circular elements (avatars, dots) |

### 2.5 Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle card elevation |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | Standard card elevation |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modal elevation |
| `--shadow-sidebar` | `2px 0 8px rgba(0,0,0,0.15)` | Sidebar shadow |

### 2.6 Transitions

| Token | Value | Usage |
|-------|-------|-------|
| `--transition-fast` | `150ms ease` | Hover states, small elements |
| `--transition-normal` | `250ms ease` | Most interactions |
| `--transition-slow` | `400ms ease` | Page transitions, large elements |

## 3. Layout Structure

### 3.1 Global Layout

```
┌──────────────────────────────────────────────────────┐
│ Top Bar (56px height)                                │
├────────┬─────────────────────────────────────────────┤
│        │                                             │
│ Side-  │  Main Content Area                          │
│ bar    │  (scrollable)                               │
│ (240px)│                                             │
│        │                                             │
│ Fixed  │                                             │
│ Left   │                                             │
│        │                                             │
└────────┴─────────────────────────────────────────────┘
```

### 3.2 Sidebar Design

**Desktop (≥1024px):** Fixed left sidebar, 240px wide.

- **Top section:** NEXORA logo + "VisionX" sub-brand
- **Navigation items:** Icon + label, grouped by module
  - Dashboard (grid icon)
  - VisionX section:
    - Upload Video (upload-cloud icon)
    - Processing Jobs (loader icon)
    - Detection Results (eye icon)
  - Events section:
    - Event Queue (alert-triangle icon)
  - GIS Operations section:
    - Venue Map (map icon)
    - Route Comparison (route icon)
  - Incidents section:
    - Incident List (shield-alert icon)
    - Resources (users icon)
  - System section:
    - Audit Trail (scroll-text icon)
    - Settings (settings icon)
- **Active state:** Left border accent (--color-secondary), lighter background
- **Hover state:** Subtle background change
- **Badge indicators:** Pending event count on Event Queue, active incident count on Incidents

**Tablet (768px–1023px):** Collapsible sidebar, icon-only by default (64px), expands on hover/toggle.

### 3.3 Top Bar Design

- **Left:** Hamburger menu (tablet) or breadcrumb trail (desktop)
- **Centre:** Current page title
- **Right:**
  - Notification bell with count badge
  - Operator name/avatar (simulated)
  - System status indicator (green dot = healthy)

## 4. Screen Specifications

### 4.1 Screen 1: Dashboard / Overview

**Purpose:** Provide at-a-glance situational awareness.  
**Target User:** Operator, Commander.  
**Data Sources:** `/api/v1/dashboard/metrics`, `/api/v1/events`, `/api/v1/incidents`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Dashboard                                      │
├──────────┬──────────┬──────────┬───────────────┤
│ Metric   │ Metric   │ Metric   │ Metric        │
│ Card 1   │ Card 2   │ Card 3   │ Card 4        │
│ Videos   │ Active   │ Pending  │ Resources     │
│ Processed│ Incidents│ Events   │ Available     │
├──────────┴──────────┼──────────┴───────────────┤
│ Detection Count     │ Recent Events            │
│ Timeline Chart      │ (Card list)              │
│ (Recharts area)     │                          │
│                     │                          │
├─────────────────────┼──────────────────────────┤
│ Incident Summary    │ Quick Actions            │
│ (By status/priority)│ - Upload Video           │
│                     │ - View Map               │
│                     │ - Review Events          │
└─────────────────────┴──────────────────────────┘
```

**Components:**
- **Metric Cards (4):** Large number, label, trend arrow (if applicable), icon. Background colour based on status.
- **Detection Timeline Chart:** Recharts AreaChart showing person counts over time from recent completed jobs.
- **Recent Events List:** Top 5 pending or recent events with severity badge, zone, timestamp.
- **Incident Summary:** Donut chart or bar chart showing incidents by status.
- **Quick Actions:** Button group for common tasks.

**Information Displayed:**
- Total videos processed (count from DB)
- Active incidents (status: open or responding)
- Pending events (status: pending_review)
- Available resources (status: available)
- Person count timeline from latest completed job
- 5 most recent events
- Incident distribution by status

**User Actions:** Click metric card → navigate to relevant section. Click event → event detail. Click quick action → navigate.

**Loading State:** Skeleton loaders for each card and chart area.  
**Empty State:** "Welcome to NEXORA. Upload your first video to get started." with prominent upload CTA.  
**Error State:** Individual card error indicators with retry buttons.

### 4.2 Screen 2: VisionX Video Upload

**Purpose:** Upload prerecorded video for analysis.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/videos/upload`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Upload Video for Analysis                      │
├────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────┐   │
│ │                                          │   │
│ │     Drag & drop area                     │   │
│ │     (dashed border, upload icon)         │   │
│ │     "Drop video file or click to browse" │   │
│ │     Supported: MP4, AVI, MOV, MKV        │   │
│ │     Max size: 500 MB                     │   │
│ │                                          │   │
│ └──────────────────────────────────────────┘   │
│                                                │
│ Processing Options                             │
│ ┌─────────────────┐ ┌────────────────────┐     │
│ │ Frame Sampling  │ │ Confidence         │     │
│ │ Interval: [2s]  │ │ Threshold: [0.5]   │     │
│ └─────────────────┘ └────────────────────┘     │
│                                                │
│ Zone Assignment                                │
│ ┌────────────────────────────────────────┐     │
│ │ Select Zone: [dropdown]                │     │
│ └────────────────────────────────────────┘     │
│                                                │
│               [Upload & Analyse]               │
├────────────────────────────────────────────────┤
│ Recent Uploads                                 │
│ ┌──────┬──────┬──────┬──────┬────────┐         │
│ │ Name │ Zone │ Date │Status│ Action │         │
│ │ ...  │ ...  │ ...  │ ...  │ View   │         │
│ └──────┴──────┴──────┴──────┴────────┘         │
└────────────────────────────────────────────────┘
```

**Components:**
- **Drag-and-drop zone:** Large dropzone with dashed border, click-to-browse fallback.
- **File preview:** Once selected, shows filename, size, type, thumbnail (if extractable).
- **Processing options:** Numeric inputs for frame interval and confidence threshold.
- **Zone selector:** Dropdown populated from venue configuration.
- **Upload button:** Primary button, disabled until file is selected.
- **Recent uploads table:** Compact table of recent jobs with status badges.

**Validation Rules:**
- File type: MP4, AVI, MOV, MKV only.
- File size: ≤ 500 MB.
- Frame interval: 0.5–30 seconds.
- Confidence threshold: 0.1–1.0.
- Zone: Required selection.

**Loading State:** Upload progress bar with percentage.  
**Empty State:** "No videos uploaded yet. Select a file to begin."  
**Error State:** Red border on dropzone with error message (e.g., "Unsupported format").  
**Success State:** Green toast: "Video uploaded successfully. Processing started." + redirect to job detail.

### 4.3 Screen 3: Video Processing Details

**Purpose:** Monitor the status and progress of a video processing job.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/videos/jobs/{id}`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ ← Back to Jobs   Processing Job #JOB-xxx       │
├────────────────────────────────────────────────┤
│ Status: [Processing ●]   Zone: [Main Gate]     │
│ Started: 2026-10-09 14:30:22                   │
│ Duration: 2m 34s (running)                     │
├────────────────────────────────────────────────┤
│ Progress                                       │
│ ████████████░░░░░░░░░ 60%                      │
│ Frames processed: 120 / 200                    │
├────────────────────┬──────────────────────────-┤
│ Job Details        │ Processing Log            │
│ Video: sample.mp4  │ 14:30:22 Job started     │
│ Size: 45.2 MB      │ 14:30:23 Extracting...   │
│ Sampling: 2s       │ 14:31:05 Frame 50/200    │
│ Threshold: 0.5     │ 14:31:45 Frame 100/200   │
│ Model: YOLOv8n     │ ...                       │
└────────────────────┴───────────────────────────┘
```

**User Actions:** View progress, navigate back, view results (when completed).  
**Loading State:** Auto-refreshing progress bar (polling or SSE).  
**Error State:** Red status badge with error details and "Retry" button.  
**Success State:** Green status badge, "View Results" button appears.

### 4.4 Screen 4: Detection Timeline and Evidence Viewer

**Purpose:** Review frame-by-frame detection results with evidence.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/videos/jobs/{id}/detections`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Detection Results — Job #JOB-xxx               │
├────────────────────────────────────────────────┤
│ Summary: 200 frames | Avg count: 34 | Max: 78  │
│ Threshold line: ─ ─ ─ ─ ─ [50] ─ ─ ─ ─ ─     │
├────────────────────────────────────────────────┤
│ Person Count Timeline                          │
│ ┌──────────────────────────────────────────┐   │
│ │ ▲                    ╭─╮                 │   │
│ │ │              ╭────╯  ╰──╮              │   │
│ │ │    ╭────────╯            ╰──╮          │   │
│ │ │ ──╯                         ╰──        │   │
│ │ └──────────────────────────────────── ▶   │   │
│ │   0:00  0:30  1:00  1:30  2:00  2:30     │   │
│ └──────────────────────────────────────────┘   │
│ [click on chart to view frame evidence]        │
├────────────────────────────────────────────────┤
│ Frame Evidence Viewer                          │
│ ┌────────────────────┬─────────────────────┐   │
│ │                    │ Frame: #120          │   │
│ │  Evidence Image    │ Time: 1:04.000       │   │
│ │  (with bounding    │ Count: 67            │   │
│ │   boxes)           │ Avg Conf: 0.82       │   │
│ │                    │ Min Conf: 0.51       │   │
│ │                    │ Max Conf: 0.97       │   │
│ │                    │ Zone: Main Gate      │   │
│ │  ◀ Prev  Next ▶   │                     │   │
│ └────────────────────┴─────────────────────┘   │
└────────────────────────────────────────────────┘
```

**Components:**
- **Summary bar:** Aggregate statistics.
- **Timeline chart:** Recharts LineChart with threshold reference line, clickable data points.
- **Evidence viewer:** Large image with metadata panel. Prev/Next navigation.
- **Frame navigation:** Arrow keys support for quick review.

**User Actions:** Click timeline point → load evidence. Navigate frames. View detection details.  
**Loading State:** Skeleton for chart and image placeholder.  
**Empty State:** "No detections found in this video. The video may contain no visible people or the confidence threshold may be too high."  
**Error State:** "Failed to load evidence image." with retry.

### 4.5 Screen 5: Event Review Queue

**Purpose:** List and filter crowd events requiring operator review.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/events`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Event Review Queue                    [Filter ▼]│
├────────────────────────────────────────────────┤
│ Filters: Status [All ▼] Zone [All ▼] Date [──] │
├────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────┐   │
│ │ ● EVT-001 | High Count: Main Gate       │   │
│ │   Count: 78 | Time: 14:32 | PENDING     │   │
│ │   Sustained: Yes (5 frames)             │   │
│ │   [Review →]                            │   │
│ ├──────────────────────────────────────────┤   │
│ │ ○ EVT-002 | High Count: East Wing       │   │
│ │   Count: 55 | Time: 14:35 | PENDING     │   │
│ │   [Review →]                            │   │
│ ├──────────────────────────────────────────┤   │
│ │ ✓ EVT-003 | High Count: North Plaza     │   │
│ │   Count: 61 | Time: 13:20 | ACKNOWLEDGED│   │
│ │   [View →]                              │   │
│ └──────────────────────────────────────────┘   │
│ Showing 3 of 12 events          [1] [2] [→]   │
└────────────────────────────────────────────────┘
```

**Components:**
- **Filter bar:** Status dropdown, zone dropdown, date range picker.
- **Event cards:** Severity indicator dot, event ID, rule type, zone, count, timestamp, status badge.
- **Pagination:** Page numbers with prev/next.

**User Actions:** Filter events. Click event → event detail. Review from card (quick action).  
**Loading State:** Skeleton cards.  
**Empty State:** "No events match your filters." or "No events generated yet."

### 4.6 Screen 6: Event Details

**Purpose:** Full event review with evidence and action buttons.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/events/{id}`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ ← Back   Event EVT-001          [PENDING ●]   │
├────────────────────────────────────────────────┤
│ ┌────────────────────┬─────────────────────┐   │
│ │                    │ Event Details        │   │
│ │  Evidence Image    │ Type: High Count     │   │
│ │  (annotated)       │ Zone: Main Gate      │   │
│ │                    │ Count: 78 persons    │   │
│ │                    │ Confidence: 0.82 avg │   │
│ │                    │ Time: 14:32:04       │   │
│ │                    │ Video: sample.mp4    │   │
│ │                    │ Sustained: 5 frames  │   │
│ │                    │ Threshold: 50        │   │
│ └────────────────────┴─────────────────────┘   │
│                                                │
│ ┌──────────────────────────────────────────┐   │
│ │  Note: High person counts do not         │   │
│ │  necessarily indicate danger. Please     │   │
│ │  review the evidence and assess the      │   │
│ │  situation before taking action.         │   │
│ └──────────────────────────────────────────┘   │
│                                                │
│ Review Actions                                 │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│ │ Acknowledge│ │  Dismiss   │ │  Escalate  │  │
│ │   (green)  │ │  (grey)    │ │  (orange)  │  │
│ └────────────┘ └────────────┘ └────────────┘  │
│                                                │
│ [View on Map]  [View Detection Timeline]       │
└────────────────────────────────────────────────┘
```

**Components:**
- **Evidence image:** Large annotated image.
- **Detail panel:** All event metadata.
- **Disclaimer notice:** Neutral info box about detection limitations.
- **Action buttons:** Acknowledge (green), Dismiss (grey), Escalate (orange).
- **Navigation links:** Map view, detection timeline.

**Validation Rules:** Confirmation dialog required for all review actions. Dismiss requires an optional reason.  
**Loading State:** Image placeholder + skeleton text.  
**Success State:** Toast notification + return to queue with updated status.

### 4.7 Screen 7: GIS Operations Map

**Purpose:** Interactive venue map with zones, cameras, walkways, events, and incidents.  
**Target User:** Operator, Commander.  
**Data Sources:** `/api/v1/venue`, `/api/v1/events`, `/api/v1/incidents`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ GIS Operations                                 │
├───────────────────────────┬────────────────────┤
│                           │ Map Controls       │
│                           │ ┌────────────────┐ │
│                           │ │ Layers:        │ │
│                           │ │ ☑ Zones        │ │
│     Interactive           │ │ ☑ Cameras      │ │
│     Leaflet Map           │ │ ☑ Walkways     │ │
│     (full height)         │ │ ☑ Exits        │ │
│                           │ │ ☑ Events       │ │
│     Zones (polygons)      │ │ ☑ Incidents    │ │
│     Cameras (markers)     │ │ ☐ Route        │ │
│     Walkways (lines)      │ └────────────────┘ │
│     Exits (green markers) │                    │
│     Events (alert badges) │ Zone Info Panel    │
│                           │ (shows on click)   │
│                           │                    │
│                           │ Legend             │
│                           │ ● Zone ● Camera   │
│                           │ ● Exit ● Blocked  │
│                           │ ● Event ● Route   │
├───────────────────────────┴────────────────────┤
│ Walkway Status: 12 open | 2 blocked    [Manage]│
└────────────────────────────────────────────────┘
```

**Components:**
- **Leaflet map:** Full-height interactive map with OSM tiles.
- **Layer toggles:** Checkbox controls for each map layer.
- **Zone info panel:** Popup or sidebar panel showing zone details on click.
- **Legend:** Colour-coded map legend.
- **Walkway status bar:** Summary with manage link.

**User Actions:** Pan/zoom map. Click zones for details. Click cameras for info. Toggle layers. Navigate to route comparison.  
**Loading State:** Map skeleton with loading spinner.  
**Error State:** "Map tiles unavailable. Venue overlay displayed without background." (functional degradation).

### 4.8 Screen 8: Route Comparison Panel

**Purpose:** Compare routes between venue locations with cost analysis.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/routes/compare`, `/api/v1/venue/edges`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Route Comparison                               │
├───────────────────────────┬────────────────────┤
│                           │ Route Controls     │
│                           │ From: [dropdown ▼] │
│     Map with Route        │ To:   [dropdown ▼] │
│     Overlays              │ [Compare Routes]   │
│                           │                    │
│     Route 1 (green)       │ Results            │
│     Route 2 (orange)      │ ┌────────────────┐ │
│     Blocked (red dashed)  │ │ Route 1 ★ Best │ │
│                           │ │ Dist: 450m     │ │
│                           │ │ Cong: +0       │ │
│                           │ │ Haz:  +0       │ │
│                           │ │ Total: 450     │ │
│                           │ ├────────────────┤ │
│                           │ │ Route 2        │ │
│                           │ │ Dist: 520m     │ │
│                           │ │ Cong: +50      │ │
│                           │ │ Total: 570     │ │
│                           │ └────────────────┘ │
│                           │                    │
│                           │ Walkway Controls   │
│                           │ [Block Walkway ▼]  │
│                           │ [Reopen Walkway ▼] │
├───────────────────────────┴────────────────────┤
│ Blocked Walkways: Gate A ↔ Junction 3 (blocked)│
└────────────────────────────────────────────────┘
```

**User Actions:** Select start/end nodes. Compare routes. Block/reopen walkways. View cost breakdown.  
**Loading State:** Spinner on "Compare Routes" button.  
**Empty State:** "Select start and end points to compare routes."  
**Error State:** "No valid route found between selected points."

### 4.9 Screen 9: Incident Management

**Purpose:** List and manage all incidents.  
**Target User:** Operator, Commander.  
**Data Sources:** `/api/v1/incidents`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Incidents                     [+ New Incident] │
├────────────────────────────────────────────────┤
│ Filters: Status [All ▼] Priority [All ▼]      │
├──────┬──────────┬──────┬──────┬──────┬────────┤
│ ID   │ Title    │ Zone │ Pri. │Status│ Action │
├──────┼──────────┼──────┼──────┼──────┼────────┤
│INC-01│ High     │ Main │ HIGH │ OPEN │[View]  │
│      │ density  │ Gate │ ■    │ ●    │        │
├──────┼──────────┼──────┼──────┼──────┼────────┤
│INC-02│ Blocked  │ East │ MED  │RESP. │[View]  │
│      │ walkway  │ Wing │ ■    │ ●    │        │
└──────┴──────────┴──────┴──────┴──────┴────────┘
│ Showing 2 incidents                            │
└────────────────────────────────────────────────┘
```

**Components:**
- **Filter bar:** Status and priority dropdowns.
- **Incident table:** Sortable columns with priority and status colour-coded badges.
- **New incident button:** Opens creation form (also accessible from event review).

**User Actions:** Filter, sort, click to view detail, create new incident.  
**Empty State:** "No incidents recorded. Incidents are created from reviewed events."

### 4.10 Screen 10: Incident Details and History

**Purpose:** Full incident view with timeline, assignments, and management controls.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/incidents/{id}`, `/api/v1/incidents/{id}/history`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ ← Back   Incident INC-001          [OPEN ●]   │
├──────────────────────┬─────────────────────────┤
│ Incident Details     │ Related Event           │
│ Title: High density  │ EVT-001 (Escalated)     │
│ Zone: Main Gate      │ Count: 78 persons       │
│ Priority: HIGH       │ [View Event →]          │
│ Created: 14:35       │                         │
│ Description: ...     │ Assigned Resources      │
│                      │ Medical Team Alpha ●    │
│ [Update Status ▼]    │ [Assign Resource]       │
├──────────────────────┴─────────────────────────┤
│ Incident History Timeline                      │
│ ┌──────────────────────────────────────────┐   │
│ │ 14:35 ● Created by Operator              │   │
│ │ 14:36 ● Resource assigned: Med Alpha     │   │
│ │ 14:38 ● Status → Responding              │   │
│ │ ...                                      │   │
│ └──────────────────────────────────────────┘   │
│                                                │
│ [View on Map]  [Export History]                 │
└────────────────────────────────────────────────┘
```

**User Actions:** Update status (dropdown), assign resource, view linked event, view on map.  
**Validation:** Status transitions must follow valid state machine. Confirmation dialog for status changes.

### 4.11 Screen 11: Resource Management

**Purpose:** View and manage simulated response resources.  
**Target User:** Operator.  
**Data Sources:** `/api/v1/resources`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Response Resources                             │
├────────────────────────────────────────────────┤
│ Summary: 8 total | 5 available | 2 assigned | 1 unavail│
├──────┬──────────────┬──────┬──────┬───────────┤
│ ID   │ Name         │ Type │Status│ Assigned  │
├──────┼──────────────┼──────┼──────┼───────────┤
│ R-01 │ Med Alpha    │ MED  │ASSIGN│ INC-001   │
│ R-02 │ Sec Bravo    │ SEC  │AVAIL │ —         │
│ R-03 │ Fire Unit 1  │ FIRE │AVAIL │ —         │
│ R-04 │ Med Beta     │ MED  │UNAVL │ —         │
└──────┴──────────────┴──────┴──────┴───────────┘
```

**User Actions:** View resource list, see assignments. Status changes happen through incident management.  
**Empty State:** "No resources configured. Add resources in Settings."

### 4.12 Screen 12: Analytics and Reports

**Purpose:** View aggregated analytics from persisted data.  
**Target User:** Commander.  
**Data Sources:** `/api/v1/analytics`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Analytics & Reports                            │
├────────────────────────────────────────────────┤
│ Date Range: [Last 24h ▼] [Custom ──]          │
├──────────────────────┬─────────────────────────┤
│ Detections Over Time │ Events by Status        │
│ (Line chart)         │ (Donut chart)           │
│                      │                         │
├──────────────────────┼─────────────────────────┤
│ Incidents by Priority│ Processing Summary      │
│ (Bar chart)          │ Jobs: 5 complete / 1 fail│
│                      │ Frames: 1200            │
│                      │ Detections: 892         │
├──────────────────────┴─────────────────────────┤
│ Recent Activity Log                            │
│ (Scrollable list of recent audit entries)      │
└────────────────────────────────────────────────┘
```

**Note:** All charts use data from `/api/v1/analytics` which queries persisted records. No hardcoded values.

### 4.13 Screen 13: Settings and Venue Configuration

**Purpose:** Configure system parameters and venue settings.  
**Target User:** Operator (admin function).  
**Data Sources:** `/api/v1/settings`, `/api/v1/venue`

**Layout:**
```
┌────────────────────────────────────────────────┐
│ Settings                                       │
├────────────────────────────────────────────────┤
│ Processing Defaults                            │
│  Frame Sampling Interval: [2] seconds          │
│  Confidence Threshold:    [0.5]                │
│  YOLO Model:              [YOLOv8n ▼]         │
│                                                │
│ Crowd Rules                                    │
│  High Count Threshold:    [50] persons         │
│  Sustained Frame Count:   [3] frames           │
│                                                │
│ Venue Configuration                            │
│  Current Venue: [Demo Festival ▼]              │
│  Zones: 6 configured                           │
│  Cameras: 8 configured                         │
│  Walkways: 15 configured                       │
│                                                │
│ System                                         │
│  Demo Reset: [Reset All Data] (confirmation)   │
│                                                │
│                        [Save Settings]         │
└────────────────────────────────────────────────┘
```

**MVP Note:** Settings may be partially implemented — core processing defaults and crowd rules are P0; venue configuration UI is P1. Default values loaded from environment configuration.

## 5. Reusable Components

### 5.1 Status Badge
Coloured pill/badge used across all entity lists.
- Variants: pending (purple), processing (cyan), completed (green), failed (red), open (blue), responding (orange), resolved (green), closed (grey), acknowledged (green), dismissed (grey), escalated (orange).
- Size: Small (tables), medium (detail views).

### 5.2 Metric Card
Dashboard summary card.
- Props: label, value, icon, trend (up/down/neutral), color.
- Hover: Subtle elevation increase.

### 5.3 Data Table
Sortable, filterable table.
- Features: Column sorting, status badge rendering, action column, pagination, empty state.

### 5.4 Confirmation Dialog
Modal dialog for critical actions.
- Props: title, message, confirmLabel, cancelLabel, variant (danger/warning/info).
- Keyboard: Enter confirms, Escape cancels.

### 5.5 Toast Notification
Temporary notification.
- Variants: success (green), error (red), warning (orange), info (blue).
- Auto-dismiss: 5 seconds (configurable).
- Position: Top-right.

### 5.6 Empty State
Consistent empty state pattern.
- Props: icon, title, description, actionLabel, actionHref.

### 5.7 Loading Skeleton
Placeholder for loading content.
- Variants: text (lines), card (rectangle), chart (area), image (square).

### 5.8 Page Header
Consistent page header.
- Props: title, breadcrumbs, actions (buttons).

### 5.9 Filter Bar
Horizontal filter controls.
- Props: filter definitions (dropdowns, date pickers, search).

### 5.10 Severity Indicator
Consistent severity display.
- Props: level (critical/high/medium/low).
- Display: Coloured dot + label.

## 6. Button Hierarchy

| Level | Style | Usage | Example |
|-------|-------|-------|---------|
| Primary | Solid fill (`--color-secondary`) | Main page action | "Upload & Analyse", "Create Incident" |
| Secondary | Outlined (`--color-secondary` border) | Secondary actions | "Compare Routes", "View on Map" |
| Danger | Solid fill (`--color-status-critical`) | Destructive actions | "Reset Data", "Delete" |
| Ghost | Text only, no border | Tertiary actions | "Cancel", "View All" |
| Icon | Icon only, no border | Toolbar actions | Map controls, navigation |

## 7. Form Design

- **Labels:** Always visible above inputs (never placeholder-only).
- **Required fields:** Marked with red asterisk (*).
- **Validation:** Inline validation messages below inputs in red. Validated on blur and on submit.
- **Input sizing:** Full-width within their container. Max-width 600px for form fields.
- **Dropdowns:** Custom styled select components matching design system.
- **Number inputs:** Increment/decrement arrows. Min/max validation.
- **File input:** Custom drag-and-drop component, not native file input.

## 8. Map Legend and Route Overlays

### Legend Items
| Symbol | Meaning |
|--------|---------|
| Blue polygon | Venue zone |
| Red polygon (pulsing) | Zone with active event |
| Purple marker (camera icon) | Camera location |
| Green marker (exit icon) | Exit point |
| Grey circle | Junction node |
| Grey line | Open walkway |
| Red dashed line | Blocked walkway |
| Green thick line | Primary/best route |
| Orange thick line | Alternative route |
| Red pulsing marker | Active incident location |

### Route Overlay Behaviour
- Routes rendered as coloured polylines on the map.
- Best route in green, alternatives in orange.
- Route cost tooltip on hover.
- Animated dash pattern for in-progress routes.

## 9. Event Severity and Status Indicators

### Severity Mapping
| Person Count Range | Severity | Colour | Icon |
|-------------------|----------|--------|------|
| > threshold × 2.0 | Critical | Red | alert-octagon |
| > threshold × 1.5 | High | Orange | alert-triangle |
| > threshold × 1.0 | Medium | Yellow/Amber | alert-circle |
| ≤ threshold | Low/Normal | Blue | info |

### Status Display
All statuses use consistent badge component with colour mapping defined in Status Colours section.

## 10. Confirmation Dialogs

Required for:
- Event review actions (acknowledge, dismiss, escalate)
- Incident creation
- Incident status changes
- Resource assignment
- Walkway blocking/reopening
- Demo data reset
- Any delete operation

Dialog includes: title, explanation text, confirm button (styled by variant), cancel button.

## 11. Responsive Behaviour

| Breakpoint | Layout Changes |
|-----------|----------------|
| ≥1280px (Desktop) | Full sidebar (240px) + full content. 4-column metric grid. Side-by-side panels. |
| 1024px–1279px | Slightly narrower content. 3-column metric grid. |
| 768px–1023px (Tablet) | Collapsed sidebar (icon-only, 64px). 2-column metric grid. Map and panel stack vertically. |
| <768px | Note: Mobile is out of scope but interface should not break. Single column. Sidebar becomes top drawer. |

---

*End of Document 05 — UI/UX Design Specification*
