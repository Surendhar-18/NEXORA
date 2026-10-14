import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { CrowdEvent, CrowdRule, EventReviewRequest } from '../types';
import { ApiClient } from '../api/client';
import { Card } from '../components/common/Card';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const EventReviewView: React.FC = () => {
  // Events state
  const [events, setEvents] = useState<CrowdEvent[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [loadingEvents, setLoadingEvents] = useState<boolean>(true);
  const [eventsError, setEventsError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('pending_review');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  // Rules state & drawer
  const [rules, setRules] = useState<CrowdRule[]>([]);
  const [showRulesModal, setShowRulesModal] = useState<boolean>(false);
  const [loadingRules, setLoadingRules] = useState<boolean>(false);
  const [rulesError, setRulesError] = useState<string | null>(null);

  // Review action modal state
  const [pendingAction, setPendingAction] = useState<'acknowledge' | 'dismiss' | 'resolve' | null>(null);
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewSuccess, setReviewSuccess] = useState<string | null>(null);

  // Phase 6 Incident Escalation state
  const [escalatingIncident, setEscalatingIncident] = useState<boolean>(false);
  const [escalateResult, setEscalateResult] = useState<string | null>(null);
  const [escalateError, setEscalateError] = useState<string | null>(null);

  const isMountedRef = useRef<boolean>(true);

  // Fetch events from API
  const fetchEvents = useCallback(async () => {
    try {
      const params: { status?: string; severity?: string } = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (severityFilter !== 'all') params.severity = severityFilter;

      const data = await ApiClient.getEvents(params);
      if (isMountedRef.current) {
        setEvents(data.events);
        setEventsError(null);

        // Auto-select first event if none selected or current selection missing
        if (data.events.length > 0) {
          if (!selectedEventId || !data.events.some((e) => e.id === selectedEventId)) {
            setSelectedEventId(data.events[0].id);
          }
        } else {
          setSelectedEventId(null);
        }
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setEventsError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (isMountedRef.current) {
        setLoadingEvents(false);
      }
    }
  }, [statusFilter, severityFilter, selectedEventId]);

  // Fetch rules from API
  const fetchRules = useCallback(async () => {
    setLoadingRules(true);
    try {
      const data = await ApiClient.getRules();
      if (isMountedRef.current) {
        setRules(data.rules);
        setRulesError(null);
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setRulesError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (isMountedRef.current) {
        setLoadingRules(false);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    fetchEvents();
    fetchRules();
    return () => {
      isMountedRef.current = false;
    };
  }, [fetchEvents, fetchRules]);

  // Polling loop for pending events
  useEffect(() => {
    const interval = setInterval(() => {
      fetchEvents();
    }, 4000);
    return () => clearInterval(interval);
  }, [fetchEvents]);

  // Toggle rule active state
  const handleToggleRuleActive = async (rule: CrowdRule) => {
    try {
      await ApiClient.updateRule(rule.id, { is_active: !rule.is_active });
      fetchRules();
    } catch (err: unknown) {
      alert(`Failed to update rule: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Submit operator review decision
  const handleSubmitReview = async () => {
    if (!selectedEventId || !pendingAction) return;

    setSubmittingReview(true);
    setReviewError(null);
    setReviewSuccess(null);

    const payload: EventReviewRequest = {
      action: pendingAction,
      notes: reviewNotes.trim() || undefined,
      operator_id: 'operator',
    };

    try {
      const res = await ApiClient.reviewEvent(selectedEventId, payload);
      setReviewSuccess(res.message);
      setPendingAction(null);
      setReviewNotes('');
      await fetchEvents();
    } catch (err: unknown) {
      setReviewError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleEscalateToIncident = async (eventId: string) => {
    setEscalatingIncident(true);
    setEscalateResult(null);
    setEscalateError(null);
    try {
      const res = await ApiClient.createIncidentFromEvent(eventId);
      setEscalateResult(`Incident created: ${res.incident_number} — ${res.title}`);
    } catch (err: unknown) {
      setEscalateError(err instanceof Error ? err.message : String(err));
    } finally {
      setEscalatingIncident(false);
    }
  };

  const selectedEvent = events.find((e) => e.id === selectedEventId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* View Header */}
      <div style={{
        padding: 'var(--space-4) var(--space-5)',
        backgroundColor: 'var(--color-carbon-lift)',
        border: 'var(--border-hairline)',
        borderRadius: 'var(--radius-xs)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
            MODULE A // HUMAN-IN-THE-LOOP ALERT TRIAGE
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 500, letterSpacing: '-0.02em', marginTop: '2px' }}>
            Crowd Rules Evaluation & Operator Event Review
          </h1>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button
            onClick={() => setShowRulesModal(true)}
            className="btn btn-secondary"
          >
            CONFIGURE RULES ({rules.length})
          </button>
          <button
            onClick={fetchEvents}
            disabled={loadingEvents}
            className="btn btn-secondary"
          >
            {loadingEvents ? 'SYNCING...' : 'REFRESH QUEUE'}
          </button>
        </div>
      </div>

      {/* Safety & Methodology Notice Banner */}
      <div style={{
        backgroundColor: 'rgba(238, 96, 24, 0.06)',
        border: '1px solid rgba(238, 96, 24, 0.25)',
        padding: 'var(--space-3) var(--space-4)',
        borderRadius: 'var(--radius-xs)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
      }}>
        <span style={{ color: 'var(--color-signal-orange)', fontSize: '18px' }}>⚠</span>
        <div style={{ fontSize: '12px', color: 'var(--color-bone)' }}>
          <strong>Decision-Support Notice:</strong> Generated alerts represent automated threshold or sustained-presence rule crossings requiring operator evaluation. Detections measure person bounding boxes per sampled frame, not unique individuals or calibrated density. NEXORA does not claim to detect panic, violence, or abnormal behavior.
        </div>
      </div>

      {/* Feedback Alerts */}
      {reviewSuccess && (
        <div style={{
          backgroundColor: '#162b14',
          border: '1px solid var(--color-metric-green)',
          padding: 'var(--space-3)',
          borderRadius: 'var(--radius-xs)',
          fontSize: '12px',
          color: 'var(--color-bone)',
        }}>
          <div className="mono-caption" style={{ color: 'var(--color-metric-green)', marginBottom: '2px' }}>
            STATUS UPDATED
          </div>
          {reviewSuccess}
        </div>
      )}

      {/* Main Workspace Grid: Event Queue (Left) + Detail Inspector (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(380px, 460px) 1fr', gap: 'var(--space-6)' }}>
        {/* Left Column: Event Queue List */}
        <Card
          title="Alert Queue"
          subtitle="FILTER & SELECT CANDIDATE EVENTS"
          badge={<StatusBadge status="active" label={`${events.length} EVENTS`} />}
        >
          {/* Queue Filter Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
            <div>
              <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                REVIEW STATUS
              </label>
              <div style={{ display: 'flex', gap: '4px' }}>
                {[
                  { id: 'pending_review', label: 'PENDING' },
                  { id: 'acknowledged', label: 'ACK' },
                  { id: 'resolved', label: 'RESOLVED' },
                  { id: 'dismissed', label: 'DISMISSED' },
                  { id: 'all', label: 'ALL' },
                ].map((st) => (
                  <button
                    key={st.id}
                    onClick={() => setStatusFilter(st.id)}
                    className={`btn ${statusFilter === st.id ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ flex: 1, padding: '4px 6px', fontSize: '10px' }}
                  >
                    {st.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
              <div style={{ flex: 1 }}>
                <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                  SEVERITY
                </label>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '5px 8px',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: 'var(--border-hairline)',
                    borderRadius: 'var(--radius-xs)',
                    color: 'var(--color-bone)',
                    fontFamily: 'var(--font-sans)',
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
            </div>
          </div>

          {/* Event List Table */}
          {loadingEvents && events.length === 0 && (
            <LoadingSpinner message="LOADING ALERT QUEUE..." />
          )}

          {eventsError && (
            <div style={{
              backgroundColor: '#2b1414',
              border: '1px solid var(--color-alert-red)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-xs)',
              fontSize: '12px',
              color: 'var(--color-bone)',
              marginBottom: 'var(--space-4)',
            }}>
              Error: {eventsError}
            </div>
          )}

          {!loadingEvents && events.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: 'var(--space-8)',
              color: 'var(--color-warm-granite)',
              backgroundColor: 'var(--color-obsidian-canvas)',
              border: '1px dashed var(--color-ash-stroke)',
              borderRadius: 'var(--radius-xs)',
            }}>
              <div className="mono-caption" style={{ marginBottom: 'var(--space-2)' }}>
                NO EVENTS IN CURRENT FILTER
              </div>
              <div style={{ fontSize: '13px' }}>
                No alert events match the selected criteria. Process video footage in Video Analysis to generate alerts.
              </div>
            </div>
          )}

          {events.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', maxHeight: '560px', overflowY: 'auto' }}>
              {events.map((ev) => {
                const isSelected = ev.id === selectedEventId;
                const severityColor =
                  ev.severity === 'critical'
                    ? 'var(--color-alert-red)'
                    : ev.severity === 'high'
                    ? 'var(--color-signal-orange)'
                    : ev.severity === 'medium'
                    ? '#f59e0b'
                    : 'var(--color-warm-granite)';

                return (
                  <div
                    key={ev.id}
                    onClick={() => setSelectedEventId(ev.id)}
                    style={{
                      padding: 'var(--space-3)',
                      backgroundColor: isSelected ? 'var(--color-carbon-lift)' : '#161413',
                      border: isSelected ? '1px solid var(--color-signal-orange)' : '1px solid var(--color-ash-stroke)',
                      borderRadius: 'var(--radius-xs)',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="mono-caption" style={{ color: severityColor, fontWeight: 600 }}>
                        ● {ev.severity.toUpperCase()} // {ev.event_type.toUpperCase()}
                      </span>
                      <StatusBadge
                        status={
                          ev.status === 'resolved'
                            ? 'healthy'
                            : ev.status === 'acknowledged'
                            ? 'active'
                            : ev.status === 'pending_review'
                            ? 'pending'
                            : 'offline'
                        }
                        label={ev.status.replace('_', ' ').toUpperCase()}
                      />
                    </div>

                    <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-bone)' }}>
                      {ev.rule_name}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2px' }}>
                      <div className="mono-caption" style={{ fontSize: '11px', color: 'var(--color-warm-granite)' }}>
                        Peak: <strong style={{ color: 'var(--color-signal-orange)' }}>{ev.person_count}</strong> (limit {ev.rule_threshold}) • {ev.zone_id}
                      </div>
                      <div className="mono-metric" style={{ fontSize: '10px' }}>
                        {new Date(ev.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        {/* Right Column: Event Detail & Supporting Evidence Inspector */}
        <Card
          title={selectedEvent ? `Event Triage // ${selectedEvent.id.slice(0, 8)}...` : 'Event Inspector'}
          subtitle="DECISION-SUPPORT EVIDENCE & ACTION WORKFLOW"
          badge={
            selectedEvent ? (
              <StatusBadge
                status={
                  selectedEvent.status === 'resolved'
                    ? 'healthy'
                    : selectedEvent.status === 'acknowledged'
                    ? 'active'
                    : selectedEvent.status === 'pending_review'
                    ? 'pending'
                    : 'offline'
                }
                label={selectedEvent.status.replace('_', ' ').toUpperCase()}
              />
            ) : undefined
          }
        >
          {selectedEvent ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
              {/* Telemetry Summary Bar */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: 'var(--space-3)',
                padding: 'var(--space-3)',
                backgroundColor: 'var(--color-obsidian-canvas)',
                border: 'var(--border-hairline)',
                borderRadius: 'var(--radius-xs)',
              }}>
                <div>
                  <div className="mono-caption">PEAK PERSON COUNT</div>
                  <div className="mono-metric" style={{ fontSize: '20px', color: 'var(--color-signal-orange)' }}>
                    {selectedEvent.person_count}
                  </div>
                  <div className="mono-caption" style={{ fontSize: '10px' }}>
                    THRESHOLD: {selectedEvent.rule_threshold}
                  </div>
                </div>

                <div>
                  <div className="mono-caption">RULE TYPE</div>
                  <div className="mono-metric" style={{ fontSize: '16px', color: 'var(--color-bone)' }}>
                    {selectedEvent.event_type.toUpperCase()}
                  </div>
                  <div className="mono-caption" style={{ fontSize: '10px' }}>
                    {selectedEvent.sustained_frames ? `${selectedEvent.sustained_frames} FRAMES` : 'INSTANT SURGE'}
                  </div>
                </div>

                <div>
                  <div className="mono-caption">WINDOW DURATION</div>
                  <div className="mono-metric" style={{ fontSize: '16px', color: 'var(--color-metric-green)' }}>
                    {selectedEvent.sustained_duration_sec !== null && selectedEvent.sustained_duration_sec !== undefined
                      ? `${selectedEvent.sustained_duration_sec.toFixed(1)}s`
                      : '0.0s'}
                  </div>
                  <div className="mono-caption" style={{ fontSize: '10px' }}>
                    {selectedEvent.window_start_sec?.toFixed(1)}s → {selectedEvent.window_end_sec?.toFixed(1)}s
                  </div>
                </div>

                <div>
                  <div className="mono-caption">MONITORED ZONE</div>
                  <div className="mono-metric" style={{ fontSize: '16px', color: 'var(--color-bone)' }}>
                    {selectedEvent.zone_id}
                  </div>
                  <div className="mono-caption" style={{ fontSize: '10px' }}>
                    JOB: {selectedEvent.job_id?.slice(0, 8)}...
                  </div>
                </div>
              </div>

              {/* Peak Evidence Frame Image */}
              <div style={{
                backgroundColor: 'var(--color-obsidian-canvas)',
                border: 'var(--border-hairline)',
                borderRadius: 'var(--radius-xs)',
                overflow: 'hidden',
                position: 'relative',
              }}>
                {selectedEvent.evidence_image_url ? (
                  <img
                    src={ApiClient.getEvidenceImageUrl(selectedEvent.evidence_image_url)}
                    alt={`Peak detection evidence frame`}
                    style={{
                      width: '100%',
                      height: 'auto',
                      maxHeight: '340px',
                      objectFit: 'contain',
                      display: 'block',
                      backgroundColor: '#000',
                    }}
                  />
                ) : (
                  <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-warm-granite)' }}>
                    No visual evidence image linked to this alert.
                  </div>
                )}

                <div style={{
                  position: 'absolute',
                  bottom: '8px',
                  right: '8px',
                  backgroundColor: 'rgba(16, 16, 16, 0.85)',
                  border: '1px solid var(--color-ash-stroke)',
                  borderRadius: 'var(--radius-xs)',
                  padding: '3px 8px',
                  fontSize: '10px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--color-bone)',
                }}>
                  PEAK EVIDENCE FRAME • {selectedEvent.person_count} PERSONS DETECTED
                </div>
              </div>

              {/* Supporting Frames Timeline (if sustained rule) */}
              {selectedEvent.supporting_frames && selectedEvent.supporting_frames.length > 0 && (
                <div style={{
                  backgroundColor: 'var(--color-obsidian-canvas)',
                  border: 'var(--border-hairline)',
                  borderRadius: 'var(--radius-xs)',
                  padding: 'var(--space-3)',
                }}>
                  <div className="mono-caption" style={{ marginBottom: 'var(--space-2)' }}>
                    QUALIFYING SAMPLED FRAMES ({selectedEvent.supporting_frames.length} RECORDED)
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', overflowX: 'auto', paddingBottom: '4px' }}>
                    {selectedEvent.supporting_frames.map((sf, idx) => (
                      <div
                        key={idx}
                        style={{
                          minWidth: '100px',
                          padding: '6px',
                          backgroundColor: '#161413',
                          border: '1px solid var(--color-ash-stroke)',
                          borderRadius: 'var(--radius-xs)',
                          textAlign: 'center',
                        }}
                      >
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-signal-orange)' }}>
                          {sf.person_count} PERSONS
                        </div>
                        <div className="mono-caption" style={{ fontSize: '9px', marginTop: '2px' }}>
                          {sf.timestamp_seconds.toFixed(1)}s • F#{sf.frame_index}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Existing Review Record (if already reviewed) */}
              {selectedEvent.reviewed_at && (
                <div style={{
                  padding: 'var(--space-3)',
                  backgroundColor: '#161413',
                  border: 'var(--border-hairline)',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '12px',
                }}>
                  <div className="mono-caption" style={{ color: 'var(--color-metric-green)', marginBottom: '4px' }}>
                    REVIEW AUDIT TRAIL
                  </div>
                  <div>Reviewed by: <strong>{selectedEvent.reviewed_by}</strong> at {new Date(selectedEvent.reviewed_at).toLocaleString()}</div>
                  {selectedEvent.review_notes && (
                    <div style={{ marginTop: '4px', fontStyle: 'italic', color: 'var(--color-warm-granite)' }}>
                      Operator Notes: "{selectedEvent.review_notes}"
                    </div>
                  )}
                </div>
              )}

              {/* Operator Action Bar */}
              {selectedEvent.status !== 'dismissed' && selectedEvent.status !== 'resolved' && (
                <div style={{
                  padding: 'var(--space-4)',
                  backgroundColor: 'var(--color-obsidian-canvas)',
                  border: '1px solid var(--color-ash-stroke)',
                  borderRadius: 'var(--radius-xs)',
                }}>
                  <div className="mono-caption" style={{ marginBottom: 'var(--space-2)' }}>
                    OPERATOR TRIAGE ACTIONS
                  </div>

                  {pendingAction ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                      <div style={{ fontSize: '13px', color: 'var(--color-bone)' }}>
                        Confirm action: <strong style={{ color: 'var(--color-signal-orange)' }}>{pendingAction.toUpperCase()}</strong>
                      </div>
                      <textarea
                        value={reviewNotes}
                        onChange={(e) => setReviewNotes(e.target.value)}
                        placeholder="Enter operational assessment or reason (e.g., 'Verified crowd movement normal', 'Confirmed surge at North Pavilion')..."
                        rows={2}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          backgroundColor: '#161413',
                          border: 'var(--border-hairline)',
                          borderRadius: 'var(--radius-xs)',
                          color: 'var(--color-bone)',
                          fontFamily: 'var(--font-sans)',
                          fontSize: '12px',
                        }}
                      />
                      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                        <button
                          onClick={handleSubmitReview}
                          disabled={submittingReview}
                          className="btn btn-primary"
                          style={{ flex: 1 }}
                        >
                          {submittingReview ? 'RECORDING AUDIT...' : `CONFIRM ${pendingAction.toUpperCase()}`}
                        </button>
                        <button
                          onClick={() => {
                            setPendingAction(null);
                            setReviewNotes('');
                          }}
                          disabled={submittingReview}
                          className="btn btn-secondary"
                        >
                          CANCEL
                        </button>
                      </div>
                      {reviewError && (
                        <div style={{ fontSize: '11px', color: 'var(--color-alert-red)', marginTop: '2px' }}>
                          {reviewError}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                      <button
                        onClick={() => setPendingAction('acknowledge')}
                        className="btn btn-secondary"
                        style={{ flex: 1 }}
                      >
                        ACKNOWLEDGE ALERT
                      </button>
                      <button
                        onClick={() => setPendingAction('resolve')}
                        className="btn btn-primary"
                        style={{ flex: 1 }}
                      >
                        RESOLVE
                      </button>
                      <button
                        onClick={() => setPendingAction('dismiss')}
                        className="btn btn-secondary"
                        style={{ flex: 1, borderColor: 'var(--color-alert-red)', color: 'var(--color-alert-red)' }}
                      >
                        DISMISS (FALSE POSITIVE)
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Phase 6: Escalate to Operational Incident */}
              {selectedEvent.status === 'acknowledged' && (
                <div style={{
                  padding: 'var(--space-4)',
                  backgroundColor: 'var(--color-carbon-lift)',
                  border: '1px solid var(--color-signal-orange)',
                  borderRadius: 'var(--radius-xs)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-2)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
                        PHASE 6 // INCIDENT ESCALATION
                      </div>
                      <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-light-cream)' }}>
                        Escalate Acknowledged Event to Incident
                      </div>
                    </div>
                    <button
                      onClick={() => handleEscalateToIncident(selectedEvent.id)}
                      disabled={escalatingIncident}
                      className="btn btn-primary"
                      style={{ backgroundColor: 'var(--color-signal-orange)', borderColor: 'var(--color-signal-orange)' }}
                    >
                      {escalatingIncident ? 'CREATING INCIDENT...' : 'ESCALATE TO INCIDENT'}
                    </button>
                  </div>
                  {escalateResult && (
                    <div style={{ fontSize: '12px', color: 'var(--color-metric-green)', marginTop: '4px' }}>
                      ✓ {escalateResult}
                    </div>
                  )}
                  {escalateError && (
                    <div style={{ fontSize: '12px', color: 'var(--color-alert-red)', marginTop: '4px' }}>
                      ⚠ {escalateError}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: 'var(--space-10)',
              color: 'var(--color-warm-granite)',
            }}>
              Select an alert event from the queue on the left to inspect telemetry, frame evidence, and record review actions.
            </div>
          )}
        </Card>
      </div>

      {/* Rules Configuration Modal */}
      {showRulesModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(10, 10, 10, 0.85)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
          padding: 'var(--space-4)',
        }}>
          <div style={{
            backgroundColor: 'var(--color-carbon-lift)',
            border: 'var(--border-hairline)',
            borderRadius: 'var(--radius-xs)',
            width: '100%',
            maxWidth: '700px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 20px 40px rgba(0,0,0,0.7)',
          }}>
            {/* Modal Header */}
            <div style={{
              padding: 'var(--space-4) var(--space-5)',
              borderBottom: 'var(--border-hairline)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
                  SETTINGS // VISIONX CROWD EVALUATION RULES
                </div>
                <h2 style={{ fontSize: '16px', fontWeight: 500, marginTop: '2px' }}>
                  Configured Threshold & Sustained Rules
                </h2>
              </div>
              <button
                onClick={() => setShowRulesModal(false)}
                className="btn btn-secondary"
                style={{ padding: '2px 8px', fontSize: '11px' }}
              >
                CLOSE
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: 'var(--space-5)', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {loadingRules && <LoadingSpinner message="LOADING RULES..." />}
              {rulesError && <div style={{ color: 'var(--color-alert-red)', fontSize: '12px' }}>{rulesError}</div>}

              {rules.map((r) => (
                <div
                  key={r.id}
                  style={{
                    padding: 'var(--space-4)',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: 'var(--border-hairline)',
                    borderRadius: 'var(--radius-xs)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <span className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
                        {r.id}
                      </span>
                      <strong style={{ fontSize: '13px', color: 'var(--color-bone)' }}>{r.name}</strong>
                    </div>
                    <button
                      onClick={() => handleToggleRuleActive(r)}
                      className={`btn ${r.is_active ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ padding: '2px 8px', fontSize: '10px' }}
                    >
                      {r.is_active ? 'ENABLED' : 'DISABLED'}
                    </button>
                  </div>

                  <div style={{ fontSize: '12px', color: 'var(--color-warm-granite)' }}>
                    {r.description}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-2)', marginTop: '4px' }}>
                    <div className="mono-caption" style={{ fontSize: '11px' }}>
                      THRESHOLD: <strong style={{ color: 'var(--color-bone)' }}>{r.threshold_count} P</strong>
                    </div>
                    <div className="mono-caption" style={{ fontSize: '11px' }}>
                      TYPE: <strong style={{ color: 'var(--color-bone)' }}>{r.rule_type.toUpperCase()}</strong>
                    </div>
                    <div className="mono-caption" style={{ fontSize: '11px' }}>
                      MIN FRAMES: <strong style={{ color: 'var(--color-bone)' }}>{r.min_consecutive_frames}</strong>
                    </div>
                    <div className="mono-caption" style={{ fontSize: '11px' }}>
                      SUSTAINED: <strong style={{ color: 'var(--color-bone)' }}>{r.sustained_seconds}s</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
