// API client for FloatChat Ultimate backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const ADMIN_API_KEY = process.env.NEXT_PUBLIC_ADMIN_API_KEY || '';

export interface ArgoFloat {
    id: number;
    wmo_number: string;
    platform_type?: string;
    last_latitude?: number;
    last_longitude?: number;
    status?: string;
    ocean_basin?: string;
}

export interface ArgoVisProfile {
    _id: string;
    basin?: number;
    data_center?: string;
    date?: string;
    date_added?: string;
    geolocation_lat?: number;
    geolocation_lon?: number;
    platform_number?: string;
    cycle_number?: number;
    source?: any[];
    data?: any[][];
    data_keys?: string[];
}

export interface ArgoVisPlatform {
    platform_number: string;
    date_updated_argovis?: string;
    most_recent_date?: string;
    most_recent_date_added?: string;
    cycle_number?: number;
}

export interface ArgoVisSearchResponse<T> {
    total: number;
    limit: number;
    data: T[];
}

export interface CMEMSCapabilities {
    raw_xml_length: number;
}

export interface CMEMSSearchResponse {
    products?: any[];
    totalElements?: number;
    totalPages?: number;
}

export interface NOAAStation {
    id: string;
    name: string;
    state: string;
    lat: number;
    lng: number;
}

export interface NOAACoopsResponse {
    metadata?: any;
    data?: any[];
    error?: any;
}

export interface NOAANdbcResponse {
    station: string;
    parsed?: any;
    raw_preview?: string;
    raw?: string;
}

export interface OBISOccurrenceResponse {
    total: number;
    results: any[];
}

export interface ArgoProfile {
    id: number;
    wmo_number: string;
    cycle_number: number;
    profile_date: string;
    latitude: number;
    longitude: number;
}

export interface Stats {
    total_floats: number;
    active_floats: number;
    total_profiles: number;
    ocean_basins: string[];
}

export interface ArgoPaginatedResponse<T> {
    total: number;
    limit: number;
    offset: number;
    data: T[];
}

export interface ArgoBBox {
    min_lon: number;
    min_lat: number;
    max_lon: number;
    max_lat: number;
}

export interface ArgoFloatFilterRequest {
    bbox?: ArgoBBox;
    start_date?: string;
    end_date?: string;
    status?: string;
    ocean_basin?: string;
    wmo_numbers?: string[];
    limit?: number;
    offset?: number;
}

export interface ArgoProfileFilterRequest {
    bbox?: ArgoBBox;
    start_date?: string;
    end_date?: string;
    wmo_numbers?: string[];
    min_depth?: number;
    max_depth?: number;
    data_mode?: string;
    limit?: number;
    offset?: number;
}

export interface ArgoMeasurementFilterRequest {
    profile_ids?: number[];
    wmo_number?: string;
    min_depth?: number;
    max_depth?: number;
    min_temperature?: number;
    max_temperature?: number;
    min_salinity?: number;
    max_salinity?: number;
    qc_max?: number;
    limit?: number;
    offset?: number;
}

export interface ArgoSummaryStats {
    total_floats: number;
    active_floats: number;
    inactive_floats: number;
    total_profiles: number;
    earliest_profile?: string | null;
    latest_profile?: string | null;
    ocean_basin_count?: number;
    total_measurements: number;
    avg_temperature?: number | null;
    avg_salinity?: number | null;
}

export interface ChatProviderHealth {
    available: boolean;
    status: string;
    latency_ms?: number;
    model?: string;
    error?: string;
    [key: string]: unknown;
}

export interface ChatProvidersResponse {
    providers: string[];
    health: Record<string, unknown>;
    error?: string;
}

export interface ChatSource {
    title: string;
    source: string;
    snippet: string;
}

export type ChatProvider = 'auto' | 'groq' | 'gemini' | 'openai' | 'ollama';

export interface ChatProviderMetric {
    provider: string;
    latency_ms: number;
    success: boolean;
    error?: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sql_query?: string;
    data?: unknown[];
    row_count?: number;
    source?: string;
    query_type?: string;
    intent?: string;
    intent_confidence?: number;
    confidence?: number;
    evidence_score?: number;
    evidence_coverage_score?: number;
    method?: string;
    data_source?: string[];
    limitations?: string[];
    next_checks?: string[];
    reliability_warnings?: string[];
    provider_metrics?: ChatProviderMetric[];
    cached?: boolean;
    sources?: ChatSource[];
}

export interface ChatResponse {
    success: boolean;
    response: string;
    sql_query?: string;
    data?: unknown[];
    row_count?: number;
    source?: string;
    query_type?: string;
    intent?: string;
    intent_confidence?: number;
    confidence?: number;
    evidence_score?: number;
    evidence_coverage_score?: number;
    method?: string;
    data_source?: string[];
    limitations?: string[];
    next_checks?: string[];
    reliability_warnings?: string[];
    provider_metrics?: ChatProviderMetric[];
    cached?: boolean;
    sources?: ChatSource[];
    error?: string;
}

