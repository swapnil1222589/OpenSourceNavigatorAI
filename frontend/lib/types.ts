export interface IssueLabel {
  name: string;
  color: string;
  description?: string | null;
}

export interface IssueItem {
  id: number;
  number: number;
  title: string;
  body: string;
  html_url: string;
  state: string;
  created_at: string;
  updated_at: string;
  comments_count: number;
  repository_name: string;
  repository_url: string;
  labels: IssueLabel[];
}

export interface IssueSearchResponse {
  total_count: number;
  items: IssueItem[];
  rate_limited: boolean;
  rate_limit_reset?: number | null;
  message?: string | null;
}

export interface SuggestedAreaHypothesis {
  area_or_path: string;
  rationale: string;
  is_hypothesis: boolean;
}

export interface AnalysisResult {
  issue_title: string;
  repository_name: string;
  issue_url: string;
  plain_english_summary: string;
  problem_description: string;
  expected_outcome: string;
  possible_skills: string[];
  estimated_difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  difficulty_rationale: string;
  investigation_plan: string[];
  suggested_inspection_areas: SuggestedAreaHypothesis[];
  testing_strategy: string[];
  common_pitfalls: string[];
  maintainer_questions: string[];
  verification_checklist: string[];
  model_used: string;
  disclaimer: string;
}

export interface ChecklistItem {
  id: string;
  text: string;
  completed: boolean;
}

export type PlanStatus = 'Not Started' | 'In Progress' | 'Completed';

export interface ContributionPlan {
  id: string;
  issue_title: string;
  repository_name: string;
  issue_url: string;
  skill_level_reason: string;
  status: PlanStatus;
  created_at: string;
  preparation_tasks: ChecklistItem[];
  investigation_tasks: ChecklistItem[];
  implementation_tasks: ChecklistItem[];
  testing_tasks: ChecklistItem[];
  pr_checklist: ChecklistItem[];
}

export interface HealthStatus {
  status: string;
  app_name: string;
  version: string;
  ollama: {
    connected: boolean;
    configured_model: string;
    available_models: string[];
  };
  github: {
    token_configured: boolean;
  };
}
