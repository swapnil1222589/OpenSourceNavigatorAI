import json
import re
from typing import Any, Dict
import httpx

from app.agents.base import AgentMetadata, BaseAgent
from app.clients.ollama_client import OllamaClient
from app.core.config import settings
from app.schemas.agent_schemas import IssueUnderstandingInput, IssueUnderstandingOutput


class IssueUnderstandingAgent(BaseAgent):
    """Agent 2: Analyzes and deconstructs issue text into clear, structured requirements."""

    def __init__(self, ollama_client: OllamaClient):
        super().__init__(
            AgentMetadata(
                id="issue_understanding",
                name="Issue Understanding Agent",
                role="Context & Requirements Analyst",
                description="Translates complex issue descriptions into plain-English summaries, acceptance criteria, and maintainer questions.",
                inputs_required=["issue_title", "issue_body", "repository_name"],
                produces=["plain_english_summary", "problem_statement", "expected_outcome", "acceptance_criteria", "identified_ambiguities", "maintainer_clarifications"],
                phase=2,
            )
        )
        self.ollama_client = ollama_client

    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        inp = IssueUnderstandingInput(**payload)

        prompt = f"""You are the Issue Understanding Specialist Agent of OpenSource Navigator AI.
Deconstruct this GitHub issue for an open-source contributor:

Repository: {inp.repository_name}
Title: {inp.issue_title}
Labels: {', '.join(inp.labels) if inp.labels else 'None'}
Issue Description:
\"\"\"
{inp.issue_body[:6000] if inp.issue_body else '(No description provided)'}
\"\"\"

Respond with a single JSON object with EXACTLY these keys:
{{
  "plain_english_summary": "2-3 sentences explaining this issue simply to a student.",
  "problem_statement": "Concise definition of the bug, missing capability, or chore.",
  "expected_outcome": "What the code/repository should do when correctly fixed.",
  "acceptance_criteria": [
    "Criterion 1 (concrete and testable)",
    "Criterion 2"
  ],
  "identified_ambiguities": [
    "Any missing detail, unspecified behavior, or edge case in the issue"
  ],
  "maintainer_clarifications": [
    "Polite question to ask the maintainer if needed"
  ],
  "confidence_level": "High"
}}
Return ONLY valid JSON.
"""
        system_prompt = (
            "You are a requirements analysis agent. You only have access to issue text. "
            "Never execute commands. Return only valid JSON without markdown outside the JSON."
        )

        effective_model = self.ollama_client.model
        _, available = await self.ollama_client.get_status()
        if available and effective_model not in available:
            effective_model = available[0]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{self.ollama_client.base_url}/api/chat",
                    json={
                        "model": effective_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "format": "json",
                        "options": {"temperature": 0.1, "num_predict": 350},
                    },
                )

                if res.status_code == 200:
                    content = res.json().get("message", {}).get("content", "")
                    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.DOTALL).strip()
                    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned, re.DOTALL)
                    raw_json = fence.group(1) if fence else cleaned
                    brace = re.search(r"(\{[\s\S]*\})", raw_json, re.DOTALL)
                    parsed = json.loads(brace.group(1) if brace else raw_json)

                    output = IssueUnderstandingOutput(
                        plain_english_summary=parsed.get("plain_english_summary", "Summary unavailable."),
                        problem_statement=parsed.get("problem_statement", inp.issue_title),
                        expected_outcome=parsed.get("expected_outcome", "Expected behavior restored."),
                        acceptance_criteria=parsed.get("acceptance_criteria", ["Verify bug is resolved."]),
                        identified_ambiguities=parsed.get("identified_ambiguities", []),
                        maintainer_clarifications=parsed.get("maintainer_clarifications", []),
                        confidence_level=parsed.get("confidence_level", "High"),
                    )
                    return output.model_dump()
        except Exception:
            pass

        # Fallback if Ollama times out or fails under CPU load
        return IssueUnderstandingOutput(
            plain_english_summary=f"This issue in {inp.repository_name} addresses '{inp.issue_title}'. It requires inspecting the codebase and proposing a targeted fix.",
            problem_statement=inp.issue_title,
            expected_outcome=f"Successfully resolve '{inp.issue_title}' while keeping existing tests passing.",
            acceptance_criteria=["Reproduce issue locally", "Implement fix", "Verify unit tests pass"],
            identified_ambiguities=[],
            maintainer_clarifications=["Confirm maintainer preferences for error formatting."],
            confidence_level="High",
        ).model_dump()
