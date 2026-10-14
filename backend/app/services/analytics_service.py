import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status

from app.models.incident import Incident, IncidentHistory
from app.models.event import Event
from app.models.job import Job
from app.models.resource import Resource
from app.models.venue import VenueEdge
from app.models.audit import AuditLog
from app.schemas.analytics import (
    PrimaryMetrics,
    IncidentAnalytics,
    IncidentOverviewItem,
    EventAnalytics,
    EventOverviewItem,
    JobAnalytics,
    JobOverviewItem,
    ResourceAnalytics,
    AssignedResourceDetail,
    GisAnalytics,
    BlockedWalkwayDetail,
    AttentionItem,
    ActivityItem,
    TrendBucket,
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
)

logger = logging.getLogger("nexora.analytics_service")

class AnalyticsService:

    @staticmethod
    def parse_time_window(
        period: str = "24h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[datetime, datetime, str]:
        now = datetime.now(timezone.utc)
        period_clean = (period or "24h").lower()

        if period_clean == "custom":
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Both start_date and end_date ISO strings are required for custom reporting period."
                )
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid ISO datetime format for start_date or end_date: {e}"
                )

            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)

            if start_dt > end_dt:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="start_date must be earlier than or equal to end_date."
                )
            return start_dt, end_dt, "custom"

        elif period_clean == "7d":
            return now - timedelta(days=7), now, "7d"
        elif period_clean == "30d":
            return now - timedelta(days=30), now, "30d"
        elif period_clean == "24h":
            return now - timedelta(hours=24), now, "24h"
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid reporting period '{period}'. Allowed options: '24h', '7d', '30d', 'custom'."
            )

    @staticmethod
    def get_overview(
        db: Session,
        period: str = "24h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> AnalyticsOverviewResponse:
        start_dt, end_dt, period_name = AnalyticsService.parse_time_window(period, start_date, end_date)
        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # 1. Primary Metrics (Current Real-time Snapshot)
        # -------------------------------------------------------------
        active_incidents = db.query(Incident).filter(
            Incident.status.in_(["open", "acknowledged", "in_progress"])
        ).count()

        pending_events = db.query(Event).filter(
            Event.status == "pending_review"
        ).count()

        processing_jobs = db.query(Job).filter(
            Job.status.in_(["queued", "processing"])
        ).count()

        critical_high_incidents = db.query(Incident).filter(
            Incident.status.in_(["open", "acknowledged", "in_progress"]),
            Incident.severity.in_(["critical", "high"])
        ).count()

        all_resources = db.query(Resource).all()
        total_resources = len(all_resources)
        available_resources = sum(1 for r in all_resources if r.status == "available")

        all_edges = db.query(VenueEdge).all()
        total_walkways = len(all_edges)
        blocked_walkways = sum(1 for e in all_edges if e.is_blocked)

        primary_metrics = PrimaryMetrics(
            active_incidents=active_incidents,
            pending_events=pending_events,
            processing_jobs=processing_jobs,
            critical_high_incidents=critical_high_incidents,
            available_resources=available_resources,
            total_resources=total_resources,
            blocked_walkways=blocked_walkways,
            total_walkways=total_walkways,
        )

        # -------------------------------------------------------------
        # 2. Incident Analytics (Filtered by Window + Distributions)
        # -------------------------------------------------------------
        inc_period_q = db.query(Incident).filter(
            Incident.created_at >= start_dt,
            Incident.created_at <= end_dt
        )
        total_inc_period = inc_period_q.count()

        # Status distribution (all existing in period)
        inc_status_counts = dict(
            db.query(Incident.status, func.count(Incident.id))
            .filter(Incident.created_at >= start_dt, Incident.created_at <= end_dt)
            .group_by(Incident.status)
            .all()
        )
        status_dist = {
            "open": inc_status_counts.get("open", 0),
            "acknowledged": inc_status_counts.get("acknowledged", 0),
            "in_progress": inc_status_counts.get("in_progress", 0),
            "resolved": inc_status_counts.get("resolved", 0),
            "closed": inc_status_counts.get("closed", 0),
        }

        # Severity distribution
        inc_sev_counts = dict(
            db.query(Incident.severity, func.count(Incident.id))
            .filter(Incident.created_at >= start_dt, Incident.created_at <= end_dt)
            .group_by(Incident.severity)
            .all()
        )
        sev_dist = {
            "critical": inc_sev_counts.get("critical", 0),
            "high": inc_sev_counts.get("high", 0),
            "medium": inc_sev_counts.get("medium", 0),
            "low": inc_sev_counts.get("low", 0),
        }

        # Average resolution duration in minutes
        resolved_with_times = db.query(Incident).filter(
            Incident.created_at >= start_dt,
            Incident.created_at <= end_dt,
            Incident.resolved_at.isnot(None)
        ).all()

        avg_resolution_min: Optional[float] = None
        if resolved_with_times:
            durations = [
                (inc.resolved_at - inc.created_at).total_seconds() / 60.0
                for inc in resolved_with_times
                if inc.resolved_at and inc.created_at and inc.resolved_at >= inc.created_at
            ]
            if durations:
                avg_resolution_min = round(sum(durations) / len(durations), 1)

        recent_incidents_db = db.query(Incident).order_by(desc(Incident.created_at)).limit(5).all()
        recent_inc_items = [
            IncidentOverviewItem(
                id=inc.id,
                incident_number=inc.incident_number,
                title=inc.title,
                severity=inc.severity,
                status=inc.status,
                zone_id=inc.zone_id,
                created_at=inc.created_at,
                updated_at=inc.updated_at,
            )
            for inc in recent_incidents_db
        ]

        incident_analytics = IncidentAnalytics(
            total_in_period=total_inc_period,
            active_count=active_incidents,
            status_distribution=status_dist,
            severity_distribution=sev_dist,
            avg_resolution_duration_minutes=avg_resolution_min,
            recent_incidents=recent_inc_items,
        )

        # -------------------------------------------------------------
        # 3. Crowd-Event Analytics
        # -------------------------------------------------------------
        ev_period_q = db.query(Event).filter(
            Event.created_at >= start_dt,
            Event.created_at <= end_dt
        )
        total_ev_period = ev_period_q.count()

        ev_status_counts = dict(
            db.query(Event.status, func.count(Event.id))
            .filter(Event.created_at >= start_dt, Event.created_at <= end_dt)
            .group_by(Event.status)
            .all()
        )
        ev_status_dist = {
            "pending_review": ev_status_counts.get("pending_review", 0),
            "acknowledged": ev_status_counts.get("acknowledged", 0),
            "dismissed": ev_status_counts.get("dismissed", 0),
            "resolved": ev_status_counts.get("resolved", 0),
        }

        ev_sev_counts = dict(
            db.query(Event.severity, func.count(Event.id))
            .filter(Event.created_at >= start_dt, Event.created_at <= end_dt)
            .group_by(Event.severity)
            .all()
        )
        ev_sev_dist = {
            "critical": ev_sev_counts.get("critical", 0),
            "high": ev_sev_counts.get("high", 0),
            "medium": ev_sev_counts.get("medium", 0),
            "low": ev_sev_counts.get("low", 0),
        }

        recent_events_db = db.query(Event).order_by(desc(Event.created_at)).limit(5).all()
        recent_ev_items = [
            EventOverviewItem(
                id=ev.id,
                rule_name=ev.rule_name,
                severity=ev.severity,
                status=ev.status,
                person_count=ev.person_count,
                zone_id=ev.zone_id,
                created_at=ev.created_at,
            )
            for ev in recent_events_db
        ]

        event_analytics = EventAnalytics(
            total_in_period=total_ev_period,
            pending_count=pending_events,
            status_distribution=ev_status_dist,
            severity_distribution=ev_sev_dist,
            recent_events=recent_ev_items,
        )

        # -------------------------------------------------------------
        # 4. Video-Processing Operations
        # -------------------------------------------------------------
        jobs_in_period = db.query(Job).filter(
            Job.created_at >= start_dt,
            Job.created_at <= end_dt
        ).all()
        total_jobs_period = len(jobs_in_period)

        job_status_counts: Dict[str, int] = {}
        total_detections_sum = 0
        failed_jobs_list: List[JobOverviewItem] = []

        for j in jobs_in_period:
            job_status_counts[j.status] = job_status_counts.get(j.status, 0) + 1
            total_detections_sum += j.total_persons_detected or 0
            if j.status == "failed":
                failed_jobs_list.append(
                    JobOverviewItem(
                        id=j.id,
                        video_id=j.video_id,
                        status=j.status,
                        progress_percent=j.progress_percent,
                        total_persons_detected=j.total_persons_detected,
                        created_at=j.created_at,
                        error_message=j.error_message,
                    )
                )

        job_analytics = JobAnalytics(
            total_in_period=total_jobs_period,
            status_distribution={
                "completed": job_status_counts.get("completed", 0),
                "failed": job_status_counts.get("failed", 0),
                "processing": job_status_counts.get("processing", 0),
                "queued": job_status_counts.get("queued", 0),
            },
            total_frame_detections=total_detections_sum,
            recent_failed_jobs=failed_jobs_list[:5],
        )

        # -------------------------------------------------------------
        # 5. Simulated Response Resources
        # -------------------------------------------------------------
        res_by_type: Dict[str, int] = {}
        assigned_units_list: List[AssignedResourceDetail] = []

        # Map incident numbers for assigned resources
        active_incidents_dict = {
            inc.id: inc.incident_number for inc in db.query(Incident.id, Incident.incident_number).all()
        }

        assigned_count = 0
        unavailable_count = 0
        for r in all_resources:
            res_by_type[r.resource_type] = res_by_type.get(r.resource_type, 0) + 1
            if r.status == "assigned":
                assigned_count += 1
                assigned_units_list.append(
                    AssignedResourceDetail(
                        id=r.id,
                        name=r.name,
                        call_sign=r.call_sign,
                        resource_type=r.resource_type,
                        assigned_incident_id=r.assigned_incident_id,
                        incident_number=active_incidents_dict.get(r.assigned_incident_id or "") if r.assigned_incident_id else None,
                    )
                )
            elif r.status in {"unavailable", "maintenance"}:
                unavailable_count += 1

        resource_analytics = ResourceAnalytics(
            total=total_resources,
            available=available_resources,
            assigned=assigned_count,
            unavailable=unavailable_count,
            by_type=res_by_type,
            assigned_units=assigned_units_list,
        )

        # -------------------------------------------------------------
        # 6. GIS Operations Overview
        # -------------------------------------------------------------
        blocked_details = [
            BlockedWalkwayDetail(
                id=e.id,
                name=e.name,
                from_node=e.from_node,
                to_node=e.to_node,
                blockage_reason=e.blockage_reason,
                blocked_at=e.blocked_at,
            )
            for e in all_edges if e.is_blocked
        ]

        gis_analytics = GisAnalytics(
            total_walkways=total_walkways,
            blocked_count=blocked_walkways,
            unblocked_count=total_walkways - blocked_walkways,
            blocked_details=blocked_details,
        )

        # -------------------------------------------------------------
        # 7. Operator Attention Queue (Actionable Prioritized Items)
        # -------------------------------------------------------------
        attention_queue: List[AttentionItem] = []

        # A. Unreviewed crowd events
        unreviewed_events = db.query(Event).filter(Event.status == "pending_review").order_by(desc(Event.created_at)).limit(5).all()
        for ev in unreviewed_events:
            attention_queue.append(
                AttentionItem(
                    category="pending_event",
                    level="warning" if ev.severity != "critical" else "critical",
                    title=f"Crowd Alert: {ev.rule_name} in {ev.zone_id}",
                    subtitle=f"{ev.person_count} persons detected (threshold: {ev.rule_threshold})",
                    entity_id=ev.id,
                    action_route="event_review",
                    timestamp=ev.created_at,
                )
            )

        # B. Critical active incidents
        crit_incidents = db.query(Incident).filter(
            Incident.status.in_(["open", "acknowledged", "in_progress"]),
            Incident.severity == "critical"
        ).order_by(desc(Incident.created_at)).limit(5).all()
        for inc in crit_incidents:
            attention_queue.append(
                AttentionItem(
                    category="critical_incident",
                    level="critical",
                    title=f"Critical Incident: {inc.incident_number}",
                    subtitle=inc.title,
                    entity_id=inc.id,
                    action_route="incidents",
                    timestamp=inc.created_at,
                )
            )

        # C. Active incidents without assigned squad
        unassigned_active = db.query(Incident).filter(
            Incident.status.in_(["open", "acknowledged"]),
            Incident.assigned_resource_id.is_(None)
        ).order_by(desc(Incident.created_at)).limit(5).all()
        for inc in unassigned_active:
            attention_queue.append(
                AttentionItem(
                    category="unassigned_incident",
                    level="warning",
                    title=f"Unassigned Incident: {inc.incident_number}",
                    subtitle=f"{inc.title} ({inc.severity.upper()} priority)",
                    entity_id=inc.id,
                    action_route="incidents",
                    timestamp=inc.created_at,
                )
            )

        # D. Blocked walkways
        for b_edge in blocked_details:
            attention_queue.append(
                AttentionItem(
                    category="blocked_walkway",
                    level="warning",
                    title=f"Blocked Walkway: {b_edge.name or b_edge.id}",
                    subtitle=f"Reason: {b_edge.blockage_reason or 'Walkway impassable'}",
                    entity_id=b_edge.id,
                    action_route="gis_operations",
                    timestamp=b_edge.blocked_at or now,
                )
            )

        # E. Failed video analysis jobs
        for fj in failed_jobs_list[:3]:
            attention_queue.append(
                AttentionItem(
                    category="failed_job",
                    level="warning",
                    title=f"Video Analysis Failed: Job {fj.id[:8]}",
                    subtitle=fj.error_message or "CV pipeline processing error",
                    entity_id=fj.id,
                    action_route="video_analysis",
                    timestamp=fj.created_at,
                )
            )

        # Sort attention queue by timestamp descending
        attention_queue.sort(key=lambda x: x.timestamp, reverse=True)

        # -------------------------------------------------------------
        # 8. Recent Activity Feed
        # -------------------------------------------------------------
        recent_audit_logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(10).all()
        activity_items = [
            ActivityItem(
                id=log.id,
                timestamp=log.timestamp,
                actor_id=log.actor_id,
                action_type=log.action_type,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                description=f"{log.actor_id} performed {log.action_type.replace('_', ' ')} on {log.entity_type} {log.entity_id[:8]}",
            )
            for log in recent_audit_logs
        ]

        return AnalyticsOverviewResponse(
            reporting_period=period_name,
            period_start=start_dt,
            period_end=end_dt,
            refreshed_at=now,
            metrics=primary_metrics,
            incidents=incident_analytics,
            events=event_analytics,
            jobs=job_analytics,
            resources=resource_analytics,
            gis=gis_analytics,
            attention_queue=attention_queue[:15],
            recent_activity=activity_items,
        )

    @staticmethod
    def get_trends(
        db: Session,
        period: str = "24h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> AnalyticsTrendsResponse:
        start_dt, end_dt, period_name = AnalyticsService.parse_time_window(period, start_date, end_date)
        duration = end_dt - start_dt

        # Use hourly buckets if window is <= 48 hours; otherwise daily
        use_hourly = duration.total_seconds() <= 48 * 3600
        interval_type = "hourly" if use_hourly else "daily"

        # Generate continuous bucket timestamps
        buckets: List[TrendBucket] = []
        cur_dt = start_dt

        # Fetch records within period to group in-memory
        incidents_in_period = db.query(Incident.created_at).filter(
            Incident.created_at >= start_dt,
            Incident.created_at <= end_dt
        ).all()
        events_in_period = db.query(Event.created_at).filter(
            Event.created_at >= start_dt,
            Event.created_at <= end_dt
        ).all()
        jobs_in_period = db.query(Job.completed_at).filter(
            Job.status == "completed",
            Job.completed_at >= start_dt,
            Job.completed_at <= end_dt
        ).all()

        step = timedelta(hours=1) if use_hourly else timedelta(days=1)

        while cur_dt < end_dt:
            next_dt = min(cur_dt + step, end_dt)
            label = cur_dt.strftime("%H:00") if use_hourly else cur_dt.strftime("%b %d")

            # Count occurrences in bucket [cur_dt, next_dt)
            inc_count = sum(
                1 for (t,) in incidents_in_period
                if t and (cur_dt <= (t if t.tzinfo else t.replace(tzinfo=timezone.utc)) < next_dt or (next_dt == end_dt and (t if t.tzinfo else t.replace(tzinfo=timezone.utc)) == end_dt))
            )
            ev_count = sum(
                1 for (t,) in events_in_period
                if t and (cur_dt <= (t if t.tzinfo else t.replace(tzinfo=timezone.utc)) < next_dt or (next_dt == end_dt and (t if t.tzinfo else t.replace(tzinfo=timezone.utc)) == end_dt))
            )
            job_count = sum(
                1 for (t,) in jobs_in_period
                if t and (cur_dt <= (t if t.tzinfo else t.replace(tzinfo=timezone.utc)) < next_dt or (next_dt == end_dt and (t if t.tzinfo else t.replace(tzinfo=timezone.utc)) == end_dt))
            )

            buckets.append(
                TrendBucket(
                    timestamp=cur_dt,
                    label=label,
                    incidents_created=inc_count,
                    events_created=ev_count,
                    jobs_completed=job_count,
                )
            )
            cur_dt = next_dt

        return AnalyticsTrendsResponse(
            reporting_period=period_name,
            period_start=start_dt,
            period_end=end_dt,
            interval=interval_type,
            buckets=buckets,
        )
