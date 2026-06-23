from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

from neotel_api.config import clean_env_value, get_settings, resolve_local_doc_path
from neotel_api.app import create_app


def build_client(monkeypatch, tmp_path: Path) -> TestClient:
    doc_path = tmp_path / "sta.md"
    doc_path.write_text(
        "# SafeNet Trusted Access\n\n"
        "SafeNet Trusted Access ajuda a controlar acesso, SSO e MFA em aplicações.\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("LOCAL_RAG_DOC_PATH", str(doc_path))
    monkeypatch.setenv("PUBLIC_DOC_LOOKUP_ENABLED", "false")
    monkeypatch.setenv("GOVERNANCE_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("GOVERNANCE_REPORT_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("BEDROCK_ENABLED", "false")

    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


def test_health_endpoint_reports_services(monkeypatch, tmp_path: Path) -> None:
    client = build_client(monkeypatch, tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "chat" in body["services"]
    assert "governance" in body["services"]
    assert body["services"]["chat"]["bedrock_enabled"] is False
    assert body["local_doc_exists"] is True
    assert body["local_doc_size_bytes"] > 0
    assert body["configured_local_doc_path"] == str(tmp_path / "sta.md")
    assert body["resolved_local_doc_path"] == str(tmp_path / "sta.md")
    assert body["public_doc_timeout_seconds"] == 5


def test_local_doc_resolver_supports_api_repo_and_current_working_directory(
    monkeypatch, tmp_path: Path
) -> None:
    cwd_doc = tmp_path / "cwd-only.md"
    cwd_doc.write_text("test", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert resolve_local_doc_path("cwd-only.md") == cwd_doc
    assert resolve_local_doc_path("apps/api/docs/sta.md").name == "sta.md"
    assert resolve_local_doc_path("README.md").name == "README.md"


def test_chat_endpoint_returns_local_fallback_answer(monkeypatch, tmp_path: Path) -> None:
    client = build_client(monkeypatch, tmp_path)

    response = client.post(
        "/api/chat",
        json={"question": "O que é SafeNet Trusted Access?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "fallback"
    assert "SafeNet Trusted Access" in body["answer"]
    assert len(body["local_sources"]) == 1
    assert body["intent"] == "concept"
    assert "CONTEXTO LOCAL" not in body["answer"]
    assert "Resumo do contexto disponível" not in body["answer"]


def test_debug_rag_returns_metadata_without_raw_document(monkeypatch, tmp_path: Path) -> None:
    client = build_client(monkeypatch, tmp_path)

    response = client.get("/api/debug/rag", params={"question": "O que é STA?"})

    assert response.status_code == 200
    body = response.json()
    assert body["detected_intent"] == "concept"
    assert body["selected_local_chunks"]
    assert "content" not in body["selected_local_chunks"][0]
    assert "bedrock_enabled" in body["mode"]
    assert body["configured_local_doc_path"] == str(tmp_path / "sta.md")
    assert body["resolved_local_doc_path"] == str(tmp_path / "sta.md")
    assert body["local_doc_exists"] is True
    assert body["local_doc_size_bytes"] > 0
    assert "preview" in body["selected_local_chunks"][0]
    assert len(body["selected_local_chunks"][0]["preview"]) <= 250
    assert "public_doc_lookup_enabled" in body
    assert "selected_public_sources" in body
    assert "local_rag_ms" in body
    assert "total_ms" in body


def test_missing_local_document_is_explicit(monkeypatch, tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.md"
    monkeypatch.setenv("LOCAL_RAG_DOC_PATH", str(missing_path))
    monkeypatch.setenv("LOCAL_RAG_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_DOC_LOOKUP_ENABLED", "false")
    monkeypatch.setenv("BEDROCK_ENABLED", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    health = client.get("/health").json()
    debug = client.get("/api/debug/rag", params={"question": "Como revogar token?"}).json()
    chat = client.post("/api/chat", json={"question": "Como revogar token?"}).json()

    assert health["local_doc_exists"] is False
    assert health["resolved_local_doc_path"] == str(missing_path)
    assert debug["local_doc_exists"] is False
    assert debug["warnings"]
    assert chat["answer"].startswith("Não encontrei informação suficiente")


def test_gridsure_uses_related_token_context_without_inventing_procedure(monkeypatch, tmp_path: Path) -> None:
    doc_path = tmp_path / "sta.md"
    doc_path.write_text(
        "# Gestão de tokens STA\n\nConfirme o estado do token e revise o Log de Autenticação.\n\n"
        "## Token bloqueado\nUse a ação documentada de desbloqueio para tokens bloqueados.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCAL_RAG_DOC_PATH", str(doc_path))
    monkeypatch.setenv("LOCAL_RAG_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_DOC_LOOKUP_ENABLED", "false")
    monkeypatch.setenv("BEDROCK_ENABLED", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    debug = client.get(
        "/api/debug/rag", params={"question": "Como revogar um token GrIDsure?"}
    ).json()
    chat = client.post(
        "/api/chat", json={"question": "Como revogar um token GrIDsure?"}
    ).json()

    assert debug["selected_local_chunks"]
    assert any("No exact GrIDsure procedure" in warning for warning in debug["warnings"])
    assert "Não encontrei um procedimento específico" in chat["answer"]
    assert "informação suficiente" not in chat["answer"]
    assert "Resposta gerada localmente" in chat["answer"]


def test_ticket_test_endpoint_supports_dry_run(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TICKET_API_MODE", "generic")
    client = build_client(monkeypatch, tmp_path)

    response = client.post("/api/tickets/test", json={"dry_run": True})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["dry_run"] is True
    assert body["mode"] == "generic"
    assert "payload" in body


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, ""), ("  Suporte  ", "Suporte"), ('"cliente@example.com"', "cliente@example.com"),
     ("'new'", "new"), ("\"mismatched'", "\"mismatched'")],
)
def test_clean_env_value_only_removes_wrapping_quotes(raw, expected) -> None:
    assert clean_env_value(raw) == expected


def test_zammad_ticket_from_chat_builds_expected_request(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TICKET_API_MODE", "zammad")
    monkeypatch.setenv("ZAMMAD_BASE_URL", "http://zammad.test")
    monkeypatch.setenv("ZAMMAD_API_TOKEN", "secret-token-for-test")
    monkeypatch.setenv("ZAMMAD_GROUP", "Suporte")
    monkeypatch.setenv("ZAMMAD_CUSTOMER_EMAIL", "cliente@example.com")
    monkeypatch.setenv("ZAMMAD_CUSTOMER_NAME", "Cliente Teste")
    monkeypatch.setenv("EMAIL_ENABLED", "false")

    captured: dict = {}

    class FakeResponse:
        def __init__(self, status_code: int, payload: object) -> None:
            self.status_code = status_code
            self._payload = payload
            self.text = str(payload)

        def json(self):
            return self._payload

    def fake_get(url: str, **kwargs):
        if url.endswith("/api/v1/users/me"):
            return FakeResponse(200, {"id": 1, "login": "admin"})
        if url.endswith("/api/v1/groups"):
            return FakeResponse(200, [{"id": 1, "name": "Suporte"}])
        if url.endswith("/api/v1/users/search"):
            return FakeResponse(200, [{"id": 7, "email": "cliente@example.com"}])
        raise AssertionError(f"GET inesperado: {url}")

    def fake_post(url: str, **kwargs):
        captured.update(url=url, **kwargs)
        return FakeResponse(201, {"id": 42, "number": "10042"})

    monkeypatch.setattr("neotel_api.services.tickets.requests.get", fake_get)
    monkeypatch.setattr("neotel_api.services.tickets.requests.post", fake_post)
    client = build_client(monkeypatch, tmp_path)
    response = client.post(
        "/api/tickets/from-chat",
        json={"question": "Como desbloquear o token?", "answer": "Siga o procedimento."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["mode"] == "zammad"
    assert body["ticket_id"] == 42
    assert body["ticket_number"] == "10042"
    assert body["ticket_url"] == "http://zammad.test/#ticket/zoom/42"
    assert body["customer_email"] == "cliente@example.com"
    assert body["customer_id"] == 7
    assert body["created_customer"] is False
    assert body["email_notification"] == {"enabled": False, "warning": False}
    assert captured["url"] == "http://zammad.test/api/v1/tickets"
    assert captured["timeout"] == 30
    assert captured["json"]["article"]["internal"] is False
    assert "secret-token-for-test" not in str(body)


def test_health_never_exposes_zammad_token(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TICKET_API_MODE", "zammad")
    monkeypatch.setenv("ZAMMAD_BASE_URL", "http://zammad.test")
    monkeypatch.setenv("ZAMMAD_API_TOKEN", "health-secret-token")
    client = build_client(monkeypatch, tmp_path)

    response = client.get("/health")
    body = response.json()

    assert body["tickets"]["mode"] == "zammad"
    assert body["tickets"]["zammad_base_url_configured"] is True
    assert body["tickets"]["zammad_token_configured"] is True
    assert "health-secret-token" not in response.text


@pytest.mark.parametrize(
    "request_error",
    [
        requests.exceptions.ConnectionError("connection refused with secret-token-for-test"),
        requests.exceptions.Timeout("timeout with secret-token-for-test"),
        requests.exceptions.RequestException("request failure with secret-token-for-test"),
    ],
)
def test_zammad_transport_errors_return_sanitized_502(
    monkeypatch, tmp_path: Path, request_error: requests.exceptions.RequestException
) -> None:
    monkeypatch.setenv("TICKET_API_MODE", "zammad")
    monkeypatch.setenv("ZAMMAD_BASE_URL", "http://zammad.test")
    monkeypatch.setenv("ZAMMAD_API_TOKEN", "secret-token-for-test")
    monkeypatch.setenv("ZAMMAD_GROUP", "Suporte")
    monkeypatch.setenv("ZAMMAD_CUSTOMER_EMAIL", "cliente@example.com")

    def failing_post(*args, **kwargs):
        raise request_error

    monkeypatch.setattr("neotel_api.services.tickets.requests.post", failing_post)
    client = build_client(monkeypatch, tmp_path)
    response = client.post(
        "/api/tickets/from-chat",
        json={"question": "Pergunta", "answer": "Resposta"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "message": "Não foi possível conectar ao Zammad.",
            "detail": "Verifique ZAMMAD_BASE_URL e se o Zammad está acessível.",
        }
    }
    assert "secret-token-for-test" not in response.text


def test_governance_preview_endpoint_returns_analysis(monkeypatch, tmp_path: Path) -> None:
    client = build_client(monkeypatch, tmp_path)

    response = client.post(
        "/api/governance/preview",
        json={"days": 2, "events_per_day": 12},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["total_log_entries"] > 0
    assert body["preview_rows"]
    assert body["privacy_issues"] == []


def test_governance_report_endpoint_returns_markdown(monkeypatch, tmp_path: Path) -> None:
    client = build_client(monkeypatch, tmp_path)

    response = client.post(
        "/api/governance/report",
        json={"days": 2, "events_per_day": 12},
    )

    assert response.status_code == 200
    body = response.json()
    assert "Relatório Executivo de Governança" in body["report_markdown"]
    assert body["mode"] == "fallback"
    assert body["privacy_issues"] == []
