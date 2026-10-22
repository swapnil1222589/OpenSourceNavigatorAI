import json
import re
from typing import Any, Dict
import httpx

from app.agents.base import AgentMetadata, BaseAgent
from app.clients.ollama_client import OllamaClient
from app.schemas.agent_schemas import PRReadinessInput, PRReadinessOutput


class PRReadinessAgent(BaseAgent):
    """Agent 7: Evaluates readiness for pull request submission and drafts descriptive PR templates."""

    def __init__(self, ollama_client: OllamaClient):
        super().__init__(
            AgentMetadata(
                id="pr_readiness",
                name="PR Readiness Agent",
                role="Pull Request Auditor & Drafter",
                description="Checks task completion, drafts proposed PR descriptions with issue references, notes limitations, and provides readiness evaluation.",
                inputs_required=["issue_title", "repository_name", "issue_url"],
                produces=["readiness_score_pct", "readiness_level", "proposed_pr_title", "proposed_pr_body", "pr_checklist", "known_limitations", "unresolved_questions"],
                phase=7,
            )
        )
        self.ollama_client = ollama_client

    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        inp = PRReadinessInput(**payload)

        # Calculate progress
        completed_count = len(inp.completed_task_ids)
        total_count = max(inp.total_task_count, 1)
        score_pct = int((completed_count / total_count) * 100) if total_count > 0 else 0

        level = "In Progress"
        if score_pct >= 90:
            level = "Ready for Review"
        elif score_pct >= 50:
            level = "Needs Testing"
        elif score_pct < 20:
            level = "Needs Setup"

        prompt = f"""You are the PR Readiness Specialist Agent of OpenSource Navigator AI.
Draft a high-quality Pull Request description for:

Repository: {inp.repository_name}
Issue: {inp.issue_title}
Issue URL: {inp.issue_url}
Completion Progress: {score_pct}% ({completed_count}/{total_count} checklist tasks completed)

Respond with a single JSON object with EXACTLY these keys:
{{
  "proposed_pr_title": "fix: resolve {inp.issue_title[:60]}",
  "proposed_pr_body": "## Overview\\nBrief summary of changes.\\n\\n## Related Issue\\nCloses {inp.issue_url}\\n\\n## Changes Made\\n- Detailed list of modifications\\n\\n## Verification\\n- Tested locally with test suite",
  "pr_checklist": [
    "Tests added or updated",
    "Code formatted and linted",
    "Documentation updated if necessary"
  ],
  "known_limitations": [
    "Any caveat or edge case not covered"
  ],
  "unresolved_questions": [
    "Any question left for the maintainer review"
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
                        {"role": "system", "content": "You are a pull request review and documentation drafting agent. Return only valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2, "num_predict": 1000},
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

            output = PRReadinessOutput(
                readiness_score_pct=score_pct,
                readiness_level=level,
                proposed_pr_title=parsed.get("proposed_pr_title", f"fix: resolve {inp.issue_title}"),
                proposed_pr_body=parsed.get("proposed_pr_body", f"Resolves {inp.issue_url}"),
                pr_checklist=parsed.get("pr_checklist", ["Verify all tests pass", "Check branch formatting"]),
                known_limitations=parsed.get("known_limitations", []),
                unresolved_questions=parsed.get("unresolved_questions", []),
                disclaimer="Readiness assessment only. Does not guarantee maintainer approval.",
            )
            return output.model_dump()
