from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.api.deps import require_observer
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
    PrimaryMetrics,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Operational Analytics & Metrics"])

@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    period: str = Query("24h", description="Reporting period: '24h', '7d', '30d', 'custom'"),
    start_date: Optional[str] = Query(None, description="ISO start datetime for custom period"),
    end_date: Optional[str] = Query(None, description="ISO end datetime for custom period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    """
    Retrieve consolidated operational dashboard intelligence across video jobs,
    crowd events, incident lifecycles, simulated response units, and GIS walkways.
    """
    return AnalyticsService.get_overview(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/trends", response_model=AnalyticsTrendsResponse)
def get_analytics_trends(
    period: str = Query("24h", description="Reporting period: '24h', '7d', '30d', 'custom'"),
    start_date: Optional[str] = Query(None, description="ISO start datetime for custom period"),
    end_date: Optional[str] = Query(None, description="ISO end datetime for custom period"),
    db: Session = Depends(get_db)
):
    """
    Retrieve gapless time-series activity trends for incidents, crowd events,
    and completed video analysis jobs over the specified window.
    """
    return AnalyticsService.get_trends(
        db=db,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/metrics", response_model=PrimaryMetrics)
def get_primary_metrics_snapshot(
    db: Session = Depends(get_db)
):
    """
    Retrieve real-time primary operational KPIs (active incidents, pending alerts,
    processing jobs, resource availability, and blocked walkways).
    """
    overview = AnalyticsService.get_overview(db=db, period="24h")
    return overview.metrics
