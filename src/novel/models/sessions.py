"""Sessions domain Pydantic models — Session logs, agent run log, metrics snapshots."""

import json

from pydantic import BaseModel, field_validator


class SessionLog(BaseModel):
    """Represents a row in the session_logs table (migration 019).

    carried_forward and chapters_touched are JSON TEXT in SQLite.
    They are parsed to Python lists on read and re-encoded via to_db_dict().
    """

    id: int | None = None
    started_at: str | None = None
    closed_at: str | None = None
    summary: str | None = None
    carried_forward: list[str] | None = None
    word_count_delta: int = 0
    chapters_touched: list[int] | None = None
    notes: str | None = None

    @field_validator("carried_forward", mode="before")
    @classmethod
    def parse_carried_forward(cls, v: object) -> list[str] | None:
        """Parse JSON string to list[str] if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            parsed = json.loads(v)
            return parsed
        return v  # type: ignore[return-value]

    @field_validator("chapters_touched", mode="before")
    @classmethod
    def parse_chapters_touched(cls, v: object) -> list[int] | None:
        """Parse JSON string to list[int] if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            parsed = json.loads(v)
            return parsed
        return v  # type: ignore[return-value]

    def to_db_dict(self) -> dict:
        """Return a dict with JSON fields re-encoded as TEXT for SQLite INSERT/UPDATE."""
        d = self.model_dump()
        d["carried_forward"] = json.dumps(self.carried_forward) if self.carried_forward is not None else None
        d["chapters_touched"] = json.dumps(self.chapters_touched) if self.chapters_touched is not None else None
        return d


class AgentRunLog(BaseModel):
    """Represents a row in the agent_run_log table (migration 019)."""

    id: int | None = None
    session_id: int | None = None
    agent_name: str
    tool_name: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    duration_ms: int | None = None
    success: bool = True
    error_message: str | None = None
    ran_at: str | None = None

    @field_validator("success", mode="before")
    @classmethod
    def coerce_bool(cls, v: object) -> bool:
        """Coerce SQLite INTEGER 0/1 to bool."""
        if isinstance(v, int):
            return bool(v)
        return v  # type: ignore[return-value]


class ProjectMetricsSnapshot(BaseModel):
    """Represents a row in the project_metrics_snapshots table (migration 020)."""

    id: int | None = None
    snapshot_at: str | None = None
    word_count: int = 0
    chapter_count: int = 0
    scene_count: int = 0
    character_count: int = 0
    session_count: int = 0
    notes: str | None = None


class PovBalanceSnapshot(BaseModel):
    """Represents a row in the pov_balance_snapshots table (migration 020)."""

    id: int | None = None
    snapshot_at: str | None = None
    chapter_id: int | None = None
    character_id: int | None = None
    chapter_count: int = 0
    word_count: int = 0


class OpenQuestion(BaseModel):
    """Represents a row in the open_questions table (migration 021)."""

    id: int | None = None
    question: str
    domain: str = "general"
    session_id: int | None = None
    answer: str | None = None
    answered_at: str | None = None
    priority: str = "normal"
    notes: str | None = None
    created_at: str | None = None


class DecisionsLogEntry(BaseModel):
    """Represents a row in the decisions_log table (migration 021)."""

    id: int | None = None
    decision_type: str = "plot"
    description: str
    rationale: str | None = None
    alternatives: str | None = None
    session_id: int | None = None
    chapter_id: int | None = None
    created_at: str | None = None
