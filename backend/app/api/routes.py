from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.clients.github_client import GitHubClient
from app.clients.ollama_client import OllamaClient
from app.core.config import settings
from app.schemas.analysis import AnalysisResult, AnalyzeRequest
from app.schemas.issue import IssueSearchResponse

router = APIRouter()
github_client = GitHubClient()
ollama_client = OllamaClient()


@router.get("/health", summary="Backend & Integration Health Check")
async def health_check() -> Dict[str, Any]:
    """Check health status of the backend and external integrations. Does not leak credentials."""
    ollama_ok, models = await ollama_client.get_status()
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ollama": {
            "connected": ollama_ok,
            "configured_model": settings.OLLAMA_MODEL,
            "available_models": models,
        },
        "github": {
            "token_configured": bool(settings.GITHUB_TOKEN),
        },
    }


@router.get(
    "/issues",
    response_model=IssueSearchResponse,
    summary="Search real public GitHub issues",
)
async def search_issues(
    q: str = Query("", description="Search keywords, repository name, or topic"),
    language: Optional[str] = Query(None, description="Programming language filter (e.g., python, typescript)"),
    label: Optional[str] = Query(None, description="Issue label filter (e.g., good first issue, help wanted)"),
    repo: Optional[str] = Query(None, description="Target repository filter (e.g., fastapi/fastapi)"),
    page: int = Query(1, ge=1, le=100, description="Page number (1 to 100)"),
    per_page: int = Query(15, ge=1, le=50, description="Results per page (1 to 50)"),
    sort: str = Query("updated", pattern="^(updated|created|comments)$", description="Sort order"),
) -> IssueSearchResponse:
    """Discover real public GitHub issues (pull requests excluded) matching query filters."""
    return await github_client.search_issues(
        query=q,
        language=language,
        label=label,
        repo=repo,
        page=page,
        per_page=per_page,
        sort=sort,
    )


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Analyze GitHub issue with repository-aware grounding",
)
async def analyze_issue(payload: AnalyzeRequest) -> AnalysisResult:
    """Analyze an issue's context using Ollama, grounded with verified repository layout and tailored to contributor skill level."""
    try:
        # Fetch repository context (top files and contributing guidelines)
        repo_context = await github_client.get_repo_context(payload.repository_name)
        return await ollama_client.analyze_issue(payload, repo_context=repo_context)
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI model produced an unparseable response: {str(e)}. Please retry the analysis.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during AI analysis: {str(e)}",
        )
