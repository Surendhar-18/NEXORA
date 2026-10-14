from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.api.deps import require_operator

router = APIRouter(prefix="/audit", tags=["Audit & Accountability"])

class AuditLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    timestamp: str
    actor_id: str
    actor_role: str
    action_type: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None

@router.get("", response_model=List[AuditLogOut], status_code=status.HTTP_200_OK)
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Retrieve audit trail records in descending chronological order.
    Demonstrates actual SQLite query execution and verifiable persistence.
    """
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    results = []
    for log in logs:
        results.append(AuditLogOut(
            id=log.id,
            timestamp=log.timestamp.isoformat() if log.timestamp else "",
            actor_id=log.actor_id,
            actor_role=log.actor_role,
            action_type=log.action_type,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details or {}
        ))
    return results