export interface AdminMetricsSummaryResponse {
    period?: {
        window_minutes: number;
        started_at: string;
        ended_at: string;
    };
    window_minutes: number;
    chat: {
        total_requests: number;
        successful_requests: number;
        failed_requests: number;
        cached_responses: number;
        cache_hit_rate?: number | null;
        success_rate?: number | null;
        latency_ms: {
            p50?: number | null;
            p95?: number | null;
            avg?: number | null;
            max?: number | null;
        };
        requested_provider_counts: Record<string, number>;
        response_source_counts: Record<string, number>;
        provider_success_counts?: Record<string, number>;
        provider_failure_counts?: Record<string, number>;
        intent_counts: Record<string, number>;
        recent_events?: Array<{
            timestamp: string;
            requested_provider: string;
            source: string;
            intent: string;
            latency_ms: number;
            success: boolean;
            cached: boolean;
        }>;
    };
    providers?: Record<string, ChatProviderHealth | Record<string, unknown>>;
    database: {
        connected: boolean;
        probe_latency_ms?: number | null;
    };
    ingestion: {
        available: boolean;
        total_jobs: number;
        status_counts: Record<string, number>;
    };
    service?: {
        uptime_seconds: number;
        started_at: string;
    };
}

export interface AdminSloResponse {
    window_minutes: number;
    overall_ok: boolean;
    checks: Array<{
        name: string;
        target: string;
        value: unknown;
        ok: boolean;
    }>;
}

export interface ChatFeedbackRequest {
    rating: 1 | -1;
    user_message?: string;
    assistant_message?: string;
    source?: string;
    query_type?: string;
}

export interface ChatFeedbackBreakdownItem {
    label: string;
    count: number;
}

export interface ChatFeedbackRecentItem {
    created_at: string | null;
    rating: 1 | -1;
    source?: string | null;
    query_type?: string | null;
}

export interface ChatFeedbackStatsResponse {
    success: boolean;
    total_feedback: number;
    helpful_count: number;
    not_helpful_count: number;
    helpful_ratio: number | null;
    by_source: ChatFeedbackBreakdownItem[];
    by_query_type: ChatFeedbackBreakdownItem[];
    recent: ChatFeedbackRecentItem[];
}

export interface GlossaryItem {
    term: string;
    category: string;
    short_definition: string;
    details: string;
    units?: string | null;
}

export interface PressureDepthRequest {
    depth_m?: number;
    pressure_dbar?: number;
    latitude?: number;
}

export interface PressureDepthResponse {
    depth_m: number;
    pressure_dbar: number;
    latitude: number;
}

export interface LearningInsight {
    title: string;
    detail: string;
    metric?: string | null;
}

export interface ToolsQuickStats {
    min_temperature?: number | null;
    max_temperature?: number | null;
    min_salinity?: number | null;
    max_salinity?: number | null;
    median_depth?: number | null;
    latest_profile_date?: string | null;
}

export interface DownloadedFile {
    blob: Blob;
    filename: string | null;
    contentType: string | null;
    citation: string | null;
}

export interface ExportSnapshotRequest {
    float_filter: ArgoFloatFilterRequest;
    profile_filter: ArgoProfileFilterRequest;
    measurement_filter: ArgoMeasurementFilterRequest;
}

export interface AuthUser {
    id: string;
    email: string;
    username: string;
    full_name?: string | null;
    is_active: boolean;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: AuthUser;
}

export interface Workspace {
    id: string;
    name: string;
    description?: string | null;
    created_at?: string;
    updated_at?: string;
    role?: string;
    owned?: boolean;
}

export interface StudyNote {
    id: string;
    content: string;
    created_at?: string;
}

export interface SavedStudyQuery {
    id: string;
    name: string;
    query_payload: Record<string, unknown>;
    created_at?: string;
}

export interface WorkspaceDashboardResponse {
    workspace: Workspace;
    counts: {
        notes: number;
        saved_queries: number;
        compare_sessions: number;
        timeline_runs: number;
        versions?: number;
    };
    recent_notes: StudyNote[];
    recent_queries: SavedStudyQuery[];
    latest_compare?: Record<string, unknown> | null;
    latest_timeline?: Record<string, unknown> | null;
}

export interface WorkspaceSnapshotResponse {
    workspace: Workspace;
    notes: StudyNote[];
    saved_queries: SavedStudyQuery[];
    compare_history: Array<Record<string, unknown>>;
    timeline_history: Array<Record<string, unknown>>;
}

export interface WorkspaceVersionSummary {
    id: string;
    label?: string | null;
    snapshot_hash: string;
    created_at?: string;
    counts: {
        notes: number;
        saved_queries: number;
        compare_history: number;
        timeline_history: number;
    };
}

export interface WorkspaceVersionDetail extends WorkspaceVersionSummary {
    workspace_id: string;
    snapshot: WorkspaceSnapshotResponse;
}

