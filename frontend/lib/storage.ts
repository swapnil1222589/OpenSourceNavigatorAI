import { AnalysisResult, ChecklistItem, ContributionPlan, PlanStatus } from './types';

const STORAGE_KEY = 'os_navigator_contribution_plans_v1';

export type PlanSectionKey =
  | 'preparation_tasks'
  | 'investigation_tasks'
  | 'implementation_tasks'
  | 'testing_tasks'
  | 'pr_checklist';

export function getStoredPlans(): ContributionPlan[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to load contribution plans from localStorage:', e);
    return [];
  }
}

export function savePlans(plans: ContributionPlan[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(plans));
  } catch (e) {
    console.error('Failed to save contribution plans to localStorage:', e);
  }
}

export function createPlanFromAnalysis(analysis: AnalysisResult): ContributionPlan {
  const toItems = (arr: string[], prefix: string): ChecklistItem[] =>
    arr.map((text, i) => ({
      id: `${prefix}-${i}-${Date.now()}`,
      text,
      completed: false,
    }));

  const prepDefaults = [
    'Fork repository to your GitHub account and clone locally',
    analysis.retrieved_repo_context?.contributing_found
      ? 'Read the verified CONTRIBUTING.md guidelines in the repository'
      : 'Verify CONTRIBUTING.md, Code of Conduct, and development guidelines',
    'Set up local development environment and ensure base test suite passes',
    'Create an isolated feature branch (e.g. git checkout -b fix/issue-name)',
  ];

  const prDefaults = [
    'Run full test suite locally and ensure 100% clean pass',
    'Follow repository code formatting, linting, and typing checks',
    'Write or update unit tests covering your changes',
    'Craft clear commit messages referencing the issue number (e.g. Closes #...)',
    'Open Pull Request with a descriptive summary and screenshots/logs if applicable',
  ];

  return {
    id: `plan-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    issue_title: analysis.issue_title,
    repository_name: analysis.repository_name,
    issue_url: analysis.issue_url,
    skill_level_reason: `${analysis.estimated_difficulty} - ${analysis.difficulty_rationale}`,
    status: 'Not Started',
    created_at: new Date().toISOString(),
    preparation_tasks: toItems(prepDefaults, 'prep'),
    investigation_tasks: toItems(analysis.investigation_plan, 'inv'),
    implementation_tasks: toItems(
      analysis.suggested_inspection_areas.map((a) => {
        const tag = a.is_verified_in_repo ? '[Verified File]' : '[Hypothesis]';
        return `${tag} ${a.area_or_path}: ${a.rationale}`;
      }),
      'impl'
    ),
    testing_tasks: toItems(analysis.testing_strategy, 'test'),
    pr_checklist: toItems(prDefaults, 'pr'),
  };
}

export function savePlan(plan: ContributionPlan): ContributionPlan[] {
  const existing = getStoredPlans();
  const index = existing.findIndex((p) => p.id === plan.id);
  let updated: ContributionPlan[];
  if (index >= 0) {
    updated = [...existing];
    updated[index] = plan;
  } else {
    updated = [plan, ...existing];
  }
  savePlans(updated);
  return updated;
}

export function deletePlan(id: string): ContributionPlan[] {
  const existing = getStoredPlans();
  const updated = existing.filter((p) => p.id !== id);
  savePlans(updated);
  return updated;
}

export function toggleTaskCompletion(
  planId: string,
  sectionKey: PlanSectionKey,
  taskId: string
): ContributionPlan[] {
  const existing = getStoredPlans();
  const updated = existing.map((p) => {
    if (p.id !== planId) return p;
    const tasks = p[sectionKey].map((t) =>
      t.id === taskId ? { ...t, completed: !t.completed } : t
    );
    return { ...p, [sectionKey]: tasks };
  });
  savePlans(updated);
  return updated;
}

export function addTaskToSection(
  planId: string,
  sectionKey: PlanSectionKey,
  taskText: string
): ContributionPlan[] {
  const clean = taskText ? taskText.trim() : '';
  if (!clean) return getStoredPlans();

  const existing = getStoredPlans();
  const updated = existing.map((p) => {
    if (p.id !== planId) return p;
    const newTask: ChecklistItem = {
      id: `custom-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      text: clean,
      completed: false,
      custom: true,
    };
    return { ...p, [sectionKey]: [...p[sectionKey], newTask] };
  });
  savePlans(updated);
  return updated;
}

export function deleteTaskFromSection(
  planId: string,
  sectionKey: PlanSectionKey,
  taskId: string
): ContributionPlan[] {
  const existing = getStoredPlans();
  const updated = existing.map((p) => {
    if (p.id !== planId) return p;
    const filtered = p[sectionKey].filter((t) => t.id !== taskId);
    return { ...p, [sectionKey]: filtered };
  });
  savePlans(updated);
  return updated;
}

export function updatePlanStatus(planId: string, status: PlanStatus): ContributionPlan[] {
  const existing = getStoredPlans();
  const updated = existing.map((p) => (p.id === planId ? { ...p, status } : p));
  savePlans(updated);
  return updated;
}

export function exportPlanToMarkdown(plan: ContributionPlan): string {
  const renderTasks = (tasks: ChecklistItem[]) =>
    tasks.map((t) => `- [${t.completed ? 'x' : ' '}] ${t.text}`).join('\n');

  return `# Contribution Roadmap: ${plan.issue_title}

**Repository:** [${plan.repository_name}](${plan.issue_url})  
**Status:** ${plan.status}  
**Skill Assessment:** ${plan.skill_level_reason}  

---

### 1. Preparation & Setup
${renderTasks(plan.preparation_tasks)}

### 2. Repository Investigation
${renderTasks(plan.investigation_tasks)}

### 3. Implementation Tasks
${renderTasks(plan.implementation_tasks)}

### 4. Testing & Verification
${renderTasks(plan.testing_tasks)}

### 5. Pull Request Preparation Checklist
${renderTasks(plan.pr_checklist)}

---
*Generated by OpenSource Navigator AI — https://github.com/swapnil1222589/OpenSourceNavigatorAI*
`;
}
