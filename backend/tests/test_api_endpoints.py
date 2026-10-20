from unittest.mock import AsyncMock, patch
from app.schemas.issue import IssueItem, IssueSearchResponse
from app.schemas.analysis import AnalysisResult, DifficultyLevel, SuggestedAreaHypothesis


def test_issues_api_validation(client):
    # Test per_page bounds
    resp = client.get("/api/v1/issues?per_page=0")
    assert resp.status_code == 422  # validation error (ge=1)

    resp = client.get("/api/v1/issues?per_page=100")
    assert resp.status_code == 422  # validation error (le=50)

    # Test invalid sort
    resp = client.get("/api/v1/issues?sort=invalid_sort")
    assert resp.status_code == 422


def test_issues_api_success(client):
    mock_resp = IssueSearchResponse(
        total_count=1,
        items=[
            IssueItem(
                id=999,
                number=42,
                title="Fix bug in parser",
                body="Details",
                html_url="https://github.com/foo/bar/issues/42",
                state="open",
                created_at="2026-10-01T00:00:00Z",
                updated_at="2026-10-02T00:00:00Z",
                comments_count=3,
                repository_name="foo/bar",
                repository_url="https://github.com/foo/bar",
                labels=[],
            )
        ],
        rate_limited=False,
    )

    with patch("app.clients.github_client.GitHubClient.search_issues", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_resp
        resp = client.get("/api/v1/issues?q=parser&language=python")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Fix bug in parser"


def test_analyze_api_validation(client):
    # Missing required issue_title
    resp = client.post("/api/v1/analyze", json={
        "repository_name": "foo/bar",
        "issue_url": "https://github.com/foo/bar/issues/1"
    })
    assert resp.status_code == 422

    # Title too short
    resp = client.post("/api/v1/analyze", json={
        "issue_title": "a",
        "repository_name": "foo/bar",
        "issue_url": "https://github.com/foo/bar/issues/1"
    })
    assert resp.status_code == 422


def test_analyze_api_success(client):
    mock_result = AnalysisResult(
        issue_title="Fix parser bug",
        repository_name="foo/bar",
        issue_url="https://github.com/foo/bar/issues/42",
        plain_english_summary="This fixes parser crashes.",
        problem_description="Unexpected token error.",
        expected_outcome="Parser gracefully handles tokens.",
        possible_skills=["Python", "AST"],
        estimated_difficulty=DifficultyLevel.INTERMEDIATE,
        difficulty_rationale="Requires understanding AST visitor pattern.",
        investigation_plan=["Reproduce with sample input"],
        suggested_inspection_areas=[
            SuggestedAreaHypothesis(
                area_or_path="foo/parser.py",
                rationale="Houses the AST parser logic",
                is_hypothesis=True,
            )
        ],
        testing_strategy=["Add unit tests in tests/test_parser.py"],
        common_pitfalls=["Edge cases with nested blocks"],
        maintainer_questions=["Should unsupported syntax raise custom exception?"],
        verification_checklist=["Run pytest tests/"],
        model_used="deepseek-r1:8b",
    )

    with patch("app.clients.ollama_client.OllamaClient.analyze_issue", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_result
        resp = client.post("/api/v1/analyze", json={
            "issue_title": "Fix parser bug",
            "repository_name": "foo/bar",
            "issue_url": "https://github.com/foo/bar/issues/42",
            "issue_body": "Unexpected token error occurs when parsing...",
            "labels": ["bug"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["estimated_difficulty"] == "Intermediate"
        assert data["plain_english_summary"] == "This fixes parser crashes."
        assert len(data["suggested_inspection_areas"]) == 1
        assert data["suggested_inspection_areas"][0]["is_hypothesis"] is True


def test_analyze_api_service_unavailable(client):
    with patch("app.clients.ollama_client.OllamaClient.analyze_issue", side_effect=ConnectionError("Ollama offline")):
        resp = client.post("/api/v1/analyze", json={
            "issue_title": "Fix parser bug",
            "repository_name": "foo/bar",
            "issue_url": "https://github.com/foo/bar/issues/42",
        })
        assert resp.status_code == 503
        assert "Ollama offline" in resp.json()["detail"]
