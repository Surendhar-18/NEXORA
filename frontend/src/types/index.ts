export type ViewMode = 
  | 'overview' 
  | 'video_analysis' 
  | 'event_review' 
  | 'gis_operations' 
  | 'incidents' 
  | 'reports_audit';

export interface StorageHealth {
  data_dir_writable: boolean;
  uploads_dir_exists: boolean;
  evidence_dir_exists: boolean;
}

export interface ModuleHealth {
  database: string;
  gis_routing: string;
  visionx_cv: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'offline';
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  database: string;
  storage: StorageHealth;
  modules: ModuleHealth;
}

export interface AuditRecord {
  id: string;
  timestamp: string;
  actor_id: string;
  actor_role: string;
  action_type: string;
  entity_type: string;
  entity_id: string;
  details?: Record<string, unknown>;
}

export interface VideoDetail {
  id: string;
  filename: string;
  original_filename: string;
  file_size_bytes: number;
  duration_seconds?: number | null;
  fps?: number | null;
  total_frames?: number | null;
  resolution?: string | null;
  zone_id?: string | null;
  uploaded_by: string;
  status: string;
  created_at: string;
}

export interface JobDetail {
  id: string;
  video_id: string;
  original_filename: string;
  file_size_bytes: number;
  file_type: string;
  zone_id?: string | null;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  current_frame: number;
  total_frames_to_process: number;
  sampling_interval_sec: number;
  confidence_threshold: number;
  model_name: string;
  total_persons_detected: number;
  max_person_count: number;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  current_frame: number;
  total_frames_to_process: number;
  error_message?: string | null;
}

export interface VideoUploadResult {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  file_type: string;
  zone_id: string;
  status: string;
  sampling_interval_sec: number;
  confidence_threshold: number;
  created_at: string;
  message: string;
}

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
  class_name: string;
}

export interface DetectionItem {
  id: string;
  video_id: string;
  job_id?: string | null;
  frame_index: number;
  timestamp_seconds: number;
  person_count: number;
  avg_confidence: number;
  max_confidence: number;
  min_confidence: number;
  evidence_image_path?: string | null;
  evidence_image_url?: string | null;
  bounding_boxes: BoundingBox[];
  created_at: string;
}

export interface JobDetectionsResponse {
  job_id: string;
  video_id: string;
  total_frames_processed: number;
  total_persons_detected: number;
  max_person_count: number;
  detections: DetectionItem[];
}

