from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .schemas import (
    ChatRequest,
    GovernanceRequest,
    TicketTestRequest,
)
from .services import ChatService, GovernanceService, TicketService


def create_app() -> FastAPI:
    settings = get_settings()
    chat_service = ChatService(settings)
    ticket_service = TicketService(settings)
    governance_service = GovernanceService(settings)

    api = FastAPI(title="NeoIA Security API", version="0.1.0")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.get("/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "services": {
                "chat": {
                    "bedrock_enabled": settings.bedrock_enabled,
                    "local_rag_enabled": settings.local_rag_enabled,
                    "public_doc_lookup_enabled": settings.public_doc_lookup_enabled,
                },
                "tickets": {"mode": settings.ticket_api_mode},
                "governance": {
                    "privacy_mode": settings.governance_privacy_mode,
                    "report_dir": str(settings.governance_report_dir),
                },
            },
        }

    @api.get("/api/technical-copilot/conversations")
    async def list_conversations() -> list[dict]:
        return chat_service.list_conversations()

    @api.get("/api/technical-copilot/conversations/{conversation_id}/messages")
    async def list_conversation_messages(conversation_id: str) -> dict:
        return {"messages": chat_service.list_messages(conversation_id)}

    @api.post("/api/chat")
    @api.post("/api/technical-copilot/chat")
    async def chat(request: ChatRequest) -> dict:
        question = request.resolved_question
        if not question:
            raise HTTPException(status_code=400, detail="Pergunta não informada.")
        response = chat_service.ask(question)
        return response.model_dump()

    @api.post("/api/tickets/test")
    async def create_ticket(request: TicketTestRequest) -> dict:
        try:
            return ticket_service.create_test_ticket(dry_run=request.dry_run).model_dump()
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/governance/preview")
    async def governance_preview(request: GovernanceRequest) -> dict:
        return governance_service.build_preview(
            days=request.days,
            events_per_day=request.events_per_day,
        ).model_dump()

    @api.post("/api/governance/report")
    async def governance_report(request: GovernanceRequest) -> dict:
        return governance_service.build_report(
            days=request.days,
            events_per_day=request.events_per_day,
        ).model_dump()

    return api


app = create_app()
