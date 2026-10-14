from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class PrimaryMetrics(BaseModel):
    active_incidents: int = Field(..., description="Incidents currently open, acknowledged, or in progress")
    pending_events: int = Field(..., description="VisionX crowd events awaiting human review")
    processing_jobs: int = Field(..., description="Video analysis jobs queued or processing")
    critical_high_incidents: int = Field(..., description="Active incidents with critical or high priority")
    available_resources: int = Field(..., description="Available simulated response squads")
    total_resources: int = Field(..., description="Total registered simulated response squads")
    blocked_walkways: int = Field(..., description="Walkways currently marked as blocked")
    total_walkways: int = Field(..., description="Total venue graph edges / walkways")

class IncidentOverviewItem(BaseModel):
    id: str
    incident_number: str
    title: str
    severity: str
    status: str
    zone_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class IncidentAnalytics(BaseModel):
    total_in_period: int
    active_count: int
    status_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    avg_resolution_duration_minutes: Optional[float] = None
    recent_incidents: List[IncidentOverviewItem] = []

class EventOverviewItem(BaseModel):
    id: str
    rule_name: str
    severity: str
    status: str
    person_count: int
    zone_id: str
    created_at: datetime

class EventAnalytics(BaseModel):
    total_in_period: int
    pending_count: int
    status_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    recent_events: List[EventOverviewItem] = []

class JobOverviewItem(BaseModel):
    id: str
    video_id: str
    status: str
    progress_percent: float
    total_persons_detected: int
    created_at: datetime
    error_message: Optional[str] = None

class JobAnalytics(BaseModel):
    total_in_period: int
    status_distribution: Dict[str, int]
    total_frame_detections: int = Field(..., description="Sum of frame-level person detections (not unique persons)")
    recent_failed_jobs: List[JobOverviewItem] = []

class AssignedResourceDetail(BaseModel):
    id: str
    name: str
    call_sign: str
    resource_type: str
    assigned_incident_id: Optional[str] = None
    incident_number: Optional[str] = None

class ResourceAnalytics(BaseModel):
    total: int
    available: int
    assigned: int
    unavailable: int
    by_type: Dict[str, int]
    assigned_units: List[AssignedResourceDetail] = []

class BlockedWalkwayDetail(BaseModel):
    id: str
    name: Optional[str] = None
    from_node: str
    to_node: str
    blockage_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None

class GisAnalytics(BaseModel):
    total_walkways: int
    blocked_count: int
    unblocked_count: int
    blocked_details: List[BlockedWalkwayDetail] = []

class AttentionItem(BaseModel):
    category: str  # pending_event, critical_incident, unassigned_incident, blocked_walkway, failed_job
    level: str     # critical, warning, info
    title: str
    subtitle: str
    entity_id: str
    action_route: str
    timestamp: datetime

class ActivityItem(BaseModel):
    id: str
    timestamp: datetime
    actor_id: str
    action_type: str
    entity_type: str
    entity_id: str
    description: str

class TrendBucket(BaseModel):
    timestamp: datetime
    label: str
    incidents_created: int
    events_created: int
    jobs_completed: int

class AnalyticsOverviewResponse(BaseModel):
    reporting_period: str
    period_start: datetime
    period_end: datetime
    refreshed_at: datetime
    metrics: PrimaryMetrics
    incidents: IncidentAnalytics
    events: EventAnalytics
    jobs: JobAnalytics
    resources: ResourceAnalytics
    gis: GisAnalytics
    attention_queue: List[AttentionItem] = []
    recent_activity: List[ActivityItem] = []

class AnalyticsTrendsResponse(BaseModel):
    reporting_period: str
    period_start: datetime
    period_end: datetime
    interval: str  # hourly, daily
    buckets: List[TrendBucket] = []
