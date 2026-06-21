from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")
load_dotenv(API_ROOT / ".env")


def _resolve_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (API_ROOT / candidate).resolve()


@dataclass(slots=True)
class Settings:
    aws_region: str
    bedrock_enabled: bool
    bedrock_model_id: str
    bedrock_fallback_model_id: str
    aws_ca_bundle: str
    requests_ca_bundle: str
    local_rag_enabled: bool
    local_rag_doc_path: Path
    local_rag_max_chunks: int
    local_rag_chunk_size: int
    public_doc_lookup_enabled: bool
    public_doc_max_urls: int
    public_doc_urls: list[str]
    combined_context_max_chars: int
    ticket_api_mode: str
    ticket_api_url: str
    ticket_api_method: str
    ticket_api_auth_type: str
    ticket_api_token: str
    ticket_api_extra_header_name: str
    ticket_api_extra_header_value: str
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
        bedrock_enabled=env_bool("BEDROCK_ENABLED", False),
        bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0"),
        bedrock_fallback_model_id=os.getenv("BEDROCK_FALLBACK_MODEL_ID", "amazon.nova-pro-v1:0"),
        aws_ca_bundle=aws_ca_bundle,
        requests_ca_bundle=requests_ca_bundle,
        local_rag_enabled=env_bool("LOCAL_RAG_ENABLED", True),
        local_rag_doc_path=_resolve_path(os.getenv("LOCAL_RAG_DOC_PATH", "../streamlit/docs/sta.md")),
        local_rag_max_chunks=env_int("LOCAL_RAG_MAX_CHUNKS", 5),
        local_rag_chunk_size=env_int("LOCAL_RAG_CHUNK_SIZE", 2500),
        public_doc_lookup_enabled=env_bool("PUBLIC_DOC_LOOKUP_ENABLED", False),
        public_doc_max_urls=env_int("PUBLIC_DOC_MAX_URLS", 6),
        public_doc_urls=[url.strip() for url in os.getenv("PUBLIC_DOC_URLS", "").split(",") if url.strip()],
        combined_context_max_chars=env_int("COMBINED_CONTEXT_MAX_CHARS", 18000),
        ticket_api_mode=os.getenv("TICKET_API_MODE", "generic").strip().lower(),
        ticket_api_url=os.getenv("TICKET_API_URL", "").strip(),
        ticket_api_method=os.getenv("TICKET_API_METHOD", "POST").strip().upper(),
        ticket_api_auth_type=os.getenv("TICKET_API_AUTH_TYPE", "bearer").strip().lower(),
        ticket_api_token=os.getenv("TICKET_API_TOKEN", "").strip(),
        ticket_api_extra_header_name=os.getenv("TICKET_API_EXTRA_HEADER_NAME", "").strip(),
        ticket_api_extra_header_value=os.getenv("TICKET_API_EXTRA_HEADER_VALUE", "").strip(),
        octadesk_api_url=os.getenv("OCTADESK_API_URL", "https://api.octadesk.services").rstrip("/"),
        octadesk_access_token=os.getenv("OCTADESK_ACCESS_TOKEN", "").strip(),
        octadesk_agent_email=os.getenv("OCTADESK_AGENT_EMAIL", "").strip(),
        octadesk_requester_email=os.getenv("OCTADESK_REQUESTER_EMAIL", "").strip(),
        governance_log_dir=_resolve_path(os.getenv("GOVERNANCE_LOG_DIR", "../streamlit/data/sta_logs_fake")),
        governance_report_dir=_resolve_path(os.getenv("GOVERNANCE_REPORT_DIR", "reports")),
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
