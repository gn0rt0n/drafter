"""Publishing domain Pydantic models — Publishing assets, submissions, research notes, documentation tasks."""

from pydantic import BaseModel


class PublishingAsset(BaseModel):
    """Represents a row in the publishing_assets table (migration 021)."""

    id: int | None = None
    asset_type: str = "query_letter"
    title: str
    content: str
    version: int = 1
    status: str = "draft"
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SubmissionEntry(BaseModel):
    """Represents a row in the submission_tracker table (migration 021)."""

    id: int | None = None
    asset_id: int | None = None
    agency_or_publisher: str
    submitted_at: str
    status: str = "pending"
    response_at: str | None = None
    response_notes: str | None = None
    follow_up_due: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ResearchNote(BaseModel):
    """Represents a row in the research_notes table (migration 021)."""

    id: int | None = None
    topic: str
    content: str
    source: str | None = None
    relevance: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DocumentationTask(BaseModel):
    """Represents a row in the documentation_tasks table (migration 021)."""

    id: int | None = None
    title: str
    description: str | None = None
    status: str = "pending"
    priority: str = "normal"
    due_chapter_id: int | None = None
    completed_at: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
