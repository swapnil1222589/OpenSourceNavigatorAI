import json
import re
from typing import Any, Dict
import httpx

from app.agents.base import AgentMetadata, BaseAgent
from app.clients.ollama_client import OllamaClient
from app.schemas.agent_schemas import TestCaseSuggestion, TestStrategyInput, TestStrategyOutput


class TestStrategyAgent(BaseAgent):
    """Agent 6: Formulates test cases, edge cases, and reproduction strategies."""
    __test__ = False

    def __init__(self, ollama_client: OllamaClient):
        super().__init__(
            AgentMetadata(
                id="test_strategy",
                name="Test Strategy Agent",
                role="Verification & QA Strategist",
                description="Devises reproduction steps, automated test case suggestions, framework recommendations, and edge case coverage.",
                inputs_required=["issue_title", "repository_name"],
                produces=["suggested_test_framework", "reproduction_steps", "test_cases", "edge_cases_to_consider", "success_indicators", "failure_indicators"],
                phase=6,
            )
        )
        self.ollama_client = ollama_client

    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        inp = TestStrategyInput(**payload)

        prompt = f"""You are the Test Strategy Specialist Agent of OpenSource Navigator AI.
Formulate a test and verification strategy for:

Repository: {inp.repository_name}
Issue Title: {inp.issue_title}
Issue Context: {inp.issue_body[:3000] if inp.issue_body else '(No details)'}
Known Files: {', '.join(inp.verified_files[:15]) if inp.verified_files else 'None retrieved'}

Respond with a single JSON object with EXACTLY these keys:
{{
  "suggested_test_framework": "pytest / Jest / Vitest / Go test",
  "reproduction_steps": [
    "Step 1 to reproduce the problem locally"
  ],
  "test_cases": [
    {{
      "name": "test_expected_behavior",
      "purpose": "Verify correct handling of standard inputs",
      "expected_result": "Produces valid output without exceptions",
      "test_type": "Unit"
    }}
  ],
  "edge_cases_to_consider": [
    "Boundary conditions, empty inputs, or null values"
  ],
  "success_indicators": [
    "Test suite exits with code 0"
  ],
  "failure_indicators": [
    "Traceback or assertion error observed"
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
                        {"role": "system", "content": "You are a QA and test automation specialist agent. Return only valid JSON."},
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

            test_cases = []
            for tc in parsed.get("test_cases", []):
                test_cases.append(
                    TestCaseSuggestion(
                        name=tc.get("name", "test_case"),
                        purpose=tc.get("purpose", "Validation"),
                        expected_result=tc.get("expected_result", "Pass"),
                        test_type=tc.get("test_type", "Unit"),
                    )
                )

            output = TestStrategyOutput(
                suggested_test_framework=parsed.get("suggested_test_framework", "Standard test framework"),
                reproduction_steps=parsed.get("reproduction_steps", ["Run test suite locally."]),
                test_cases=test_cases,
                edge_cases_to_consider=parsed.get("edge_cases_to_consider", []),
                success_indicators=parsed.get("success_indicators", ["Tests pass without error."]),
                failure_indicators=parsed.get("failure_indicators", ["Assertions fail."]),
            )
            return output.model_dump()
