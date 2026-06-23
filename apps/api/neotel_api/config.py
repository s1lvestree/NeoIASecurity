from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def clean_env_value(value: str | None) -> str:
    """Trim an env value and remove one pair of quotes wrapping the whole value."""
    cleaned = (value or "").strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1].strip()
    return cleaned


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


API_ROOT = Path(__file__).resolve().parents[1]
_parents = Path(__file__).resolve().parents
REPO_ROOT = _parents[3] if len(_parents) > 3 else API_ROOT
load_dotenv(REPO_ROOT / ".env")
load_dotenv(API_ROOT / ".env")


def resolve_local_doc_path(configured_path: str) -> Path:
    """Resolve the STA RAG document in local and Docker executions."""
    raw_path = (configured_path or "apps/api/docs/sta.md").strip()
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()

    candidates = [
        Path.cwd() / candidate,
        REPO_ROOT / candidate,
        API_ROOT / candidate,
        Path("/app") / candidate,
        Path("/app/docs/sta.md"),
        REPO_ROOT / "apps/api/docs/sta.md",
    ]

    parts = candidate.parts
    if len(parts) >= 2 and parts[:2] == ("apps", "api"):
        candidates.insert(3, API_ROOT.joinpath(*parts[2:]))
        candidates.insert(4, Path("/app").joinpath(*parts[2:]))

    unique_candidates: list[Path] = []
    for item in candidates:
        resolved = item.resolve()
        if resolved not in unique_candidates:
            unique_candidates.append(resolved)
    return next((item for item in unique_candidates if item.is_file()), unique_candidates[0])


def _resolve_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (API_ROOT / candidate).resolve()