export interface CrowdRule {
  id: string;
  name: string;
  description?: string | null;
  rule_type: string;
  operator: string;
  threshold_count: number;
  sustained_seconds: number;
  min_consecutive_frames: number;
  zone_id?: string | null;
  severity: string;
  cooldown_seconds: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface SupportingFrameItem {
  frame_index: number;
  timestamp_seconds: number;
  person_count: number;
  evidence_image_path?: string | null;
  evidence_image_url?: string | null;
}

export interface CrowdEvent {
  id: string;
  video_id?: string | null;
  job_id?: string | null;
  detection_id?: string | null;
  rule_id?: string | null;
  zone_id: string;
  camera_id?: string | null;
  event_type: string;
  severity: string;
  person_count: number;
  rule_name: string;
  rule_threshold: number;
  sustained_frames?: number | null;
  sustained_duration_sec?: number | null;
  window_start_sec?: number | null;
  window_end_sec?: number | null;
  description?: string | null;
  evidence_image_path?: string | null;
  evidence_image_url?: string | null;
  supporting_frames: SupportingFrameItem[];
  status: 'pending_review' | 'acknowledged' | 'dismissed' | 'resolved';
  review_notes?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface EventReviewRequest {
  action: 'acknowledge' | 'dismiss' | 'resolve';
  notes?: string;
  operator_id?: string;
}

export interface EventReviewResponse {
  id: string;
  status: string;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  review_notes?: string | null;
  message: string;
}

export interface VenueZone {
  id: string;
  name: string;
  polygon: number[][];
  color: string;
  description?: string | null;
  camera_ids?: string[];
}

export interface VenueNode {
  id: string;
  name: string;
  node_type: 'junction' | 'exit' | 'gate' | 'poi' | string;
  latitude: number;
  longitude: number;
  zone_id?: string | null;
  capacity?: number | null;
  description?: string | null;
  is_active: boolean;
}

export interface VenueEdge {
  id: string;
  from_node: string;
  to_node: string;
  name?: string | null;
  distance_meters: number;
  width_meters: number;
  congestion_penalty: number;
  hazard_penalty: number;
  is_bidirectional: boolean;
  is_blocked: boolean;
  blocked_at?: string | null;
  blocked_by?: string | null;
  blockage_reason?: string | null;
  description?: string | null;
}

export interface VenueCamera {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  zone_id?: string | null;
  direction?: string | null;
}

export interface VenueDetail {
  id: string;
  venue_name: string;
  description?: string | null;
  center: { latitude: number; longitude: number };
  zoom_level: number;
  zones: VenueZone[];
  nodes: VenueNode[];
  edges: VenueEdge[];
  cameras: VenueCamera[];
}

export interface VenueSummary {
  id: string;
  name: string;
  description?: string | null;
  center_lat: number;
  center_lng: number;
  default_zoom: number;
}

export interface RouteSegment {
  from: string;
  to: string;
  edge_id: string;
  name?: string | null;
  distance: number;
  congestion: number;
  hazard: number;
  cost: number;
}

export interface RouteAlternative {
  rank: number;
  is_best: boolean;
  path: string[];
  edge_ids: string[];
  total_cost: number;
  distance_meters: number;
  congestion_penalty: number;
  hazard_penalty: number;
  segments: RouteSegment[];
}

export interface RouteComparisonResponse {
  from_node: string;
  to_node: string;
  routes_found: number;
  routes: RouteAlternative[];
  blocked_edges: string[];
  message?: string | null;
  advisory_notice?: string;
}

export interface WalkwayBlockResponse {
  id: string;
  name?: string | null;
  is_blocked: boolean;
  blocked_at?: string | null;
  blocked_by?: string | null;
  blockage_reason?: string | null;
  message: string;
}

// --- Response Resource Types ---
export interface ResourceItem {
  id: string;
  name: string;
  resource_type: string;
  call_sign: string;
  status: 'available' | 'assigned' | 'unavailable' | string;
  assigned_incident_id?: string | null;
  current_zone_id?: string | null;
  description?: string | null;
  contact_info?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResourceListResponse {
  resources: ResourceItem[];
  total: number;
  available: number;
  assigned: number;
  unavailable: number;
}

// --- Incident Management Types ---
export interface IncidentHistoryItem {
  id: string;
  action: string;
  old_value?: string | null;
  new_value?: string | null;
  details?: Record<string, any> | null;
  performed_by: string;
  created_at: string;
}

export interface IncidentNoteItem {
  id: string;
  note_text: string;
  author: string;
  created_at: string;
}

export interface IncidentSummary {
  id: string;
  incident_number: string;
  title: string;
  zone_id?: string | null;
  venue_id?: string | null;
  location_status: 'confirmed' | 'unconfirmed' | 'unknown' | string;
  severity: 'low' | 'medium' | 'high' | 'critical' | string;
  status: 'open' | 'acknowledged' | 'in_progress' | 'resolved' | 'closed' | string;
  event_id?: string | null;
  assigned_resource_id?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentDetail {
  id: string;
  incident_number: string;
  title: string;
  description: string;
  venue_id?: string | null;
  zone_id?: string | null;
  location_status: 'confirmed' | 'unconfirmed' | 'unknown' | string;
  severity: 'low' | 'medium' | 'high' | 'critical' | string;
  status: 'open' | 'acknowledged' | 'in_progress' | 'resolved' | 'closed' | string;
  event_id?: string | null;
  assigned_resource?: ResourceItem | null;
  created_by: string;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  resolved_at?: string | null;
  resolved_by?: string | null;
  resolution_notes?: string | null;
  closed_at?: string | null;
  closed_by?: string | null;
  created_at: string;
  updated_at: string;
  evidence_image_url?: string | null;
  history: IncidentHistoryItem[];
  notes: IncidentNoteItem[];
}

export interface IncidentListResponse {
  incidents: IncidentSummary[];
  total: number;
  limit: number;
  offset: number;
}

// =========================================================
// Phase 7: Analytics & Operational Metrics Interfaces
// =========================================================

export interface PrimaryMetrics {
  active_incidents: number;
  pending_events: number;
  processing_jobs: number;
  critical_high_incidents: number;
  available_resources: number;
  total_resources: number;
  blocked_walkways: number;
  total_walkways: number;
}

export interface IncidentOverviewItem {
  id: string;
  incident_number: string;
  title: string;
  severity: string;
  status: string;
  zone_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentAnalytics {
  total_in_period: number;
  active_count: number;
  status_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  avg_resolution_duration_minutes?: number | null;
  recent_incidents: IncidentOverviewItem[];
}

export interface EventOverviewItem {
  id: string;
  rule_name: string;
  severity: string;
  status: string;
  person_count: number;
  zone_id: string;
  created_at: string;
}

export interface EventAnalytics {
  total_in_period: number;
  pending_count: number;
  status_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  recent_events: EventOverviewItem[];
}

export interface JobOverviewItem {
  id: string;
  video_id: string;
  status: string;
  progress_percent: number;
  total_persons_detected: number;
  created_at: string;
  error_message?: string | null;
}

export interface JobAnalytics {
  total_in_period: number;
  status_distribution: Record<string, number>;
  total_frame_detections: number;
  recent_failed_jobs: JobOverviewItem[];
}

export interface AssignedResourceDetail {
  id: string;
  name: string;
  call_sign: string;
  resource_type: string;
  assigned_incident_id?: string | null;
  incident_number?: string | null;
}

export interface ResourceAnalytics {
  total: number;
  available: number;
  assigned: number;
  unavailable: number;
  by_type: Record<string, number>;
  assigned_units: AssignedResourceDetail[];
}

export interface BlockedWalkwaySummary {
  id: string;
  name?: string | null;
  from_node: string;
  to_node: string;
  blockage_reason?: string | null;
  blocked_at?: string | null;
}

export interface GisAnalytics {
  total_walkways: number;
  blocked_count: number;
  unblocked_count: number;
  blocked_details: BlockedWalkwaySummary[];
}

export interface AttentionItem {
  category: string;
  level: string;
  title: string;
  subtitle: string;
  entity_id: string;
  action_route: string;
  timestamp: string;
}

export interface ActivityItem {
  id: string;
  timestamp: string;
  actor_id: string;
  action_type: string;
  entity_type: string;
  entity_id: string;
  description: string;
}

export interface AnalyticsOverviewResponse {
  reporting_period: string;
  period_start: string;
  period_end: string;
  refreshed_at: string;
  metrics: PrimaryMetrics;
  incidents: IncidentAnalytics;
  events: EventAnalytics;
  jobs: JobAnalytics;
  resources: ResourceAnalytics;
  gis: GisAnalytics;
  attention_queue: AttentionItem[];
  recent_activity: ActivityItem[];
}

export interface TrendBucket {
  timestamp: string;
  label: string;
  incidents_created: number;
  events_created: number;
  jobs_completed: number;
}

export interface AnalyticsTrendsResponse {
  reporting_period: string;
  period_start: string;
  period_end: string;
  interval: string;
  buckets: TrendBucket[];
}

// ---------------------------------------------------------------------------
// Phase 8: Reports & Audit Types
// ---------------------------------------------------------------------------

export interface ReportFilterOptionItem {
  value: string;
  label: string;
}

export interface ReportFilterOption {
  name: string;
  field: string;
  type: string;
  default?: string;
  options?: ReportFilterOptionItem[];
}

export interface ReportTypeInfo {
  report_type: string;
  title: string;
  description: string;
  supported_formats: string[];
  available_filters: ReportFilterOption[];
}

export interface ReportTypesResponse {
  report_types: ReportTypeInfo[];
}

export interface ReportGenerateRequest {
  report_type: string;
  period: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  severity?: string;
  zone_id?: string;
  action_type?: string;
  entity_type?: string;
  filters?: Record<string, unknown>;
  limit?: number;
}

export interface ReportMetadata {
  report_id: string;
  report_type: string;
  report_title: string;
  generation_time: string;
  reporting_period: string;
  period_start: string;
  period_end: string;
  timezone: string;
  applied_filters: Record<string, unknown>;
  record_count: number;
  system_mode: string;
  disclaimer: string;
}

export interface ReportPreviewResponse {
  metadata: ReportMetadata;
  summary_metrics: Record<string, unknown>;
  columns: string[];
  records: Array<Record<string, unknown>>;
}

export interface AuditExportRequest {
  period: string;
  start_date?: string;
  end_date?: string;
  action_type?: string;
  entity_type?: string;
  format: 'csv' | 'pdf';
  limit?: number;
}

export type UserRole = 'admin' | 'operator' | 'observer';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: UserProfile;
}



