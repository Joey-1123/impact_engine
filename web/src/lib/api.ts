const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface OverviewResponse {
  total_files: number;
  total_functions: number;
  total_classes: number;
  languages: Record<string, number>;
  layers: Record<string, number>;
  health_score: number;
}

export interface GraphResponse {
  nodes: { id: string; type: string; file_path: string; label: string; layer: string; pagerank: number; community: number; complexity: string }[];
  edges: { source: string; target: string; type: string }[];
  layers: string[];
  fingerprint: string;
}

export interface HealthScoreResponse {
  overall: number;
  defect: number;
  maintainability: number;
  performance: number;
  findings_count: number;
  kpis: Record<string, number>;
}

export interface CostResponse {
  model: string;
  estimated_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  breakdown: { page_type: string; count: number; input_tokens: number; output_tokens: number }[];
}

export interface DecisionResponse {
  decisions: { title: string; decision: string; rationale: string; source: string; confidence: number; status: string }[];
  total: number;
}

export function getHealth(): Promise<HealthResponse> {
  return apiFetch("/health");
}

export function getOverview(repoId: string): Promise<OverviewResponse> {
  return apiFetch(`/api/repos/${repoId}/overview`);
}

export function getGraph(repoId: string, entryPoints?: string): Promise<GraphResponse> {
  const params = entryPoints ? `?entry_points=${encodeURIComponent(entryPoints)}` : "";
  return apiFetch(`/api/repos/${repoId}/graph${params}`);
}

export function getHealthScore(repoId: string, mode?: string): Promise<HealthScoreResponse> {
  const params = mode ? `?mode=${mode}` : "";
  return apiFetch(`/api/repos/${repoId}/health-score${params}`);
}

export function getCosts(repoId: string, pageTypes?: string, count?: number, model?: string): Promise<CostResponse> {
  const params = new URLSearchParams();
  if (pageTypes) params.set("page_types", pageTypes);
  if (count) params.set("count", String(count));
  if (model) params.set("model", model);
  return apiFetch(`/api/repos/${repoId}/costs?${params}`);
}

export function getDecisions(repoId: string, status?: string, limit?: number): Promise<DecisionResponse> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (limit) params.set("limit", String(limit));
  return apiFetch(`/api/repos/${repoId}/decisions?${params}`);
}
