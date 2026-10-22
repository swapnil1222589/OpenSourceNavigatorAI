import asyncio
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.agents.base import AgentMetadata, AgentRunStatus, WorkflowRunRecord
from app.agents.registry import registry
from app.agents.task_store import task_store
from app.clients.github_client import GitHubClient
from app.schemas.agent_schemas import WorkflowRunRequest, WorkflowRunResponse

router = APIRouter()
github_client = GitHubClient()


@router.get("/agents", response_model=List[AgentMetadata], summary="List registered specialist agents")
async def list_agents() -> List[AgentMetadata]:
    """Retrieve metadata, descriptions, and phases for all registered specialist agents."""
    return registry.list_metadata()


@router.get("/agents/runs", response_model=List[WorkflowRunRecord], summary="List recent agent workflow runs")
async def list_runs(limit: int = Query(20, ge=1, le=50)) -> List[WorkflowRunRecord]:
    """Retrieve recent task execution history with status, timings, and durations."""
    return task_store.list_runs(limit=limit)


async def _execute_workflow_task(run_id: str, payload: Dict[str, Any]):
    orchestrator = registry.get_orchestrator()
    try:
        await orchestrator.execute(payload, {"run_id": run_id})
    except Exception as e:
        task_store.finish_run(run_id=run_id, status=AgentRunStatus.FAILED, error=str(e))


@router.post("/agents/runs", response_model=WorkflowRunResponse, status_code=status.HTTP_202_ACCEPTED, summary="Trigger agent or full workflow run")
async def start_run(req: WorkflowRunRequest, background_tasks: BackgroundTasks) -> WorkflowRunResponse:
    """Trigger an individual specialist agent or coordinate the full multi-agent pipeline."""
    target = req.target_agent
    if target != "orchestrator" and not registry.get_agent(target):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{target}' is not registered.",
        )

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    issue_context = {
        "title": req.issue_title,
        "repo": req.repository_name,
        "url": req.issue_url,
    }

    task_store.create_run(
        run_id=run_id,
        target_agent=target,
        issue_context=issue_context,
        user_skill_level=req.user_experience,
    )

    payload = req.model_dump()
    background_tasks.add_task(_execute_workflow_task, run_id, payload)

    return WorkflowRunResponse(
        run_id=run_id,
        status="queued",
        target_agent=target,
        created_at=task_store.get_run(run_id).created_at,  # type: ignore
        message=f"Agent run '{run_id}' initiated for target '{target}'.",
    )


@router.get("/agents/runs/{run_id}", response_model=WorkflowRunRecord, summary="Get run status and output")
async def get_run_status(run_id: str) -> WorkflowRunRecord:
    """Poll execution state, per-agent node status, and accumulated outputs for a run."""
    record = task_store.get_run(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return record


@router.post("/agents/runs/{run_id}/retry", response_model=WorkflowRunResponse, summary="Retry a failed run")
async def retry_run(run_id: str, background_tasks: BackgroundTasks) -> WorkflowRunResponse:
    """Retry an existing run if failed or cancelled."""
    record = task_store.get_run(run_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found.")

    if record.status == AgentRunStatus.RUNNING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run is already in progress.")

    record.status = AgentRunStatus.QUEUED
    record.error = None
    payload = {
        "target_agent": record.target_agent,
        "issue_title": (record.issue_context or {}).get("title"),
        "repository_name": (record.issue_context or {}).get("repo"),
        "issue_url": (record.issue_context or {}).get("url"),
        "user_experience": record.user_skill_level,
    }
    background_tasks.add_task(_execute_workflow_task, run_id, payload)

    return WorkflowRunResponse(
        run_id=run_id,
        status="queued",
        target_agent=record.target_agent,
        created_at=record.created_at,
        message=f"Run '{run_id}' re-queued for execution.",
    )


@router.post("/agents/runs/{run_id}/cancel", summary="Cancel a running task")
async def cancel_run(run_id: str) -> Dict[str, Any]:
    """Request graceful cancellation of a running agent workflow."""
    success = task_store.cancel_run(run_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found.")
    return {"run_id": run_id, "status": "cancelled", "message": "Cancellation flag set."}


# Repository Explorer API
@router.get("/repository/explore", summary="Explore repository structure")
async def explore_repository(repo: str = Query(..., description="Repository in owner/name format")) -> Dict[str, Any]:
    """Retrieve verified file hierarchy and contributing guidelines for the repository."""
    return await github_client.get_repo_context(repo)


@router.get("/repository/file", summary="Inspect safe repository file content")
async def inspect_repository_file(
    repo: str = Query(..., description="Repository in owner/name format"),
    path: str = Query(..., description="File path within the repository"),
) -> Dict[str, Any]:
    """Safely fetch and inspect text file contents from GitHub within strict size bounds."""
    return await github_client.get_file_content(repo, path)
