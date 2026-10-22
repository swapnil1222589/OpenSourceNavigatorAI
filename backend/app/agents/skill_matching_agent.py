import json
import re
from typing import Any, Dict
import httpx

from app.agents.base import AgentMetadata, BaseAgent
from app.clients.ollama_client import OllamaClient
from app.schemas.agent_schemas import SkillMatchingInput, SkillMatchingOutput


class SkillMatchingAgent(BaseAgent):
    """Agent 4: Compares contributor skill profile with issue demands to assess suitability."""

    def __init__(self, ollama_client: OllamaClient):
        super().__init__(
            AgentMetadata(
                id="skill_matching",
                name="Skill Matching Agent",
                role="Contributor Competency & Readiness Evaluator",
                description="Assesses alignment between contributor experience, languages, and issue demands. Explains prerequisites and prep steps.",
                inputs_required=["issue_title", "repository_name", "user_experience"],
                produces=["suitability_assessment", "suitability_reasons", "required_skills", "missing_prerequisites", "recommended_prep_steps", "estimated_difficulty"],
                phase=4,
            )
        )
        self.ollama_client = ollama_client

    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        inp = SkillMatchingInput(**payload)

        prompt = f"""You are the Skill Matching Specialist Agent of OpenSource Navigator AI.
Assess contributor readiness for this GitHub issue:

Repository: {inp.repository_name}
Issue Title: {inp.issue_title}
Issue Summary: {inp.issue_body[:2000] if inp.issue_body else '(No details)'}

Contributor Profile:
- Experience Level: {inp.user_experience}
- Preferred Languages: {', '.join(inp.preferred_languages) if inp.preferred_languages else 'General'}
- Learning Goals: {inp.learning_goals or 'Make first open-source contribution'}
- Available Hours: {inp.available_hours_per_week} hrs/week

Respond with a single JSON object with EXACTLY these keys:
{{
  "contributor_level": "{inp.user_experience}",
  "suitability_assessment": "Excellent",
  "suitability_reasons": [
    "Reason why this issue suits or challenges this contributor profile"
  ],
  "required_skills": [
    "Python", "Git", "Regex"
  ],
  "missing_prerequisites": [
    "Any technology or pattern the contributor should brush up on first"
  ],
  "recommended_prep_steps": [
    "Step 1 to prepare before coding"
  ],
  "estimated_difficulty": "{inp.user_experience}",
  "uncertainty_note": "Difficulty estimation is an approximation based on issue text without examining full commit history."
}}
Note: "suitability_assessment" must be one of: "Excellent", "Moderate", "Challenging".
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
                        {"role": "system", "content": "You are a developer skills evaluation agent. Return only valid JSON."},
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

            output = SkillMatchingOutput(
                contributor_level=inp.user_experience,
                suitability_assessment=parsed.get("suitability_assessment", "Moderate"),
                suitability_reasons=parsed.get("suitability_reasons", ["Matches general development skill level."]),
                required_skills=parsed.get("required_skills", ["Git", "GitHub"]),
                missing_prerequisites=parsed.get("missing_prerequisites", []),
                recommended_prep_steps=parsed.get("recommended_prep_steps", ["Review CONTRIBUTING.md"]),
                estimated_difficulty=parsed.get("estimated_difficulty", inp.user_experience),
                uncertainty_note=parsed.get("uncertainty_note", "Estimated based on issue text."),
            )
            return output.model_dump()
