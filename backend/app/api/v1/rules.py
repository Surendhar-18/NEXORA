import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.rule import CrowdRule
from app.models.job import Job
from app.models.audit import AuditLog
from app.models.user import User
from app.api.deps import require_operator, require_observer
from app.schemas.rule import (
    CrowdRuleCreate,
    CrowdRuleUpdate,
    CrowdRuleResponse,
    RuleListResponse,
)
from app.schemas.event import RuleEvaluationResponse, EventDetailResponse
from app.services.crowd_rules_engine import (
    evaluate_rules_for_job,
    seed_default_rules,
)

router = APIRouter(prefix="/rules", tags=["VisionX Crowd Rules"])

@router.get("", response_model=RuleListResponse)
def list_rules(
    active_only: bool = Query(False, description="Filter for active rules only"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """List all configured crowd-count rules."""
    seed_default_rules(db)
    query = db.query(CrowdRule)
    if active_only:
        query = query.filter(CrowdRule.is_active.is_(True))
    rules = query.order_by(CrowdRule.id.asc()).all()
    return RuleListResponse(
        rules=[build_rule_response(r) for r in rules],
        total=len(rules),
    )

@router.get("/{rule_id}", response_model=CrowdRuleResponse)
def get_rule_detail(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """Retrieve details of a single crowd-count rule."""
    rule = db.query(CrowdRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crowd rule '{rule_id}' not found",
        )
    return build_rule_response(rule)

@router.post("", response_model=CrowdRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: CrowdRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """Create a new configurable crowd-count rule."""
    actor_id = current_user.username
    rule_id = payload.id or f"RULE-CUSTOM-{uuid.uuid4().hex[:6].upper()}"
    existing = db.query(CrowdRule).filter_by(id=rule_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Rule with ID '{rule_id}' already exists",
        )

    if payload.rule_type not in ("threshold", "sustained"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="rule_type must be either 'threshold' or 'sustained'",
        )

    if payload.operator not in (">=", ">"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="operator must be either '>=' or '>'",
        )

    new_rule = CrowdRule(
        id=rule_id,
        name=payload.name,
        description=payload.description,
        rule_type=payload.rule_type,
        operator=payload.operator,
        threshold_count=payload.threshold_count,
        sustained_seconds=payload.sustained_seconds,
        min_consecutive_frames=payload.min_consecutive_frames,
        zone_id=payload.zone_id,
        severity=payload.severity,
        cooldown_seconds=payload.cooldown_seconds,
        is_active=payload.is_active,
        created_by=actor_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_rule)
    db.add(
        AuditLog(
            actor_id=actor_id,
            actor_role="operator",
            action_type="RULE_CREATED",
            entity_type="RULE",
            entity_id=new_rule.id,
            details={
                "name": new_rule.name,
                "threshold_count": new_rule.threshold_count,
                "rule_type": new_rule.rule_type,
            },
        )
    )
    db.commit()
    db.refresh(new_rule)
    return build_rule_response(new_rule)

@router.put("/{rule_id}", response_model=CrowdRuleResponse)
def update_rule(
    rule_id: str,
    payload: CrowdRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """Update configuration properties of an existing crowd rule."""
    rule = db.query(CrowdRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crowd rule '{rule_id}' not found",
        )

    updates = payload.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(rule, key, val)

    rule.updated_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_id=current_user.username,
            actor_role=current_user.role,
            action_type="RULE_UPDATED",
            entity_type="RULE",
            entity_id=rule.id,
            details=updates,
        )
    )
    db.commit()
    db.refresh(rule)
    return build_rule_response(rule)

@router.post("/evaluate/{job_id}", response_model=RuleEvaluationResponse)
def evaluate_job_rules(
    job_id: str,
    dry_run: bool = Query(False, description="Simulate evaluation without persisting events"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Explicitly trigger or re-evaluate crowd rules against a completed VisionX processing job.
    Idempotent: prevents duplicate event creation.
    """
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot evaluate rules on job with status '{job.status}'. Job must be 'completed'.",
        )

    events = evaluate_rules_for_job(job_id=job.id, db=db, dry_run=dry_run)

    from app.api.v1.events import build_event_response
    return RuleEvaluationResponse(
        job_id=job.id,
        events_generated_count=len(events),
        events=[build_event_response(ev) for ev in events],
    )

def build_rule_response(rule: CrowdRule) -> CrowdRuleResponse:
    return CrowdRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        operator=rule.operator,
        threshold_count=rule.threshold_count,
        sustained_seconds=rule.sustained_seconds,
        min_consecutive_frames=rule.min_consecutive_frames,
        zone_id=rule.zone_id,
        severity=rule.severity,
        cooldown_seconds=rule.cooldown_seconds,
        is_active=rule.is_active,
        created_by=rule.created_by,
        created_at=rule.created_at.isoformat() if rule.created_at else "",
        updated_at=rule.updated_at.isoformat() if rule.updated_at else "",
    )
