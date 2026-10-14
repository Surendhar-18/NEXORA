import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MapPin,
  Navigation,
  Ban,
  CheckCircle,
  AlertTriangle,
  RotateCcw,
  Layers,
  ArrowRight,
  ShieldAlert,
  Info,
  Maximize2
} from 'lucide-react';
import { ApiClient } from '../api/client';
import type {
  VenueDetail,
  VenueNode,
  RouteComparisonResponse,
  CrowdEvent
} from '../types';

export const GisOperationsView: React.FC = () => {
  // Map and Data State
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersGroupRef = useRef<L.LayerGroup | null>(null);

  const [venue, setVenue] = useState<VenueDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Routing State
  const [originNodeId, setOriginNodeId] = useState<string>('gate_main');
  const [destNodeId, setDestNodeId] = useState<string>('exit_north');
  const [maxRoutes, setMaxRoutes] = useState<number>(3);
  const [routingResult, setRoutingResult] = useState<RouteComparisonResponse | null>(null);
  const [selectedRouteRank, setSelectedRouteRank] = useState<number>(1);
  const [calculatingRoute, setCalculatingRoute] = useState<boolean>(false);

  // Walkway Inspection & Blockage State
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [blockModalOpen, setBlockModalOpen] = useState<boolean>(false);
  const [blockReason, setBlockReason] = useState<string>('Heavy congestion diversion');
  const [actionInProgress, setActionInProgress] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Active Tab: 'route' | 'walkways' | 'zones'
  const [activeTab, setActiveTab] = useState<'route' | 'walkways' | 'zones'>('route');

  // Crowd Events for Zone Linkage
  const [events, setEvents] = useState<CrowdEvent[]>([]);

  // Load Venue Data
  const loadVenueData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiClient.getVenue();
      setVenue(data);

      // Also fetch events to link zones
      try {
        const evData = await ApiClient.getEvents({ limit: 50 });
        setEvents(evData.events);
      } catch {
        // Non-critical if events fail to load
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load venue GIS topology');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVenueData();
  }, []);

  // Initialize and Render Map
  useEffect(() => {
    if (!mapContainerRef.current || !venue) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [venue.center.latitude, venue.center.longitude],
        zoom: venue.zoom_level || 17,
        zoomControl: true,
        attributionControl: true,
      });

      // Basemap tile layer configuration:
      // If a CARTO API key is provided via VITE_CARTO_API_KEY, use CARTO raster tiles with the key.
      // Otherwise, use Stadia Alidade Smooth Dark (licensed for localhost development without key).
      const cartoKey = import.meta.env.VITE_CARTO_API_KEY;
      const customTileUrl = import.meta.env.VITE_MAP_TILE_URL;

      let tileUrl = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png';
      let tileAttribution = '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors';
      let subdomains: string | string[] = 'abc';

      if (customTileUrl) {
        tileUrl = customTileUrl;
        tileAttribution = import.meta.env.VITE_MAP_ATTRIBUTION || '&copy; OpenStreetMap contributors';
      } else if (cartoKey) {
        tileUrl = `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${encodeURIComponent(cartoKey)}`;
        tileAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
        subdomains = 'abcd';
      }

      L.tileLayer(tileUrl, {
        attribution: tileAttribution,
        subdomains,
        maxZoom: 20,
      }).addTo(map);

      const layersGroup = L.layerGroup().addTo(map);
      layersGroupRef.current = layersGroup;
      mapInstanceRef.current = map;
    }

    renderMapLayers();
  }, [venue, routingResult, selectedRouteRank, selectedEdgeId]);

  // Clean up Leaflet on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Render Zones, Edges, Routes, and Nodes onto Map
  const renderMapLayers = () => {
    if (!mapInstanceRef.current || !layersGroupRef.current || !venue) return;

    const group = layersGroupRef.current;
    group.clearLayers();

    const nodeMap = new Map<string, VenueNode>();
    venue.nodes.forEach((n) => nodeMap.set(n.id, n));

    // 1. Render Zones
    venue.zones.forEach((zone) => {
      if (zone.polygon && zone.polygon.length >= 3) {
        const latLngs = zone.polygon.map((pt) => [pt[0], pt[1]] as [number, number]);
        const poly = L.polygon(latLngs, {
          color: zone.color,
          fillColor: zone.color,
          fillOpacity: 0.12,
          weight: 1.5,
          dashArray: '4, 4',
        });

        poly.bindTooltip(
          `<div style="font-family: var(--font-mono); font-size: 11px; color: ${zone.color};">
            <strong>${zone.name}</strong><br/>
            <span style="color: #999;">${zone.id}</span>
          </div>`,
          { sticky: true, opacity: 0.9 }
        );

        poly.on('click', () => {
          setActiveTab('zones');
        });

        poly.addTo(group);
      }
    });

    // 2. Render Walkways (Base Edges)
    venue.edges.forEach((edge) => {
      const u = nodeMap.get(edge.from_node);
      const v = nodeMap.get(edge.to_node);
      if (!u || !v) return;

      const isSelected = selectedEdgeId === edge.id;
      const isBlocked = edge.is_blocked;

      let color = '#555555';
      let weight = 3;
      let dashArray: string | undefined = undefined;
      let opacity = 0.6;

      if (isBlocked) {
        color = '#EF4444';
        weight = 4;
        dashArray = '6, 6';
        opacity = 0.95;
      } else if (isSelected) {
        color = 'var(--color-signal-orange)';
        weight = 5;
        opacity = 1;
      }

      const line = L.polyline(
        [
          [u.latitude, u.longitude],
          [v.latitude, v.longitude],
        ],
        { color, weight, dashArray, opacity }
      );

      const statusBadge = isBlocked
        ? '<span style="color: #EF4444; font-weight: bold;">[BLOCKED]</span>'
        : '<span style="color: #A0CA92;">[AVAILABLE]</span>';

      line.bindTooltip(
        `<div style="font-family: var(--font-mono); font-size: 11px;">
          <strong>${edge.name || edge.id}</strong> ${statusBadge}<br/>
          Length: ${edge.distance_meters}m | Width: ${edge.width_meters}m<br/>
          Endpoints: ${edge.from_node} ↔ ${edge.to_node}
          ${edge.blockage_reason ? `<br/><span style="color: #EF4444;">Reason: ${edge.blockage_reason}</span>` : ''}
        </div>`,
        { sticky: true }
      );

      line.on('click', () => {
        setSelectedEdgeId(edge.id);
        setActiveTab('walkways');
      });

      line.addTo(group);
    });

    // 3. Render Calculated Route Overlay
    if (routingResult && routingResult.routes_found > 0) {
      // Find the currently selected or best route
      const activeRoute =
        routingResult.routes.find((r) => r.rank === selectedRouteRank) ||
        routingResult.routes[0];

      if (activeRoute) {
        const pathCoords: [number, number][] = [];
        activeRoute.path.forEach((nodeId) => {
          const n = nodeMap.get(nodeId);
          if (n) pathCoords.push([n.latitude, n.longitude]);
        });

        if (pathCoords.length >= 2) {
          const routeLine = L.polyline(pathCoords, {
            color: activeRoute.is_best ? 'var(--color-metric-green)' : 'var(--color-signal-orange)',
            weight: 6,
            opacity: 0.95,
          });

          routeLine.bindTooltip(
            `<div style="font-family: var(--font-mono); font-size: 11px;">
              <strong style="color: ${activeRoute.is_best ? 'var(--color-metric-green)' : 'var(--color-signal-orange)'};">
                Route ${activeRoute.rank} ${activeRoute.is_best ? '(Recommended)' : '(Alternative)'}
              </strong><br/>
              Distance: ${activeRoute.distance_meters} m | Cost: ${activeRoute.total_cost} units
            </div>`,
            { sticky: true }
          );

          routeLine.addTo(group);
        }
      }
    }

    // 4. Render Nodes
    venue.nodes.forEach((node) => {
      const isOrigin = node.id === originNodeId;
      const isDest = node.id === destNodeId;

      let radius = 6;
      let strokeColor = '#FAFAFA';
      let fillColor = '#1D1A18';
      let weight = 2;

      if (node.node_type === 'exit') {
        radius = 8;
        strokeColor = 'var(--color-metric-green)';
        fillColor = '#102A18';
      } else if (node.node_type === 'gate') {
        radius = 8;
        strokeColor = '#3B82F6';
        fillColor = '#0E1F3D';
      }

      if (isOrigin) {
        strokeColor = 'var(--color-metric-green)';
        fillColor = 'var(--color-metric-green)';
        radius = 9;
        weight = 3;
      } else if (isDest) {
        strokeColor = 'var(--color-signal-orange)';
        fillColor = 'var(--color-signal-orange)';
        radius = 9;
        weight = 3;
      }

      const marker = L.circleMarker([node.latitude, node.longitude], {
        radius,
        color: strokeColor,
        fillColor,
        fillOpacity: 1,
        weight,
      });

      marker.bindTooltip(
        `<div style="font-family: var(--font-mono); font-size: 11px;">
          <strong>${node.name}</strong> (${node.node_type.toUpperCase()})<br/>
          ID: ${node.id} | Zone: ${node.zone_id || 'unassigned'}<br/>
          Capacity: ${node.capacity || 'N/A'} persons/min
          <div style="margin-top: 4px; color: #888;">Click to select as Origin or Destination</div>
        </div>`,
        { direction: 'top', offset: [0, -6] }
      );

      marker.on('click', () => {
        if (!originNodeId || (originNodeId && destNodeId)) {
          setOriginNodeId(node.id);
          setDestNodeId('');
        } else if (originNodeId && !destNodeId && originNodeId !== node.id) {
          setDestNodeId(node.id);
        }
        setActiveTab('route');
      });

      marker.addTo(group);
    });
  };

  // Calculate Routes
  const handleCalculateRoutes = async () => {
    if (!originNodeId || !destNodeId) {
      setError('Please select both Origin and Destination nodes.');
      return;
    }
    if (originNodeId === destNodeId) {
      setError('Origin and Destination cannot be the same node.');
      return;
    }

    try {
      setCalculatingRoute(true);
      setError(null);
      const res = await ApiClient.compareRoutes(originNodeId, destNodeId, maxRoutes);
      setRoutingResult(res);
      setSelectedRouteRank(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Route calculation failed');
    } finally {
      setCalculatingRoute(false);
    }
  };

  // Block Walkway Action
  const handleBlockWalkway = async () => {
    if (!selectedEdgeId) return;
    try {
      setActionInProgress(true);
      setActionError(null);
      await ApiClient.blockWalkway(selectedEdgeId, blockReason);
      setBlockModalOpen(false);
      // Reload venue and recompute route if active
      await loadVenueData();
      if (originNodeId && destNodeId) {
        const res = await ApiClient.compareRoutes(originNodeId, destNodeId, maxRoutes);
        setRoutingResult(res);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to block walkway');
    } finally {
      setActionInProgress(false);
    }
  };

  // Reopen Walkway Action
  const handleReopenWalkway = async (edgeId: string) => {
    try {
      setActionInProgress(true);
      setActionError(null);
      await ApiClient.reopenWalkway(edgeId);
      await loadVenueData();
      if (originNodeId && destNodeId) {
        const res = await ApiClient.compareRoutes(originNodeId, destNodeId, maxRoutes);
        setRoutingResult(res);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to reopen walkway');
    } finally {
      setActionInProgress(false);
    }
  };

  const selectedEdge = venue?.edges.find((e) => e.id === selectedEdgeId);
  const blockedEdges = venue?.edges.filter((e) => e.is_blocked) || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', height: 'calc(100vh - 120px)' }}>
      {/* Telemetry Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: 'var(--space-3) var(--space-5)',
          backgroundColor: 'var(--color-carbon-lift)',
          border: 'var(--border-hairline)',
          borderRadius: 'var(--radius-xs)',
        }}
      >
        <div>
          <div className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
            MODULE B // GIS VENUE TOPOLOGY & ROUTING FOUNDATION
          </div>
          <h1 style={{ fontSize: '18px', fontWeight: 500, letterSpacing: '-0.02em', marginTop: '2px' }}>
            {venue?.venue_name || (loading ? 'Loading Venue GIS...' : 'Venue Offline')}
            {loading && <span style={{ fontSize: '12px', color: 'var(--color-signal-orange)', marginLeft: '8px' }}>[SYNCING...]</span>}
          </h1>
        </div>

        {venue && (
          <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
            <div style={{ textAlign: 'right' }}>
              <div className="mono-caption" style={{ color: 'var(--color-bone-muted)' }}>TOPOLOGY EXTENT</div>
              <div className="mono-code" style={{ fontSize: '12px' }}>
                {venue.center.latitude.toFixed(4)}°N, {venue.center.longitude.toFixed(4)}°E
              </div>
            </div>

            <div style={{ height: '24px', width: '1px', backgroundColor: 'var(--color-ash)' }} />

            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              <span className="badge badge-neutral" title="Configured Venue Zones">
                <Layers size={11} style={{ marginRight: '4px' }} /> {venue.zones.length} ZONES
              </span>
              <span className="badge badge-neutral" title="Topological Routing Nodes">
                <MapPin size={11} style={{ marginRight: '4px' }} /> {venue.nodes.length} NODES
              </span>
              <span className="badge badge-neutral" title="Total Walkways">
                <Navigation size={11} style={{ marginRight: '4px' }} /> {venue.edges.length} EDGES
              </span>
              {blockedEdges.length > 0 ? (
                <span className="badge badge-critical" title="Currently Blocked Walkways">
                  <Ban size={11} style={{ marginRight: '4px' }} /> {blockedEdges.length} BLOCKED
                </span>
              ) : (
                <span className="badge badge-success" title="All Walkways Available">
                  <CheckCircle size={11} style={{ marginRight: '4px' }} /> 0 BLOCKED
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div
          style={{
            padding: 'var(--space-2) var(--space-4)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--color-hazard-red)',
            color: 'var(--color-hazard-red)',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            borderRadius: 'var(--radius-xs)',
          }}
        >
          [ERROR] {error}
        </div>
      )}

      {/* Main Split Layout: Map on Left (65%), Control Console on Right (35%) */}
      <div style={{ display: 'flex', gap: 'var(--space-4)', flex: 1, minHeight: 0 }}>
        {/* Leaflet Map Canvas */}
        <div
          style={{
            flex: '1 1 65%',
            position: 'relative',
            backgroundColor: 'var(--color-obsidian)',
            border: 'var(--border-hairline)',
            borderRadius: 'var(--radius-xs)',
            overflow: 'hidden',
          }}
        >
          <div
            id="nexora-gis-map"
            ref={mapContainerRef}
            style={{ width: '100%', height: '100%', backgroundColor: '#101010' }}
          />

          {/* Map Legend Overlay */}
          <div
            style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              zIndex: 1000,
              backgroundColor: 'rgba(29, 26, 24, 0.9)',
              backdropFilter: 'blur(4px)',
              border: 'var(--border-hairline)',
              borderRadius: 'var(--radius-xs)',
              padding: 'var(--space-2) var(--space-3)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              color: 'var(--color-bone-muted)',
            }}
          >
            <div style={{ color: 'var(--color-bone)', fontWeight: 600, marginBottom: '2px' }}>MAP LEGEND</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '3px', backgroundColor: '#555555' }} /> Open Walkway
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '3px', borderTop: '2px dashed #EF4444' }} /> Blocked Walkway
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '4px', backgroundColor: 'var(--color-metric-green)' }} /> Best Route
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#3B82F6' }} /> Gate / Ingress
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-metric-green)' }} /> Perimeter Exit
            </div>
          </div>
        </div>

        {/* Right Operator Console */}
        <div
          style={{
            flex: '0 0 380px',
            backgroundColor: 'var(--color-carbon)',
            border: 'var(--border-hairline)',
            borderRadius: 'var(--radius-xs)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Console Tab Selector */}
          <div
            style={{
              display: 'flex',
              borderBottom: 'var(--border-hairline)',
              backgroundColor: 'var(--color-carbon-lift)',
            }}
          >
            <button
              onClick={() => setActiveTab('route')}
              style={{
                flex: 1,
                padding: 'var(--space-2)',
                backgroundColor: activeTab === 'route' ? 'var(--color-carbon)' : 'transparent',
                border: 'none',
                borderBottom: activeTab === 'route' ? '2px solid var(--color-signal-orange)' : 'none',
                color: activeTab === 'route' ? 'var(--color-bone)' : 'var(--color-bone-muted)',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              ROUTE PLANNER
            </button>
            <button
              onClick={() => setActiveTab('walkways')}
              style={{
                flex: 1,
                padding: 'var(--space-2)',
                backgroundColor: activeTab === 'walkways' ? 'var(--color-carbon)' : 'transparent',
                border: 'none',
                borderBottom: activeTab === 'walkways' ? '2px solid var(--color-signal-orange)' : 'none',
                color: activeTab === 'walkways' ? 'var(--color-bone)' : 'var(--color-bone-muted)',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              WALKWAYS ({venue?.edges.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('zones')}
              style={{
                flex: 1,
                padding: 'var(--space-2)',
                backgroundColor: activeTab === 'zones' ? 'var(--color-carbon)' : 'transparent',
                border: 'none',
                borderBottom: activeTab === 'zones' ? '2px solid var(--color-signal-orange)' : 'none',
                color: activeTab === 'zones' ? 'var(--color-bone)' : 'var(--color-bone-muted)',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              ZONES ({venue?.zones.length || 0})
            </button>
          </div>

          {/* Console Tab Content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {/* TAB 1: ROUTE PLANNER */}
            {activeTab === 'route' && (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  <div>
                    <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                      ORIGIN NODE (INGRESS / START)
                    </label>
                    <select
                      value={originNodeId}
                      onChange={(e) => setOriginNodeId(e.target.value)}
                      className="form-control"
                      style={{
                        width: '100%',
                        backgroundColor: 'var(--color-obsidian)',
                        color: 'var(--color-bone)',
                        border: 'var(--border-hairline)',
                        padding: '6px 8px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '12px',
                      }}
                    >
                      {venue?.nodes.map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.name} [{n.node_type.toUpperCase()}]
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                      DESTINATION NODE (EGRESS / EXIT)
                    </label>
                    <select
                      value={destNodeId}
                      onChange={(e) => setDestNodeId(e.target.value)}
                      className="form-control"
                      style={{
                        width: '100%',
                        backgroundColor: 'var(--color-obsidian)',
                        color: 'var(--color-bone)',
                        border: 'var(--border-hairline)',
                        padding: '6px 8px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '12px',
                      }}
                    >
                      {venue?.nodes.map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.name} [{n.node_type.toUpperCase()}]
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                      MAX ROUTE ALTERNATIVES
                    </label>
                    <select
                      value={maxRoutes}
                      onChange={(e) => setMaxRoutes(Number(e.target.value))}
                      className="form-control"
                      style={{
                        width: '100%',
                        backgroundColor: 'var(--color-obsidian)',
                        color: 'var(--color-bone)',
                        border: 'var(--border-hairline)',
                        padding: '6px 8px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '12px',
                      }}
                    >
                      <option value={1}>1 Path (Shortest Direct Only)</option>
                      <option value={2}>2 Alternatives</option>
                      <option value={3}>3 Alternatives (Standard Recommended)</option>
                      <option value={5}>5 Alternatives (Exhaustive)</option>
                    </select>
                  </div>

                  {/* Quick Scenario Buttons */}
                  <div>
                    <div className="mono-caption" style={{ marginBottom: '4px' }}>QUICK SCENARIOS</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                      <button
                        onClick={() => { setOriginNodeId('gate_main'); setDestNodeId('exit_north'); }}
                        className="btn btn-secondary"
                        style={{ fontSize: '10px', padding: '4px 6px', textAlign: 'left' }}
                      >
                        Gate → Exit North
                      </button>
                      <button
                        onClick={() => { setOriginNodeId('gate_main'); setDestNodeId('exit_east'); }}
                        className="btn btn-secondary"
                        style={{ fontSize: '10px', padding: '4px 6px', textAlign: 'left' }}
                      >
                        Gate → Exit East
                      </button>
                      <button
                        onClick={() => { setOriginNodeId('gate_main'); setDestNodeId('exit_south'); }}
                        className="btn btn-secondary"
                        style={{ fontSize: '10px', padding: '4px 6px', textAlign: 'left' }}
                      >
                        Gate → Exit South
                      </button>
                      <button
                        onClick={() => { setOriginNodeId('gate_main'); setDestNodeId('exit_west'); }}
                        className="btn btn-secondary"
                        style={{ fontSize: '10px', padding: '4px 6px', textAlign: 'left' }}
                      >
                        Gate → Exit West
                      </button>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                    <button
                      onClick={handleCalculateRoutes}
                      disabled={calculatingRoute || !originNodeId || !destNodeId}
                      className="btn btn-primary"
                      style={{ flex: 1, padding: '8px 12px' }}
                    >
                      {calculatingRoute ? 'EVALUATING GRAPH...' : 'CALCULATE ROUTE'}
                    </button>
                    {routingResult && (
                      <button
                        onClick={() => { setRoutingResult(null); }}
                        className="btn btn-secondary"
                        title="Clear Route"
                      >
                        <RotateCcw size={14} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Route Result Display */}
                {routingResult && (
                  <div
                    style={{
                      border: 'var(--border-hairline)',
                      borderRadius: 'var(--radius-xs)',
                      backgroundColor: 'var(--color-carbon-lift)',
                      padding: 'var(--space-3)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-3)',
                    }}
                  >
                    {routingResult.routes_found === 0 ? (
                      <div
                        style={{
                          padding: 'var(--space-3)',
                          backgroundColor: 'rgba(239, 68, 68, 0.1)',
                          border: '1px solid var(--color-hazard-red)',
                          borderRadius: 'var(--radius-xs)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-hazard-red)', fontWeight: 600, fontSize: '12px' }}>
                          <AlertTriangle size={14} /> NO VALID ROUTE FOUND
                        </div>
                        <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--color-bone-muted)' }}>
                          {routingResult.message}
                        </p>
                        {routingResult.blocked_edges.length > 0 && (
                          <div style={{ marginTop: '8px', fontSize: '10px', fontFamily: 'var(--font-mono)' }}>
                            <span style={{ color: '#EF4444' }}>Contributing Blockages:</span>{' '}
                            {routingResult.blocked_edges.join(', ')}
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>
                            {routingResult.routes_found} ALTERNATIVE(S) COMPUTED
                          </span>
                          <span className="badge badge-success">TOPOLOGY VALID</span>
                        </div>

                        {/* Route Rank Tabs */}
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {routingResult.routes.map((r) => (
                            <button
                              key={r.rank}
                              onClick={() => setSelectedRouteRank(r.rank)}
                              style={{
                                flex: 1,
                                padding: '4px 6px',
                                fontSize: '11px',
                                fontFamily: 'var(--font-mono)',
                                backgroundColor:
                                  selectedRouteRank === r.rank ? 'var(--color-signal-orange)' : 'var(--color-obsidian)',
                                color: selectedRouteRank === r.rank ? '#FFFFFF' : 'var(--color-bone-muted)',
                                border: 'var(--border-hairline)',
                                borderRadius: 'var(--radius-xs)',
                                cursor: 'pointer',
                              }}
                            >
                              Route {r.rank} {r.is_best ? '★' : ''}
                            </button>
                          ))}
                        </div>

                        {/* Selected Route Telemetry */}
                        {(() => {
                          const r =
                            routingResult.routes.find((alt) => alt.rank === selectedRouteRank) ||
                            routingResult.routes[0];
                          return (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)' }}>
                                <div style={{ backgroundColor: 'var(--color-obsidian)', padding: '6px', borderRadius: 'var(--radius-xs)' }}>
                                  <div className="mono-caption">TOTAL DISTANCE</div>
                                  <div className="mono-code" style={{ fontSize: '14px', color: 'var(--color-bone)' }}>
                                    {r.distance_meters} <span style={{ fontSize: '10px' }}>meters</span>
                                  </div>
                                </div>
                                <div style={{ backgroundColor: 'var(--color-obsidian)', padding: '6px', borderRadius: 'var(--radius-xs)' }}>
                                  <div className="mono-caption">WEIGHTED COST</div>
                                  <div className="mono-code" style={{ fontSize: '14px', color: 'var(--color-signal-orange)' }}>
                                    {r.total_cost} <span style={{ fontSize: '10px' }}>units</span>
                                  </div>
                                </div>
                              </div>

                              <div>
                                <div className="mono-caption" style={{ marginBottom: '4px' }}>HOP SEQUENCE ({r.path.length} NODES)</div>
                                <div
                                  className="mono-code"
                                  style={{
                                    fontSize: '11px',
                                    color: 'var(--color-bone)',
                                    backgroundColor: 'var(--color-obsidian)',
                                    padding: '6px 8px',
                                    borderRadius: 'var(--radius-xs)',
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: '4px',
                                    alignItems: 'center',
                                  }}
                                >
                                  {r.path.map((nodeId, idx) => (
                                    <React.Fragment key={idx}>
                                      <span style={{ color: idx === 0 ? 'var(--color-metric-green)' : (idx === r.path.length - 1 ? 'var(--color-signal-orange)' : 'var(--color-bone)') }}>
                                        {nodeId}
                                      </span>
                                      {idx < r.path.length - 1 && <ArrowRight size={10} style={{ color: '#666' }} />}
                                    </React.Fragment>
                                  ))}
                                </div>
                              </div>

                              {/* Segment details */}
                              <div>
                                <div className="mono-caption" style={{ marginBottom: '4px' }}>EDGE BREAKDOWN</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', maxHeight: '120px', overflowY: 'auto' }}>
                                  {r.segments.map((seg, sIdx) => (
                                    <div
                                      key={sIdx}
                                      style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        fontSize: '10px',
                                        fontFamily: 'var(--font-mono)',
                                        padding: '3px 6px',
                                        backgroundColor: 'var(--color-obsidian)',
                                        borderRadius: '2px',
                                      }}
                                    >
                                      <span>{seg.from} → {seg.to}</span>
                                      <span style={{ color: 'var(--color-bone-muted)' }}>{seg.distance}m (cost {seg.cost})</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          );
                        })()}

                        {/* Safety Disclaimer Banner */}
                        <div
                          style={{
                            padding: '6px 8px',
                            backgroundColor: 'rgba(238, 96, 24, 0.08)',
                            borderLeft: '2px solid var(--color-signal-orange)',
                            fontSize: '10px',
                            color: 'var(--color-bone-muted)',
                            lineHeight: 1.4,
                          }}
                        >
                          <Info size={11} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle', color: 'var(--color-signal-orange)' }} />
                          {routingResult.advisory_notice}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </>
            )}

            {/* TAB 2: WALKWAYS INSPECTOR & BLOCK CONTROLS */}
            {activeTab === 'walkways' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {selectedEdge ? (
                  <div
                    style={{
                      border: 'var(--border-hairline)',
                      backgroundColor: 'var(--color-carbon-lift)',
                      padding: 'var(--space-3)',
                      borderRadius: 'var(--radius-xs)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-2)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="mono-caption" style={{ color: 'var(--color-signal-orange)' }}>SELECTED WALKWAY</span>
                      {selectedEdge.is_blocked ? (
                        <span className="badge badge-critical">BLOCKED</span>
                      ) : (
                        <span className="badge badge-success">AVAILABLE</span>
                      )}
                    </div>

                    <h3 style={{ fontSize: '14px', fontWeight: 600 }}>{selectedEdge.name || selectedEdge.id}</h3>
                    <div className="mono-code" style={{ fontSize: '11px', color: 'var(--color-bone-muted)' }}>
                      ID: {selectedEdge.id} | {selectedEdge.from_node} ↔ {selectedEdge.to_node}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', margin: '4px 0' }}>
                      <div style={{ backgroundColor: 'var(--color-obsidian)', padding: '6px', borderRadius: 'var(--radius-xs)' }}>
                        <div className="mono-caption">LENGTH</div>
                        <div className="mono-code">{selectedEdge.distance_meters} m</div>
                      </div>
                      <div style={{ backgroundColor: 'var(--color-obsidian)', padding: '6px', borderRadius: 'var(--radius-xs)' }}>
                        <div className="mono-caption">WIDTH</div>
                        <div className="mono-code">{selectedEdge.width_meters} m</div>
                      </div>
                    </div>

                    {selectedEdge.is_blocked && (
                      <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: '6px 8px', borderRadius: 'var(--radius-xs)', borderLeft: '2px solid var(--color-hazard-red)' }}>
                        <div className="mono-caption" style={{ color: 'var(--color-hazard-red)' }}>BLOCKAGE REASON</div>
                        <div style={{ fontSize: '11px', color: 'var(--color-bone)' }}>{selectedEdge.blockage_reason || 'Manual operator blockage'}</div>
                        <div className="mono-caption" style={{ marginTop: '4px' }}>
                          Blocked by: {selectedEdge.blocked_by || 'operator'} at {selectedEdge.blocked_at?.slice(11, 19)}
                        </div>
                      </div>
                    )}

                    <div style={{ marginTop: 'var(--space-2)' }}>
                      {selectedEdge.is_blocked ? (
                        <button
                          onClick={() => handleReopenWalkway(selectedEdge.id)}
                          disabled={actionInProgress}
                          className="btn btn-success"
                          style={{ width: '100%', padding: '6px' }}
                        >
                          {actionInProgress ? 'REOPENING...' : 'REOPEN WALKWAY (RESTORE ELIGIBILITY)'}
                        </button>
                      ) : (
                        <button
                          onClick={() => setBlockModalOpen(true)}
                          disabled={actionInProgress}
                          className="btn btn-danger"
                          style={{ width: '100%', padding: '6px' }}
                        >
                          BLOCK WALKWAY (EXCLUDE FROM ROUTING)
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: 'var(--space-3)', backgroundColor: 'var(--color-carbon-lift)', borderRadius: 'var(--radius-xs)', fontSize: '12px', color: 'var(--color-bone-muted)' }}>
                    Select any walkway on the map to inspect properties or modify blockage availability.
                  </div>
                )}

                {/* Currently Blocked Walkways Quick List */}
                <div>
                  <div className="mono-caption" style={{ marginBottom: '6px', color: blockedEdges.length > 0 ? 'var(--color-hazard-red)' : 'var(--color-bone-muted)' }}>
                    CURRENTLY BLOCKED WALKWAYS ({blockedEdges.length})
                  </div>
                  {blockedEdges.length === 0 ? (
                    <div style={{ fontSize: '11px', color: 'var(--color-bone-muted)', fontStyle: 'italic' }}>
                      No blocked walkways. All network paths active.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {blockedEdges.map((e) => (
                        <div
                          key={e.id}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            backgroundColor: 'var(--color-obsidian)',
                            border: '1px solid rgba(239, 68, 68, 0.4)',
                            padding: '6px 8px',
                            borderRadius: 'var(--radius-xs)',
                          }}
                        >
                          <div>
                            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-bone)' }}>{e.name || e.id}</div>
                            <div className="mono-caption" style={{ color: 'var(--color-hazard-red)' }}>{e.blockage_reason || 'Blocked'}</div>
                          </div>
                          <button
                            onClick={() => handleReopenWalkway(e.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '10px', padding: '2px 6px' }}
                          >
                            Reopen
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 3: VENUE ZONES & EVENT LINKAGE */}
            {activeTab === 'zones' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div className="mono-caption" style={{ color: 'var(--color-bone-muted)' }}>
                  MONITORED VENUE ZONES & CROWD EVENT CORRELATION
                </div>

                {venue?.zones.map((zone) => {
                  const matchingEvents = events.filter((ev) => ev.zone_id === zone.id);
                  return (
                    <div
                      key={zone.id}
                      style={{
                        backgroundColor: 'var(--color-carbon-lift)',
                        border: 'var(--border-hairline)',
                        borderLeft: `3px solid ${zone.color}`,
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-xs)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '13px', fontWeight: 600 }}>{zone.name}</span>
                        {matchingEvents.length > 0 ? (
                          <span className="badge badge-critical">{matchingEvents.length} ALERT(S)</span>
                        ) : (
                          <span className="badge badge-neutral">CLEAR</span>
                        )}
                      </div>

                      <div className="mono-caption">{zone.description || zone.id}</div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px', fontSize: '11px', color: 'var(--color-bone-muted)' }}>
                        <span>Cameras: {zone.camera_ids?.join(', ') || 'None'}</span>
                        <button
                          onClick={() => {
                            if (mapInstanceRef.current && zone.polygon && zone.polygon.length > 0) {
                              const lat = zone.polygon[0][0];
                              const lng = zone.polygon[0][1];
                              mapInstanceRef.current.setView([lat, lng], 18);
                            }
                          }}
                          className="btn btn-secondary"
                          style={{ fontSize: '9px', padding: '2px 4px' }}
                        >
                          <Maximize2 size={10} style={{ marginRight: '2px' }} /> Focus
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Modal for Walkway Blockage */}
      {blockModalOpen && selectedEdge && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            backdropFilter: 'blur(3px)',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--color-carbon-lift)',
              border: '1px solid var(--color-hazard-red)',
              borderRadius: 'var(--radius-sm)',
              width: '420px',
              padding: 'var(--space-5)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-hazard-red)' }}>
              <ShieldAlert size={18} />
              <h2 style={{ fontSize: '16px', fontWeight: 600 }}>CONFIRM WALKWAY BLOCKAGE</h2>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--color-bone)', lineHeight: 1.5 }}>
              You are marking <strong>{selectedEdge.name || selectedEdge.id}</strong> ({selectedEdge.from_node} ↔ {selectedEdge.to_node}) as <strong>BLOCKED</strong>.
              This will immediately exclude this edge from all subsequent route evaluations and may alter safe crowd dispersal paths.
            </p>

            <div>
              <label className="mono-caption" style={{ display: 'block', marginBottom: '4px' }}>
                REASON FOR BLOCKAGE (RECORDED IN AUDIT LOG)
              </label>
              <input
                type="text"
                value={blockReason}
                onChange={(e) => setBlockReason(e.target.value)}
                className="form-control"
                style={{
                  width: '100%',
                  backgroundColor: 'var(--color-obsidian)',
                  color: 'var(--color-bone)',
                  border: 'var(--border-hairline)',
                  padding: '6px 8px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                }}
              />
            </div>

            {actionError && (
              <div style={{ color: 'var(--color-hazard-red)', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                {actionError}
              </div>
            )}

            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
              <button
                onClick={() => setBlockModalOpen(false)}
                className="btn btn-secondary"
                disabled={actionInProgress}
              >
                CANCEL
              </button>
              <button
                onClick={handleBlockWalkway}
                className="btn btn-danger"
                disabled={actionInProgress || !blockReason.trim()}
              >
                {actionInProgress ? 'COMMITTING...' : 'CONFIRM & EXCLUDE'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
