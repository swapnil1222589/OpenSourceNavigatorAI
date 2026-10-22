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

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                        suggested_test_framework=parsed.get("suggested_test_framework", "pytest"),
                        reproduction_steps=parsed.get("reproduction_steps", ["Run test suite locally."]),
                        test_cases=test_cases,
                        edge_cases_to_consider=parsed.get("edge_cases_to_consider", []),
                        success_indicators=parsed.get("success_indicators", ["Tests pass without error."]),
                        failure_indicators=parsed.get("failure_indicators", ["Assertions fail."]),
                    )
                    return output.model_dump()
        except Exception:
            pass

        # Fallback test strategy if Ollama times out
        fallback_test = TestCaseSuggestion(
            name="test_reproduce_and_verify_fix",
            purpose="Assert that the reported issue is fixed without regressions",
            expected_result="Test passes with expected return value / exception",
            test_type="Unit",
        )
        return TestStrategyOutput(
            suggested_test_framework="pytest" if "flask" in inp.repository_name.lower() or "python" in inp.repository_name.lower() else "Jest / Vitest",
            reproduction_steps=[
                f"1. Run existing test suite in {inp.repository_name}",
                f"2. Trigger scenario described in '{inp.issue_title}'",
                "3. Assert expected output matches requirements",
            ],
            test_cases=[fallback_test],
            edge_cases_to_consider=["Boundary conditions and empty input values"],
            success_indicators=["All test suite assertions pass cleanly with 0 failures"],
            failure_indicators=["AssertionError or unexpected unhandled exception"],
        ).model_dump()
