import asyncio
import time
from typing import Any, Dict, Optional
from app.agents.base import AgentMetadata, AgentRunStatus, BaseAgent
from app.agents.task_store import task_store
from app.schemas.agent_schemas import WorkflowRunRequest


class OrchestratorAgent(BaseAgent):
    """Agent 8: Coordinates specialist agents in a deterministic, observable execution pipeline."""

    def __init__(self, agents_map: Dict[str, BaseAgent]):
        super().__init__(
            AgentMetadata(
                id="orchestrator",
                name="Workflow Orchestrator",
                role="Pipeline Dispatcher & Conductor",
                description="Coordinates specialist agents deterministically, passes validated context, manages cancellation, and records stage transitions.",
                inputs_required=["target_agent"],
                produces=["combined_result", "agents_state", "duration_ms"],
                phase=0,
                is_autonomous=False,
            )
        )
        self.agents_map = agents_map

    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow for run_id."""
        run_id = context.get("run_id", f"run-{int(time.time())}")
        target = payload.get("target_agent", "orchestrator")

        if target != "orchestrator" and target in self.agents_map:
            # Run single agent
            return await self._run_single_agent(target, payload, context)

        # Run complete pipeline
        return await self._run_pipeline(run_id, payload)

    async def _run_single_agent(self, agent_id: str, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        run_id = context.get("run_id", f"run-{int(time.time())}")
        agent = self.agents_map[agent_id]
        t0 = time.time()

        task_store.update_agent_state(
            run_id=run_id,
            agent_id=agent.metadata.id,
            agent_name=agent.metadata.name,
            status=AgentRunStatus.RUNNING,
            started_at=t0,
            input_summary=f"Direct run of {agent.metadata.name}",
        )

        try:
            res = await agent.execute(payload, context)
            duration = round((time.time() - t0) * 1000, 2)
            task_store.update_agent_state(
                run_id=run_id,
                agent_id=agent.metadata.id,
                agent_name=agent.metadata.name,
                status=AgentRunStatus.COMPLETED,
                completed_at=time.time(),
                duration_ms=duration,
                output_data=res,
            )
            task_store.finish_run(run_id=run_id, status=AgentRunStatus.COMPLETED, combined_result={agent_id: res})
            return res
        except Exception as e:
            duration = round((time.time() - t0) * 1000, 2)
            task_store.update_agent_state(
                run_id=run_id,
                agent_id=agent.metadata.id,
                agent_name=agent.metadata.name,
                status=AgentRunStatus.FAILED,
                completed_at=time.time(),
                duration_ms=duration,
                error=str(e),
            )
            task_store.finish_run(run_id=run_id, status=AgentRunStatus.FAILED, error=str(e))
            raise

    async def _run_pipeline(self, run_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        combined_result: Dict[str, Any] = {}
        issue_title = payload.get("issue_title") or "General Open Source Task"
        issue_body = payload.get("issue_body") or ""
        repo_name = payload.get("repository_name") or ""
        issue_url = payload.get("issue_url") or ""
        labels = payload.get("labels") or []
        user_experience = payload.get("user_experience") or "Beginner"
        preferred_languages = payload.get("preferred_languages") or ["Python", "TypeScript"]
        learning_goals = payload.get("learning_goals")

        # Ordered pipeline phases
        pipeline_sequence = [
            "issue_understanding",
            "repository_context",
            "skill_matching",
            "contribution_planning",
            "test_strategy",
            "pr_readiness",
        ]

        for agent_id in pipeline_sequence:
            if task_store.is_cancelled(run_id):
                task_store.finish_run(run_id=run_id, status=AgentRunStatus.CANCELLED, combined_result=combined_result)
                return combined_result

            agent = self.agents_map.get(agent_id)
            if not agent:
                continue

            t0 = time.time()
            task_store.update_agent_state(
                run_id=run_id,
                agent_id=agent.metadata.id,
                agent_name=agent.metadata.name,
                status=AgentRunStatus.RUNNING,
                started_at=t0,
                input_summary=f"Running phase {agent.metadata.phase}: {agent.metadata.name}",
            )

            # Build inputs with accumulated context
            agent_payload: Dict[str, Any] = {
                "issue_title": issue_title,
                "issue_body": issue_body,
                "repository_name": repo_name,
                "issue_url": issue_url,
                "labels": labels,
                "user_experience": user_experience,
                "preferred_languages": preferred_languages,
                "learning_goals": learning_goals,
            }

            if agent_id == "contribution_planning":
                agent_payload["understanding"] = combined_result.get("issue_understanding")
                agent_payload["repo_context"] = combined_result.get("repository_context")
                agent_payload["skill_match"] = combined_result.get("skill_matching")
            elif agent_id == "test_strategy":
                repo_ctx = combined_result.get("repository_context") or {}
                agent_payload["verified_files"] = repo_ctx.get("verified_files", [])
            elif agent_id == "pr_readiness":
                agent_payload["understanding"] = combined_result.get("issue_understanding")
                agent_payload["test_strategy"] = combined_result.get("test_strategy")
                plan_res = combined_result.get("contribution_planning") or {}
                tasks = plan_res.get("roadmap_tasks") or []
                agent_payload["total_task_count"] = len(tasks)
                agent_payload["completed_task_ids"] = []

            try:
                res = await agent.execute(agent_payload, {"run_id": run_id})
                duration = round((time.time() - t0) * 1000, 2)
                task_store.update_agent_state(
                    run_id=run_id,
                    agent_id=agent.metadata.id,
                    agent_name=agent.metadata.name,
                    status=AgentRunStatus.COMPLETED,
                    completed_at=time.time(),
                    duration_ms=duration,
                    output_data=res,
                )
                combined_result[agent_id] = res
            except Exception as e:
                duration = round((time.time() - t0) * 1000, 2)
                task_store.update_agent_state(
                    run_id=run_id,
                    agent_id=agent.metadata.id,
                    agent_name=agent.metadata.name,
                    status=AgentRunStatus.FAILED,
                    completed_at=time.time(),
                    duration_ms=duration,
                    error=str(e),
                )
                # Keep partial results and mark run as failed
                task_store.finish_run(run_id=run_id, status=AgentRunStatus.FAILED, combined_result=combined_result, error=str(e))
                return combined_result

        task_store.finish_run(run_id=run_id, status=AgentRunStatus.COMPLETED, combined_result=combined_result)
        return combined_result