@dataclass(slots=True)
class Settings:
    aws_region: str
    aws_bearer_token_bedrock: str
    bedrock_enabled: bool
    bedrock_model_id: str
    bedrock_fallback_model_id: str
    aws_ca_bundle: str
    requests_ca_bundle: str
    local_rag_enabled: bool
    configured_local_doc_path: str
    local_rag_doc_path: Path
    local_rag_max_chunks: int
    local_rag_chunk_size: int
    public_doc_lookup_enabled: bool
    public_doc_max_urls: int
    public_doc_max_urls_per_query: int
    public_doc_urls: list[str]
    public_doc_cache_ttl_seconds: int
    combined_context_max_chars: int
    chat_request_timeout_seconds: int
    public_doc_timeout_seconds: int
    bedrock_timeout_seconds: int
    ticket_api_mode: str
    ticket_api_url: str
    ticket_api_method: str
    ticket_api_auth_type: str
    ticket_api_token: str
    ticket_api_extra_header_name: str
    ticket_api_extra_header_value: str
    zammad_base_url: str
    zammad_api_token: str
    zammad_group: str
    zammad_customer_email: str
    zammad_customer_name: str
    zammad_technician_email: str
    zammad_ticket_state: str
    zammad_ticket_priority: str
    email_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from: str
    smtp_use_tls: bool
    smtp_subject_prefix: str
    notify_requester: bool
    notify_technician: bool
    requester_email: str
    technician_email: str
    octadesk_api_url: str
    octadesk_access_token: str
    octadesk_agent_email: str
    octadesk_requester_email: str
    governance_log_dir: Path
    governance_report_dir: Path
    governance_default_days: int
    governance_default_log_count: int
    governance_use_fake_sta_api: bool
    governance_privacy_mode: bool
    governance_hash_salt: str
    governance_send_raw_logs_to_ai: bool
    governance_max_sanitized_samples: int
    governance_mask_ip_mode: str
    governance_remove_session_identifiers: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    aws_ca_bundle = os.getenv("AWS_CA_BUNDLE", "").strip()
    requests_ca_bundle = os.getenv("REQUESTS_CA_BUNDLE", "").strip()
    if aws_ca_bundle:
        os.environ["AWS_CA_BUNDLE"] = aws_ca_bundle
    if requests_ca_bundle:
        os.environ["REQUESTS_CA_BUNDLE"] = requests_ca_bundle

    return Settings(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        aws_bearer_token_bedrock=os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip(),
        bedrock_enabled=env_bool("BEDROCK_ENABLED", False),
        bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0"),
        bedrock_fallback_model_id=os.getenv("BEDROCK_FALLBACK_MODEL_ID", "amazon.nova-pro-v1:0"),
        aws_ca_bundle=aws_ca_bundle,
        requests_ca_bundle=requests_ca_bundle,
        local_rag_enabled=env_bool("LOCAL_RAG_ENABLED", True),
        configured_local_doc_path=os.getenv("LOCAL_RAG_DOC_PATH", "apps/api/docs/sta.md").strip(),
        local_rag_doc_path=resolve_local_doc_path(os.getenv("LOCAL_RAG_DOC_PATH", "apps/api/docs/sta.md")),
        local_rag_max_chunks=env_int("LOCAL_RAG_MAX_CHUNKS", 5),
        local_rag_chunk_size=env_int("LOCAL_RAG_CHUNK_SIZE", 2500),
        public_doc_lookup_enabled=env_bool("PUBLIC_DOC_LOOKUP_ENABLED", False),
        public_doc_max_urls=env_int("PUBLIC_DOC_MAX_URLS", 6),
        public_doc_max_urls_per_query=env_int("PUBLIC_DOC_MAX_URLS_PER_QUERY", 3),
        public_doc_urls=[url.strip() for url in os.getenv("PUBLIC_DOC_URLS", "").split(",") if url.strip()],
        public_doc_cache_ttl_seconds=env_int("PUBLIC_DOC_CACHE_TTL_SECONDS", 900),
        combined_context_max_chars=env_int("COMBINED_CONTEXT_MAX_CHARS", 18000),
        chat_request_timeout_seconds=env_int("CHAT_REQUEST_TIMEOUT_SECONDS", 60),
        public_doc_timeout_seconds=env_int("PUBLIC_DOC_TIMEOUT_SECONDS", 5),
        bedrock_timeout_seconds=env_int("BEDROCK_TIMEOUT_SECONDS", 45),
        ticket_api_mode=os.getenv("TICKET_API_MODE", "generic").strip().lower(),
        ticket_api_url=os.getenv("TICKET_API_URL", "").strip(),
        ticket_api_method=os.getenv("TICKET_API_METHOD", "POST").strip().upper(),
        ticket_api_auth_type=os.getenv("TICKET_API_AUTH_TYPE", "bearer").strip().lower(),
        ticket_api_token=os.getenv("TICKET_API_TOKEN", "").strip(),
        ticket_api_extra_header_name=os.getenv("TICKET_API_EXTRA_HEADER_NAME", "").strip(),
        ticket_api_extra_header_value=os.getenv("TICKET_API_EXTRA_HEADER_VALUE", "").strip(),
        zammad_base_url=clean_env_value(os.getenv("ZAMMAD_BASE_URL")).rstrip("/"),
        zammad_api_token=clean_env_value(os.getenv("ZAMMAD_API_TOKEN")),
        zammad_group=clean_env_value(os.getenv("ZAMMAD_GROUP", "Suporte")),
        zammad_customer_email=clean_env_value(os.getenv("ZAMMAD_CUSTOMER_EMAIL")),
        zammad_customer_name=clean_env_value(os.getenv("ZAMMAD_CUSTOMER_NAME")),
        zammad_technician_email=clean_env_value(os.getenv("ZAMMAD_TECHNICIAN_EMAIL")),
        zammad_ticket_state=clean_env_value(os.getenv("ZAMMAD_TICKET_STATE", "new")),
        zammad_ticket_priority=clean_env_value(
            os.getenv("ZAMMAD_TICKET_PRIORITY", "2 normal")
        ),
        email_enabled=env_bool("EMAIL_ENABLED", False),
        smtp_host=os.getenv("SMTP_HOST", "smtp.office365.com").strip(),
        smtp_port=env_int("SMTP_PORT", 587),
        smtp_username=os.getenv("SMTP_USERNAME", "").strip(),
        smtp_password=os.getenv("SMTP_PASSWORD", "").strip(),
        smtp_from=os.getenv("SMTP_FROM", "").strip(),
        smtp_use_tls=env_bool("SMTP_USE_TLS", True),
        smtp_subject_prefix=os.getenv("SMTP_SUBJECT_PREFIX", "[NeoIASecurity]").strip(),
        notify_requester=env_bool("NOTIFY_REQUESTER", True),
        notify_technician=env_bool("NOTIFY_TECHNICIAN", True),
        requester_email=os.getenv("REQUESTER_EMAIL", "").strip(),
        technician_email=os.getenv("TECHNICIAN_EMAIL", "").strip(),
        octadesk_api_url=os.getenv("OCTADESK_API_URL", "https://api.octadesk.services").rstrip("/"),
        octadesk_access_token=os.getenv("OCTADESK_ACCESS_TOKEN", "").strip(),
        octadesk_agent_email=os.getenv("OCTADESK_AGENT_EMAIL", "").strip(),
        octadesk_requester_email=os.getenv("OCTADESK_REQUESTER_EMAIL", "").strip(),
        governance_log_dir=_resolve_path(os.getenv("GOVERNANCE_LOG_DIR", "data/sta_logs")),
        governance_report_dir=_resolve_path(os.getenv("GOVERNANCE_REPORT_DIR", "generated_reports")),
        governance_default_days=env_int("GOVERNANCE_DEFAULT_DAYS", 7),
        governance_default_log_count=env_int("GOVERNANCE_DEFAULT_LOG_COUNT", 500),
        governance_use_fake_sta_api=env_bool("GOVERNANCE_USE_FAKE_STA_API", True),
        governance_privacy_mode=env_bool("GOVERNANCE_PRIVACY_MODE", True),
        governance_hash_salt=os.getenv("GOVERNANCE_HASH_SALT", "CHANGE_ME_DEMO_SALT"),
        governance_send_raw_logs_to_ai=env_bool("GOVERNANCE_SEND_RAW_LOGS_TO_AI", False),
        governance_max_sanitized_samples=env_int("GOVERNANCE_MAX_SANITIZED_SAMPLES", 20),
        governance_mask_ip_mode=os.getenv("GOVERNANCE_MASK_IP_MODE", "partial").strip().lower(),
        governance_remove_session_identifiers=env_bool("GOVERNANCE_REMOVE_SESSION_IDENTIFIERS", True),
    )
