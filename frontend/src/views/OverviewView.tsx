import React, { useState, useEffect, useCallback, useMemo } from 'react';
import type {
  HealthResponse,
  ViewMode,
  AnalyticsOverviewResponse,
  AnalyticsTrendsResponse,
  TrendBucket,
  AttentionItem,
} from '../types';
import { ApiClient } from '../api/client';
import { Card } from '../components/common/Card';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  RotateCcw,
  AlertTriangle,
  Flame,
  Shield,
  Video,
  Eye,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  MapPin,
  Calendar,
  ChevronRight,
} from 'lucide-react';

interface OverviewViewProps {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
  onRefreshHealth: () => void;
  onNavigate?: (view: ViewMode) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  health,
  onRefreshHealth,
  onNavigate,
}) => {
  // Period filter state
  const [period, setPeriod] = useState<'24h' | '7d' | '30d' | 'custom'>('24h');
  const [customStart, setCustomStart] = useState<string>('');
  const [customEnd, setCustomEnd] = useState<string>('');
  const [customInputError, setCustomInputError] = useState<string | null>(null);

  // Overview and Trends data state
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrendsResponse | null>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState<boolean>(true);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState<boolean>(true);
  const [hoveredBucket, setHoveredBucket] = useState<TrendBucket | null>(null);

  // Fetch Analytics Function
  const fetchAnalytics = useCallback(async () => {
    setLoadingAnalytics(true);
    setAnalyticsError(null);
    setCustomInputError(null);

    const params: { period?: string; start_date?: string; end_date?: string } = {
      period,
    };

    if (period === 'custom') {
      if (!customStart || !customEnd) {
        setCustomInputError('Both start and end dates are required for custom time window.');
        setLoadingAnalytics(false);
        return;
      }
      if (new Date(customStart) >= new Date(customEnd)) {
        setCustomInputError('Start date must be earlier than end date.');
        setLoadingAnalytics(false);
        return;
      }
      params.start_date = new Date(customStart).toISOString();
      params.end_date = new Date(customEnd).toISOString();
    }

    try {
      const [overviewData, trendsData] = await Promise.all([
        ApiClient.getAnalyticsOverview(params),
        ApiClient.getAnalyticsTrends(params),
      ]);
      setOverview(overviewData);
      setTrends(trendsData);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      setAnalyticsError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoadingAnalytics(false);
    }
  }, [period, customStart, customEnd]);

  // Initial load and periodic refresh (30s)
  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  useEffect(() => {
    if (!autoRefreshEnabled) return;
    const interval = setInterval(() => {
      fetchAnalytics();
      onRefreshHealth();
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefreshEnabled, fetchAnalytics, onRefreshHealth]);

  // Format Helper
  const formatDateTime = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
    try {
      const dt = new Date(isoString);
      return dt.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
    } catch {
      return isoString;
    }
  };

  // SVG Chart Scaling Calculations
  const chartHeight = 160;
  const chartWidth = 720;
  const chartPadding = { top: 20, right: 20, bottom: 30, left: 40 };

  const { maxVal, pointsIncidents, pointsEvents, pointsJobs, xStep } = useMemo(() => {
    if (!trends || !trends.buckets || trends.buckets.length === 0) {
      return { maxVal: 5, pointsIncidents: '', pointsEvents: '', pointsJobs: '', xStep: 0 };
    }
    const buckets = trends.buckets;
    let max = 1;
    buckets.forEach((b) => {
      if (b.incidents_created > max) max = b.incidents_created;
      if (b.events_created > max) max = b.events_created;
      if (b.jobs_completed > max) max = b.jobs_completed;
    });
    const ceilMax = Math.ceil(max * 1.25);
    const usableWidth = chartWidth - chartPadding.left - chartPadding.right;
    const usableHeight = chartHeight - chartPadding.top - chartPadding.bottom;
    const step = buckets.length > 1 ? usableWidth / (buckets.length - 1) : usableWidth;

    const getX = (idx: number) => chartPadding.left + idx * step;
    const getY = (val: number) => chartHeight - chartPadding.bottom - (val / ceilMax) * usableHeight;

    const pInc = buckets.map((b, i) => `${getX(i)},${getY(b.incidents_created)}`).join(' ');
    const pEv = buckets.map((b, i) => `${getX(i)},${getY(b.events_created)}`).join(' ');
    const pJob = buckets.map((b, i) => `${getX(i)},${getY(b.jobs_completed)}`).join(' ');

    return {
      maxVal: ceilMax,
      pointsIncidents: pInc,
      pointsEvents: pEv,
      pointsJobs: pJob,
      xStep: step,
    };
  }, [trends]);

  const handleNavigate = (view: ViewMode) => {
    if (onNavigate) {
      onNavigate(view);
    }
  };

  const handleAttentionClick = (item: AttentionItem) => {
    if (item.action_route?.includes('/events') || item.category === 'pending_event') {
      handleNavigate('event_review');
    } else if (item.action_route?.includes('/incidents') || item.category === 'critical_incident' || item.category === 'unassigned_incident') {
      handleNavigate('incidents');
    } else if (item.action_route?.includes('/venue') || item.category === 'blocked_walkway') {
      handleNavigate('gis_operations');
    } else if (item.action_route?.includes('/jobs') || item.category === 'failed_job') {
      handleNavigate('video_analysis');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* =========================================================
          1. Operational Header & Controls
          ========================================================= */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 'var(--space-4)',
          padding: 'var(--space-4) var(--space-5)',
          backgroundColor: 'var(--color-carbon-lift)',
          border: 'var(--border-hairline)',
          borderRadius: 'var(--radius-xs)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span
              className="mono-caption"
              style={{
                color: 'var(--color-signal-orange)',
                fontWeight: 600,
                letterSpacing: '0.06em',
              }}
            >
              NEXORA OPERATIONAL INTELLIGENCE // REAL-TIME CONSOLE
            </span>
            <span
              className="mono-caption"
              style={{
                backgroundColor: '#262220',
                padding: '1px 6px',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--color-ash-stroke)',
                color: 'var(--color-pale-stone)',
              }}
            >
              POST-ANALYSIS DATASTORE
            </span>
            {health && (
              <StatusBadge
                status={health.status === 'healthy' ? 'healthy' : 'degraded'}
                label={`API: ${health.status.toUpperCase()}`}
              />
            )}
          </div>
          <h1
            style={{
              fontSize: '22px',
              fontWeight: 500,
              letterSpacing: '-0.02em',
              marginTop: '4px',
              color: 'var(--color-chalk)',
            }}
          >
            Unified Operational Command & Analytics
          </h1>
          <p
            style={{
              fontSize: '12px',
              color: 'var(--color-warm-granite)',
              marginTop: '2px',
            }}
          >
            Recorded video analysis and persisted operations datastore. Metrics reflect verified SQLite records.
          </p>
        </div>

        {/* Controls: Reporting Window & Refresh Actions */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Period Selector Tabs */}
          <div
            style={{
              display: 'flex',
              backgroundColor: 'var(--color-obsidian-canvas)',
              border: 'var(--border-hairline)',
              borderRadius: 'var(--radius-xs)',
              padding: '2px',
            }}
          >
            {(['24h', '7d', '30d', 'custom'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                style={{
                  background: period === p ? 'var(--color-graphite-mid)' : 'transparent',
                  color: period === p ? 'var(--color-chalk)' : 'var(--color-pale-stone)',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-xs)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontWeight: period === p ? 600 : 400,
                  transition: 'background 0.15s ease',
                }}
              >
                {p.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Freshness Badge & Auto Refresh Toggle */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-warm-granite)',
            }}
          >
            <Clock size={12} color="var(--color-warm-granite)" />
            <span>LAST SYNC: {lastRefreshed || 'INITIALIZING'}</span>
          </div>

          <button
            onClick={fetchAnalytics}
            disabled={loadingAnalytics}
            className="btn btn-secondary"
            title="Force immediate reload of all operational metrics"
            style={{ minWidth: '100px', fontSize: '12px', padding: '5px 12px' }}
          >
            <RotateCcw size={13} className={loadingAnalytics ? 'animate-spin' : ''} />
            {loadingAnalytics ? 'SYNCING...' : 'REFRESH'}
          </button>

          <button
            onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
            className="btn"
            style={{
              backgroundColor: autoRefreshEnabled ? '#1e2b1d' : 'var(--color-carbon-lift)',
              borderColor: autoRefreshEnabled ? 'var(--color-metric-green)' : 'var(--color-ash-stroke)',
              color: autoRefreshEnabled ? 'var(--color-metric-green)' : 'var(--color-warm-granite)',
              fontSize: '11px',
              padding: '5px 10px',
            }}
            title="Toggle 30-second background polling"
          >
            {autoRefreshEnabled ? '● AUTO (30S)' : '○ PAUSED'}
          </button>
        </div>
      </div>

      {/* Custom Window Expandable Form */}
      {period === 'custom' && (
        <div
          style={{
            backgroundColor: 'var(--color-carbon-lift)',
            border: 'var(--border-hairline)',
            borderRadius: 'var(--radius-xs)',
            padding: 'var(--space-3) var(--space-4)',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 'var(--space-4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Calendar size={14} color="var(--color-signal-orange)" />
            <span className="mono-caption" style={{ color: 'var(--color-chalk)' }}>
              CUSTOM TIME BOUNDARY (UTC):
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <label className="mono-caption">FROM:</label>
            <input
              type="datetime-local"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              style={{
                backgroundColor: 'var(--color-obsidian-canvas)',
                color: 'var(--color-bone)',
                border: 'var(--border-hairline)',
                padding: '4px 8px',
                borderRadius: 'var(--radius-xs)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <label className="mono-caption">TO:</label>
            <input
              type="datetime-local"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              style={{
                backgroundColor: 'var(--color-obsidian-canvas)',
                color: 'var(--color-bone)',
                border: 'var(--border-hairline)',
                padding: '4px 8px',
                borderRadius: 'var(--radius-xs)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
              }}
            />
          </div>
          <button onClick={fetchAnalytics} className="btn btn-primary" style={{ padding: '4px 12px', fontSize: '12px' }}>
            APPLY FILTER
          </button>
          {customInputError && (
            <span style={{ color: 'var(--color-alert-red)', fontSize: '12px' }}>{customInputError}</span>
          )}
        </div>
      )}

      {/* Global Error Banner */}
      {analyticsError && (
        <div
          style={{
            backgroundColor: '#2b1414',
            border: '1px solid var(--color-alert-red)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-xs)',
            color: 'var(--color-bone)',
          }}
        >
          <div className="mono-caption" style={{ color: 'var(--color-alert-red)' }}>
            METRIC AGGREGATION FAILURE
          </div>
          <div style={{ marginTop: 'var(--space-2)', fontSize: '13px' }}>{analyticsError}</div>
          <button
            onClick={fetchAnalytics}
            className="btn btn-secondary"
            style={{ marginTop: 'var(--space-3)', fontSize: '12px' }}
          >
            RETRY AGGREGATION
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loadingAnalytics && !overview && <LoadingSpinner message="AGGREGATING OPERATIONAL INTELLIGENCE METRICS..." />}

      {overview && (
        <>
          {/* =========================================================
              2. Key Operational Metrics Cards (6 Primary Cards)
              ========================================================= */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: 'var(--space-3)',
            }}
          >
            {/* Card 1: Active Incidents */}
            <div
              onClick={() => handleNavigate('incidents')}
              className="card-surface"
              style={{
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, background 0.15s ease',
                position: 'relative',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="mono-caption">ACTIVE INCIDENTS</span>
                <ArrowUpRight size={14} color="var(--color-warm-granite)" />
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  color: overview.metrics.active_incidents > 0 ? 'var(--color-signal-orange)' : 'var(--color-bone)',
                  margin: 'var(--space-2) 0',
                }}
              >
                {overview.metrics.active_incidents}
              </div>
              <div className="mono-caption" style={{ fontSize: '10px' }}>
                OPEN / ACK / IN PROGRESS (EXCL RESOLVED)
              </div>
            </div>

            {/* Card 2: Pending Crowd Events */}
            <div
              onClick={() => handleNavigate('event_review')}
              className="card-surface"
              style={{
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, background 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="mono-caption">PENDING REVIEW</span>
                <Eye size={14} color="var(--color-warm-granite)" />
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  color: overview.metrics.pending_events > 0 ? 'var(--color-signal-orange)' : 'var(--color-bone)',
                  margin: 'var(--space-2) 0',
                }}
              >
                {overview.metrics.pending_events}
              </div>
              <div className="mono-caption" style={{ fontSize: '10px' }}>
                UNREVIEWED THRESHOLD SURGES
              </div>
            </div>

            {/* Card 3: Active Video Jobs */}
            <div
              onClick={() => handleNavigate('video_analysis')}
              className="card-surface"
              style={{
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, background 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="mono-caption">ACTIVE JOBS</span>
                <Video size={14} color="var(--color-warm-granite)" />
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  color: overview.metrics.processing_jobs > 0 ? 'var(--color-metric-green)' : 'var(--color-bone)',
                  margin: 'var(--space-2) 0',
                }}
              >
                {overview.metrics.processing_jobs}
              </div>
              <div className="mono-caption" style={{ fontSize: '10px' }}>
                QUEUED OR IN-PROGRESS CV PIPELINE
              </div>
            </div>

            {/* Card 4: Critical Severity Incidents */}
            <div
              onClick={() => handleNavigate('incidents')}
              className="card-surface"
              style={{
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, background 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="mono-caption">CRITICAL LEVEL</span>
                <Flame
                  size={14}
                  color={overview.metrics.critical_high_incidents > 0 ? 'var(--color-alert-red)' : 'var(--color-warm-granite)'}
                />
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  color: overview.metrics.critical_high_incidents > 0 ? 'var(--color-alert-red)' : 'var(--color-bone)',
                  margin: 'var(--space-2) 0',
                }}
              >
                {overview.metrics.critical_high_incidents}
              </div>
              <div className="mono-caption" style={{ fontSize: '10px' }}>
                ACTIVE HIGH-RISK INCIDENTS
              </div>
            </div>

            {/* Card 5: Available Response Units */}
            <div
              onClick={() => handleNavigate('incidents')}
              className="card-surface"
              style={{
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, background 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="mono-caption">AVAILABLE SQUADS</span>
                <Shield size={14} color="var(--color-warm-granite)" />
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--color-metric-green)',
                  margin: 'var(--space-2) 0',
                }}
              >
                {overview.metrics.available_resources}
                <span style={{ fontSize: '16px', color: 'var(--color-warm-granite)', fontWeight: 400 }}>
                  {' '}
                  / {overview.metrics.total_resources}
                </span>
              </div>
              <div className="mono-caption" style={{ fontSize: '10px' }}>
                SIMULATED REGISTRY UNITS (DEMO)
              </div>
            </div>

            {/* Card 6: Blocked Walkways */}
            <div
              onClick={() => handleNavigate('gis_operations')}
              className="card-surface"
              style={{
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, background 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="mono-caption">BLOCKED PATHS</span>
                <MapPin
                  size={14}
                  color={overview.metrics.blocked_walkways > 0 ? 'var(--color-signal-orange)' : 'var(--color-warm-granite)'}
                />
              </div>
              <div
                style={{
                  fontSize: '32px',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  color: overview.metrics.blocked_walkways > 0 ? 'var(--color-signal-orange)' : 'var(--color-bone)',
                  margin: 'var(--space-2) 0',
                }}
              >
                {overview.metrics.blocked_walkways}
                <span style={{ fontSize: '16px', color: 'var(--color-warm-granite)', fontWeight: 400 }}>
                  {' '}
                  / {overview.metrics.total_walkways}
                </span>
              </div>
              <div className="mono-caption" style={{ fontSize: '10px' }}>
                IMPASSABLE GIS SEGMENTS
              </div>
            </div>
          </div>

          {/* =========================================================
              3. Time-Series Trends: Gapless Activity History
              ========================================================= */}
          <Card
            title={`Operational Activity History // ${period.toUpperCase()}`}
            subtitle={`CHRONOLOGICAL PERSISTENCE TIMELINE (${trends?.interval.toUpperCase() || 'HOURLY'} BUCKETS)`}
            badge={
              <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--color-signal-orange)' }}>
                  <span style={{ width: 8, height: 8, backgroundColor: 'var(--color-signal-orange)', display: 'inline-block' }} />
                  INCIDENTS
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#68b4f0' }}>
                  <span style={{ width: 8, height: 8, backgroundColor: '#68b4f0', display: 'inline-block' }} />
                  EVENTS
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--color-metric-green)' }}>
                  <span style={{ width: 8, height: 8, backgroundColor: 'var(--color-metric-green)', display: 'inline-block' }} />
                  JOBS DONE
                </span>
              </div>
            }
          >
            <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
              {trends && trends.buckets && trends.buckets.length > 0 ? (
                <svg
                  viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                  style={{ width: '100%', minWidth: '600px', height: '160px', display: 'block' }}
                >
                  {/* Grid Lines */}
                  {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
                    const y = chartHeight - chartPadding.bottom - pct * (chartHeight - chartPadding.top - chartPadding.bottom);
                    const val = Math.round(pct * maxVal);
                    return (
                      <g key={i}>
                        <line
                          x1={chartPadding.left}
                          y1={y}
                          x2={chartWidth - chartPadding.right}
                          y2={y}
                          stroke="#23201e"
                          strokeDasharray="3 3"
                        />
                        <text
                          x={chartPadding.left - 8}
                          y={y + 3}
                          fill="var(--color-warm-granite)"
                          fontSize="9"
                          fontFamily="var(--font-mono)"
                          textAnchor="end"
                        >
                          {val}
                        </text>
                      </g>
                    );
                  })}

                  {/* Lines for Trends */}
                  {pointsEvents && (
                    <polyline
                      fill="none"
                      stroke="#68b4f0"
                      strokeWidth="2"
                      points={pointsEvents}
                      strokeLinecap="round"
                    />
                  )}
                  {pointsIncidents && (
                    <polyline
                      fill="none"
                      stroke="var(--color-signal-orange)"
                      strokeWidth="2"
                      points={pointsIncidents}
                      strokeLinecap="round"
                    />
                  )}
                  {pointsJobs && (
                    <polyline
                      fill="none"
                      stroke="var(--color-metric-green)"
                      strokeWidth="1.5"
                      strokeDasharray="4 2"
                      points={pointsJobs}
                    />
                  )}

                  {/* Interactive Bucket Anchors */}
                  {trends.buckets.map((b, i) => {
                    const x = chartPadding.left + (trends.buckets.length > 1 ? i * xStep : 0);
                    return (
                      <g
                        key={i}
                        onMouseEnter={() => setHoveredBucket(b)}
                        onMouseLeave={() => setHoveredBucket(null)}
                        style={{ cursor: 'pointer' }}
                      >
                        <rect
                          x={x - (xStep ? xStep / 2 : 10)}
                          y={chartPadding.top}
                          width={xStep || 20}
                          height={chartHeight - chartPadding.top - chartPadding.bottom}
                          fill="transparent"
                        />
                        <circle
                          cx={x}
                          cy={chartHeight - chartPadding.bottom - (b.incidents_created / maxVal) * (chartHeight - chartPadding.top - chartPadding.bottom)}
                          r={hoveredBucket?.timestamp === b.timestamp ? 4 : 2}
                          fill="var(--color-signal-orange)"
                        />
                        <circle
                          cx={x}
                          cy={chartHeight - chartPadding.bottom - (b.events_created / maxVal) * (chartHeight - chartPadding.top - chartPadding.bottom)}
                          r={hoveredBucket?.timestamp === b.timestamp ? 4 : 2}
                          fill="#68b4f0"
                        />
                      </g>
                    );
                  })}
                </svg>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--color-warm-granite)' }}>
                  No historical activity recorded in this time window.
                </div>
              )}

              {/* Tooltip Overlay */}
              {hoveredBucket && (
                <div
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '12px',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: '1px solid var(--color-ash-stroke)',
                    padding: 'var(--space-2) var(--space-3)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  }}
                >
                  <div style={{ color: 'var(--color-chalk)', fontWeight: 600 }}>{hoveredBucket.label}</div>
                  <div style={{ color: 'var(--color-signal-orange)', marginTop: '2px' }}>
                    INCIDENTS CREATED: {hoveredBucket.incidents_created}
                  </div>
                  <div style={{ color: '#68b4f0' }}>EVENTS DETECTED: {hoveredBucket.events_created}</div>
                  <div style={{ color: 'var(--color-metric-green)' }}>JOBS COMPLETED: {hoveredBucket.jobs_completed}</div>
                </div>
              )}
            </div>
            <div
              style={{
                fontSize: '11px',
                color: 'var(--color-warm-granite)',
                marginTop: 'var(--space-2)',
                borderTop: '1px solid #23201e',
                paddingTop: '6px',
              }}
            >
              Time-series reflects genuine creation timestamps. Zero-activity intervals appear as explicit 0s.
            </div>
          </Card>

          {/* =========================================================
              4. Operational Breakdown: Incidents & Crowd Events
              ========================================================= */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            {/* Column A: Incident Lifecycle Breakdown */}
            <Card
              title="Incident Management Lifecycle"
              subtitle={`LIFECYCLE & SEVERITY TAXONOMY (${overview.incidents.total_in_period} TOTAL)`}
              badge={
                <button
                  onClick={() => handleNavigate('incidents')}
                  className="btn btn-secondary"
                  style={{ fontSize: '11px', padding: '3px 8px' }}
                >
                  VIEW ALL INCIDENTS <ChevronRight size={12} />
                </button>
              }
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {/* Status Bar Distribution */}
                <div>
                  <div className="mono-caption" style={{ marginBottom: '6px' }}>
                    STATUS PROGRESSION
                  </div>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(5, 1fr)',
                      gap: '4px',
                      textAlign: 'center',
                    }}
                  >
                    {[
                      { key: 'open', label: 'OPEN', color: 'var(--color-signal-orange)' },
                      { key: 'acknowledged', label: 'ACK', color: '#e69500' },
                      { key: 'in_progress', label: 'IN PROG', color: '#388bfd' },
                      { key: 'resolved', label: 'RESOLVED', color: 'var(--color-metric-green)' },
                      { key: 'closed', label: 'CLOSED', color: 'var(--color-warm-granite)' },
                    ].map((s) => (
                      <div
                        key={s.key}
                        style={{
                          backgroundColor: 'var(--color-obsidian-canvas)',
                          border: 'var(--border-hairline)',
                          padding: '6px 4px',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        <div style={{ fontSize: '16px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: s.color }}>
                          {overview.incidents.status_distribution[s.key] || 0}
                        </div>
                        <div style={{ fontSize: '9px', color: 'var(--color-warm-granite)', marginTop: '2px' }}>
                          {s.label}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Severity Breakdown & Resolution Time */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: 'var(--border-hairline)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-xs)',
                  }}
                >
                  <div>
                    <div className="mono-caption">SEVERITY SPREAD</div>
                    <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: '4px', fontSize: '12px' }}>
                      <span style={{ color: 'var(--color-alert-red)' }}>
                        CRIT: {overview.incidents.severity_distribution['critical'] || 0}
                      </span>
                      <span style={{ color: 'var(--color-signal-orange)' }}>
                        HIGH: {overview.incidents.severity_distribution['high'] || 0}
                      </span>
                      <span style={{ color: '#e69500' }}>
                        MED: {overview.incidents.severity_distribution['medium'] || 0}
                      </span>
                      <span style={{ color: 'var(--color-warm-granite)' }}>
                        LOW: {overview.incidents.severity_distribution['low'] || 0}
                      </span>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="mono-caption">AVG RESOLUTION TIME</div>
                    <div
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '14px',
                        color:
                          overview.incidents.avg_resolution_duration_minutes !== null
                            ? 'var(--color-metric-green)'
                            : 'var(--color-warm-granite)',
                      }}
                    >
                      {overview.incidents.avg_resolution_duration_minutes !== null
                        ? `${overview.incidents.avg_resolution_duration_minutes} MIN`
                        : 'N/A (NO RESOLUTIONS)'}
                    </div>
                  </div>
                </div>

                {/* Recent Incidents mini list */}
                <div>
                  <div className="mono-caption" style={{ marginBottom: '6px' }}>
                    RECENT INCIDENT RECORDS
                  </div>
                  {overview.incidents.recent_incidents.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {overview.incidents.recent_incidents.slice(0, 3).map((inc) => (
                        <div
                          key={inc.id}
                          onClick={() => handleNavigate('incidents')}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '6px 10px',
                            backgroundColor: 'var(--color-obsidian-canvas)',
                            border: '1px solid #23201e',
                            borderRadius: 'var(--radius-xs)',
                            cursor: 'pointer',
                          }}
                        >
                          <div>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-pale-stone)' }}>
                              {inc.incident_number}
                            </span>
                            <span style={{ marginLeft: '8px', fontSize: '12px', color: 'var(--color-bone)' }}>
                              {inc.title}
                            </span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span
                              style={{
                                fontSize: '10px',
                                fontFamily: 'var(--font-mono)',
                                color: inc.severity === 'critical' ? 'var(--color-alert-red)' : 'var(--color-signal-orange)',
                              }}
                            >
                              {inc.severity.toUpperCase()}
                            </span>
                            <StatusBadge
                              status={
                                inc.status === 'resolved' || inc.status === 'closed'
                                  ? 'healthy'
                                  : inc.status === 'in_progress'
                                  ? 'active'
                                  : 'pending'
                              }
                              label={inc.status.toUpperCase()}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '12px', color: 'var(--color-warm-granite)' }}>No incidents created in period.</div>
                  )}
                </div>
              </div>
            </Card>

            {/* Column B: Crowd Event & Review Workflow */}
            <Card
              title="Crowd Event Monitoring & Review"
              subtitle={`VISIONX RULE EVALUATION (${overview.events.total_in_period} EVENTS DETECTED)`}
              badge={
                <button
                  onClick={() => handleNavigate('event_review')}
                  className="btn btn-secondary"
                  style={{ fontSize: '11px', padding: '3px 8px' }}
                >
                  EVENT REVIEW DESK <ChevronRight size={12} />
                </button>
              }
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {/* Event Review Statuses */}
                <div>
                  <div className="mono-caption" style={{ marginBottom: '6px' }}>
                    HUMAN OPERATOR REVIEW DISPOSITION
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
                    <div
                      style={{
                        backgroundColor: 'var(--color-obsidian-canvas)',
                        border: 'var(--border-hairline)',
                        padding: '8px',
                        borderRadius: 'var(--radius-xs)',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-signal-orange)' }}>
                        {overview.events.pending_count}
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', marginTop: '2px' }}>
                        PENDING REVIEW
                      </div>
                    </div>
                    <div
                      style={{
                        backgroundColor: 'var(--color-obsidian-canvas)',
                        border: 'var(--border-hairline)',
                        padding: '8px',
                        borderRadius: 'var(--radius-xs)',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-metric-green)' }}>
                        {overview.events.status_distribution['acknowledged'] || 0}
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', marginTop: '2px' }}>
                        ACKNOWLEDGED
                      </div>
                    </div>
                    <div
                      style={{
                        backgroundColor: 'var(--color-obsidian-canvas)',
                        border: 'var(--border-hairline)',
                        padding: '8px',
                        borderRadius: 'var(--radius-xs)',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-warm-granite)' }}>
                        {overview.events.status_distribution['dismissed'] || 0}
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', marginTop: '2px' }}>
                        DISMISSED / NO ACTION
                      </div>
                    </div>
                  </div>
                </div>

                {/* Person Detections Clarification */}
                <div
                  style={{
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: '1px solid #23201e',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-xs)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="mono-caption">SAMPLED FRAME PERSON DETECTIONS</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', color: 'var(--color-chalk)' }}>
                      {(overview.jobs.total_frame_detections || 0).toLocaleString()} DETECTIONS
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-warm-granite)', marginTop: '4px' }}>
                    Note: YOLO person detections reflect frame-level bounding sightings. They do not represent unique attendees or total venue occupancy.
                  </div>
                </div>

                {/* Recent Events List */}
                <div>
                  <div className="mono-caption" style={{ marginBottom: '6px' }}>
                    RECENT EVENT ALERTS
                  </div>
                  {overview.events.recent_events.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {overview.events.recent_events.slice(0, 3).map((ev) => (
                        <div
                          key={ev.id}
                          onClick={() => handleNavigate('event_review')}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '6px 10px',
                            backgroundColor: 'var(--color-obsidian-canvas)',
                            border: '1px solid #23201e',
                            borderRadius: 'var(--radius-xs)',
                            cursor: 'pointer',
                          }}
                        >
                          <div>
                            <span style={{ fontSize: '12px', color: 'var(--color-bone)' }}>{ev.rule_name}</span>
                            <span style={{ marginLeft: '8px', fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--color-warm-granite)' }}>
                              ZONE: {ev.zone_id}
                            </span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--color-signal-orange)' }}>
                              {ev.person_count} PERS
                            </span>
                            <StatusBadge
                              status={
                                ev.status === 'acknowledged'
                                  ? 'healthy'
                                  : ev.status === 'dismissed'
                                  ? 'offline'
                                  : 'pending'
                              }
                              label={ev.status.toUpperCase()}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '12px', color: 'var(--color-warm-granite)' }}>No crowd events detected in period.</div>
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* =========================================================
              5. Subsystems: Simulated Resources & GIS Walkways
              ========================================================= */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            {/* Column C: Simulated Response Registry */}
            <Card
              title="Simulated Response Resources"
              subtitle="PHASE 6 SIMULATED REGISTRY // DEMONSTRATION ENVIRONMENT"
              badge={
                <span
                  className="mono-caption"
                  style={{
                    backgroundColor: '#262220',
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--color-pale-stone)',
                  }}
                >
                  DEMO SQUADS ONLY
                </span>
              }
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {/* Disclaimer */}
                <div
                  style={{
                    backgroundColor: '#1f1b18',
                    border: '1px solid var(--color-ash-stroke)',
                    padding: '6px 10px',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '11px',
                    color: 'var(--color-pale-stone)',
                  }}
                >
                  Notice: Simulated response resources represent demo software entities. They are not connected to real municipal 911 or emergency personnel.
                </div>

                {/* Status counts */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
                  <div
                    style={{
                      backgroundColor: 'var(--color-obsidian-canvas)',
                      border: 'var(--border-hairline)',
                      padding: '8px',
                      borderRadius: 'var(--radius-xs)',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-metric-green)' }}>
                      {overview.resources.available}
                    </div>
                    <div className="mono-caption" style={{ fontSize: '10px' }}>AVAILABLE</div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--color-obsidian-canvas)',
                      border: 'var(--border-hairline)',
                      padding: '8px',
                      borderRadius: 'var(--radius-xs)',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-signal-orange)' }}>
                      {overview.resources.assigned}
                    </div>
                    <div className="mono-caption" style={{ fontSize: '10px' }}>ASSIGNED / BUSY</div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--color-obsidian-canvas)',
                      border: 'var(--border-hairline)',
                      padding: '8px',
                      borderRadius: 'var(--radius-xs)',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-warm-granite)' }}>
                      {overview.resources.unavailable}
                    </div>
                    <div className="mono-caption" style={{ fontSize: '10px' }}>UNAVAILABLE</div>
                  </div>
                </div>

                {/* Type Distribution */}
                <div>
                  <div className="mono-caption" style={{ marginBottom: '6px' }}>
                    SQUAD ALLOCATION BY SPECIALTY
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                    {Object.entries(overview.resources.by_type).map(([rtype, rcount]) => (
                      <span
                        key={rtype}
                        style={{
                          backgroundColor: 'var(--color-obsidian-canvas)',
                          border: '1px solid #23201e',
                          padding: '3px 8px',
                          borderRadius: 'var(--radius-xs)',
                          fontSize: '11px',
                          fontFamily: 'var(--font-mono)',
                          color: 'var(--color-bone)',
                        }}
                      >
                        {rtype.toUpperCase()}: {rcount}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Active Assignments */}
                {overview.resources.assigned_units.length > 0 && (
                  <div>
                    <div className="mono-caption" style={{ marginBottom: '6px' }}>
                      CURRENT INCIDENT ASSIGNMENTS
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {overview.resources.assigned_units.map((unit) => (
                        <div
                          key={unit.id}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '6px 10px',
                            backgroundColor: 'var(--color-obsidian-canvas)',
                            border: '1px solid #23201e',
                            borderRadius: 'var(--radius-xs)',
                            fontSize: '11px',
                          }}
                        >
                          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-signal-orange)' }}>
                            {unit.call_sign} [{unit.resource_type.toUpperCase()}]
                          </span>
                          <span style={{ color: 'var(--color-warm-granite)' }}>
                            ASSIGNED TO INCIDENT
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* Column D: GIS Venue Walkway Integrity */}
            <Card
              title="GIS Venue Infrastructure"
              subtitle={`TRIVENI STADIUM GRAPH (${overview.gis.total_walkways} WALKWAYS REGISTERED)`}
              badge={
                <button
                  onClick={() => handleNavigate('gis_operations')}
                  className="btn btn-secondary"
                  style={{ fontSize: '11px', padding: '3px 8px' }}
                >
                  GIS ROUTE MAP <ChevronRight size={12} />
                </button>
              }
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {/* Passage Status Bar */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
                  <div
                    style={{
                      backgroundColor: 'var(--color-obsidian-canvas)',
                      border: 'var(--border-hairline)',
                      padding: '8px',
                      borderRadius: 'var(--radius-xs)',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: '18px', fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--color-metric-green)' }}>
                      {overview.gis.unblocked_count}
                    </div>
                    <div className="mono-caption" style={{ fontSize: '10px' }}>OPEN / PASSABLE</div>
                  </div>
                  <div
                    style={{
                      backgroundColor: 'var(--color-obsidian-canvas)',
                      border: 'var(--border-hairline)',
                      padding: '8px',
                      borderRadius: 'var(--radius-xs)',
                      textAlign: 'center',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '18px',
                        fontWeight: 600,
                        fontFamily: 'var(--font-mono)',
                        color: overview.gis.blocked_count > 0 ? 'var(--color-alert-red)' : 'var(--color-bone)',
                      }}
                    >
                      {overview.gis.blocked_count}
                    </div>
                    <div className="mono-caption" style={{ fontSize: '10px' }}>BLOCKED / IMPASSABLE</div>
                  </div>
                </div>

                {/* Blocked Walkway Details */}
                <div>
                  <div className="mono-caption" style={{ marginBottom: '6px' }}>
                    ACTIVE WALKWAY BLOCKAGES
                  </div>
                  {overview.gis.blocked_details.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {overview.gis.blocked_details.map((edge) => (
                        <div
                          key={edge.id}
                          onClick={() => handleNavigate('gis_operations')}
                          style={{
                            padding: '8px 10px',
                            backgroundColor: 'var(--color-obsidian-canvas)',
                            border: '1px solid #3d2424',
                            borderRadius: 'var(--radius-xs)',
                            cursor: 'pointer',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-alert-red)' }}>
                              {edge.name || edge.id}
                            </span>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--color-warm-granite)' }}>
                              {edge.from_node} ➔ {edge.to_node}
                            </span>
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--color-pale-stone)', marginTop: '2px' }}>
                            Reason: {edge.blockage_reason || 'Hazard / Obstacle reported'}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div
                      style={{
                        backgroundColor: 'var(--color-obsidian-canvas)',
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid #23201e',
                        fontSize: '12px',
                        color: 'var(--color-metric-green)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-2)',
                      }}
                    >
                      <CheckCircle2 size={14} color="var(--color-metric-green)" />
                      All venue walkways are open. Emergency routing operates with zero detour penalty.
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </div>

          {/* =========================================================
              6. Actionable Work: Attention Queue & Activity Log
              ========================================================= */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            {/* Attention Queue */}
            <Card
              title="Operator Action Queue"
              subtitle={`PRIORITIZED OPERATIONAL TASKS (${overview.attention_queue.length} PENDING)`}
              badge={
                overview.attention_queue.length > 0 ? (
                  <StatusBadge status="degraded" label="ATTENTION NEEDED" />
                ) : (
                  <StatusBadge status="healthy" label="ALL CLEAR" />
                )
              }
            >
              {overview.attention_queue.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {overview.attention_queue.map((item, idx) => (
                    <div
                      key={`${item.category}-${item.entity_id}-${idx}`}
                      onClick={() => handleAttentionClick(item)}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 12px',
                        backgroundColor: 'var(--color-obsidian-canvas)',
                        border: 'var(--border-hairline)',
                        borderRadius: 'var(--radius-xs)',
                        cursor: 'pointer',
                        transition: 'border-color 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                        {item.level === 'critical' ? (
                          <AlertTriangle size={16} color="var(--color-alert-red)" />
                        ) : (
                          <AlertTriangle size={16} color="var(--color-signal-orange)" />
                        )}
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-chalk)' }}>
                            {item.title}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--color-pale-stone)', marginTop: '1px' }}>
                            {item.subtitle}
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <span className="mono-caption" style={{ fontSize: '10px' }}>
                          {formatDateTime(item.timestamp)}
                        </span>
                        <button className="btn btn-secondary" style={{ fontSize: '10px', padding: '3px 8px' }}>
                          ACTION <ChevronRight size={10} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--color-warm-granite)' }}>
                  No high-priority alerts or unassigned incidents require attention.
                </div>
              )}
            </Card>

            {/* Recent Activity Log */}
            <Card
              title="Operational Activity Trail"
              subtitle="CHRONOLOGICAL PERSISTED AUDIT LOG"
              badge={
                <button
                  onClick={() => handleNavigate('reports_audit')}
                  className="btn btn-secondary"
                  style={{ fontSize: '11px', padding: '3px 8px' }}
                >
                  AUDIT LOG <ChevronRight size={12} />
                </button>
              }
            >
              {overview.recent_activity.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {overview.recent_activity.map((act) => (
                    <div
                      key={act.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '6px 10px',
                        backgroundColor: 'var(--color-obsidian-canvas)',
                        border: '1px solid #23201e',
                        borderRadius: 'var(--radius-xs)',
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '12px', color: 'var(--color-bone)' }}>{act.description}</div>
                        <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--color-warm-granite)', marginTop: '1px' }}>
                          {act.action_type.toUpperCase()} // ACTOR: {act.actor_id}
                        </div>
                      </div>
                      <span className="mono-caption" style={{ fontSize: '10px' }}>
                        {formatDateTime(act.timestamp)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--color-warm-granite)' }}>
                  No audit activity recorded yet.
                </div>
              )}
            </Card>
          </div>

          {/* =========================================================
              7. Governance & Architectural Safety Notice
              ========================================================= */}
          <Card
            title="Operational Architecture & Ethical Boundaries"
            subtitle="SAFETY CONSOLE SPECIFICATION"
            variant="light"
          >
            <div style={{ fontSize: '12px', lineHeight: 1.6, color: '#222' }}>
              <p style={{ marginBottom: 'var(--space-2)' }}>
                <strong>Decision Support System Notice:</strong> NEXORA is an operational decision support console designed for venue safety operators and emergency coordinators. It does not provide autonomous emergency service dispatch, automated 911 interfacing, or guaranteed evacuation clearance. All incident escalations and resource assignments require human operator review.
              </p>
              <p>
                <strong>Privacy & Computer Vision Integrity:</strong> The VisionX pipeline operates purely on anonymous bounding box detections from uploaded CCTV recordings. Biometric facial recognition, demographic classification, and behavioral intent prediction are strictly prohibited by system governance.
              </p>
            </div>
          </Card>
        </>
      )}
    </div>
  );
};
