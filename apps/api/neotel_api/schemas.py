from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    role: Literal["assistant", "user", "system"]
    content: str


class ChatRequest(BaseModel):
    question: str | None = None
    content: str | None = None
    message: str | None = None
    conversation_id: str | None = None
    conversationId: str | None = None
    messages: list[MessageIn] = Field(default_factory=list)

    @property
    def resolved_question(self) -> str:
        for candidate in (self.question, self.content, self.message):
            if candidate and candidate.strip():
                return candidate.strip()
        return ""


class ChatResponse(BaseModel):
    id: str
    role: Literal["assistant"] = "assistant"
    answer: str
    content: str
    timestamp: str
    mode: str
    local_sources: list[str] = Field(default_factory=list)
    public_sources: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: str
    title: str
    preview: str
    dateLabel: str
    timeLabel: str
    active: bool = False


class TicketTestRequest(BaseModel):
    dry_run: bool = True


class TicketTestResponse(BaseModel):
    ok: bool
    dry_run: bool
    mode: str
    payload: dict
    endpoint: str | None = None
    response: dict | str | None = None


class GovernanceRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=30)
    events_per_day: int = Field(default=50, ge=5, le=500)


class GovernancePreviewRow(BaseModel):
    timestamp: str
    principalId: str
    applicationName: str
    accessState: str
    authResult: str
    riskSignal: str
    source_ip: str = ""


class GovernancePreviewResponse(BaseModel):
    metadata: dict
    analysis: dict
    preview_rows: list[GovernancePreviewRow]
    recommendations: list[dict]
    privacy_issues: list[str]
    risk_score: int = 0
    events_per_day: dict = Field(default_factory=dict)


class GovernanceReportResponse(BaseModel):
    metadata: dict
    analysis: dict
    report_markdown: str
    recommendations: list[dict]
    privacy_issues: list[str]
    mode: str
