import {
  AgentMetadata,
  AnalysisResult,
  HealthStatus,
  IssueSearchResponse,
  RepoFileContentResponse,
  RepoFileExploreResponse,
  WorkflowRunRecord,
  WorkflowRunRequest,
  WorkflowRunResponse,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function getHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/v1/health`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Health check failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchIssues(params: {
  q?: string;
  language?: string;
  label?: string;
  repo?: string;
  page?: number;
  per_page?: number;
  sort?: string;
}): Promise<IssueSearchResponse> {
  const query = new URLSearchParams();
  if (params.q) query.set('q', params.q);
  if (params.language && params.language !== 'all') query.set('language', params.language);
  if (params.label && params.label !== 'all') query.set('label', params.label);
  if (params.repo) query.set('repo', params.repo);
  if (params.page) query.set('page', params.page.toString());
  if (params.per_page) query.set('per_page', params.per_page.toString());
  if (params.sort) query.set('sort', params.sort);

  const res = await fetch(`${API_BASE}/api/v1/issues?${query.toString()}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch issues: HTTP ${res.status}`);
  }

  return res.json();
}

export async function analyzeIssue(payload: {
  issue_title: string;
  issue_body?: string;
  repository_name: string;
  issue_url: string;
  labels?: string[];
  user_skill_level?: string;
}): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `AI analysis failed: HTTP ${res.status}`);
  }

  return res.json();
}

// ==========================================
// Multi-Agent API Endpoints
// ==========================================

export async function listAgents(): Promise<AgentMetadata[]> {
  const res = await fetch(`${API_BASE}/api/v1/agents`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch agent list: HTTP ${res.status}`);
  }
  return res.json();
}

export async function listRuns(limit = 20): Promise<WorkflowRunRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/agents/runs?limit=${limit}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch workflow runs: HTTP ${res.status}`);
  }
  return res.json();
}

export async function startWorkflowRun(
  payload: WorkflowRunRequest
): Promise<WorkflowRunResponse> {
  const res = await fetch(`${API_BASE}/api/v1/agents/runs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to trigger workflow run: HTTP ${res.status}`);
  }
  return res.json();
}

export async function getRunStatus(runId: string): Promise<WorkflowRunRecord> {
  const res = await fetch(`${API_BASE}/api/v1/agents/runs/${runId}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch run status: HTTP ${res.status}`);
  }
  return res.json();
}

export async function retryRun(runId: string): Promise<WorkflowRunResponse> {
  const res = await fetch(`${API_BASE}/api/v1/agents/runs/${runId}/retry`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to retry run: HTTP ${res.status}`);
  }
  return res.json();
}

export async function cancelRun(
  runId: string
): Promise<{ run_id: string; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/agents/runs/${runId}/cancel`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to cancel run: HTTP ${res.status}`);
  }
  return res.json();
}

// ==========================================
// Repository Exploration Endpoints
// ==========================================

export async function exploreRepository(
  repo: string,
  maxFiles = 60
): Promise<RepoFileExploreResponse> {
  const query = new URLSearchParams({
    repo,
    max_files: maxFiles.toString(),
  });
  const res = await fetch(`${API_BASE}/api/v1/repository/explore?${query.toString()}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to explore repository: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchRepositoryFile(
  repo: string,
  filePath: string
): Promise<RepoFileContentResponse> {
  const query = new URLSearchParams({
    repo,
    path: filePath,
  });
  const res = await fetch(`${API_BASE}/api/v1/repository/file?${query.toString()}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch repository file: HTTP ${res.status}`);
  }
  return res.json();
}
