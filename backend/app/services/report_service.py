"""
NEXORA Phase 8 - Report Generation & Export Service.
Coordinates querying persisted SQLite operational records, calculating consistent
metrics with Phase 7 semantics, formatting preview responses, and generating
streamlined PDF and CSV exports.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from fastapi import HTTPException, status

from app.models.incident import Incident, IncidentHistory
from app.models.event import Event
from app.models.job import Job
from app.models.video import Video
from app.models.detection import Detection
from app.models.resource import Resource
from app.models.venue import Venue, VenueZone, VenueNode, VenueEdge
from app.models.audit import AuditLog
from app.services.analytics_service import AnalyticsService
from app.schemas.report import (
    ReportTypeInfo,
    ReportFilterOption,
    ReportFilterOptionItem,
    ReportGenerateRequest,
    ReportMetadata,
    ReportPreviewResponse,
    AuditExportRequest,
)
from app.utils.csv_exporter import generate_csv_report
from app.utils.pdf_exporter import build_pdf_document

logger = logging.getLogger("nexora.report_service")

SUPPORTED_REPORT_TYPES: List[ReportTypeInfo] = [
    ReportTypeInfo(
        report_type="operational_summary",
        title="Operational Summary Report",
        description="Consolidated overview of incidents, crowd events, video processing jobs, simulated resources, and GIS venue status.",
        supported_formats=["pdf", "csv"],
        available_filters=[
            ReportFilterOption(
                name="Period",
                field="period",
                type="select",
                default="24h",
                options=[
                    ReportFilterOptionItem(value="24h", label="Last 24 Hours"),
                    ReportFilterOptionItem(value="7d", label="Last 7 Days"),
                    ReportFilterOptionItem(value="30d", label="Last 30 Days"),
                    ReportFilterOptionItem(value="custom", label="Custom Range"),
                ],
            )
        ],
    ),
    ReportTypeInfo(
        report_type="incident_report",
        title="Incident Management Report",
        description="Historical and active incident logs, severities, response progression, and resolution timing.",
        supported_formats=["pdf", "csv"],
        available_filters=[
            ReportFilterOption(
                name="Period",
                field="period",
                type="select",
                default="24h",
                options=[
                    ReportFilterOptionItem(value="24h", label="Last 24 Hours"),
                    ReportFilterOptionItem(value="7d", label="Last 7 Days"),
                    ReportFilterOptionItem(value="30d", label="Last 30 Days"),
                    ReportFilterOptionItem(value="custom", label="Custom Range"),
                ],
            ),
            ReportFilterOption(
                name="Severity",
                field="severity",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All Severities"),
                    ReportFilterOptionItem(value="critical", label="Critical"),
                    ReportFilterOptionItem(value="high", label="High"),
                    ReportFilterOptionItem(value="medium", label="Medium"),
                    ReportFilterOptionItem(value="low", label="Low"),
                ],
            ),
            ReportFilterOption(
                name="Status",
                field="status",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All Statuses"),
                    ReportFilterOptionItem(value="open", label="Open"),
                    ReportFilterOptionItem(value="acknowledged", label="Acknowledged"),
                    ReportFilterOptionItem(value="in_progress", label="In Progress"),
                    ReportFilterOptionItem(value="resolved", label="Resolved"),
                    ReportFilterOptionItem(value="closed", label="Closed"),
                ],
            ),
            ReportFilterOption(name="Zone ID", field="zone_id", type="text"),
        ],
    ),
    ReportTypeInfo(
        report_type="crowd_event_report",
        title="Crowd Event & Review Report",
        description="Sampled-frame YOLO detections exceeding configured thresholds, reviewer disposition, and timestamps.",
        supported_formats=["pdf", "csv"],
        available_filters=[
            ReportFilterOption(
                name="Period",
                field="period",
                type="select",
                default="24h",
                options=[
                    ReportFilterOptionItem(value="24h", label="Last 24 Hours"),
                    ReportFilterOptionItem(value="7d", label="Last 7 Days"),
                    ReportFilterOptionItem(value="30d", label="Last 30 Days"),
                    ReportFilterOptionItem(value="custom", label="Custom Range"),
                ],
            ),
            ReportFilterOption(
                name="Severity",
                field="severity",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All Severities"),
                    ReportFilterOptionItem(value="critical", label="Critical"),
                    ReportFilterOptionItem(value="high", label="High"),
                    ReportFilterOptionItem(value="medium", label="Medium"),
                    ReportFilterOptionItem(value="low", label="Low"),
                ],
            ),
            ReportFilterOption(
                name="Review Status",
                field="status",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All Review States"),
                    ReportFilterOptionItem(value="pending_review", label="Pending Review"),
                    ReportFilterOptionItem(value="acknowledged", label="Acknowledged"),
                    ReportFilterOptionItem(value="dismissed", label="Dismissed"),
                    ReportFilterOptionItem(value="resolved", label="Resolved"),
                ],
            ),
            ReportFilterOption(name="Zone ID", field="zone_id", type="text"),
        ],
    ),
    ReportTypeInfo(
        report_type="video_analysis_report",
        title="Video Analysis & Job Processing Report",
        description="Performance and detection throughput across uploaded recorded video footage and background processing jobs.",
        supported_formats=["pdf", "csv"],
        available_filters=[
            ReportFilterOption(
                name="Period",
                field="period",
                type="select",
                default="24h",
                options=[
                    ReportFilterOptionItem(value="24h", label="Last 24 Hours"),
                    ReportFilterOptionItem(value="7d", label="Last 7 Days"),
                    ReportFilterOptionItem(value="30d", label="Last 30 Days"),
                    ReportFilterOptionItem(value="custom", label="Custom Range"),
                ],
            ),
            ReportFilterOption(
                name="Job Status",
                field="status",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All Statuses"),
                    ReportFilterOptionItem(value="queued", label="Queued"),
                    ReportFilterOptionItem(value="processing", label="Processing"),
                    ReportFilterOptionItem(value="completed", label="Completed"),
                    ReportFilterOptionItem(value="failed", label="Failed"),
                ],
            ),
        ],
    ),
    ReportTypeInfo(
        report_type="gis_operations_report",
        title="GIS Operations & Walkway Report",
        description="Venue walkway blockage records, pedestrian connectivity, and decision-support routing status.",
        supported_formats=["pdf", "csv"],
        available_filters=[
            ReportFilterOption(
                name="Venue ID",
                field="venue_id",
                type="select",
                default="venue_triveni",
                options=[ReportFilterOptionItem(value="venue_triveni", label="Triveni Sangam Venue")],
            ),
            ReportFilterOption(
                name="Blockage State",
                field="status",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All Walkways"),
                    ReportFilterOptionItem(value="blocked_only", label="Blocked Walkways Only"),
                    ReportFilterOptionItem(value="open_only", label="Open Walkways Only"),
                ],
            ),
        ],
    ),
    ReportTypeInfo(
        report_type="resource_deployment_report",
        title="Resource Deployment Report",
        description="Simulated emergency response units, availability states, and incident allocations.",
        supported_formats=["pdf", "csv"],
        available_filters=[
            ReportFilterOption(
                name="Status",
                field="status",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All States"),
                    ReportFilterOptionItem(value="available", label="Available"),
                    ReportFilterOptionItem(value="assigned", label="Assigned"),
                    ReportFilterOptionItem(value="unavailable", label="Unavailable"),
                ],
            ),
            ReportFilterOption(
                name="Resource Type",
                field="resource_type",
                type="select",
                default="all",
                options=[
                    ReportFilterOptionItem(value="all", label="All Types"),
                    ReportFilterOptionItem(value="medical", label="Medical Unit"),
                    ReportFilterOptionItem(value="security", label="Security Team"),
                    ReportFilterOptionItem(value="crowd_controller", label="Crowd Controller"),
                    ReportFilterOptionItem(value="fire", label="Fire Rescue"),
                    ReportFilterOptionItem(value="logistics", label="Logistics"),
                ],
            ),
        ],
    ),
    ReportTypeInfo(
        report_type="audit_report",
        title="Comprehensive Audit Log Report",
        description="Chronological, deterministic record of system actions, operator inputs, state transitions, and exports.",
        supported_formats=["pdf", "csv"],
        available_filters=[
            ReportFilterOption(
                name="Period",
                field="period",
                type="select",
                default="24h",
                options=[
                    ReportFilterOptionItem(value="24h", label="Last 24 Hours"),
                    ReportFilterOptionItem(value="7d", label="Last 7 Days"),
                    ReportFilterOptionItem(value="30d", label="Last 30 Days"),
                    ReportFilterOptionItem(value="custom", label="Custom Range"),
                ],
            ),
            ReportFilterOption(name="Action Type", field="action_type", type="text"),
            ReportFilterOption(name="Entity Type", field="entity_type", type="text"),
        ],
    ),
]


class ReportService:

    @staticmethod
    def get_supported_types() -> List[ReportTypeInfo]:
        return SUPPORTED_REPORT_TYPES

    @staticmethod
    def _validate_report_type(report_type: str) -> ReportTypeInfo:
        for rt in SUPPORTED_REPORT_TYPES:
            if rt.report_type == report_type:
                return rt
        valid = [rt.report_type for rt in SUPPORTED_REPORT_TYPES]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported report type '{report_type}'. Supported types: {valid}"
        )

    @staticmethod
    def _extract_merged_filters(req: ReportGenerateRequest) -> Dict[str, Any]:
        merged = dict(req.filters or {})
        if req.status is not None:
            merged["status"] = req.status
        if req.severity is not None:
            merged["severity"] = req.severity
        if req.zone_id is not None:
            merged["zone_id"] = req.zone_id
        if req.action_type is not None:
            merged["action_type"] = req.action_type
        if req.entity_type is not None:
            merged["entity_type"] = req.entity_type
        return merged

    @staticmethod
    def generate_report_data(
        db: Session,
        req: ReportGenerateRequest
    ) -> Tuple[ReportMetadata, Dict[str, Any], List[str], List[Dict[str, Any]], str]:
        """
        Executes query based on report_type and filters.
        Returns: (metadata, summary_metrics, columns, records, disclaimer)
        """
        rt_info = ReportService._validate_report_type(req.report_type)
        start_dt, end_dt, period_name = AnalyticsService.parse_time_window(
            req.period, req.start_date, req.end_date
        )

        merged_filters = ReportService._extract_merged_filters(req)
        now_utc = datetime.now(timezone.utc)
        report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"

        metadata = ReportMetadata(
            report_id=report_id,
            report_type=req.report_type,
            report_title=rt_info.title,
            generation_time=now_utc.isoformat(),
            reporting_period=period_name,
            period_start=start_dt.isoformat(),
            period_end=end_dt.isoformat(),
            timezone="UTC",
            applied_filters=merged_filters,
            record_count=0,
            system_mode="decision_support_prototype",
            disclaimer="",
        )

        if req.report_type == "operational_summary":
            return ReportService._build_operational_summary(db, start_dt, end_dt, metadata, merged_filters)
        elif req.report_type == "incident_report":
            return ReportService._build_incident_report(db, start_dt, end_dt, metadata, merged_filters)
        elif req.report_type == "crowd_event_report":
            return ReportService._build_crowd_event_report(db, start_dt, end_dt, metadata, merged_filters)
        elif req.report_type == "video_analysis_report":
            return ReportService._build_video_analysis_report(db, start_dt, end_dt, metadata, merged_filters)
        elif req.report_type == "gis_operations_report":
            return ReportService._build_gis_operations_report(db, start_dt, end_dt, metadata, merged_filters)
        elif req.report_type == "resource_deployment_report":
            return ReportService._build_resource_deployment_report(db, start_dt, end_dt, metadata, merged_filters)
        elif req.report_type == "audit_report":
            return ReportService._build_audit_report(db, start_dt, end_dt, metadata, merged_filters)
        else:
            raise HTTPException(status_code=400, detail="Unhandled report type.")

    # --------------------------------------------------------------------------
    # Handlers for each report category
    # --------------------------------------------------------------------------

    @staticmethod
    def _build_operational_summary(
        db: Session,
        start_dt: datetime,
        end_dt: datetime,
        meta: ReportMetadata,
        filters: Dict[str, Any]
    ):
        active_incidents = db.query(Incident).filter(
            Incident.status.in_(["open", "acknowledged", "in_progress"])
        ).count()

        incidents_created = db.query(Incident).filter(
            Incident.created_at >= start_dt,
            Incident.created_at <= end_dt
        ).count()

        resolved_incidents = db.query(Incident).filter(
            Incident.resolved_at >= start_dt,
            Incident.resolved_at <= end_dt
        ).all()
        resolved_count = len(resolved_incidents)

        avg_res_min = None
        if resolved_count > 0:
            durations = [
                (inc.resolved_at - inc.created_at).total_seconds() / 60.0
                for inc in resolved_incidents
                if inc.resolved_at and inc.created_at and inc.resolved_at >= inc.created_at
            ]
            if durations:
                avg_res_min = round(sum(durations) / len(durations), 1)

        pending_events = db.query(Event).filter(Event.status == "pending_review").count()
        events_created = db.query(Event).filter(
            Event.created_at >= start_dt,
            Event.created_at <= end_dt
        ).count()

        active_jobs = db.query(Job).filter(Job.status.in_(["queued", "processing"])).count()
        jobs_created = db.query(Job).filter(
            Job.created_at >= start_dt,
            Job.created_at <= end_dt
        ).count()

        sampled_detections = db.query(Detection).filter(
            Detection.created_at >= start_dt,
            Detection.created_at <= end_dt
        ).count()

        all_res = db.query(Resource).all()
        total_res = len(all_res)
        avail_res = sum(1 for r in all_res if r.status == "available")

        triveni_edges = db.query(VenueEdge).filter(VenueEdge.venue_id == "venue_triveni").all()
        blocked_walkways = sum(1 for e in triveni_edges if e.is_blocked)

        audit_count = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_dt,
            AuditLog.timestamp <= end_dt
        ).count()

        summary_metrics = {
            "active_incidents_now": active_incidents,
            "incidents_created_in_period": incidents_created,
            "incidents_resolved_in_period": resolved_count,
            "avg_resolution_min": avg_res_min,
            "pending_events_now": pending_events,
            "events_created_in_period": events_created,
            "active_video_jobs_now": active_jobs,
            "jobs_created_in_period": jobs_created,
            "sampled_detections_in_period": sampled_detections,
            "available_resources_now": f"{avail_res}/{total_res} (Simulated)",
            "blocked_walkways_triveni_now": f"{blocked_walkways}/{len(triveni_edges)}",
            "audit_records_in_period": audit_count,
        }

        records = []
        recent_incidents = db.query(Incident).filter(
            Incident.created_at >= start_dt,
            Incident.created_at <= end_dt
        ).order_by(desc(Incident.created_at)).limit(50).all()

        for inc in recent_incidents:
            records.append({
                "timestamp": inc.created_at.isoformat() if inc.created_at else "N/A",
                "category": "Incident",
                "reference_id": inc.incident_number,
                "severity_or_status": f"{inc.severity.upper()} / {inc.status}",
                "summary": inc.title,
            })

        recent_events = db.query(Event).filter(
            Event.created_at >= start_dt,
            Event.created_at <= end_dt
        ).order_by(desc(Event.created_at)).limit(50).all()

        for ev in recent_events:
            records.append({
                "timestamp": ev.created_at.isoformat() if ev.created_at else "N/A",
                "category": "Crowd Event",
                "reference_id": ev.id[:8],
                "severity_or_status": f"{ev.severity.upper()} / {ev.status}",
                "summary": f"{ev.rule_name} (Sampled count: {ev.person_count})",
            })

        records.sort(key=lambda r: r["timestamp"], reverse=True)
        columns = ["timestamp", "category", "reference_id", "severity_or_status", "summary"]
        meta.record_count = len(records)
        disclaimer = (
            "Operational demonstration report. Metric definitions conform to NEXORA Phase 7 analytics. "
            "Resources and dispatch recommendations are simulated."
        )
        meta.disclaimer = disclaimer
        return meta, summary_metrics, columns, records, disclaimer

    @staticmethod
    def _build_incident_report(
        db: Session,
        start_dt: datetime,
        end_dt: datetime,
        meta: ReportMetadata,
        filters: Dict[str, Any]
    ):
        query = db.query(Incident).filter(
            Incident.created_at >= start_dt,
            Incident.created_at <= end_dt
        )

        severity_filter = filters.get("severity")
        if severity_filter and severity_filter != "all":
            query = query.filter(Incident.severity == severity_filter)

        status_filter = filters.get("status")
        if status_filter and status_filter != "all":
            query = query.filter(Incident.status == status_filter)

        zone_filter = filters.get("zone_id")
        if zone_filter and zone_filter.strip():
            query = query.filter(Incident.zone_id == zone_filter.strip())

        incidents = query.order_by(desc(Incident.created_at), desc(Incident.id)).all()

        total = len(incidents)
        active_count = sum(1 for i in incidents if i.status in ["open", "acknowledged", "in_progress"])
        resolved_count = sum(1 for i in incidents if i.status in ["resolved", "closed"])
        crit_high = sum(1 for i in incidents if i.severity in ["critical", "high"])

        summary_metrics = {
            "total_incidents_in_period": total,
            "currently_active_subset": active_count,
            "resolved_subset": resolved_count,
            "critical_or_high_subset": crit_high,
        }

        columns = [
            "incident_number",
            "created_at",
            "severity",
            "status",
            "title",
            "zone_id",
            "assigned_resource",
            "acknowledged_at",
            "resolved_at",
        ]
        records = []
        for inc in incidents:
            assigned_name = inc.assigned_resource.name if inc.assigned_resource else "None"
            records.append({
                "incident_number": inc.incident_number,
                "created_at": inc.created_at.isoformat() if inc.created_at else "—",
                "severity": inc.severity.upper(),
                "status": inc.status,
                "title": inc.title,
                "zone_id": inc.zone_id or "—",
                "assigned_resource": assigned_name,
                "acknowledged_at": inc.acknowledged_at.isoformat() if inc.acknowledged_at else "—",
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else "—",
            })

        meta.record_count = len(records)
        disclaimer = "Incidents list derived directly from persisted incident tables. Historical lifecycle transitions are preserved in incident history."
        meta.disclaimer = disclaimer
        return meta, summary_metrics, columns, records, disclaimer

    @staticmethod
    def _build_crowd_event_report(
        db: Session,
        start_dt: datetime,
        end_dt: datetime,
        meta: ReportMetadata,
        filters: Dict[str, Any]
    ):
        query = db.query(Event).filter(
            Event.created_at >= start_dt,
            Event.created_at <= end_dt
        )

        severity_filter = filters.get("severity")
        if severity_filter and severity_filter != "all":
            query = query.filter(Event.severity == severity_filter)

        status_filter = filters.get("status")
        if status_filter and status_filter != "all":
            query = query.filter(Event.status == status_filter)

        zone_filter = filters.get("zone_id")
        if zone_filter and zone_filter.strip():
            query = query.filter(Event.zone_id == zone_filter.strip())

        events = query.order_by(desc(Event.created_at), desc(Event.id)).all()

        total = len(events)
        pending = sum(1 for e in events if e.status == "pending_review")
        acknowledged = sum(1 for e in events if e.status == "acknowledged")
        dismissed = sum(1 for e in events if e.status == "dismissed")
        peak_count = max([e.person_count for e in events], default=0)

        summary_metrics = {
            "total_events_in_period": total,
            "pending_review_count": pending,
            "acknowledged_count": acknowledged,
            "dismissed_count": dismissed,
            "max_sampled_frame_count": peak_count,
        }

        columns = [
            "event_id",
            "created_at",
            "rule_name",
            "severity",
            "status",
            "person_count",
            "zone_id",
            "reviewed_by",
            "reviewed_at",
        ]
        records = []
        for ev in events:
            records.append({
                "event_id": ev.id[:8],
                "created_at": ev.created_at.isoformat() if ev.created_at else "—",
                "rule_name": ev.rule_name,
                "severity": ev.severity.upper(),
                "status": ev.status,
                "person_count": ev.person_count,
                "zone_id": ev.zone_id or "—",
                "reviewed_by": ev.reviewed_by or "—",
                "reviewed_at": ev.reviewed_at.isoformat() if ev.reviewed_at else "—",
            })

        meta.record_count = len(records)
        disclaimer = (
            "Sampled-frame detection counts reflect person bounding boxes from recorded video models, "
            "not unique individuals, venue turnstile occupancy, or behavioral panic detection."
        )
        meta.disclaimer = disclaimer
        return meta, summary_metrics, columns, records, disclaimer

    @staticmethod
    def _build_video_analysis_report(
        db: Session,
        start_dt: datetime,
        end_dt: datetime,
        meta: ReportMetadata,
        filters: Dict[str, Any]
    ):
        query = db.query(Job).filter(
            Job.created_at >= start_dt,
            Job.created_at <= end_dt
        )

        status_filter = filters.get("status")
        if status_filter and status_filter != "all":
            query = query.filter(Job.status == status_filter)

        jobs = query.order_by(desc(Job.created_at), desc(Job.id)).all()

        total_jobs = len(jobs)
        completed = sum(1 for j in jobs if j.status == "completed")
        failed = sum(1 for j in jobs if j.status == "failed")
        active = sum(1 for j in jobs if j.status in ["queued", "processing"])
        total_detections_sum = sum(j.total_persons_detected for j in jobs)

        summary_metrics = {
            "total_jobs_in_period": total_jobs,
            "completed_jobs": completed,
            "failed_jobs": failed,
            "active_jobs": active,
            "total_sampled_detections_sum": total_detections_sum,
        }

        columns = [
            "job_id",
            "video_filename",
            "status",
            "progress_percent",
            "sampling_interval_sec",
            "total_persons_detected",
            "max_person_count",
            "started_at",
            "completed_at",
        ]
        records = []
        for job in jobs:
            # Safe filename only - never expose private filesystem storage paths!
            v_name = job.video.original_filename if job.video else (job.video.filename if job.video else "N/A")
            records.append({
                "job_id": job.id[:8],
                "video_filename": v_name,
                "status": job.status,
                "progress_percent": f"{job.progress_percent:.1f}%",
                "sampling_interval_sec": f"{job.sampling_interval_sec}s",
                "total_persons_detected": job.total_persons_detected,
                "max_person_count": job.max_person_count,
                "started_at": job.started_at.isoformat() if job.started_at else "—",
                "completed_at": job.completed_at.isoformat() if job.completed_at else "—",
            })

        meta.record_count = len(records)
        disclaimer = "Videos represent uploaded recorded test footage processed via OpenCV frame sampling and YOLOv8."
        meta.disclaimer = disclaimer
        return meta, summary_metrics, columns, records, disclaimer

    @staticmethod
    def _build_gis_operations_report(
        db: Session,
        start_dt: datetime,
        end_dt: datetime,
        meta: ReportMetadata,
        filters: Dict[str, Any]
    ):
        venue_id = filters.get("venue_id") or "venue_triveni"
        query = db.query(VenueEdge).filter(VenueEdge.venue_id == venue_id)

        blockage_filter = filters.get("status") or filters.get("is_blocked")
        if blockage_filter in ["blocked_only", True, "true", "True"]:
            query = query.filter(VenueEdge.is_blocked == True)
        elif blockage_filter in ["open_only", False, "false", "False"]:
            query = query.filter(VenueEdge.is_blocked == False)

        edges = query.order_by(VenueEdge.id).all()

        total_walkways = len(edges)
        blocked_count = sum(1 for e in edges if e.is_blocked)
        zone_count = db.query(VenueZone).filter(VenueZone.venue_id == venue_id).count()
        node_count = db.query(VenueNode).filter(VenueNode.venue_id == venue_id).count()

        summary_metrics = {
            "venue_id": venue_id,
            "total_walkways_assessed": total_walkways,
            "currently_blocked_walkways": blocked_count,
            "total_venue_zones": zone_count,
            "total_graph_nodes": node_count,
        }

        columns = [
            "edge_id",
            "name",
            "from_node",
            "to_node",
            "is_blocked",
            "blockage_reason",
            "distance_meters",
            "blocked_at",
        ]
        records = []
        for edge in edges:
            records.append({
                "edge_id": edge.id,
                "name": edge.name or "—",
                "from_node": edge.from_node_id,
                "to_node": edge.to_node_id,
                "is_blocked": "BLOCKED" if edge.is_blocked else "OPEN",
                "blockage_reason": edge.blockage_reason or "—",
                "distance_meters": f"{edge.distance_meters:.1f}m" if edge.distance_meters else "—",
                "blocked_at": edge.blocked_at.isoformat() if edge.blocked_at else "—",
            })

        meta.record_count = len(records)
        disclaimer = (
            "Walkway blockage state reflects the current database snapshot. Routing calculations provide "
            "decision support and do not guarantee hazardous condition avoidance."
        )
        meta.disclaimer = disclaimer
        return meta, summary_metrics, columns, records, disclaimer

    @staticmethod
    def _build_resource_deployment_report(
        db: Session,
        start_dt: datetime,
        end_dt: datetime,
        meta: ReportMetadata,
        filters: Dict[str, Any]
    ):
        query = db.query(Resource)

        status_filter = filters.get("status")
        if status_filter and status_filter != "all":
            query = query.filter(Resource.status == status_filter)

        type_filter = filters.get("resource_type")
        if type_filter and type_filter != "all":
            query = query.filter(Resource.resource_type == type_filter)

        resources = query.order_by(Resource.call_sign).all()

        total = len(resources)
        available = sum(1 for r in resources if r.status == "available")
        assigned = sum(1 for r in resources if r.status == "assigned")
        unavailable = sum(1 for r in resources if r.status == "unavailable")

        summary_metrics = {
            "total_simulated_resources": total,
            "available_resources": available,
            "assigned_resources": assigned,
            "unavailable_resources": unavailable,
        }

        columns = [
            "call_sign",
            "name",
            "resource_type",
            "status",
            "assigned_incident",
            "current_zone_id",
        ]
        records = []
        for r in resources:
            inc_label = "None"
            if r.incidents:
                inc_label = r.incidents[0].incident_number
            records.append({
                "call_sign": r.call_sign,
                "name": r.name,
                "resource_type": r.resource_type.replace("_", " ").title(),
                "status": r.status.upper(),
                "assigned_incident": inc_label,
                "current_zone_id": r.current_zone_id or "—",
            })

        meta.record_count = len(records)
        disclaimer = (
            "NOTICE: All resources in the NEXORA prototype are SIMULATED DEMO UNITS. "
            "No real-world ambulances, police, fire, or municipal emergency units have been notified or dispatched."
        )
        meta.disclaimer = disclaimer
        return meta, summary_metrics, columns, records, disclaimer

    @staticmethod
    def _build_audit_report(
        db: Session,
        start_dt: datetime,
        end_dt: datetime,
        meta: ReportMetadata,
        filters: Dict[str, Any]
    ):
        query = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_dt,
            AuditLog.timestamp <= end_dt
        )

        action_filter = filters.get("action_type")
        if action_filter and action_filter.strip():
            query = query.filter(AuditLog.action_type == action_filter.strip())

        entity_filter = filters.get("entity_type")
        if entity_filter and entity_filter.strip():
            query = query.filter(AuditLog.entity_type == entity_filter.strip())

        # Deterministic chronological order: timestamp.desc(), id.desc()
        logs = query.order_by(desc(AuditLog.timestamp), desc(AuditLog.id)).limit(1000).all()

        total = len(logs)
        actions_count = len(set(l.action_type for l in logs))

        summary_metrics = {
            "total_audit_records": total,
            "unique_action_types": actions_count,
            "ordering_mode": "Deterministic Chronological (Timestamp + ID)",
        }

        columns = [
            "audit_id",
            "timestamp",
            "actor_id",
            "actor_role",
            "action_type",
            "entity_type",
            "entity_id",
            "ip_address",
        ]
        records = []
        for l in logs:
            records.append({
                "audit_id": l.id[:8],
                "timestamp": l.timestamp.isoformat() if l.timestamp else "—",
                "actor_id": l.actor_id,
                "actor_role": l.actor_role,
                "action_type": l.action_type,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "ip_address": l.ip_address or "—",
            })

        meta.record_count = len(records)
        disclaimer = (
            "Audit export provides a complete chronological ledger of logged application actions. "
            "Records are ordered deterministically by timestamp and stable primary key."
        )
        meta.disclaimer = disclaimer
        return meta, summary_metrics, columns, records, disclaimer

    # --------------------------------------------------------------------------
    # Preview and Export Generation
    # --------------------------------------------------------------------------

    @staticmethod
    def generate_preview(db: Session, req: ReportGenerateRequest) -> ReportPreviewResponse:
        meta, summary_metrics, columns, records, disclaimer = ReportService.generate_report_data(db, req)
        preview_records = records[: req.limit]
        return ReportPreviewResponse(
            metadata=meta,
            summary_metrics=summary_metrics,
            columns=columns,
            records=preview_records,
        )

    @staticmethod
    def export_csv(db: Session, req: ReportGenerateRequest) -> Tuple[str, bytes]:
        meta, summary_metrics, columns, records, disclaimer = ReportService.generate_report_data(db, req)
        metadata_dict = meta.model_dump()
        csv_bytes = generate_csv_report(
            report_title=meta.report_title,
            metadata=metadata_dict,
            summary_metrics=summary_metrics,
            columns=columns,
            records=records,
            include_bom=True,
        )
        filename = f"nexora_{req.report_type}_{req.period}.csv"
        ReportService._log_export_audit(db, req.report_type, "csv")
        return filename, csv_bytes

    @staticmethod
    def export_pdf(db: Session, req: ReportGenerateRequest) -> Tuple[str, bytes]:
        meta, summary_metrics, columns, records, disclaimer = ReportService.generate_report_data(db, req)
        metadata_dict = meta.model_dump()
        pdf_bytes = build_pdf_document(
            report_title=meta.report_title,
            metadata=metadata_dict,
            summary_metrics=summary_metrics,
            columns=columns,
            records=records,
            disclaimer=disclaimer,
        )
        filename = f"nexora_{req.report_type}_{req.period}.pdf"
        ReportService._log_export_audit(db, req.report_type, "pdf")
        return filename, pdf_bytes

    @staticmethod
    def _log_export_audit(db: Session, report_type: str, export_format: str):
        if report_type == "audit_report":
            # Section 9 requirement: prevent recursive audit generation
            return
        try:
            audit = AuditLog(
                actor_id="operator",
                actor_role="supervisor",
                action_type="report_exported",
                entity_type="report",
                entity_id=report_type,
                details={"format": export_format, "timestamp": datetime.now(timezone.utc).isoformat()},
                ip_address="127.0.0.1",
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            logger.warning("Failed to log export audit action: %s", e)
            db.rollback()