export interface WorkspaceMember {
    user_id: string;
    role: 'owner' | 'editor' | 'viewer';
    status: 'active' | 'revoked';
    is_owner?: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface WorkspaceReproPackageResponse {
    metadata: {
        workspace_id: string;
        generated_at: string;
        version: {
            id?: string | null;
            label?: string | null;
            snapshot_hash?: string | null;
            created_at?: string | null;
        };
        counts: {
            notes: number;
            saved_queries: number;
            compare_history: number;
            timeline_history: number;
        };
        citation: string;
        repro_steps: string[];
    };
    snapshot: WorkspaceSnapshotResponse;
}

export interface WorkspaceNotebookTemplateResponse {
    workspace_id: string;
    version_id?: string | null;
    language: 'python' | 'r';
    filename: string;
    format: 'ipynb' | 'r_script';
    content: string;
}

export interface StudyBackgroundJob {
    id: string;
    job_type: string;
    status: 'queued' | 'running' | 'completed' | 'failed';
    progress: number;
    message?: string;
    payload_meta?: Record<string, unknown>;
    result?: unknown;
    error?: unknown;
    created_at?: string | null;
    started_at?: string | null;
    completed_at?: string | null;
}

export interface CompareRunResponse {
    session_id?: string;
    region_a: string;
    region_b: string;
    floats_a: number;
    floats_b: number;
    profiles_a: number;
    profiles_b: number;
    delta_floats: number;
    delta_profiles: number;
    insights?: string[];
    statistics?: {
        temperature?: {
            metric: string;
            available: boolean;
            count_a: number;
            count_b: number;
            mean_a?: number | null;
            mean_b?: number | null;
            delta?: number | null;
            confidence_interval_95?: { lower: number; upper: number } | null;
            p_value_approx?: number | null;
            effect_size_cohen_d?: number | null;
            anomaly_score?: number | null;
            interpretation?: string;
        };
        salinity?: {
            metric: string;
            available: boolean;
            count_a: number;
            count_b: number;
            mean_a?: number | null;
            mean_b?: number | null;
            delta?: number | null;
            confidence_interval_95?: { lower: number; upper: number } | null;
            p_value_approx?: number | null;
            effect_size_cohen_d?: number | null;
            anomaly_score?: number | null;
            interpretation?: string;
        };
    };
}

export interface TimelineSeriesPoint {
    month: string;
    profiles: number;
}

export interface TimelineResponse {
    id: string;
    series: TimelineSeriesPoint[];
    points: number;
}

export interface BGCProfile {
    id: number;
    wmo_number: string;
    cycle_number?: number | null;
    profile_date?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    chlorophyll?: number | null;
    nitrate?: number | null;
    oxygen?: number | null;
    ph?: number | null;
    source_file?: string | null;
}

export interface BGCSummary {
    total_profiles: number;
    total_floats: number;
    avg_chlorophyll?: number | null;
    avg_nitrate?: number | null;
    avg_oxygen?: number | null;
    avg_ph?: number | null;
}

class ApiClient {
    private baseUrl: string;
    private authToken: string | null = null;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    setAuthToken(token: string | null) {
        this.authToken = token;
    }

    getAuthToken(): string | null {
        return this.authToken;
    }

    private buildHeaders(extra?: HeadersInit): HeadersInit {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };
        if (this.authToken) {
            headers.Authorization = `Bearer ${this.authToken}`;
        }
        if (extra) {
            return {
                ...headers,
                ...extra,
            };
        }
        return headers;
    }

    private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: this.buildHeaders(options?.headers),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Health check
    async healthCheck(): Promise<{ status: string; database: string; mode?: string }> {
        return this.request('/health');
    }

    // Get ARGO floats
    async getFloats(params?: { limit?: number; ocean_basin?: string }): Promise<ArgoFloat[]> {
        const queryParams = new URLSearchParams();
        if (params?.limit) queryParams.append('limit', params.limit.toString());
        if (params?.ocean_basin) queryParams.append('ocean_basin', params.ocean_basin);

        const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
        return this.request(`/api/floats${query}`);
    }

    // Get specific float
    async getFloat(wmoNumber: string): Promise<ArgoFloat> {
        return this.request(`/api/floats/${wmoNumber}`);
    }

    // Get profiles
    async getProfiles(params?: { wmo_number?: string; limit?: number }): Promise<ArgoProfile[]> {
        const queryParams = new URLSearchParams();
        if (params?.wmo_number) queryParams.append('wmo_number', params.wmo_number);
        if (params?.limit) queryParams.append('limit', params.limit.toString());

        const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
        return this.request(`/api/profiles${query}`);
    }

    // Get statistics
    async getStats(): Promise<Stats> {
        return this.request('/api/stats');
    }

