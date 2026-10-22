import json
import re
from typing import Any, Dict
import httpx

from app.agents.base import AgentMetadata, BaseAgent
from app.clients.ollama_client import OllamaClient
from app.schemas.agent_schemas import ContributionPlanningInput, ContributionPlanningOutput, PlanTask


class ContributionPlanningAgent(BaseAgent):
    """Agent 5: Structures the issue into a chronological, step-by-step contribution roadmap."""

    def __init__(self, ollama_client: OllamaClient):
        super().__init__(
            AgentMetadata(
                id="contribution_planning",
                name="Contribution Planning Agent",
                role="Roadmap & Task Architect",
                description="Synthesizes understanding, repo structure, and skill match into an actionable sequential contribution plan.",
                inputs_required=["issue_title", "repository_name", "issue_url"],
                produces=["roadmap_tasks", "key_risks", "verification_criteria"],
                phase=5,
            )
        )
        self.ollama_client = ollama_client

    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        inp = ContributionPlanningInput(**payload)

        verified_files = []
        if inp.repo_context and "verified_files" in inp.repo_context:
            verified_files = inp.repo_context["verified_files"]

        prompt = f"""You are the Contribution Planning Specialist Agent of OpenSource Navigator AI.
Build a sequential, realistic contribution plan for:

Repository: {inp.repository_name}
Issue: {inp.issue_title}
Verified Repository Root Files: {', '.join(verified_files[:20]) if verified_files else 'None retrieved'}

Generate a structured roadmap with tasks across these phases:
- preparation (environment setup, fork, branch)
- investigation (locate relevant code, reproduce locally)
- implementation (modify code or docs safely)
- testing (run unit tests, verify edge cases)
- pr (clean commits, PR description, checklist)

Respond with a single JSON object with EXACTLY these keys:
{{
  "roadmap_tasks": [
    {{
      "id": "prep-1",
      "title": "Fork and clone repository locally",
      "phase": "preparation",
      "description": "Fork to personal account, git clone, and configure upstream remote.",
      "is_hypothesis": false
    }},
    {{
      "id": "inv-1",
      "title": "Inspect suspected code files",
      "phase": "investigation",
      "description": "Locate problem area in codebase and verify behavior.",
      "is_hypothesis": true
    }},
    {{
      "id": "impl-1",
      "title": "Implement targeted fix",
      "phase": "implementation",
      "description": "Apply minimal, well-documented changes.",
      "is_hypothesis": false
    }},
    {{
      "id": "test-1",
      "title": "Execute test suite locally",
      "phase": "testing",
      "description": "Run existing test suite and add tests for this issue.",
      "is_hypothesis": false
    }},
    {{
      "id": "pr-1",
      "title": "Submit clean Pull Request",
      "phase": "pr",
      "description": "Reference issue number, provide test output, and await review.",
      "is_hypothesis": false
    }}
  ],
  "key_risks": [
    "Breaking existing tests or introducing regressions"
  ],
  "verification_criteria": [
    "All unit tests pass cleanly and issue is reproduced then resolved."
  ]
}}
Return ONLY valid JSON.
"""
        effective_model = self.ollama_client.model
        _, available = await self.ollama_client.get_status()
        if available and effective_model not in available:
            effective_model = available[0]

        async with httpx.AsyncClient(timeout=self.ollama_client.timeout) as client:
            res = await client.post(
                f"{self.ollama_client.base_url}/api/chat",
                json={
                    "model": effective_model,
                    "messages": [
                        {"role": "system", "content": "You are a software contribution planning agent. Return only valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2, "num_predict": 1200},
                },
            )

            if res.status_code != 200:
                raise RuntimeError(f"Ollama returned HTTP {res.status_code}: {res.text}")

            content = res.json().get("message", {}).get("content", "")
            cleaned = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.DOTALL).strip()
            fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned, re.DOTALL)
            raw_json = fence.group(1) if fence else cleaned
            brace = re.search(r"(\{[\s\S]*\})", raw_json, re.DOTALL)
            parsed = json.loads(brace.group(1) if brace else raw_json)

            tasks = []
            for t in parsed.get("roadmap_tasks", []):
                tasks.append(
                    PlanTask(
                        id=t.get("id", f"task-{len(tasks)+1}"),
                        title=t.get("title", "Task"),
                        phase=t.get("phase", "implementation"),
                        description=t.get("description", ""),
                        is_hypothesis=t.get("is_hypothesis", False),
                    )
                )

            output = ContributionPlanningOutput(
                issue_title=inp.issue_title,
                repository_name=inp.repository_name,
                roadmap_tasks=tasks,
                key_risks=parsed.get("key_risks", ["Potential regressions in adjacent modules"]),
                verification_criteria=parsed.get("verification_criteria", ["All tests pass locally"]),
            )
            return output.model_dump()
