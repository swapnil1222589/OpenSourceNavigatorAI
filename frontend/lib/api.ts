import { AnalysisResult, HealthStatus, IssueSearchResponse } from './types';

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