    private async requestFile(endpoint: string, options?: RequestInit): Promise<DownloadedFile> {
        const url = `${this.baseUrl}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: this.buildHeaders(options?.headers),
            });

            if (!response.ok) {
                let detail = `HTTP error! status: ${response.status}`;
                try {
                    const parsed = await response.json();
                    if (parsed?.detail && typeof parsed.detail === 'string') {
                        detail = parsed.detail;
                    }
                } catch {
                    // noop
                }
                throw new Error(detail);
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            const contentType = response.headers.get('content-type');
            const citation = response.headers.get('x-suggested-citation');
            let filename: string | null = null;

            if (contentDisposition) {
                const match = contentDisposition.match(/filename=\"?([^\";]+)\"?/i);
                if (match && match[1]) {
                    filename = match[1];
                }
            }

            return { blob, filename, contentType, citation };
        } catch (error) {
            console.error(`API file request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // ARGO v1 filtered dataset endpoints
    async filterArgoFloats(filter: ArgoFloatFilterRequest): Promise<ArgoPaginatedResponse<ArgoFloat>> {
        return this.request('/api/v1/argo/floats/filter', {
            method: 'POST',
            body: JSON.stringify(filter),
        });
    }

    async filterArgoProfiles(filter: ArgoProfileFilterRequest): Promise<ArgoPaginatedResponse<ArgoProfile>> {
        return this.request('/api/v1/argo/profiles/filter', {
            method: 'POST',
            body: JSON.stringify(filter),
        });
    }

    async filterArgoMeasurements(filter: ArgoMeasurementFilterRequest): Promise<ArgoPaginatedResponse<Record<string, unknown>>> {
        return this.request('/api/v1/argo/measurements/filter', {
            method: 'POST',
            body: JSON.stringify(filter),
        });
    }

    async getArgoSummaryStats(): Promise<ArgoSummaryStats> {
        return this.request('/api/v1/argo/stats/summary');
    }

    async getChatProviders(): Promise<ChatProvidersResponse> {
        return this.request('/api/chat/providers');
    }

    async getAdminMetricsSummary(params?: {
        windowMinutes?: number;
        includeRecentEvents?: number;
        adminKey?: string;
    }): Promise<AdminMetricsSummaryResponse> {
        const windowMinutes = params?.windowMinutes ?? 60;
        const includeRecentEvents = params?.includeRecentEvents ?? 20;
        const query = new URLSearchParams({
            window_minutes: String(windowMinutes),
            include_recent_events: String(includeRecentEvents),
        });
        const key = params?.adminKey ?? ADMIN_API_KEY;
        const headers: HeadersInit | undefined = key ? { 'X-Admin-Key': key } : undefined;
        return this.request(`/api/admin/metrics/summary?${query.toString()}`, { headers });
    }

    async getAdminSloStatus(params?: {
        windowMinutes?: number;
        adminKey?: string;
    }): Promise<AdminSloResponse> {
        const windowMinutes = params?.windowMinutes ?? 60;
        const key = params?.adminKey ?? ADMIN_API_KEY;
        const headers: HeadersInit | undefined = key ? { 'X-Admin-Key': key } : undefined;
        return this.request(`/api/admin/metrics/slo?window_minutes=${windowMinutes}`, { headers });
    }

    async getAdminPrometheusMetrics(params?: {
        windowMinutes?: number;
        adminKey?: string;
    }): Promise<string> {
        const windowMinutes = params?.windowMinutes ?? 60;
        const key = params?.adminKey ?? ADMIN_API_KEY;
        const headers: HeadersInit = key ? { 'X-Admin-Key': key } : {};
        const response = await fetch(`${this.baseUrl}/api/admin/metrics/prometheus?window_minutes=${windowMinutes}`, {
            headers: this.buildHeaders(headers),
        });
        if (!response.ok) {
            throw new Error(`Prometheus metrics fetch failed: ${response.status}`);
        }
        return response.text();
    }

    // Research tools endpoints
    async getToolsGlossary(q?: string, limit: number = 50): Promise<GlossaryItem[]> {
        const queryParams = new URLSearchParams();
        if (q) queryParams.append('q', q);
        queryParams.append('limit', String(limit));
        const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
        return this.request(`/api/v1/tools/glossary${query}`);
    }

    async calculatePressureDepth(payload: PressureDepthRequest): Promise<PressureDepthResponse> {
        return this.request('/api/v1/tools/calculate/pressure-depth', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getLearningInsights(): Promise<LearningInsight[]> {
        return this.request('/api/v1/tools/learn/insights');
    }

    async getToolsQuickStats(): Promise<ToolsQuickStats> {
        return this.request('/api/v1/tools/quick-stats');
    }

    // Export endpoints
    async exportFloatsCsv(filter: ArgoFloatFilterRequest, exportLimit: number = 10000): Promise<DownloadedFile> {
        return this.requestFile(`/api/v1/export/floats/csv?export_limit=${exportLimit}`, {
            method: 'POST',
            body: JSON.stringify(filter),
        });
    }

    async exportProfilesCsv(filter: ArgoProfileFilterRequest, exportLimit: number = 20000): Promise<DownloadedFile> {
        return this.requestFile(`/api/v1/export/profiles/csv?export_limit=${exportLimit}`, {
            method: 'POST',
            body: JSON.stringify(filter),
        });
    }

    async exportMeasurementsCsv(filter: ArgoMeasurementFilterRequest, exportLimit: number = 50000): Promise<DownloadedFile> {
        return this.requestFile(`/api/v1/export/measurements/csv?export_limit=${exportLimit}`, {
            method: 'POST',
            body: JSON.stringify(filter),
        });
    }

    async exportMeasurementsNetcdf(filter: ArgoMeasurementFilterRequest, exportLimit: number = 50000): Promise<DownloadedFile> {
        return this.requestFile(`/api/v1/export/measurements/netcdf?export_limit=${exportLimit}`, {
            method: 'POST',
            body: JSON.stringify(filter),
        });
    }

    async exportSnapshotJson(payload: ExportSnapshotRequest, exportLimitEach: number = 10000): Promise<DownloadedFile> {
        return this.requestFile(`/api/v1/export/snapshot/json?export_limit_each=${exportLimitEach}`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    // Send chat message (provider: 'auto' | 'ollama' | 'openai' | 'gemini')
    async sendChatMessage(message: string, provider: ChatProvider = 'auto'): Promise<ChatResponse> {
        return this.request('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message, provider }),
        });
    }

    async sendChatFeedback(payload: ChatFeedbackRequest): Promise<{ success: boolean; message?: string }> {
        return this.request('/api/chat/feedback', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getChatFeedbackStats(limit: number = 20): Promise<ChatFeedbackStatsResponse> {
        const queryLimit = Number.isFinite(limit) ? Math.max(1, Math.min(100, Math.trunc(limit))) : 20;
        return this.request(`/api/chat/feedback/stats?limit=${queryLimit}`);
    }

    // Auth endpoints
    async register(payload: { email: string; username: string; password: string; full_name?: string }): Promise<AuthResponse> {
        return this.request('/api/v1/auth/register', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async login(payload: { username_or_email: string; password: string }): Promise<AuthResponse> {
        return this.request('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async me(): Promise<AuthUser> {
        return this.request('/api/v1/auth/me');
    }

    // Study/workspace endpoints
    async listWorkspaces(): Promise<Workspace[]> {
        return this.request('/api/v1/study/workspaces');
    }

    async createWorkspace(payload: { name: string; description?: string }): Promise<Workspace> {
        return this.request('/api/v1/study/workspaces', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async cloneWorkspace(
        workspaceId: string,
        payload?: { name?: string; include_notes?: boolean; include_queries?: boolean },
    ): Promise<{
        id: string;
        name: string;
        source_workspace_id: string;
        notes_cloned: number;
        queries_cloned: number;
    }> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/clone`, {
            method: 'POST',
            body: JSON.stringify(payload ?? {}),
        });
    }

    async listWorkspaceNotes(workspaceId: string): Promise<StudyNote[]> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/notes`);
    }

    async searchWorkspaceNotes(workspaceId: string, q: string, limit: number = 20): Promise<StudyNote[]> {
        const query = new URLSearchParams({ q, limit: String(limit) });
        return this.request(`/api/v1/study/workspaces/${workspaceId}/notes/search?${query.toString()}`);
    }

    async createWorkspaceNote(workspaceId: string, payload: { content: string }): Promise<StudyNote> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/notes`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async deleteWorkspaceNote(noteId: string): Promise<{ success: boolean }> {
        return this.request(`/api/v1/study/notes/${noteId}`, {
            method: 'DELETE',
        });
    }

    async listWorkspaceQueries(workspaceId: string): Promise<SavedStudyQuery[]> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/queries`);
    }

    async saveWorkspaceQuery(workspaceId: string, payload: { name: string; query_payload: Record<string, unknown> }): Promise<SavedStudyQuery> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/queries`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getWorkspaceDashboard(workspaceId: string): Promise<WorkspaceDashboardResponse> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/dashboard`);
    }

    async listWorkspaceMembers(workspaceId: string): Promise<WorkspaceMember[]> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/members`);
    }

    async addWorkspaceMember(
        workspaceId: string,
        payload: { user_identifier: string; role: 'viewer' | 'editor' },
    ): Promise<{
        workspace_id: string;
        user_id: string;
        email: string;
        username: string;
        role: 'viewer' | 'editor';
        status: 'active';
    }> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/members`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async updateWorkspaceMember(
        workspaceId: string,
        memberUserId: string,
        payload: { role: 'viewer' | 'editor'; status?: 'active' | 'revoked' },
    ): Promise<{ success: boolean }> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/members/${memberUserId}`, {
            method: 'PATCH',
            body: JSON.stringify({
                role: payload.role,
                status: payload.status ?? 'active',
            }),
        });
    }

    async removeWorkspaceMember(workspaceId: string, memberUserId: string): Promise<{ success: boolean }> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/members/${memberUserId}`, {
            method: 'DELETE',
        });
    }

    async getWorkspaceSnapshot(
        workspaceId: string,
        params?: {
            include_notes?: boolean;
            include_queries?: boolean;
            include_compare_history?: boolean;
            include_timeline_history?: boolean;
            history_limit?: number;
        },
    ): Promise<WorkspaceSnapshotResponse> {
        const query = new URLSearchParams();
        if (typeof params?.include_notes === 'boolean') query.set('include_notes', String(params.include_notes));
        if (typeof params?.include_queries === 'boolean') query.set('include_queries', String(params.include_queries));
        if (typeof params?.include_compare_history === 'boolean') query.set('include_compare_history', String(params.include_compare_history));
        if (typeof params?.include_timeline_history === 'boolean') query.set('include_timeline_history', String(params.include_timeline_history));
        if (typeof params?.history_limit === 'number') query.set('history_limit', String(params.history_limit));
        const suffix = query.toString() ? `?${query.toString()}` : '';
        return this.request(`/api/v1/study/workspaces/${workspaceId}/snapshot${suffix}`);
    }

    async createWorkspaceVersion(
        workspaceId: string,
        payload?: {
            label?: string;
            include_notes?: boolean;
            include_queries?: boolean;
            include_compare_history?: boolean;
            include_timeline_history?: boolean;
            history_limit?: number;
        },
    ): Promise<WorkspaceVersionSummary> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/versions`, {
            method: 'POST',
            body: JSON.stringify(payload ?? {}),
        });
    }

    async listWorkspaceVersions(workspaceId: string, limit: number = 20): Promise<WorkspaceVersionSummary[]> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/versions?limit=${Math.max(1, Math.min(100, Math.trunc(limit)))}`);
    }

    async getWorkspaceVersion(workspaceId: string, versionId: string): Promise<WorkspaceVersionDetail> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/versions/${versionId}`);
    }

    async restoreWorkspaceVersion(
        workspaceId: string,
        versionId: string,
        payload?: {
            dry_run?: boolean;
            restore_notes?: boolean;
            restore_queries?: boolean;
            restore_compare_history?: boolean;
            restore_timeline_history?: boolean;
            mode?: 'replace';
        },
    ): Promise<{
        success: boolean;
        dry_run: boolean;
        mode: 'replace';
        workspace_id: string;
        version_id: string;
        planned_restore?: Record<string, number>;
        restored?: Record<string, number>;
    }> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/versions/${versionId}/restore`, {
            method: 'POST',
            body: JSON.stringify(payload ?? { dry_run: true }),
        });
    }

    async getWorkspaceReproPackage(
        workspaceId: string,
        params?: {
            version_id?: string;
            include_notes?: boolean;
            include_queries?: boolean;
            include_compare_history?: boolean;
            include_timeline_history?: boolean;
            history_limit?: number;
        },
    ): Promise<WorkspaceReproPackageResponse> {
        const query = new URLSearchParams();
        if (params?.version_id) query.set('version_id', params.version_id);
        if (typeof params?.include_notes === 'boolean') query.set('include_notes', String(params.include_notes));
        if (typeof params?.include_queries === 'boolean') query.set('include_queries', String(params.include_queries));
        if (typeof params?.include_compare_history === 'boolean') query.set('include_compare_history', String(params.include_compare_history));
        if (typeof params?.include_timeline_history === 'boolean') query.set('include_timeline_history', String(params.include_timeline_history));
        if (typeof params?.history_limit === 'number') query.set('history_limit', String(params.history_limit));
        const suffix = query.toString() ? `?${query.toString()}` : '';
        return this.request(`/api/v1/study/workspaces/${workspaceId}/repro-package${suffix}`);
    }

    async getWorkspaceNotebookTemplate(
        workspaceId: string,
        params?: {
            language?: 'python' | 'r';
            version_id?: string;
        },
    ): Promise<WorkspaceNotebookTemplateResponse> {
        const query = new URLSearchParams();
        query.set('language', params?.language || 'python');
        if (params?.version_id) query.set('version_id', params.version_id);
        return this.request(`/api/v1/study/workspaces/${workspaceId}/notebook-template?${query.toString()}`);
    }

    async queueWorkspaceReproPackageJob(
        workspaceId: string,
        payload?: { version_id?: string },
    ): Promise<StudyBackgroundJob> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/repro-package/jobs`, {
            method: 'POST',
            body: JSON.stringify(payload ?? {}),
        });
    }

    async listWorkspaceJobs(workspaceId: string, limit: number = 20): Promise<StudyBackgroundJob[]> {
        const safeLimit = Number.isFinite(limit) ? Math.max(1, Math.min(100, Math.trunc(limit))) : 20;
        return this.request(`/api/v1/study/workspaces/${workspaceId}/jobs?limit=${safeLimit}`);
    }

    async getWorkspaceJob(workspaceId: string, jobId: string): Promise<StudyBackgroundJob> {
        return this.request(`/api/v1/study/workspaces/${workspaceId}/jobs/${jobId}`);
    }

    async runStudyCompare(payload: {
        region_a: string;
        region_b: string;
        bbox_a?: ArgoBBox;
        bbox_b?: ArgoBBox;
        start_date?: string;
        end_date?: string;
        workspace_id?: string;
        save_session?: boolean;
    }): Promise<CompareRunResponse> {
        return this.request('/api/v1/study/compare/run', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getStudyCompareHistory(workspaceId?: string): Promise<Array<Record<string, unknown>>> {
        const query = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : '';
        return this.request(`/api/v1/study/compare/history${query}`);
    }

    async runProfileTimeline(payload: {
        bbox?: ArgoBBox;
        start_date?: string;
        end_date?: string;
        workspace_id?: string;
        label?: string;
    }): Promise<TimelineResponse> {
        return this.request('/api/v1/study/timeline/profiles', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getTimelineHistory(workspaceId?: string): Promise<Array<Record<string, unknown>>> {
        const query = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : '';
        return this.request(`/api/v1/study/timeline/history${query}`);
    }

    // BGC-Argo endpoints
    async filterBGCProfiles(payload: {
        bbox?: ArgoBBox;
        start_date?: string;
        end_date?: string;
        wmo_numbers?: string[];
        parameter?: string;
        limit?: number;
        offset?: number;
    }): Promise<ArgoPaginatedResponse<BGCProfile>> {
        return this.request('/api/v1/bgc/profiles/filter', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async getBGCSummary(): Promise<BGCSummary> {
        return this.request('/api/v1/bgc/stats/summary');
    }

    // --- ArgoVis External API Methods ---

    async argovisPing(): Promise<{ ok: boolean; argovis_response?: any; error?: string }> {
        return this.request('/api/v1/argovis/ping');
    }

    async searchArgoVisProfiles(params: {
        startDate?: string;
        endDate?: string;
        polygon?: string;
        box?: string;
        center?: string;
        radius?: number;
        platform?: string;
        source?: string;
        data?: string;
        compression?: string;
        limit?: number;
    }): Promise<ArgoVisSearchResponse<ArgoVisProfile>> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/argovis/profiles?${queryParams.toString()}`);
    }

    async getArgoVisProfile(profileId: string, data?: string): Promise<ArgoVisProfile> {
        const query = data ? `?data=${data}` : '';
        return this.request(`/api/v1/argovis/profiles/${profileId}${query}`);
    }

    async listArgoVisPlatforms(): Promise<{ total: number; data: string[] }> {
        return this.request('/api/v1/argovis/platforms');
    }

    async getArgoVisPlatformProfiles(
        platformNumber: string,
        params: {
            startDate?: string;
            endDate?: string;
            data?: string;
            compression?: string;
        } = {}
    ): Promise<{ platform: string; total: number; data: ArgoVisProfile[] }> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/argovis/platforms/${platformNumber}?${queryParams.toString()}`);
    }

    async getLatestArgoVisProfiles(limit: number = 20): Promise<ArgoVisSearchResponse<ArgoVisProfile>> {
        return this.request(`/api/v1/argovis/latest?limit=${limit}`);
    }

    async getArgoVisProfilesByRegion(
        bbox: { sw_lon: number; sw_lat: number; ne_lon: number; ne_lat: number },
        params: {
            startDate?: string;
            endDate?: string;
            data?: string;
            limit?: number;
        } = {}
    ): Promise<ArgoVisSearchResponse<ArgoVisProfile>> {
        const queryParams = new URLSearchParams();
        queryParams.append('sw_lon', bbox.sw_lon.toString());
        queryParams.append('sw_lat', bbox.sw_lat.toString());
        queryParams.append('ne_lon', bbox.ne_lon.toString());
        queryParams.append('ne_lat', bbox.ne_lat.toString());
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/argovis/region?${queryParams.toString()}`);
    }

    // --- Copernicus CMEMS API Methods ---

    async cmemsPing(): Promise<{ ok: boolean; has_credentials: boolean; username?: string; message?: string }> {
        return this.request('/api/v1/cmems/ping');
    }

    async getCMEMSCapabilities(): Promise<CMEMSCapabilities> {
        return this.request('/api/v1/cmems/wmts/capabilities');
    }

    async searchCMEMSCatalogue(query: string = 'temperature'): Promise<CMEMSSearchResponse> {
        return this.request(`/api/v1/cmems/catalogue/search?query=${encodeURIComponent(query)}`);
    }

    // --- NOAA API Methods ---

    async noaaPing(): Promise<{ ok: boolean; message: string }> {
        return this.request('/api/v1/noaa/ping');
    }

    async getNOAAStations(): Promise<{ total: number; stations: NOAAStation[] }> {
        return this.request('/api/v1/noaa/coops/stations');
    }

    async getNOAAData(
        station: string,
        product: string = 'water_level',
        date: string = 'latest',
        datum: string = 'MLLW'
    ): Promise<NOAACoopsResponse> {
        const queryParams = new URLSearchParams({ station, product, date, datum });
        return this.request(`/api/v1/noaa/coops/data?${queryParams.toString()}`);
    }

    async getNOAANdbcLatest(station: string): Promise<NOAANdbcResponse> {
        return this.request(`/api/v1/noaa/ndbc/latest?station=${station}`);
    }

    // --- OBIS API Methods ---

    async obisPing(): Promise<{ ok: boolean; message: string }> {
        return this.request('/api/v1/obis/ping');
    }

    async getOBISOccurrences(params: {
        scientificname?: string;
        geometry?: string;
        startdate?: string;
        enddate?: string;
        size?: number;
    }): Promise<OBISOccurrenceResponse> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/obis/occurrence?${queryParams.toString()}`);
    }

    async getOBISTaxon(scientificname: string): Promise<any> {
        return this.request(`/api/v1/obis/taxon/${encodeURIComponent(scientificname)}`);
    }

    // --- Open-Meteo Marine API Methods ---

    async openMeteoMarinePing(): Promise<{ ok: boolean; status_code?: number }> {
        return this.request('/api/v1/open-meteo-marine/ping');
    }

    async getMarineForecast(params: {
        latitude: number;
        longitude: number;
        hourly?: string;
        daily?: string;
        timezone?: string;
        forecast_days?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/open-meteo-marine/forecast?${queryParams.toString()}`);
    }

    async getWaveData(latitude: number, longitude: number, forecastDays: number = 7): Promise<any> {
        return this.request(`/api/v1/open-meteo-marine/wave?latitude=${latitude}&longitude=${longitude}&forecast_days=${forecastDays}`);
    }

    async getSeaTemperature(latitude: number, longitude: number, forecastDays: number = 7): Promise<any> {
        return this.request(`/api/v1/open-meteo-marine/sea-temperature?latitude=${latitude}&longitude=${longitude}&forecast_days=${forecastDays}`);
    }

    // --- ERDDAP API Methods ---

    async erddapPing(server: string = 'oceanobservatories'): Promise<any> {
        return this.request(`/api/v1/erddap/ping?server=${server}`);
    }

    async listERDDAPDatasets(params: {
        server?: string;
        search_for?: string;
        page?: number;
        items_per_page?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/erddap/datasets?${queryParams.toString()}`);
    }

    async searchERDDAP(query: string, server: string = 'oceanobservatories', limit: number = 20): Promise<any> {
        return this.request(`/api/v1/erddap/search?query=${encodeURIComponent(query)}&server=${server}&limit=${limit}`);
    }

    // --- GEBCO API Methods ---

    async gebcoPing(): Promise<{ ok: boolean; status_code?: number }> {
        return this.request('/api/v1/gebco/ping');
    }

    async getElevation(lat: number, lon: number): Promise<any> {
        return this.request(`/api/v1/gebco/elevation?lat=${lat}&lon=${lon}`);
    }

    async getBathymetryRegion(params: {
        sw_lat: number;
        sw_lon: number;
        ne_lat: number;
        ne_lon: number;
        num_points?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/gebco/region?${queryParams.toString()}`);
    }

    // --- Global Fishing Watch API Methods ---

    async gfwPing(): Promise<{ ok: boolean; has_api_key?: boolean }> {
        return this.request('/api/v1/gfw/ping');
    }

    async searchGFWVessels(query: string, limit: number = 10): Promise<any> {
        return this.request(`/api/v1/gfw/vessels/search?query=${encodeURIComponent(query)}&limit=${limit}`);
    }

    async getGFWFishingEffort(params: {
        start_date: string;
        end_date: string;
        dataset?: string;
        spatial_resolution?: string;
        temporal_resolution?: string;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/gfw/fishing-effort?${queryParams.toString()}`);
    }

    // --- World Ocean Database API Methods ---

    async wodPing(): Promise<{ ok: boolean; status_code?: number }> {
        return this.request('/api/v1/wod/ping');
    }

    async searchWOD(query: string, limit: number = 20): Promise<any> {
        return this.request(`/api/v1/wod/search?query=${encodeURIComponent(query)}&limit=${limit}`);
    }

    async getWODProfiles(params: {
        lat: number;
        lon: number;
        radius?: number;
        date_start?: string;
        date_end?: string;
        variables?: string;
        limit?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/wod/profiles?${queryParams.toString()}`);
    }

    async getWODRegions(): Promise<any> {
        return this.request('/api/v1/wod/regions');
    }

    async getWODVariables(): Promise<any> {
        return this.request('/api/v1/wod/variables');
    }

    // --- Ocean Observatories Initiative API Methods ---

    async ooiPing(): Promise<{ ok: boolean; status_code?: number }> {
        return this.request('/api/v1/ooi/ping');
    }

    async listOOIArrays(): Promise<any> {
        return this.request('/api/v1/ooi/arrays');
    }

    async listOOIInstruments(params?: { array?: string; limit?: number }): Promise<any> {
        const queryParams = new URLSearchParams();
        if (params?.array) queryParams.append('array', params.array);
        if (params?.limit) queryParams.append('limit', params.limit.toString());
        return this.request(`/api/v1/ooi/instruments?${queryParams.toString()}`);
    }

    async getOOIData(params: {
        instrument_id: string;
        start_date: string;
        end_date: string;
        parameters?: string;
        bin_size?: string;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/ooi/data?${queryParams.toString()}`);
    }

    async getOOIMap(): Promise<any> {
        return this.request('/api/v1/ooi/map');
    }

    // --- ICOADS API Methods ---

    async icoadsPing(): Promise<{ ok: boolean; status_code?: number }> {
        return this.request('/api/v1/icoads/ping');
    }

    async getICOADSObservations(params: {
        lat_min?: number;
        lat_max?: number;
        lon_min?: number;
        lon_max?: number;
        year?: number;
        month?: number;
        limit?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/icoads/observations?${queryParams.toString()}`);
    }

    async getICOADSVariables(): Promise<any> {
        return this.request('/api/v1/icoads/variables');
    }

    // --- IOOS API Methods ---

    async ioosPing(): Promise<{ ok: boolean; status_code?: number }> {
        return this.request('/api/v1/ioos/ping');
    }

    async listIOOSRegions(): Promise<any> {
        return this.request('/api/v1/ioos/regions');
    }

    async listIOOSStations(params?: {
        region?: string;
        type?: string;
        lat_min?: number;
        lat_max?: number;
        lon_min?: number;
        lon_max?: number;
        limit?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params || {}).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/ioos/stations?${queryParams.toString()}`);
    }

    async getIOOSData(params: {
        station_id: string;
        start_date: string;
        end_date: string;
        parameters?: string;
        limit?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/ioos/data?${queryParams.toString()}`);
    }

    // --- Ocean Networks Canada API Methods ---

    async oncPing(): Promise<{ ok: boolean; status_code?: number }> {
        return this.request('/api/v1/onc/ping');
    }

    async listONCLocations(): Promise<any> {
        return this.request('/api/v1/onc/locations');
    }

    async listONCInstruments(params?: { location?: string; type?: string; limit?: number }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params || {}).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/onc/instruments?${queryParams.toString()}`);
    }

    async getONCData(params: {
        instrument_id: string;
        start_date: string;
        end_date: string;
        parameters?: string;
        limit?: number;
    }): Promise<any> {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) queryParams.append(key, value.toString());
        });
        return this.request(`/api/v1/onc/data?${queryParams.toString()}`);
    }
}



// Export singleton instance
export const apiClient = new ApiClient();

// Export class for custom instances
export default ApiClient;
