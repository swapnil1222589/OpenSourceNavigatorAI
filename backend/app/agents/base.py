from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time


class AgentRunStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"


class AgentMetadata(BaseModel):
    id: str
    name: str
    role: str
    description: str
    inputs_required: List[str]
    produces: List[str]
    phase: int
    is_autonomous: bool = True


class AgentExecutionRecord(BaseModel):
    agent_id: str
    agent_name: str
    status: AgentRunStatus = AgentRunStatus.IDLE
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    input_summary: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowRunRecord(BaseModel):
    run_id: str
    target_agent: str  # specific agent id or "orchestrator" for full workflow
    status: AgentRunStatus = AgentRunStatus.QUEUED
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    issue_context: Optional[Dict[str, Any]] = None
    user_skill_level: str = "Beginner"
    agents_state: Dict[str, AgentExecutionRecord] = Field(default_factory=dict)
    combined_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """Abstract base class for all specialist agents."""

    def __init__(self, metadata: AgentMetadata):
        self.metadata = metadata

    @abstractmethod
    async def execute(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent task and return a validated dictionary."""
        pass
