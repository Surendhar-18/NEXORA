"""
NEXORA Phase 8 - Reports & Comprehensive Audit Export API Router.
Endpoints:
- GET /api/v1/reports/types
- POST /api/v1/reports/generate (Preview)
- POST /api/v1/reports/export/pdf
- POST /api/v1/reports/export/csv
- POST /api/v1/reports/audit/export
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.api.deps import require_operator, require_observer
from app.schemas.report import (
    ReportTypesResponse,
    ReportGenerateRequest,
    ReportPreviewResponse,
    AuditExportRequest,
)
from app.services.report_service import ReportService
from app.utils.csv_exporter import sanitize_filename

logger = logging.getLogger("nexora.api.reports")
router = APIRouter(prefix="/reports", tags=["Reports & Audit"])


@router.get(
    "/types",
    response_model=ReportTypesResponse,
    summary="List supported report types and configuration capabilities",
)
def get_supported_report_types(
    current_user: User = Depends(require_observer)
):
    types_list = ReportService.get_supported_types()
    return ReportTypesResponse(report_types=types_list)


@router.post(
    "/generate",
    response_model=ReportPreviewResponse,
    summary="Generate report preview and aggregated summary metrics",
)
def generate_report_preview(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    try:
        return ReportService.generate_preview(db, req)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate report preview: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating report data: {str(e)}",
        )


@router.post(
    "/export/pdf",
    summary="Export operational report as formatted PDF",
)
def export_report_pdf(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    try:
        filename, pdf_bytes = ReportService.export_pdf(db, req)
        safe_fname = sanitize_filename(filename)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_fname}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to export report PDF: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF document: {str(e)}",
        )


@router.post(
    "/export/csv",
    summary="Export operational report as sanitized CSV",
)
def export_report_csv(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer),
):
    try:
        filename, csv_bytes = ReportService.export_csv(db, req)
        safe_fname = sanitize_filename(filename)
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_fname}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to export report CSV: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CSV export: {str(e)}",
        )


@router.post(
    "/audit/export",
    summary="Direct export of chronological audit records",
)
def export_audit_log(
    req: AuditExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Dedicated shortcut for exporting deterministic chronological audit logs.
    """
    try:
        gen_req = ReportGenerateRequest(
            report_type="audit_report",
            period=req.period,
            start_date=req.start_date,
            end_date=req.end_date,
            action_type=req.action_type,
            entity_type=req.entity_type,
            limit=req.limit,
        )
        if req.format.lower() == "pdf":
            filename, pdf_bytes = ReportService.export_pdf(db, gen_req)
            safe_fname = sanitize_filename(filename)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_fname}"',
                    "Access-Control-Expose-Headers": "Content-Disposition",
                },
            )
        else:
            filename, csv_bytes = ReportService.export_csv(db, gen_req)
            safe_fname = sanitize_filename(filename)
            return Response(
                content=csv_bytes,
                media_type="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_fname}"',
                    "Access-Control-Expose-Headers": "Content-Disposition",
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to export audit log: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit records: {str(e)}",
        )
