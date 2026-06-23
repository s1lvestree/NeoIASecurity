from __future__ import annotations

import asyncio
import logging

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .schemas import (
    ChatRequest,
    GovernanceReportRequest,
    GovernanceRequest,
    TicketFromChatRequest,
    TicketTestRequest,
)
from .services import ChatService, GovernanceService, TicketService
from .services.tickets import ZammadIntegrationError

logger = logging.getLogger(__name__)


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
        local_doc_exists = settings.local_rag_doc_path.is_file()
        local_doc_size = settings.local_rag_doc_path.stat().st_size if local_doc_exists else 0
        governance_health = {
            "governance_enabled": True,
            "fake_sta_logs_available": governance_service.fake_logs_available(),
            "report_generation_available": governance_service.report_generation_available(),
            "report_output_dir": str(settings.governance_report_dir),
            "privacy_mode": settings.governance_privacy_mode,
            "report_dir": str(settings.governance_report_dir),
        }
        return {
            "status": "ok",
            "bedrock_enabled": settings.bedrock_enabled,
            "bedrock_model_id": settings.bedrock_model_id,
            "local_rag_enabled": settings.local_rag_enabled,
            "configured_local_doc_path": settings.configured_local_doc_path,
            "resolved_local_doc_path": str(settings.local_rag_doc_path),
            "local_doc_exists": local_doc_exists,
            "local_doc_size_bytes": local_doc_size,
            "public_doc_lookup_enabled": settings.public_doc_lookup_enabled,
            "public_doc_urls_count": len(settings.public_doc_urls),
            "public_doc_timeout_seconds": settings.public_doc_timeout_seconds,
            "last_public_doc_error": chat_service.last_public_doc_error,
            "ticket_mode": settings.ticket_api_mode,
            "tickets": {
                "mode": settings.ticket_api_mode,
                "zammad_base_url_configured": bool(settings.zammad_base_url),
                "zammad_base_url": settings.zammad_base_url,
                "zammad_token_configured": bool(settings.zammad_api_token),
                "zammad_group": settings.zammad_group,
                "zammad_customer_email": settings.zammad_customer_email,
                "email_enabled": settings.email_enabled,
            },
            "governance": governance_health,
            "last_bedrock_error": chat_service.last_bedrock_error,
            "services": {
                "chat": {
                    "bedrock_enabled": settings.bedrock_enabled,
                    "bedrock_model_id": settings.bedrock_model_id,
                    "local_rag_enabled": settings.local_rag_enabled,
                    "configured_local_doc_path": settings.configured_local_doc_path,
                    "resolved_local_doc_path": str(settings.local_rag_doc_path),
                    "local_doc_exists": local_doc_exists,
                    "local_doc_size_bytes": local_doc_size,
                    "public_doc_lookup_enabled": settings.public_doc_lookup_enabled,
                    "public_doc_urls_count": len(settings.public_doc_urls),
                    "public_doc_timeout_seconds": settings.public_doc_timeout_seconds,
                    "last_public_doc_error": chat_service.last_public_doc_error,
                    "last_bedrock_error": chat_service.last_bedrock_error,
                },
                "tickets": {
                    "mode": settings.ticket_api_mode,
                    "zammad_base_url_configured": bool(settings.zammad_base_url),
                    "zammad_base_url": settings.zammad_base_url,
                    "zammad_token_configured": bool(settings.zammad_api_token),
                    "zammad_group": settings.zammad_group,
                    "zammad_customer_email": settings.zammad_customer_email,
                    "email_enabled": settings.email_enabled,
                },
                "governance": governance_health,
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
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(chat_service.ask, question),
                timeout=settings.chat_request_timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning("Chat request exceeded configured timeout")
            response = chat_service.timeout_response(question)
        except Exception:
            logger.exception("Unexpected chat failure")
            response = chat_service.error_response(question)
        return response.model_dump()

    @api.get("/api/debug/rag")
    async def debug_rag(question: str = Query(min_length=1, max_length=1000)) -> dict:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(chat_service.debug_retrieval, question),
                timeout=settings.chat_request_timeout_seconds,
            )
        except asyncio.TimeoutError:
            return chat_service.debug_timeout(question)
        except Exception:
            logger.exception("Unexpected RAG debug failure")
            return {
                **chat_service.debug_timeout(question),
                "error": "retrieval_error",
            }

    @api.post("/api/tickets/test")
    async def create_ticket(request: TicketTestRequest) -> dict:
        try:
            return ticket_service.create_test_ticket(dry_run=request.dry_run).model_dump()
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/tickets/from-chat")
    async def create_ticket_from_chat(request: TicketFromChatRequest) -> dict:
        try:
            return await asyncio.to_thread(
                ticket_service.create_ticket, request.question, request.answer
            )
        except requests.exceptions.ConnectionError as exc:
            logger.warning(
                "Zammad connection failed: type=%s",
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Não foi possível conectar ao Zammad.",
                    "detail": "Verifique ZAMMAD_BASE_URL e se o Zammad está acessível.",
                },
            ) from None
        except requests.exceptions.Timeout as exc:
            logger.warning(
                "Zammad request timed out: type=%s",
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Não foi possível conectar ao Zammad.",
                    "detail": "Verifique ZAMMAD_BASE_URL e se o Zammad está acessível.",
                },
            ) from None
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Zammad request failed: type=%s",
                type(exc).__name__,
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Não foi possível conectar ao Zammad.",
                    "detail": "Verifique ZAMMAD_BASE_URL e se o Zammad está acessível.",
                },
            ) from None
        except ZammadIntegrationError as exc:
            raise HTTPException(status_code=exc.http_status, detail=exc.detail) from None
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

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

    @api.get("/api/governance/sta/summary")
    async def governance_sta_summary(days: int = Query(default=7, ge=1, le=90)) -> dict:
        return governance_service.build_summary(days=days)

    @api.post("/api/governance/reports")
    async def create_governance_report(request: GovernanceReportRequest) -> dict:
        try:
            return governance_service.create_pdf_report(solution=request.solution, days=request.days)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @api.get("/api/governance/reports/{report_id}/download")
    async def download_governance_report(report_id: str):
        report_path = governance_service.report_path(report_id)
        if not report_path or not report_path.is_file():
            raise HTTPException(status_code=404, detail="Relatório não encontrado.")
        filename = governance_service.report_filename(report_id)
        return FileResponse(
            path=report_path,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @api.get("/api/governance/debug/sta")
    async def governance_sta_debug(days: int = Query(default=7, ge=1, le=90)) -> dict:
        return governance_service.debug_sta(days=days)

    return api


app = create_app()
