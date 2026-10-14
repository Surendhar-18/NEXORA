from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ReportFilterOptionItem(BaseModel):
    value: str
    label: str


class ReportFilterOption(BaseModel):
    name: str
    field: str
    type: str  # select, text, date
    default: Optional[str] = None
    options: Optional[List[ReportFilterOptionItem]] = None


class ReportTypeInfo(BaseModel):
    report_type: str
    title: str
    description: str
    supported_formats: List[str] = ["pdf", "csv"]
    available_filters: List[ReportFilterOption] = []


class ReportTypesResponse(BaseModel):
    report_types: List[ReportTypeInfo]


class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="Report category type")
    period: str = Field("24h", description="Standard period (24h, 7d, 30d, custom)")
    start_date: Optional[str] = Field(None, description="ISO datetime string for custom start")
    end_date: Optional[str] = Field(None, description="ISO datetime string for custom end")
    status: Optional[str] = Field(None, description="Optional status filter")
    severity: Optional[str] = Field(None, description="Optional severity filter")
    zone_id: Optional[str] = Field(None, description="Optional venue zone filter")
    action_type: Optional[str] = Field(None, description="Optional audit action type filter")
    entity_type: Optional[str] = Field(None, description="Optional audit entity type filter")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generic filter dictionary")
    limit: int = Field(500, ge=1, le=1000, description="Max records to include")


class ReportMetadata(BaseModel):
    report_id: str
    report_type: str
    report_title: str
    generation_time: str
    reporting_period: str
    period_start: str
    period_end: str
    timezone: str = "UTC"
    applied_filters: Dict[str, Any] = Field(default_factory=dict)
    record_count: int
    system_mode: str = "decision_support_prototype"
    disclaimer: str


class ReportPreviewResponse(BaseModel):
    metadata: ReportMetadata
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    columns: List[str] = Field(default_factory=list)
    records: List[Dict[str, Any]] = Field(default_factory=list)


class AuditExportRequest(BaseModel):
    period: str = Field("24h", description="Standard period (24h, 7d, 30d, custom)")
    start_date: Optional[str] = Field(None, description="ISO start date")
    end_date: Optional[str] = Field(None, description="ISO end date")
    action_type: Optional[str] = Field(None, description="Action filter")
    entity_type: Optional[str] = Field(None, description="Entity type filter")
    format: str = Field("csv", description="Export format (csv or pdf)")
    limit: int = Field(500, ge=1, le=2000, description="Max audit records")
