import React, { useState, useEffect, useCallback, useRef } from 'react';
import type {
  IncidentSummary,
  IncidentDetail,
  ResourceItem,
  ResourceListResponse,
} from '../types';
import { ApiClient } from '../api/client';
import { Card } from '../components/common/Card';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

interface IncidentsViewProps {
  onNavigateToGis?: () => void;
}

export const IncidentsView: React.FC<IncidentsViewProps> = ({ onNavigateToGis }) => {
  // Incident queue state
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<IncidentDetail | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  // Resources state
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [resourceStats, setResourceStats] = useState<{ available: number; assigned: number }>({ available: 0, assigned: 0 });
  const [selectedResourceId, setSelectedResourceId] = useState<string>('');
  const [assigningResource, setAssigningResource] = useState<boolean>(false);
  const [releasingResource, setReleasingResource] = useState<boolean>(false);

  // Actions state
  const [updatingStatus, setUpdatingStatus] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Resolution modal state
  const [showResolveModal, setShowResolveModal] = useState<boolean>(false);
  const [resolutionSummary, setResolutionSummary] = useState<string>('');
  const [resolveOperator, setResolveOperator] = useState<string>('operator');

  // Notes state
  const [newNoteText, setNewNoteText] = useState<string>('');
  const [addingNote, setAddingNote] = useState<boolean>(false);

  // Manual incident creation modal state
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [createTitle, setCreateTitle] = useState<string>('');
  const [createDescription, setCreateDescription] = useState<string>('');
  const [createSeverity, setCreateSeverity] = useState<string>('medium');
  const [createZoneId, setCreateZoneId] = useState<string>('zone_central_stage');
  const [creatingIncident, setCreatingIncident] = useState<boolean>(false);

  // Manual location update inline state
  const [editingLocation, setEditingLocation] = useState<boolean>(false);
  const [newZoneId, setNewZoneId] = useState<string>('zone_central_stage');
  const [updatingLocation, setUpdatingLocation] = useState<boolean>(false);

  const isMountedRef = useRef<boolean>(true);

  // Fetch incidents list
  const fetchIncidents = useCallback(async () => {
    setLoadingList(true);
    setListError(null);
    try {
      const data = await ApiClient.getIncidents({
        status: statusFilter,
        severity: severityFilter,
      });
      if (isMountedRef.current) {
        setIncidents(data.incidents);
        if (!selectedIncidentId && data.incidents.length > 0) {
          setSelectedIncidentId(data.incidents[0].id);
        }
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setListError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (isMountedRef.current) {
        setLoadingList(false);
      }
    }
  }, [statusFilter, severityFilter, selectedIncidentId]);

  // Fetch resources
  const fetchResources = useCallback(async () => {
    try {
      const data: ResourceListResponse = await ApiClient.getResources();
      if (isMountedRef.current) {
        setResources(data.resources);
        setResourceStats({ available: data.available, assigned: data.assigned });
        const firstAvail = data.resources.find((r) => r.status === 'available');
        if (firstAvail) setSelectedResourceId(firstAvail.id);
      }
    } catch {
      // Ignore background resource fetch error
    }
  }, []);

  // Fetch selected incident detail
  const fetchDetail = useCallback(async (incidentId: string) => {
    setLoadingDetail(true);
    setDetailError(null);
    setActionError(null);
    try {
      const data = await ApiClient.getIncidentDetail(incidentId);
      if (isMountedRef.current) {
        setSelectedIncident(data);
        setNewZoneId(data.zone_id || 'zone_central_stage');
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setDetailError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      if (isMountedRef.current) {
        setLoadingDetail(false);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    fetchIncidents();
    fetchResources();
    return () => {
      isMountedRef.current = false;
    };
  }, [fetchIncidents, fetchResources]);

  useEffect(() => {
    if (selectedIncidentId) {
      fetchDetail(selectedIncidentId);
    } else {
      setSelectedIncident(null);
    }
  }, [selectedIncidentId, fetchDetail]);

  // Handle status update
  const handleUpdateStatus = async (targetStatus: string, notes?: string) => {
    if (!selectedIncidentId) return;
    setUpdatingStatus(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await ApiClient.updateIncidentStatus(selectedIncidentId, {
        status: targetStatus,
        notes: notes,
        operator: resolveOperator || 'operator',
      });
      setSelectedIncident(res);
      setActionSuccess(`Status transitioned to ${targetStatus.toUpperCase()}`);
      await fetchIncidents();
      await fetchResources();
      if (targetStatus === 'resolved') {
        setShowResolveModal(false);
        setResolutionSummary('');
      }
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setUpdatingStatus(false);
    }
  };

  // Handle resource assignment
  const handleAssignResource = async () => {
    if (!selectedIncidentId || !selectedResourceId) return;
    setAssigningResource(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await ApiClient.assignResource(selectedIncidentId, selectedResourceId);
      setSelectedIncident(res);
      setActionSuccess(`Resource assigned successfully. Incident marked IN_PROGRESS.`);
      await fetchIncidents();
      await fetchResources();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setAssigningResource(false);
    }
  };

  // Handle resource release
  const handleReleaseResource = async () => {
    if (!selectedIncidentId) return;
    setReleasingResource(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const res = await ApiClient.releaseResource(selectedIncidentId);
      setSelectedIncident(res);
      setActionSuccess('Resource released and returned to available status.');
      await fetchIncidents();
      await fetchResources();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setReleasingResource(false);
    }
  };

  // Handle adding note
  const handleAddNote = async () => {
    if (!selectedIncidentId || !newNoteText.trim()) return;
    setAddingNote(true);
    setActionError(null);
    try {
      await ApiClient.addIncidentNote(selectedIncidentId, newNoteText.trim());
      setNewNoteText('');
      await fetchDetail(selectedIncidentId);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setAddingNote(false);
    }
  };

  // Handle manual location update
  const handleUpdateLocation = async () => {
    if (!selectedIncidentId) return;
    setUpdatingLocation(true);
    setActionError(null);
    try {
      const res = await ApiClient.updateIncidentLocation(selectedIncidentId, {
        venue_id: selectedIncident?.venue_id || 'venue_triveni',
        zone_id: newZoneId,
      });
      setSelectedIncident(res);
      setEditingLocation(false);
      setActionSuccess(`Location updated to ${newZoneId} (Confirmed).`);
      await fetchIncidents();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setUpdatingLocation(false);
    }
  };

  // Handle creating manual incident
  const handleCreateIncident = async () => {
    if (!createTitle.trim() || !createDescription.trim()) return;
    setCreatingIncident(true);
    setActionError(null);
    try {
      const res = await ApiClient.createIncident({
        title: createTitle.trim(),
        description: createDescription.trim(),
        priority: createSeverity,
        zone_id: createZoneId,
        venue_id: 'venue_triveni',
      });
      setShowCreateModal(false);
      setCreateTitle('');
      setCreateDescription('');
      await fetchIncidents();
      setSelectedIncidentId(res.id);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setCreatingIncident(false);
    }
  };

  // Status colors helper
  const getStatusStyle = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return { color: 'var(--color-signal-orange)', bg: '#2B160C', border: '#7E2D07' };
      case 'acknowledged':
        return { color: '#E5A93C', bg: '#2B210C', border: '#7E5307' };
      case 'in_progress':
        return { color: '#68B0F8', bg: '#0C1C2B', border: '#07457E' };
      case 'resolved':
        return { color: 'var(--color-metric-green)', bg: '#0F2615', border: '#1B542B' };
      case 'closed':
        return { color: 'var(--color-warm-granite)', bg: '#1A1817', border: '#3D3A39' };
      default:
        return { color: 'var(--color-bone)', bg: '#1D1A18', border: '#3D3A39' };
    }
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return { color: '#FF4D4D', bg: '#330A0A', border: '#801414' };
      case 'high':
        return { color: 'var(--color-signal-orange)', bg: '#2B160C', border: '#7E2D07' };
      case 'medium':
        return { color: '#E5A93C', bg: '#2B210C', border: '#7E5307' };
      case 'low':
      default:
        return { color: 'var(--color-metric-green)', bg: '#0F2615', border: '#1B542B' };
    }
  };

  const availableUnits = resources.filter((r) => r.status === 'available');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header Banner */}
      <div style={{
        padding: 'var(--space-4) var(--space-5)',
        backgroundColor: 'var(--color-carbon-lift)',
        border: 'var(--border-hairline)',
        borderRadius: 'var(--radius-xs)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 'var(--space-3)',
      }}>
        <div>
          <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
            MODULE B // EMERGENCY INCIDENT DISPATCH & RESPONSE COORDINATION
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 500, letterSpacing: '-0.02em', marginTop: '2px' }}>
            Operational Incidents & Emergency Response
          </h1>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-secondary"
            style={{ borderColor: 'var(--color-signal-orange)', color: 'var(--color-signal-orange)' }}
          >
            + REPORT MANUAL INCIDENT
          </button>
          <button
            onClick={() => {
              fetchIncidents();
              fetchResources();
              if (selectedIncidentId) fetchDetail(selectedIncidentId);
            }}
            disabled={loadingList}
            className="btn btn-secondary"
          >
            {loadingList ? 'REFRESHING...' : 'REFRESH QUEUE'}
          </button>
        </div>
      </div>

      {/* Safety & Protocol Notice */}
      <div style={{
        padding: 'var(--space-3) var(--space-4)',
        backgroundColor: 'var(--color-obsidian-canvas)',
        border: '1px solid var(--color-ash-stroke)',
        borderRadius: 'var(--radius-xs)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
      }}>
        <div style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: 'var(--color-signal-orange)',
        }} />
        <div style={{ fontSize: '12px', color: 'var(--color-warm-granite)', lineHeight: 1.4 }}>
          <strong>DECISION-SUPPORT SYSTEM:</strong> Incident dispatch coordinates simulated on-site response teams (First Aid, Security Patrols, Wardens). The system does not automatically dispatch municipal emergency services or claim guaranteed evacuation safety.
        </div>
      </div>

      {/* Operational Metrics Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 'var(--space-4)',
      }}>
        <div style={{
          padding: 'var(--space-3) var(--space-4)',
          backgroundColor: 'var(--color-carbon-lift)',
          border: 'var(--border-hairline)',
          borderRadius: 'var(--radius-xs)',
        }}>
          <div className="mono-caption">ACTIVE INCIDENTS</div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: 'var(--color-bone)', marginTop: '2px' }}>
            {incidents.filter((i) => i.status !== 'resolved' && i.status !== 'closed').length}
          </div>
        </div>
        <div style={{
          padding: 'var(--space-3) var(--space-4)',
          backgroundColor: 'var(--color-carbon-lift)',
          border: 'var(--border-hairline)',
          borderRadius: 'var(--radius-xs)',
        }}>
          <div className="mono-caption">IN PROGRESS / DISPATCHED</div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: '#68B0F8', marginTop: '2px' }}>
            {incidents.filter((i) => i.status === 'in_progress').length}
          </div>
        </div>
        <div style={{
          padding: 'var(--space-3) var(--space-4)',
          backgroundColor: 'var(--color-carbon-lift)',
          border: 'var(--border-hairline)',
          borderRadius: 'var(--radius-xs)',
        }}>
          <div className="mono-caption">RESOLVED TODAY</div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: 'var(--color-metric-green)', marginTop: '2px' }}>
            {incidents.filter((i) => i.status === 'resolved' || i.status === 'closed').length}
          </div>
        </div>
        <div style={{
          padding: 'var(--space-3) var(--space-4)',
          backgroundColor: 'var(--color-carbon-lift)',
          border: 'var(--border-hairline)',
          borderRadius: 'var(--radius-xs)',
        }}>
          <div className="mono-caption">AVAILABLE RESPONSE UNITS</div>
          <div style={{ fontSize: '22px', fontWeight: 600, color: resourceStats.available > 0 ? 'var(--color-metric-green)' : 'var(--color-alert-red)', marginTop: '2px' }}>
            {resourceStats.available} / {resources.length}
          </div>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(340px, 420px) 1fr',
        gap: 'var(--space-6)',
        alignItems: 'start',
      }}>
        {/* Left: Incident Triage Queue */}
        <Card title={`INCIDENT QUEUE (${incidents.length})`}>
          {/* Queue Filters */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
            <div>
              <div className="mono-caption" style={{ marginBottom: '4px' }}>STATUS FILTER</div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {['ALL', 'OPEN', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    style={{
                      padding: '3px 8px',
                      fontSize: '10px',
                      fontFamily: 'var(--font-mono)',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: statusFilter === st ? 'var(--color-signal-orange)' : '#161413',
                      color: statusFilter === st ? '#FFFFFF' : 'var(--color-bone)',
                      border: statusFilter === st ? '1px solid var(--color-signal-orange)' : 'var(--border-hairline)',
                      cursor: 'pointer',
                    }}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="mono-caption" style={{ marginBottom: '4px' }}>SEVERITY FILTER</div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setSeverityFilter(sev)}
                    style={{
                      padding: '3px 8px',
                      fontSize: '10px',
                      fontFamily: 'var(--font-mono)',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: severityFilter === sev ? 'var(--color-ash-stroke)' : '#161413',
                      color: severityFilter === sev ? '#FFFFFF' : 'var(--color-bone)',
                      border: 'var(--border-hairline)',
                      cursor: 'pointer',
                    }}
                  >
                    {sev}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Incidents List Container */}
          {loadingList ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-8)' }}>
              <LoadingSpinner message="LOADING INCIDENT QUEUE..." />
            </div>
          ) : listError ? (
            <div style={{
              padding: 'var(--space-4)',
              backgroundColor: '#330A0A',
              border: '1px solid #801414',
              borderRadius: 'var(--radius-xs)',
              fontSize: '12px',
              color: '#FF8080',
            }}>
              Error loading incidents: {listError}
            </div>
          ) : incidents.length === 0 ? (
            <div style={{
              padding: 'var(--space-8)',
              textAlign: 'center',
              color: 'var(--color-warm-granite)',
              fontSize: '12px',
              border: '1px dashed var(--color-ash-stroke)',
              borderRadius: 'var(--radius-xs)',
            }}>
              No incidents matching filter criteria.
              <div style={{ marginTop: 'var(--space-2)' }}>
                <button
                  onClick={() => { setStatusFilter('ALL'); setSeverityFilter('ALL'); }}
                  className="btn btn-secondary"
                  style={{ fontSize: '11px', padding: '4px 10px' }}
                >
                  RESET FILTERS
                </button>
              </div>
            </div>
          ) : (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
              maxHeight: '620px',
              overflowY: 'auto',
            }}>
              {incidents.map((inc) => {
                const isSelected = inc.id === selectedIncidentId;
                const statusStyle = getStatusStyle(inc.status);
                const sevStyle = getSeverityStyle(inc.severity);

                return (
                  <div
                    key={inc.id}
                    onClick={() => setSelectedIncidentId(inc.id)}
                    style={{
                      padding: 'var(--space-3)',
                      backgroundColor: isSelected ? 'var(--color-carbon-lift)' : 'var(--color-obsidian-canvas)',
                      border: isSelected ? '1px solid var(--color-signal-orange)' : 'var(--border-hairline)',
                      borderRadius: 'var(--radius-xs)',
                      cursor: 'pointer',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span className="mono-caption" style={{ color: 'var(--color-bone)', fontWeight: 600 }}>
                        {inc.incident_number}
                      </span>
                      <span style={{
                        padding: '1px 6px',
                        fontSize: '10px',
                        fontFamily: 'var(--font-mono)',
                        borderRadius: '2px',
                        color: sevStyle.color,
                        backgroundColor: sevStyle.bg,
                        border: `1px solid ${sevStyle.border}`,
                        textTransform: 'uppercase',
                        fontWeight: 600,
                      }}>
                        {inc.severity}
                      </span>
                    </div>

                    <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-light-cream)', marginBottom: '6px' }}>
                      {inc.title}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px' }}>
                      <span style={{
                        padding: '1px 6px',
                        fontSize: '10px',
                        fontFamily: 'var(--font-mono)',
                        borderRadius: '2px',
                        color: statusStyle.color,
                        backgroundColor: statusStyle.bg,
                        border: `1px solid ${statusStyle.border}`,
                        textTransform: 'uppercase',
                      }}>
                        {inc.status.replace('_', ' ')}
                      </span>

                      <span className="mono-caption" style={{ color: inc.zone_id ? 'var(--color-bone)' : 'var(--color-alert-red)' }}>
                        {inc.zone_id ? inc.zone_id : 'UNKNOWN LOC'}
                      </span>
                    </div>

                    <div className="mono-caption" style={{ fontSize: '10px', marginTop: '6px', color: 'var(--color-warm-granite)' }}>
                      {new Date(inc.created_at).toLocaleTimeString()} • {new Date(inc.created_at).toLocaleDateString()}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        {/* Right: Incident Inspector & Coordination Console */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {loadingDetail ? (
            <Card title="INCIDENT INSPECTOR">
              <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-12)' }}>
                <LoadingSpinner message="LOADING INCIDENT DOSSIER..." />
              </div>
            </Card>
          ) : detailError ? (
            <Card title="INCIDENT INSPECTOR">
              <div style={{
                padding: 'var(--space-4)',
                backgroundColor: '#330A0A',
                border: '1px solid #801414',
                borderRadius: 'var(--radius-xs)',
                fontSize: '12px',
                color: '#FF8080',
              }}>
                Error retrieving incident details: {detailError}
              </div>
            </Card>
          ) : selectedIncident ? (
            <>
              {/* Incident Header Card */}
              <Card title={`INCIDENT RECORD // ${selectedIncident.incident_number}`}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  {/* Top Badge Row */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                    <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                      <span style={{
                        padding: '2px 8px',
                        fontSize: '11px',
                        fontFamily: 'var(--font-mono)',
                        borderRadius: '2px',
                        ...getSeverityStyle(selectedIncident.severity),
                        fontWeight: 600,
                        textTransform: 'uppercase',
                      }}>
                        {selectedIncident.severity} PRIORITY
                      </span>

                      <span style={{
                        padding: '2px 8px',
                        fontSize: '11px',
                        fontFamily: 'var(--font-mono)',
                        borderRadius: '2px',
                        ...getStatusStyle(selectedIncident.status),
                        fontWeight: 600,
                        textTransform: 'uppercase',
                      }}>
                        STATUS: {selectedIncident.status.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="mono-caption">
                      LOGGED BY: <strong>{selectedIncident.created_by}</strong> • {new Date(selectedIncident.created_at).toLocaleString()}
                    </div>
                  </div>

                  {/* Incident Title & Description */}
                  <div>
                    <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-bone)', marginBottom: '6px' }}>
                      {selectedIncident.title}
                    </h2>
                    <p style={{ fontSize: '13px', color: 'var(--color-bone)', lineHeight: 1.5, margin: 0 }}>
                      {selectedIncident.description}
                    </p>
                  </div>

                  {/* Location & GIS Linkage */}
                  <div style={{
                    padding: 'var(--space-3) var(--space-4)',
                    backgroundColor: '#161413',
                    border: 'var(--border-hairline)',
                    borderRadius: 'var(--radius-xs)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 'var(--space-3)',
                  }}>
                    <div>
                      <div className="mono-caption" style={{ marginBottom: '2px' }}>
                        GIS LOCATION CONTEXT
                      </div>
                      <div style={{ fontSize: '12px' }}>
                        Venue: <strong>{selectedIncident.venue_id || 'Triveni Arena'}</strong> • Zone: <strong>{selectedIncident.zone_id || 'Unassigned'}</strong>
                        <span style={{
                          marginLeft: '8px',
                          padding: '1px 6px',
                          fontSize: '10px',
                          fontFamily: 'var(--font-mono)',
                          borderRadius: '2px',
                          backgroundColor: selectedIncident.location_status === 'confirmed' ? '#0F2615' : '#2B160C',
                          color: selectedIncident.location_status === 'confirmed' ? 'var(--color-metric-green)' : 'var(--color-signal-orange)',
                          border: `1px solid ${selectedIncident.location_status === 'confirmed' ? '#1B542B' : '#7E2D07'}`,
                        }}>
                          {selectedIncident.location_status.toUpperCase()}
                        </span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                      <button
                        onClick={() => setEditingLocation(!editingLocation)}
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '4px 10px' }}
                      >
                        {editingLocation ? 'CANCEL EDIT' : 'EDIT LOCATION'}
                      </button>

                      {onNavigateToGis && selectedIncident.zone_id && (
                        <button
                          onClick={onNavigateToGis}
                          className="btn btn-primary"
                          style={{ fontSize: '11px', padding: '4px 12px' }}
                        >
                          EVALUATE ROUTE IN GIS →
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Inline Location Editor */}
                  {editingLocation && (
                    <div style={{
                      padding: 'var(--space-3)',
                      backgroundColor: 'var(--color-obsidian-canvas)',
                      border: '1px solid var(--color-ash-stroke)',
                      borderRadius: 'var(--radius-xs)',
                      display: 'flex',
                      gap: 'var(--space-3)',
                      alignItems: 'center',
                    }}>
                      <div style={{ flex: 1 }}>
                        <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                          TARGET VENUE ZONE
                        </label>
                        <select
                          value={newZoneId}
                          onChange={(e) => setNewZoneId(e.target.value)}
                          style={{
                            width: '100%',
                            padding: '6px 8px',
                            backgroundColor: '#161413',
                            border: 'var(--border-hairline)',
                            color: 'var(--color-bone)',
                            borderRadius: 'var(--radius-xs)',
                            fontFamily: 'var(--font-sans)',
                          }}
                        >
                          <option value="zone_main_gate">Zone Main Gate (Gate 1 & Plaza)</option>
                          <option value="zone_central_stage">Zone Central Stage (Main Arena)</option>
                          <option value="zone_north_plaza">Zone North Plaza (Concourse)</option>
                          <option value="zone_east_concourse">Zone East Concourse</option>
                        </select>
                      </div>
                      <button
                        onClick={handleUpdateLocation}
                        disabled={updatingLocation}
                        className="btn btn-primary"
                        style={{ alignSelf: 'flex-end' }}
                      >
                        {updatingLocation ? 'SAVING...' : 'CONFIRM LOCATION'}
                      </button>
                    </div>
                  )}

                  {/* Originating Event & Evidence Snapshot */}
                  {selectedIncident.event_id && (
                    <div style={{
                      padding: 'var(--space-3) var(--space-4)',
                      backgroundColor: '#161413',
                      border: 'var(--border-hairline)',
                      borderRadius: 'var(--radius-xs)',
                    }}>
                      <div className="mono-caption" style={{ color: 'var(--color-signal-orange)', marginBottom: '4px' }}>
                        ORIGINATING VISIONX CROWD ALERT
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-bone)' }}>
                        Linked Event ID: <code>{selectedIncident.event_id}</code>
                      </div>
                      {selectedIncident.evidence_image_url && (
                        <div style={{ marginTop: 'var(--space-3)' }}>
                          <div className="mono-caption" style={{ marginBottom: '4px' }}>
                            CAMERA DETECTION SNAPSHOT
                          </div>
                          <img
                            src={ApiClient.getEvidenceImageUrl(selectedIncident.evidence_image_url)}
                            alt="Detection evidence"
                            style={{
                              maxWidth: '100%',
                              maxHeight: '260px',
                              objectFit: 'contain',
                              borderRadius: 'var(--radius-xs)',
                              border: '1px solid var(--color-ash-stroke)',
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Resolution Summary (if resolved or closed) */}
                  {(selectedIncident.status === 'resolved' || selectedIncident.status === 'closed') && selectedIncident.resolution_notes && (
                    <div style={{
                      padding: 'var(--space-3) var(--space-4)',
                      backgroundColor: '#0F2615',
                      border: '1px solid #1B542B',
                      borderRadius: 'var(--radius-xs)',
                    }}>
                      <div className="mono-caption" style={{ color: 'var(--color-metric-green)', marginBottom: '2px' }}>
                        OFFICIAL RESOLUTION SUMMARY
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-bone)', lineHeight: 1.5 }}>
                        "{selectedIncident.resolution_notes}"
                      </div>
                      <div className="mono-caption" style={{ fontSize: '10px', marginTop: '4px', color: 'var(--color-warm-granite)' }}>
                        Resolved by: <strong>{selectedIncident.resolved_by || 'operator'}</strong> at {selectedIncident.resolved_at ? new Date(selectedIncident.resolved_at).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                  )}

                  {/* Action Notifications */}
                  {actionSuccess && (
                    <div style={{ fontSize: '12px', color: 'var(--color-metric-green)' }}>
                      ✓ {actionSuccess}
                    </div>
                  )}
                  {actionError && (
                    <div style={{ fontSize: '12px', color: 'var(--color-alert-red)' }}>
                      ⚠ {actionError}
                    </div>
                  )}

                  {/* Lifecycle Progression Control Bar */}
                  <div style={{
                    padding: 'var(--space-4)',
                    backgroundColor: 'var(--color-obsidian-canvas)',
                    border: '1px solid var(--color-ash-stroke)',
                    borderRadius: 'var(--radius-xs)',
                  }}>
                    <div className="mono-caption" style={{ marginBottom: 'var(--space-3)' }}>
                      LIFECYCLE STATUS PROGRESSION
                    </div>

                    <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                      {selectedIncident.status === 'open' && (
                        <>
                          <button
                            onClick={() => handleUpdateStatus('acknowledged')}
                            disabled={updatingStatus}
                            className="btn btn-secondary"
                            style={{ flex: 1 }}
                          >
                            ACKNOWLEDGE INCIDENT
                          </button>
                          <button
                            onClick={() => handleUpdateStatus('in_progress')}
                            disabled={updatingStatus}
                            className="btn btn-primary"
                            style={{ flex: 1 }}
                          >
                            START RESPONSE
                          </button>
                        </>
                      )}

                      {selectedIncident.status === 'acknowledged' && (
                        <>
                          <button
                            onClick={() => handleUpdateStatus('in_progress')}
                            disabled={updatingStatus}
                            className="btn btn-primary"
                            style={{ flex: 1 }}
                          >
                            START RESPONSE
                          </button>
                          <button
                            onClick={() => setShowResolveModal(true)}
                            disabled={updatingStatus}
                            className="btn btn-secondary"
                            style={{ flex: 1, borderColor: 'var(--color-metric-green)', color: 'var(--color-metric-green)' }}
                          >
                            MARK RESOLVED
                          </button>
                        </>
                      )}

                      {selectedIncident.status === 'in_progress' && (
                        <button
                          onClick={() => setShowResolveModal(true)}
                          disabled={updatingStatus}
                          className="btn btn-primary"
                          style={{ flex: 1, backgroundColor: 'var(--color-metric-green)', borderColor: 'var(--color-metric-green)', color: '#000000' }}
                        >
                          RESOLVE INCIDENT
                        </button>
                      )}

                      {selectedIncident.status === 'resolved' && (
                        <button
                          onClick={() => handleUpdateStatus('closed', 'Administrative closure by operator.')}
                          disabled={updatingStatus}
                          className="btn btn-secondary"
                          style={{ flex: 1 }}
                        >
                          CLOSE INCIDENT (ARCHIVE)
                        </button>
                      )}

                      {selectedIncident.status === 'closed' && (
                        <div className="mono-caption" style={{ color: 'var(--color-warm-granite)', padding: '6px 0' }}>
                          INCIDENT CLOSED — TERMINAL AUDIT RECORD PERSISTED
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Simulated Resource Assignment Panel */}
              <Card title="SIMULATED RESPONSE RESOURCE ALLOCATION">
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  <div className="mono-caption" style={{ color: 'var(--color-warm-granite)' }}>
                    DEMO SQUAD REGISTRY // On-site venue response teams for crowd safety operations
                  </div>

                  {selectedIncident.assigned_resource ? (
                    <div style={{
                      padding: 'var(--space-4)',
                      backgroundColor: '#161413',
                      border: '1px solid #07457E',
                      borderRadius: 'var(--radius-xs)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: 'var(--space-3)',
                    }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                          <span style={{ fontSize: '14px', fontWeight: 600, color: '#68B0F8' }}>
                            {selectedIncident.assigned_resource.name}
                          </span>
                          <span className="mono-caption" style={{ color: 'var(--color-bone)' }}>
                            [{selectedIncident.assigned_resource.call_sign}]
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--color-warm-granite)', marginTop: '2px' }}>
                          Type: <strong>{selectedIncident.assigned_resource.resource_type.toUpperCase()}</strong> • Contact: {selectedIncident.assigned_resource.contact_info || 'N/A'}
                        </div>
                        {selectedIncident.assigned_resource.description && (
                          <div style={{ fontSize: '11px', color: 'var(--color-bone)', marginTop: '4px' }}>
                            {selectedIncident.assigned_resource.description}
                          </div>
                        )}
                      </div>

                      {selectedIncident.status !== 'resolved' && selectedIncident.status !== 'closed' && (
                        <button
                          onClick={handleReleaseResource}
                          disabled={releasingResource}
                          className="btn btn-secondary"
                          style={{ borderColor: 'var(--color-alert-red)', color: 'var(--color-alert-red)' }}
                        >
                          {releasingResource ? 'RELEASING...' : 'RELEASE UNIT'}
                        </button>
                      )}
                    </div>
                  ) : (
                    <div style={{
                      padding: 'var(--space-4)',
                      backgroundColor: '#161413',
                      border: 'var(--border-hairline)',
                      borderRadius: 'var(--radius-xs)',
                    }}>
                      {selectedIncident.status === 'resolved' || selectedIncident.status === 'closed' ? (
                        <div className="mono-caption" style={{ color: 'var(--color-warm-granite)' }}>
                          No response resource currently allocated. Incident is resolved/closed.
                        </div>
                      ) : availableUnits.length === 0 ? (
                        <div style={{ fontSize: '12px', color: 'var(--color-alert-red)' }}>
                          ⚠ All simulated response units are currently assigned or in maintenance.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', flexWrap: 'wrap' }}>
                          <div style={{ flex: 1, minWidth: '220px' }}>
                            <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                              SELECT AVAILABLE SQUAD ({availableUnits.length} READY)
                            </label>
                            <select
                              value={selectedResourceId}
                              onChange={(e) => setSelectedResourceId(e.target.value)}
                              style={{
                                width: '100%',
                                padding: '6px 8px',
                                backgroundColor: 'var(--color-obsidian-canvas)',
                                border: 'var(--border-hairline)',
                                color: 'var(--color-bone)',
                                borderRadius: 'var(--radius-xs)',
                                fontFamily: 'var(--font-sans)',
                                fontSize: '12px',
                              }}
                            >
                              {availableUnits.map((r) => (
                                <option key={r.id} value={r.id}>
                                  {r.name} [{r.call_sign}] — {r.resource_type.toUpperCase()}
                                </option>
                              ))}
                            </select>
                          </div>

                          <button
                            onClick={handleAssignResource}
                            disabled={assigningResource || !selectedResourceId}
                            className="btn btn-primary"
                            style={{ alignSelf: 'flex-end' }}
                          >
                            {assigningResource ? 'ASSIGNING...' : 'ASSIGN RESPONSE UNIT'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </Card>

              {/* Operator Notes & Incident Audit History */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: 'var(--space-6)',
              }}>
                {/* Notes Thread */}
                <Card title={`OPERATOR NOTES (${selectedIncident.notes.length})`}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                    {/* Add note input */}
                    <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                      <input
                        type="text"
                        value={newNoteText}
                        onChange={(e) => setNewNoteText(e.target.value)}
                        placeholder="Add operator assessment note..."
                        style={{
                          flex: 1,
                          padding: '6px 10px',
                          backgroundColor: '#161413',
                          border: 'var(--border-hairline)',
                          borderRadius: 'var(--radius-xs)',
                          color: 'var(--color-bone)',
                          fontSize: '12px',
                        }}
                      />
                      <button
                        onClick={handleAddNote}
                        disabled={addingNote || !newNoteText.trim()}
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '4px 10px' }}
                      >
                        {addingNote ? 'SAVING...' : 'ADD NOTE'}
                      </button>
                    </div>

                    {/* Notes list */}
                    {selectedIncident.notes.length === 0 ? (
                      <div className="mono-caption" style={{ padding: 'var(--space-3)', color: 'var(--color-warm-granite)' }}>
                        No operator notes logged yet.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', maxHeight: '220px', overflowY: 'auto' }}>
                        {selectedIncident.notes.map((n) => (
                          <div
                            key={n.id}
                            style={{
                              padding: '8px',
                              backgroundColor: '#161413',
                              border: 'var(--border-hairline)',
                              borderRadius: 'var(--radius-xs)',
                              fontSize: '12px',
                            }}
                          >
                            <div style={{ color: 'var(--color-bone)', lineHeight: 1.4 }}>
                              {n.note_text}
                            </div>
                            <div className="mono-caption" style={{ fontSize: '10px', marginTop: '4px', color: 'var(--color-warm-granite)' }}>
                              {n.author} • {new Date(n.created_at).toLocaleTimeString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </Card>

                {/* Audit Trail */}
                <Card title={`AUDIT TRAIL (${selectedIncident.history.length})`}>
                  {selectedIncident.history.length === 0 ? (
                    <div className="mono-caption" style={{ padding: 'var(--space-3)', color: 'var(--color-warm-granite)' }}>
                      No audit history entries recorded.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', maxHeight: '260px', overflowY: 'auto' }}>
                      {selectedIncident.history.map((h) => (
                        <div
                          key={h.id}
                          style={{
                            padding: '6px 8px',
                            backgroundColor: '#161413',
                            border: 'var(--border-hairline)',
                            borderRadius: 'var(--radius-xs)',
                            fontSize: '11px',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span className="mono-caption" style={{ color: 'var(--color-signal-orange)', fontWeight: 600 }}>
                              {h.action.toUpperCase()}
                            </span>
                            <span className="mono-caption" style={{ fontSize: '9px', color: 'var(--color-warm-granite)' }}>
                              {new Date(h.created_at).toLocaleTimeString()}
                            </span>
                          </div>
                          {h.old_value && h.new_value && (
                            <div style={{ fontSize: '10px', color: 'var(--color-bone)', marginTop: '2px' }}>
                              {h.old_value} → {h.new_value}
                            </div>
                          )}
                          <div className="mono-caption" style={{ fontSize: '9px', color: 'var(--color-warm-granite)', marginTop: '2px' }}>
                            Actor: {h.performed_by}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              </div>
            </>
          ) : (
            <Card title="INCIDENT INSPECTOR">
              <div style={{
                textAlign: 'center',
                padding: 'var(--space-12)',
                color: 'var(--color-warm-granite)',
                fontSize: '13px',
              }}>
                Select an incident from the queue on the left to inspect situation details, coordinate response resources, and review audit history.
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Mandatory Resolution Summary Modal */}
      {showResolveModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            width: '90%',
            maxWidth: '520px',
            backgroundColor: 'var(--color-carbon-lift)',
            border: '1px solid var(--color-ash-stroke)',
            borderRadius: 'var(--radius-xs)',
            padding: 'var(--space-6)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)',
          }}>
            <div>
              <div className="mono-caption" style={{ color: 'var(--color-metric-green)' }}>
                MANDATORY RESOLUTION PROTOCOL
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-bone)', marginTop: '2px' }}>
                Resolve Incident {selectedIncident?.incident_number}
              </h3>
            </div>

            <div style={{ fontSize: '12px', color: 'var(--color-warm-granite)', lineHeight: 1.4 }}>
              Per venue safety protocol, marking an incident as resolved strictly requires a descriptive resolution summary note. Any assigned resource will automatically be released back to the available registry.
            </div>

            <div>
              <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                RESOLUTION SUMMARY & OPERATIONAL OUTCOME *
              </label>
              <textarea
                value={resolutionSummary}
                onChange={(e) => setResolutionSummary(e.target.value)}
                rows={3}
                placeholder="Describe resolution outcome (e.g. 'Paramedic team treated minor heat exhaustion at North Plaza. Crowd dispersed safely; egress route normal.')..."
                style={{
                  width: '100%',
                  padding: '8px',
                  backgroundColor: '#161413',
                  border: 'var(--border-hairline)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--color-bone)',
                  fontSize: '12px',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>

            <div>
              <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                RESOLVING OPERATOR IDENTIFIER
              </label>
              <input
                type="text"
                value={resolveOperator}
                onChange={(e) => setResolveOperator(e.target.value)}
                style={{
                  width: '100%',
                  padding: '6px 8px',
                  backgroundColor: '#161413',
                  border: 'var(--border-hairline)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--color-bone)',
                  fontSize: '12px',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
              <button
                onClick={() => setShowResolveModal(false)}
                className="btn btn-secondary"
              >
                CANCEL
              </button>
              <button
                onClick={() => handleUpdateStatus('resolved', resolutionSummary)}
                disabled={updatingStatus || !resolutionSummary.trim()}
                className="btn btn-primary"
                style={{ backgroundColor: 'var(--color-metric-green)', borderColor: 'var(--color-metric-green)', color: '#000000' }}
              >
                {updatingStatus ? 'COMMITTING RESOLUTION...' : 'CONFIRM RESOLUTION'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manual Incident Creation Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            width: '90%',
            maxWidth: '520px',
            backgroundColor: 'var(--color-carbon-lift)',
            border: '1px solid var(--color-ash-stroke)',
            borderRadius: 'var(--radius-xs)',
            padding: 'var(--space-6)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-4)',
          }}>
            <div>
              <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
                MANUAL OPERATOR ENTRY
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-bone)', marginTop: '2px' }}>
                Log Operational Incident
              </h3>
            </div>

            <div>
              <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                INCIDENT TITLE *
              </label>
              <input
                type="text"
                value={createTitle}
                onChange={(e) => setCreateTitle(e.target.value)}
                placeholder="e.g., Gate 1 Bottleneck Surge"
                style={{
                  width: '100%',
                  padding: '6px 8px',
                  backgroundColor: '#161413',
                  border: 'var(--border-hairline)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--color-bone)',
                  fontSize: '12px',
                }}
              />
            </div>

            <div>
              <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                OPERATIONAL DESCRIPTION *
              </label>
              <textarea
                value={createDescription}
                onChange={(e) => setCreateDescription(e.target.value)}
                rows={3}
                placeholder="Detail the operational situation and required response..."
                style={{
                  width: '100%',
                  padding: '8px',
                  backgroundColor: '#161413',
                  border: 'var(--border-hairline)',
                  borderRadius: 'var(--radius-xs)',
                  color: 'var(--color-bone)',
                  fontSize: '12px',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
              <div>
                <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                  PRIORITY SEVERITY
                </label>
                <select
                  value={createSeverity}
                  onChange={(e) => setCreateSeverity(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 8px',
                    backgroundColor: '#161413',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '12px',
                  }}
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div>
                <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                  VENUE ZONE
                </label>
                <select
                  value={createZoneId}
                  onChange={(e) => setCreateZoneId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 8px',
                    backgroundColor: '#161413',
                    border: 'var(--border-hairline)',
                    color: 'var(--color-bone)',
                    borderRadius: 'var(--radius-xs)',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '12px',
                  }}
                >
                  <option value="zone_main_gate">Zone Main Gate (Gate 1)</option>
                  <option value="zone_central_stage">Zone Central Stage</option>
                  <option value="zone_north_plaza">Zone North Plaza</option>
                  <option value="zone_east_concourse">Zone East Concourse</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn btn-secondary"
              >
                CANCEL
              </button>
              <button
                onClick={handleCreateIncident}
                disabled={creatingIncident || !createTitle.trim() || !createDescription.trim()}
                className="btn btn-primary"
              >
                {creatingIncident ? 'CREATING...' : 'CREATE INCIDENT'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
