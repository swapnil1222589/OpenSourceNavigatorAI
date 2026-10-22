import threading
import time
from typing import Dict, List, Optional
from app.agents.base import AgentExecutionRecord, AgentRunStatus, WorkflowRunRecord


class TaskStore:
    """Bounded, thread-safe in-memory store for agent workflow executions."""

    def __init__(self, max_runs: int = 50):
        self._max_runs = max_runs
        self._runs: Dict[str, WorkflowRunRecord] = {}
        self._cancelled_runs: set = set()
        self._lock = threading.Lock()

    def create_run(
        self,
        run_id: str,
        target_agent: str,
        issue_context: Optional[dict] = None,
        user_skill_level: str = "Beginner",
    ) -> WorkflowRunRecord:
        with self._lock:
            record = WorkflowRunRecord(
                run_id=run_id,
                target_agent=target_agent,
                status=AgentRunStatus.QUEUED,
                created_at=time.time(),
                issue_context=issue_context,
                user_skill_level=user_skill_level,
                agents_state={},
            )
            record.sync_aliases()
            self._runs[run_id] = record

            # Evict oldest if exceeding max_runs
            if len(self._runs) > self._max_runs:
                oldest_id = sorted(self._runs.keys(), key=lambda k: self._runs[k].created_at)[0]
                del self._runs[oldest_id]
                self._cancelled_runs.discard(oldest_id)

            return record

    def get_run(self, run_id: str) -> Optional[WorkflowRunRecord]:
        with self._lock:
            run = self._runs.get(run_id)
            if run:
                run.sync_aliases()
            return run

    def list_runs(self, limit: int = 20) -> List[WorkflowRunRecord]:
        with self._lock:
            runs = sorted(self._runs.values(), key=lambda r: r.created_at, reverse=True)
            for r in runs:
                r.sync_aliases()
            return runs[:limit]

    def update_agent_state(
        self,
        run_id: str,
        agent_id: str,
        agent_name: str,
        status: AgentRunStatus,
        started_at: Optional[float] = None,
        completed_at: Optional[float] = None,
        duration_ms: Optional[float] = None,
        input_summary: Optional[str] = None,
        output_data: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return

            current = run.agents_state.get(agent_id) or AgentExecutionRecord(
                agent_id=agent_id,
                agent_name=agent_name,
            )

            current.status = status
            if started_at is not None:
                current.started_at = started_at
            if completed_at is not None:
                current.completed_at = completed_at
            if duration_ms is not None:
                current.duration_ms = duration_ms
            if input_summary is not None:
                current.input_summary = input_summary
            if output_data is not None:
                current.output_data = output_data
            if error is not None:
                current.error = error

            run.agents_state[agent_id] = current
            # If any agent is running, mark run as running
            if status == AgentRunStatus.RUNNING and run.status != AgentRunStatus.CANCELLED:
                run.status = AgentRunStatus.RUNNING

            run.sync_aliases()

    def finish_run(
        self,
        run_id: str,
        status: AgentRunStatus,
        combined_result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return

            # Don't overwrite cancelled status unless explicit
            if run.status == AgentRunStatus.CANCELLED and status != AgentRunStatus.CANCELLED:
                return

            run.status = status
            run.completed_at = time.time()
            if run.created_at:
                run.duration_ms = round((run.completed_at - run.created_at) * 1000, 2)
            if combined_result is not None:
                run.combined_result = combined_result
            if error is not None:
                run.error = error

            run.sync_aliases()

    def cancel_run(self, run_id: str) -> bool:
        with self._lock:
            if run_id in self._runs:
                self._cancelled_runs.add(run_id)
                self._runs[run_id].status = AgentRunStatus.CANCELLED
                self._runs[run_id].sync_aliases()
                return True
            return False

    def is_cancelled(self, run_id: str) -> bool:
        with self._lock:
            return run_id in self._cancelled_runs


task_store = TaskStore()
