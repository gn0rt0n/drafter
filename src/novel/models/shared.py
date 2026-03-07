"""Shared error contract types returned by MCP tools."""

from pydantic import BaseModel


class NotFoundResponse(BaseModel):
    """Returned by MCP tools when a record is not found. Never raise — return this."""
    not_found_message: str


class ValidationFailure(BaseModel):
    """Returned by MCP tools on validation failure. Never raise — return this."""
    is_valid: bool = False
    errors: list[str]


class GateViolation(BaseModel):
    """Returned by prose-phase tools when architecture gate is not certified."""
    requires_action: str
