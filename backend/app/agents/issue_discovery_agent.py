from typing import Any, Dict
from app.agents.base import AgentMetadata, BaseAgent
from app.clients.github_client import GitHubClient
from app.schemas.agent_schemas import IssueDiscoveryInput, IssueDiscoveryOutput


class IssueDiscoveryAgent(BaseAgent):
    """Agent 1: Discovers and normalizes real public GitHub issues."""

    def __init__(self, github_client: GitHubClient):
        super().__init__(
            AgentMetadata(
                id="issue_discovery",
                name="Issue Discovery Agent",
                role="Repository Issue Scout",
                description="Queries GitHub REST API, excludes PRs, applies filters, and normalizes real issues.",
                inputs_required=["query", "language", "label", "repo", "page", "per_page"],
                produces=["total_count", "items", "page", "total_pages"],
                phase=1,
            )
        )
        self.github_client = github_client

    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        inp = IssueDiscoveryInput(**payload)
        resp = await self.github_client.search_issues(
            query=inp.query,
            language=inp.language,
            label=inp.label,
            repo=inp.repo,
            page=inp.page,
            per_page=inp.per_page,
            sort=inp.sort,
        )

        output = IssueDiscoveryOutput(
            total_count=resp.total_count,
            items=resp.items,
            page=resp.page,
            per_page=resp.per_page,
            total_pages=resp.total_pages,
            rate_limited=resp.rate_limited,
            source="GitHub REST API (is:issue, state:open)",
        )
        return output.model_dump()
