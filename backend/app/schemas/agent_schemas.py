from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.issue import IssueItem


# 1. Issue Discovery Agent
class IssueDiscoveryInput(BaseModel):
    query: str = ""
    language: Optional[str] = None
    label: Optional[str] = None
    repo: Optional[str] = None
    page: int = 1
    per_page: int = 15
    sort: str = "updated"


class IssueDiscoveryOutput(BaseModel):
    total_count: int
    items: List[IssueItem]
    page: int
    per_page: int
    total_pages: int
    rate_limited: bool = False
    source: str = "GitHub REST API"


# 2. Issue Understanding Agent
class IssueUnderstandingInput(BaseModel):
    issue_title: str
    issue_body: Optional[str] = ""
    repository_name: str
    issue_url: str
    labels: List[str] = Field(default_factory=list)


class IssueUnderstandingOutput(BaseModel):
    plain_english_summary: str
    problem_statement: str
    expected_outcome: str
    acceptance_criteria: List[str]
    identified_ambiguities: List[str]
    maintainer_clarifications: List[str]
    confidence_level: str = "High"


# 3. Repository Context Agent
class RepositoryContextInput(BaseModel):
    repository_name: str


class RepositoryContextOutput(BaseModel):
    repository_name: str
    verified_files: List[str]
    contributing_found: bool
    contributing_url: Optional[str] = None
    readme_snippet: Optional[str] = None
    primary_language: Optional[str] = None
    provenance: str = "GitHub Contents API"


# 4. Skill Matching Agent
class SkillMatchingInput(BaseModel):
    issue_title: str
    issue_body: Optional[str] = ""
    repository_name: str
    user_experience: str = "Beginner"  # Beginner, Intermediate, Advanced
    preferred_languages: List[str] = Field(default_factory=lambda: ["Python", "TypeScript"])
    learning_goals: Optional[str] = None
    available_hours_per_week: Optional[int] = 5


class SkillMatchingOutput(BaseModel):
    contributor_level: str
    suitability_assessment: str  # Excellent, Moderate, Challenging
    suitability_reasons: List[str]
    required_skills: List[str]
    missing_prerequisites: List[str]
    recommended_prep_steps: List[str]
    estimated_difficulty: str
    uncertainty_note: str


# 5. Contribution Planning Agent
class ContributionPlanningInput(BaseModel):
    issue_title: str
    repository_name: str
    issue_url: str
    understanding: Optional[Dict[str, Any]] = None
    repo_context: Optional[Dict[str, Any]] = None
    skill_match: Optional[Dict[str, Any]] = None


class PlanTask(BaseModel):
    id: str
    title: str
    phase: str  # preparation, investigation, implementation, testing, pr
    description: str
    is_hypothesis: bool = False
    dependencies: List[str] = Field(default_factory=list)
    completed: bool = False


class ContributionPlanningOutput(BaseModel):
    issue_title: str
    repository_name: str
    roadmap_tasks: List[PlanTask]
    key_risks: List[str]
    verification_criteria: List[str]


# 6. Test Strategy Agent
class TestStrategyInput(BaseModel):
    __test__ = False
    issue_title: str
    issue_body: Optional[str] = ""
    repository_name: str
    verified_files: List[str] = Field(default_factory=list)


class TestCaseSuggestion(BaseModel):
    __test__ = False
    name: str
    purpose: str
    expected_result: str
    test_type: str = "Unit"  # Unit, Integration, Manual Reproduction


class TestStrategyOutput(BaseModel):
    __test__ = False
    suggested_test_framework: str
    reproduction_steps: List[str]
    test_cases: List[TestCaseSuggestion]
    edge_cases_to_consider: List[str]
    success_indicators: List[str]
    failure_indicators: List[str]


# 7. PR Readiness Agent
class PRReadinessInput(BaseModel):
    issue_title: str
    repository_name: str
    issue_url: str
    completed_task_ids: List[str] = Field(default_factory=list)
    total_task_count: int = 0
    understanding: Optional[Dict[str, Any]] = None
    test_strategy: Optional[Dict[str, Any]] = None


class PRReadinessOutput(BaseModel):
    readiness_score_pct: int
    readiness_level: str  # "Ready for Review", "Needs Testing", "In Progress", "Needs Setup"
    proposed_pr_title: str
    proposed_pr_body: str
    pr_checklist: List[str]
    known_limitations: List[str]
    unresolved_questions: List[str]
    disclaimer: str = "Readiness assessment only. Does not guarantee maintainer approval."


# Workflow Run Request & Response
class WorkflowRunRequest(BaseModel):
    target_agent: str = "orchestrator"  # "orchestrator" or agent ID
    agent_name: Optional[str] = None  # alias for target_agent
    issue_title: Optional[str] = None
    issue_body: Optional[str] = ""
    repository_name: Optional[str] = None
    issue_url: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    user_experience: str = "Beginner"
    user_skill_level: Optional[str] = None
    preferred_languages: List[str] = Field(default_factory=list)
    learning_goals: Optional[str] = None
    search_params: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.agent_name and self.target_agent == "orchestrator":
            self.target_agent = self.agent_name
        if self.user_skill_level and self.user_experience == "Beginner":
            self.user_experience = self.user_skill_level


class WorkflowRunResponse(BaseModel):
    run_id: str
    status: str
    target_agent: str
    created_at: float
    message: str
    record: Optional[Dict[str, Any]] = None
