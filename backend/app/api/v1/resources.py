from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.resource import ResourceListResponse, ResourceResponse
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["Response Resources"])

@router.get("", response_model=ResourceListResponse)
def list_resources(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by availability status (available, assigned, maintenance)"),
    resource_type: Optional[str] = Query(None, alias="type", description="Filter by resource type"),
    db: Session = Depends(get_db)
):
    """
    List all simulated response units with current availability and assignments.
    Notice: All units are simulated demo resources for operational planning.
    """
    result = ResourceService.list_resources(
        db=db,
        status_filter=status_filter,
        type_filter=resource_type
    )
    return ResourceListResponse(
        resources=[ResourceResponse.model_validate(r) for r in result["resources"]],
        total=result["total"],
        available=result["available"],
        assigned=result["assigned"],
        unavailable=result["unavailable"],
    )
