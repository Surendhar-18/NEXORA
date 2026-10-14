import type {
  HealthResponse,
  AuditRecord,
  VideoDetail,
  JobDetail,
  JobStatus,
  VideoUploadResult,
  JobDetectionsResponse,
  CrowdRule,
  CrowdEvent,
  EventReviewRequest,
  EventReviewResponse,
  VenueDetail,
  VenueSummary,
  RouteComparisonResponse,
  WalkwayBlockResponse,
  ResourceListResponse,
  IncidentListResponse,
  IncidentDetail,
  IncidentNoteItem,
  AnalyticsOverviewResponse,
  AnalyticsTrendsResponse,
  PrimaryMetrics,
  ReportTypesResponse,
  ReportGenerateRequest,
  ReportPreviewResponse,
  AuditExportRequest,
  UserProfile,
  TokenResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

export class ApiClient {
  public static getAuthToken(): string | null {
    try {
      return localStorage.getItem('nexora_token');
    } catch {
      return null;
    }
  }

  public static setAuthToken(token: string | null): void {
    try {
      if (token) {
        localStorage.setItem('nexora_token', token);
      } else {
        localStorage.removeItem('nexora_token');
      }
    } catch {
      // storage unavailable
    }
  }

  private static async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = this.getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers as Record<string, string> || {}),
    };
    try {
      const response = await fetch(url, {
        headers,
        ...options,
      });

      if (!response.ok) {
        let errorDetail = response.statusText;
        try {
          const errJson = await response.json();
          errorDetail = errJson.detail || JSON.stringify(errJson);
        } catch {
          const rawText = await response.text();
          if (rawText) errorDetail = rawText;
        }
        throw new Error(`API error ${response.status}: ${errorDetail}`);
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof Error) {
        throw err;
      }
      throw new Error(String(err));
    }
  }

  public static async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  public static async getAuditLogs(): Promise<AuditRecord[]> {
    return this.request<AuditRecord[]>('/audit');
  }

  public static async uploadVideo(
    formData: FormData,
    onProgress?: (progressPercent: number) => void
  ): Promise<VideoUploadResult> {
    const url = `${API_BASE_URL}/videos/upload`;

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', url);

      if (onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText) as VideoUploadResult;
            resolve(data);
          } catch (e) {
            reject(new Error(`Failed to parse response: ${e}`));
          }
        } else {
          let errorMsg = `Upload failed with status ${xhr.status}`;
          try {
            const errJson = JSON.parse(xhr.responseText);
            if (errJson.detail) errorMsg = errJson.detail;
          } catch {
            if (xhr.responseText) errorMsg = xhr.responseText;
          }
          reject(new Error(errorMsg));
        }
      };

      xhr.onerror = () => {
        reject(new Error('Network error during video upload. Verify backend connectivity.'));
      };

      xhr.send(formData);
    });
  }

  public static async getVideos(): Promise<{ videos: VideoDetail[]; total: number }> {
    return this.request<{ videos: VideoDetail[]; total: number }>('/videos');
  }

  public static async getJobs(): Promise<{ jobs: JobDetail[]; total: number }> {
    return this.request<{ jobs: JobDetail[]; total: number }>('/jobs');
  }

  public static async getJobDetail(jobId: string): Promise<JobDetail> {
    return this.request<JobDetail>(`/jobs/${jobId}`);
  }

  public static async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/jobs/${jobId}/status`);
  }

  public static async createJob(params: {
    video_id: string;
    zone_id?: string;
    sampling_interval_sec?: number;
    confidence_threshold?: number;
  }): Promise<JobDetail> {
    return this.request<JobDetail>('/jobs', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  public static async getJobDetections(jobId: string): Promise<JobDetectionsResponse> {
    return this.request<JobDetectionsResponse>(`/jobs/${jobId}/detections`);
  }

  public static getEvidenceImageUrl(relativeUrl: string): string {
    if (relativeUrl.startsWith('http://') || relativeUrl.startsWith('https://')) {
      return relativeUrl;
    }
    const cleanPath = relativeUrl.startsWith('/') ? relativeUrl : `/${relativeUrl}`;
    // Base API is http://127.0.0.1:8000/api/v1 -> host is http://127.0.0.1:8000
    const host = API_BASE_URL.replace(/\/api\/v1\/?$/, '');
    return `${host}${cleanPath}`;
  }

  // --- Crowd Rules API ---
  public static async getRules(activeOnly?: boolean): Promise<{ rules: CrowdRule[]; total: number }> {
    const q = activeOnly ? '?active_only=true' : '';
    return this.request<{ rules: CrowdRule[]; total: number }>(`/rules${q}`);
  }

  public static async updateRule(ruleId: string, updates: Partial<CrowdRule>): Promise<CrowdRule> {
    return this.request<CrowdRule>(`/rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  public static async createRule(rule: Partial<CrowdRule>): Promise<CrowdRule> {
    return this.request<CrowdRule>('/rules', {
      method: 'POST',
      body: JSON.stringify(rule),
    });
  }

  public static async evaluateJobRules(jobId: string, dryRun: boolean = false): Promise<{ job_id: string; events_generated_count: number; events: CrowdEvent[] }> {
    return this.request<{ job_id: string; events_generated_count: number; events: CrowdEvent[] }>(`/rules/evaluate/${jobId}?dry_run=${dryRun}`, {
      method: 'POST',
    });
  }

  // --- Crowd Events & Operator Review API ---
  public static async getEvents(params?: {
    status?: string;
    zone_id?: string;
    severity?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ events: CrowdEvent[]; total: number; limit: number; offset: number }> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.zone_id) searchParams.set('zone_id', params.zone_id);
    if (params?.severity) searchParams.set('severity', params.severity);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    const qs = searchParams.toString();
    return this.request<{ events: CrowdEvent[]; total: number; limit: number; offset: number }>(`/events${qs ? `?${qs}` : ''}`);
  }

  public static async getEventDetail(eventId: string): Promise<CrowdEvent> {
    return this.request<CrowdEvent>(`/events/${eventId}`);
  }

  public static async reviewEvent(eventId: string, request: EventReviewRequest): Promise<EventReviewResponse> {
    return this.request<EventReviewResponse>(`/events/${eventId}/review`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  }

  // --- GIS Venue & Routing API ---
  public static async getVenue(venueId?: string): Promise<VenueDetail> {
    const qs = venueId ? `?venue_id=${encodeURIComponent(venueId)}` : '';
    return this.request<VenueDetail>(`/venue${qs}`);
  }

  public static async getVenues(): Promise<VenueSummary[]> {
    return this.request<VenueSummary[]>('/venues');
  }

  public static async compareRoutes(
    fromNode: string,
    toNode: string,
    maxRoutes: number = 3,
    venueId?: string
  ): Promise<RouteComparisonResponse> {
    const params = new URLSearchParams({
      from_node: fromNode,
      to_node: toNode,
      max_routes: maxRoutes.toString(),
    });
    if (venueId) params.set('venue_id', venueId);
    return this.request<RouteComparisonResponse>(`/routes/compare?${params.toString()}`);
  }

  public static async blockWalkway(edgeId: string, reason?: string): Promise<WalkwayBlockResponse> {
    return this.request<WalkwayBlockResponse>(`/venue/edges/${edgeId}/block`, {
      method: 'PUT',
      body: JSON.stringify({ reason }),
    });
  }

  public static async reopenWalkway(edgeId: string): Promise<WalkwayBlockResponse> {
    return this.request<WalkwayBlockResponse>(`/venue/edges/${edgeId}/reopen`, {
      method: 'PUT',
    });
  }

  // --- Response Resources API ---
  public static async getResources(filters?: { status?: string; type?: string }): Promise<ResourceListResponse> {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.type) params.set('type', filters.type);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return this.request<ResourceListResponse>(`/resources${qs}`);
  }

  // --- Incident Management API ---
  public static async getIncidents(filters?: {
    status?: string;
    severity?: string;
    venue_id?: string;
    zone_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<IncidentListResponse> {
    const params = new URLSearchParams();
    if (filters?.status && filters.status !== 'ALL') params.set('status', filters.status);
    if (filters?.severity && filters.severity !== 'ALL') params.set('severity', filters.severity);
    if (filters?.venue_id) params.set('venue_id', filters.venue_id);
    if (filters?.zone_id) params.set('zone_id', filters.zone_id);
    if (filters?.limit) params.set('limit', filters.limit.toString());
    if (filters?.offset) params.set('offset', filters.offset.toString());
    const qs = params.toString() ? `?${params.toString()}` : '';
    return this.request<IncidentListResponse>(`/incidents${qs}`);
  }

  public static async getIncidentDetail(incidentId: string): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/${incidentId}`);
  }

  public static async createIncident(data: {
    title: string;
    description: string;
    priority?: string;
    zone_id?: string;
    venue_id?: string;
    event_id?: string;
  }): Promise<IncidentDetail> {
    return this.request<IncidentDetail>('/incidents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  public static async createIncidentFromEvent(eventId: string): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/from-event/${eventId}`, {
      method: 'POST',
    });
  }

  public static async updateIncidentStatus(
    incidentId: string,
    data: { status: string; notes?: string; operator?: string }
  ): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/${incidentId}/status`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  public static async assignResource(incidentId: string, resourceId: string): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/${incidentId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ resource_id: resourceId }),
    });
  }

  public static async releaseResource(incidentId: string): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/${incidentId}/release`, {
      method: 'POST',
    });
  }

  public static async addIncidentNote(incidentId: string, noteText: string): Promise<IncidentNoteItem> {
    return this.request<IncidentNoteItem>(`/incidents/${incidentId}/notes`, {
      method: 'POST',
      body: JSON.stringify({ note_text: noteText }),
    });
  }

  public static async updateIncidentLocation(
    incidentId: string,
    data: { venue_id?: string; zone_id: string }
  ): Promise<IncidentDetail> {
    return this.request<IncidentDetail>(`/incidents/${incidentId}/location`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // --- Dashboard & Operational Analytics API ---
  public static async getAnalyticsOverview(params?: {
    period?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<AnalyticsOverviewResponse> {
    const searchParams = new URLSearchParams();
    if (params?.period) searchParams.set('period', params.period);
    if (params?.start_date) searchParams.set('start_date', params.start_date);
    if (params?.end_date) searchParams.set('end_date', params.end_date);
    const qs = searchParams.toString();
    return this.request<AnalyticsOverviewResponse>(`/analytics/overview${qs ? `?${qs}` : ''}`);
  }

  public static async getAnalyticsTrends(params?: {
    period?: string;
    interval?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<AnalyticsTrendsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.period) searchParams.set('period', params.period);
    if (params?.interval) searchParams.set('interval', params.interval);
    if (params?.start_date) searchParams.set('start_date', params.start_date);
    if (params?.end_date) searchParams.set('end_date', params.end_date);
    const qs = searchParams.toString();
    return this.request<AnalyticsTrendsResponse>(`/analytics/trends${qs ? `?${qs}` : ''}`);
  }

  public static async getPrimaryMetrics(): Promise<PrimaryMetrics> {
    return this.request<PrimaryMetrics>('/analytics/metrics');
  }

  // --- Reports & Comprehensive Audit Export API ---
  private static async downloadBlob(endpoint: string, body: unknown): Promise<{ blob: Blob; filename: string }> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = this.getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || JSON.stringify(errJson);
      } catch {
        const rawText = await response.text();
        if (rawText) errorDetail = rawText;
      }
      throw new Error(`Export error ${response.status}: ${errorDetail}`);
    }

    const contentDisposition = response.headers.get('Content-Disposition') || '';
    let filename = 'nexora_export';
    const match = contentDisposition.match(/filename=["']?([^"';]+)["']?/);
    if (match && match[1]) {
      filename = match[1];
    }
    const blob = await response.blob();
    return { blob, filename };
  }

  public static async getReportTypes(): Promise<ReportTypesResponse> {
    return this.request<ReportTypesResponse>('/reports/types');
  }

  public static async generateReportPreview(data: ReportGenerateRequest): Promise<ReportPreviewResponse> {
    return this.request<ReportPreviewResponse>('/reports/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  public static async downloadReportPdf(data: ReportGenerateRequest): Promise<{ blob: Blob; filename: string }> {
    return this.downloadBlob('/reports/export/pdf', data);
  }

  public static async downloadReportCsv(data: ReportGenerateRequest): Promise<{ blob: Blob; filename: string }> {
    return this.downloadBlob('/reports/export/csv', data);
  }

  public static async exportAudit(data: AuditExportRequest): Promise<{ blob: Blob; filename: string }> {
    return this.downloadBlob('/reports/audit/export', data);
  }

  // --- Phase 10 Authentication & Identity API ---
  public static async login(credentials: { username: string; password: string }): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    if (res.access_token) {
      this.setAuthToken(res.access_token);
    }
    return res;
  }

  public static async getCurrentUser(): Promise<UserProfile> {
    return this.request<UserProfile>('/auth/me');
  }

  public static logout(): void {
    this.setAuthToken(null);
  }
}

