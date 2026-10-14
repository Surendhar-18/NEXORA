import React, { useEffect, useState, useCallback } from 'react';
import type {
  ReportTypeInfo,
  ReportPreviewResponse,
  AuditExportRequest,
} from '../types';
import { ApiClient } from '../api/client';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { StatusBadge } from '../components/common/StatusBadge';

export const ReportsAuditView: React.FC = () => {
  // Report Configuration State
  const [reportTypes, setReportTypes] = useState<ReportTypeInfo[]>([]);
  const [selectedType, setSelectedType] = useState<string>('operational_summary');
  const [period, setPeriod] = useState<string>('24h');
  const [customStart, setCustomStart] = useState<string>('');
  const [customEnd, setCustomEnd] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [zoneFilter, setZoneFilter] = useState<string>('');
  const [actionTypeFilter, setActionTypeFilter] = useState<string>('');

  // Generation & Export State
  const [preview, setPreview] = useState<ReportPreviewResponse | null>(null);
  const [loadingPreview, setLoadingPreview] = useState<boolean>(false);
  const [exportingPdf, setExportingPdf] = useState<boolean>(false);
  const [exportingCsv, setExportingCsv] = useState<boolean>(false);
  const [exportingAudit, setExportingAudit] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Helper: Trigger browser file download from Blob
  const triggerDownload = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 200);
  };

  // Load supported report types on mount
  useEffect(() => {
    const loadTypes = async () => {
      try {
        const res = await ApiClient.getReportTypes();
        setReportTypes(res.report_types);
        if (res.report_types.length > 0) {
          setSelectedType(res.report_types[0].report_type);
        }
      } catch (err) {
        console.error('Failed to load report types:', err);
      }
    };
    loadTypes();
  }, []);

  // Generate Report Preview
  const handleGeneratePreview = useCallback(async () => {
    setLoadingPreview(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const filters: Record<string, unknown> = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (severityFilter !== 'all') filters.severity = severityFilter;
      if (zoneFilter.trim()) filters.zone_id = zoneFilter.trim();
      if (actionTypeFilter.trim()) filters.action_type = actionTypeFilter.trim();

      const res = await ApiClient.generateReportPreview({
        report_type: selectedType,
        period,
        start_date: period === 'custom' ? customStart : undefined,
        end_date: period === 'custom' ? customEnd : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        severity: severityFilter !== 'all' ? severityFilter : undefined,
        zone_id: zoneFilter.trim() || undefined,
        action_type: actionTypeFilter.trim() || undefined,
        filters,
        limit: 500,
      });
      setPreview(res);
      setSuccessMessage(`Generated preview with ${res.metadata.record_count} records.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoadingPreview(false);
    }
  }, [selectedType, period, customStart, customEnd, statusFilter, severityFilter, zoneFilter, actionTypeFilter]);

  // Initial preview generation once report types are ready
  useEffect(() => {
    if (reportTypes.length > 0) {
      handleGeneratePreview();
    }
  }, [selectedType, handleGeneratePreview, reportTypes.length]);

  // Export PDF
  const handleExportPdf = async () => {
    setExportingPdf(true);
    setError(null);
    try {
      const filters: Record<string, unknown> = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (severityFilter !== 'all') filters.severity = severityFilter;
      if (zoneFilter.trim()) filters.zone_id = zoneFilter.trim();
      if (actionTypeFilter.trim()) filters.action_type = actionTypeFilter.trim();

      const { blob, filename } = await ApiClient.downloadReportPdf({
        report_type: selectedType,
        period,
        start_date: period === 'custom' ? customStart : undefined,
        end_date: period === 'custom' ? customEnd : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        severity: severityFilter !== 'all' ? severityFilter : undefined,
        zone_id: zoneFilter.trim() || undefined,
        action_type: actionTypeFilter.trim() || undefined,
        filters,
        limit: 1000,
      });
      triggerDownload(blob, filename);
      setSuccessMessage(`Downloaded PDF report: ${filename}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setExportingPdf(false);
    }
  };

  // Export CSV
  const handleExportCsv = async () => {
    setExportingCsv(true);
    setError(null);
    try {
      const filters: Record<string, unknown> = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (severityFilter !== 'all') filters.severity = severityFilter;
      if (zoneFilter.trim()) filters.zone_id = zoneFilter.trim();
      if (actionTypeFilter.trim()) filters.action_type = actionTypeFilter.trim();

      const { blob, filename } = await ApiClient.downloadReportCsv({
        report_type: selectedType,
        period,
        start_date: period === 'custom' ? customStart : undefined,
        end_date: period === 'custom' ? customEnd : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        severity: severityFilter !== 'all' ? severityFilter : undefined,
        zone_id: zoneFilter.trim() || undefined,
        action_type: actionTypeFilter.trim() || undefined,
        filters,
        limit: 1000,
      });
      triggerDownload(blob, filename);
      setSuccessMessage(`Downloaded CSV report: ${filename}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setExportingCsv(false);
    }
  };

  // Direct Audit Export
  const handleQuickAuditExport = async (format: 'csv' | 'pdf') => {
    setExportingAudit(true);
    setError(null);
    try {
      const req: AuditExportRequest = {
        period,
        start_date: period === 'custom' ? customStart : undefined,
        end_date: period === 'custom' ? customEnd : undefined,
        format,
        limit: 1000,
      };
      const { blob, filename } = await ApiClient.exportAudit(req);
      triggerDownload(blob, filename);
      setSuccessMessage(`Downloaded Audit Log (${format.toUpperCase()}): ${filename}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setExportingAudit(false);
    }
  };

  const activeTypeInfo = reportTypes.find((t) => t.report_type === selectedType);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* 1. Header Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: 'var(--space-4) var(--space-5)',
          backgroundColor: 'var(--color-carbon-lift)',
          border: 'var(--border-hairline)',
          borderRadius: 'var(--radius-xs)',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
        }}
      >
        <div>
          <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
            OPERATIONAL COMPLIANCE // PHASE 8 REPORTS & AUDIT LEDGER
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 500, letterSpacing: '-0.02em', marginTop: '2px' }}>
            Reports & Comprehensive Audit Export
          </h1>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <button
            onClick={() => handleQuickAuditExport('csv')}
            disabled={exportingAudit}
            className="btn btn-secondary"
            style={{ fontSize: '12px' }}
          >
            {exportingAudit ? 'EXPORTING...' : 'EXPORT AUDIT CSV'}
          </button>
          <button
            onClick={() => handleQuickAuditExport('pdf')}
            disabled={exportingAudit}
            className="btn btn-secondary"
            style={{ fontSize: '12px' }}
          >
            {exportingAudit ? 'EXPORTING...' : 'EXPORT AUDIT PDF'}
          </button>
        </div>
      </div>

      {/* 2. Success / Error Feedback Alerts */}
      {error && (
        <div
          style={{
            backgroundColor: '#2b1414',
            border: '1px solid var(--color-alert-red)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-xs)',
            fontSize: '13px',
            color: 'var(--color-bone)',
          }}
        >
          {error}
        </div>
      )}

      {successMessage && (
        <div
          style={{
            backgroundColor: '#162319',
            border: '1px solid var(--color-metric-green)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-xs)',
            fontSize: '13px',
            color: 'var(--color-light)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>{successMessage}</span>
          <button
            onClick={() => setSuccessMessage(null)}
            style={{ background: 'none', border: 'none', color: 'var(--color-pale-stone)', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* 3. Report Configuration Section */}
      <Card
        title="Report Parameters & Scope Configuration"
        subtitle="FILTERED SERVER-SIDE EXTRACTION FROM PERSISTED NEXORA DATA"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Report Type Selector Pills */}
          <div>
            <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-2)' }}>
              1. Select Report Category
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
              {reportTypes.map((rt) => {
                const isActive = rt.report_type === selectedType;
                return (
                  <button
                    key={rt.report_type}
                    onClick={() => {
                      setSelectedType(rt.report_type);
                      setStatusFilter('all');
                      setSeverityFilter('all');
                      setZoneFilter('');
                      setActionTypeFilter('');
                    }}
                    style={{
                      padding: '6px 12px',
                      fontSize: '12px',
                      fontFamily: 'var(--font-sans)',
                      borderRadius: 'var(--radius-xs)',
                      border: isActive ? '1px solid var(--color-signal-orange)' : '1px solid var(--color-ash-stroke)',
                      backgroundColor: isActive ? 'rgba(238, 96, 24, 0.15)' : 'var(--color-carbon-lift)',
                      color: isActive ? 'var(--color-bone)' : 'var(--color-pale-stone)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {rt.title}
                  </button>
                );
              })}
            </div>
            {activeTypeInfo && (
              <p style={{ fontSize: '12px', color: 'var(--color-pale-stone)', marginTop: 'var(--space-2)', marginBlockEnd: 0 }}>
                {activeTypeInfo.description}
              </p>
            )}
          </div>

          {/* Reporting Period & Scope Filters */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)', alignItems: 'end' }}>
            {/* Period Selector */}
            <div>
              <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                Reporting Period
              </label>
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="input-select"
                style={{
                  width: '100%',
                  padding: '6px 10px',
                  backgroundColor: 'var(--color-obsidian)',
                  border: 'var(--border-hairline)',
                  color: 'var(--color-bone)',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '12px',
                }}
              >
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="custom">Custom ISO Date Range</option>
              </select>
            </div>

            {/* Custom Date Inputs if selected */}
            {period === 'custom' && (
              <>
                <div>
                  <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                    Start Date / Time (UTC)
                  </label>
                  <input
                    type="datetime-local"
                    value={customStart}
                    onChange={(e) => setCustomStart(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '5px 8px',
                      backgroundColor: 'var(--color-obsidian)',
                      border: 'var(--border-hairline)',
                      color: 'var(--color-bone)',
                      borderRadius: 'var(--radius-xs)',
                      fontSize: '12px',
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                    End Date / Time (UTC)
                  </label>
                  <input
                    type="datetime-local"
                    value={customEnd}
                    onChange={(e) => setCustomEnd(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '5px 8px',
                      backgroundColor: 'var(--color-obsidian)',
                      border: 'var(--border-hairline)',
                      color: 'var(--color-bone)',
                      borderRadius: 'var(--radius-xs)',
                      fontSize: '12px',
                    }}
                  />
                </div>
              </>
            )}

            {/* Dynamic Filters depending on type */}
            {(selectedType === 'incident_report' || selectedType === 'crowd_event_report') && (
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Severity Filter
                </label>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    backgroundColor: 'var(--color-obsidian)',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12px',
                  }}
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            )}

            {selectedType === 'incident_report' && (
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Incident Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    backgroundColor: 'var(--color-obsidian)',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12px',
                  }}
                >
                  <option value="all">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="acknowledged">Acknowledged</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            )}

            {selectedType === 'crowd_event_report' && (
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Review Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    backgroundColor: 'var(--color-obsidian)',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12px',
                  }}
                >
                  <option value="all">All States</option>
                  <option value="pending_review">Pending Review</option>
                  <option value="acknowledged">Acknowledged</option>
                  <option value="dismissed">Dismissed</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
            )}

            {selectedType === 'video_analysis_report' && (
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Job Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    backgroundColor: 'var(--color-obsidian)',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12px',
                  }}
                >
                  <option value="all">All Statuses</option>
                  <option value="queued">Queued</option>
                  <option value="processing">Processing</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            )}

            {selectedType === 'gis_operations_report' && (
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Walkway Blockage
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    backgroundColor: 'var(--color-obsidian)',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12px',
                  }}
                >
                  <option value="all">All Walkways</option>
                  <option value="blocked_only">Blocked Walkways Only</option>
                  <option value="open_only">Open Walkways Only</option>
                </select>
              </div>
            )}

            {selectedType === 'resource_deployment_report' && (
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Resource Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    backgroundColor: 'var(--color-obsidian)',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12px',
                  }}
                >
                  <option value="all">All Statuses</option>
                  <option value="available">Available</option>
                  <option value="assigned">Assigned</option>
                  <option value="unavailable">Unavailable</option>
                </select>
              </div>
            )}

            {selectedType === 'audit_report' && (
              <div>
                <label style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-warm-granite)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Action Type
                </label>
                <input
                  type="text"
                  placeholder="e.g. incident_status_update"
                  value={actionTypeFilter}
                  onChange={(e) => setActionTypeFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px',
                    backgroundColor: 'var(--color-obsidian)',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '12px',
                  }}
                />
              </div>
            )}

            {/* Action Button: Generate Preview */}
            <div>
              <button
                onClick={handleGeneratePreview}
                disabled={loadingPreview}
                className="btn btn-primary"
                style={{ width: '100%', padding: '7px 12px', fontSize: '12px' }}
              >
                {loadingPreview ? 'GENERATING PREVIEW...' : 'GENERATE PREVIEW'}
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* 4. Report Preview Area */}
      <Card
        title={preview ? preview.metadata.report_title : 'Report Preview'}
        subtitle={preview ? `REPORT ID: ${preview.metadata.report_id} // PERIOD: ${preview.metadata.reporting_period}` : 'OPERATIONAL PREVIEW'}
        badge={
          preview ? (
            <StatusBadge status="active" label={`${preview.metadata.record_count} RECORDS`} />
          ) : undefined
        }
      >
        {loadingPreview && <LoadingSpinner message="Aggregating records and compiling summary metrics..." />}

        {!loadingPreview && !preview && (
          <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--color-warm-granite)' }}>
            Configure reporting filters above and click &quot;Generate Preview&quot; to review data.
          </div>
        )}

        {!loadingPreview && preview && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            {/* Disclaimer & Metadata Banner */}
            <div
              style={{
                backgroundColor: 'rgba(238, 96, 24, 0.08)',
                border: '1px solid rgba(238, 96, 24, 0.4)',
                borderRadius: 'var(--radius-xs)',
                padding: 'var(--space-3) var(--space-4)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 'var(--space-2)',
              }}
            >
              <div style={{ fontSize: '12px', color: 'var(--color-bone)' }}>
                <strong>NOTICE:</strong> {preview.metadata.disclaimer}
              </div>
              <div className="mono-metric" style={{ fontSize: '11px', color: 'var(--color-warm-granite)' }}>
                Gen: {preview.metadata.generation_time.slice(0, 19).replace('T', ' ')} UTC
              </div>
            </div>

            {/* Summary Metrics KPI Grid */}
            {preview.summary_metrics && Object.keys(preview.summary_metrics).length > 0 && (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: 'var(--space-3)',
                }}
              >
                {Object.entries(preview.summary_metrics).map(([key, val]) => (
                  <div
                    key={key}
                    style={{
                      backgroundColor: 'var(--color-carbon-lift)',
                      border: 'var(--border-hairline)',
                      borderRadius: 'var(--radius-xs)',
                      padding: 'var(--space-3)',
                    }}
                  >
                    <div className="mono-caption" style={{ color: 'var(--color-warm-granite)', marginBottom: '4px' }}>
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </div>
                    <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-bone)', fontFamily: 'var(--font-mono)' }}>
                      {val !== null && val !== undefined ? String(val) : '—'}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Export Toolbar */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingTop: 'var(--space-2)',
                borderTop: 'var(--border-hairline)',
                flexWrap: 'wrap',
                gap: 'var(--space-2)',
              }}
            >
              <div style={{ fontSize: '12px', color: 'var(--color-pale-stone)' }}>
                Records returned: <strong>{preview.metadata.record_count}</strong> (Showing up to {preview.records.length} in preview)
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                <button
                  onClick={handleExportPdf}
                  disabled={exportingPdf || preview.records.length === 0}
                  className="btn btn-secondary"
                  style={{
                    fontSize: '12px',
                    borderColor: 'var(--color-signal-orange)',
                    color: 'var(--color-signal-orange)',
                  }}
                >
                  {exportingPdf ? 'GENERATING PDF...' : 'EXPORT PDF'}
                </button>
                <button
                  onClick={handleExportCsv}
                  disabled={exportingCsv || preview.records.length === 0}
                  className="btn btn-secondary"
                  style={{ fontSize: '12px' }}
                >
                  {exportingCsv ? 'GENERATING CSV...' : 'EXPORT CSV'}
                </button>
              </div>
            </div>

            {/* Data Records Table */}
            {preview.records.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: 'var(--space-6)',
                  color: 'var(--color-warm-granite)',
                  backgroundColor: 'var(--color-carbon-lift)',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                No records matched the selected filters and time period.
              </div>
            ) : (
              <div style={{ overflowX: 'auto', border: 'var(--border-hairline)', borderRadius: 'var(--radius-xs)' }}>
                <table className="data-table" style={{ width: '100%', margin: 0 }}>
                  <thead>
                    <tr>
                      {preview.columns.map((col) => (
                        <th key={col} style={{ textTransform: 'capitalize' }}>
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.records.map((row, idx) => (
                      <tr key={idx}>
                        {preview.columns.map((col) => {
                          const val = row[col];
                          const isTimestamp = col.includes('at') || col.includes('timestamp');
                          const isId = col.includes('id') || col.includes('number') || col.includes('call_sign');
                          return (
                            <td
                              key={col}
                              className={isTimestamp || isId ? 'mono-metric' : undefined}
                              style={{
                                fontSize: '12px',
                                whiteSpace: isTimestamp ? 'nowrap' : undefined,
                              }}
                            >
                              {val !== null && val !== undefined ? String(val) : '—'}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
