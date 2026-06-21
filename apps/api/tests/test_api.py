from pathlib import Path

from fastapi.testclient import TestClient

from neotel_api.config import get_settings
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


def test_ticket_test_endpoint_supports_dry_run(monkeypatch, tmp_path: Path) -> None:
    client = build_client(monkeypatch, tmp_path)

    response = client.post("/api/tickets/test", json={"dry_run": True})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["dry_run"] is True
    assert body["mode"] == "generic"
    assert "payload" in body


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
