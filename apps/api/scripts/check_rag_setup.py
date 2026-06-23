#!/usr/bin/env python3
"""Safe local RAG setup diagnostic. It never prints environment secrets."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from dotenv import load_dotenv


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
load_dotenv(API_ROOT / ".env", override=True)

from neotel_api.config import get_settings  # noqa: E402
from neotel_api.services.chat import ChatService  # noqa: E402


QUERIES = (
    "O que é o STA?",
    "Como revogar um token GrIDsure?",
    "Como desbloquear token STA?",
    "Quais métodos de autenticação o STA suporta?",
    "Aplicação SAML não redireciona corretamente, o que validar?",
)
KEYWORDS = ("GrIDsure", "token", "revoke", "revogar", "MobilePASS")


def main() -> int:
    settings = get_settings()
    service = ChatService(settings)
    path = settings.local_rag_doc_path
    exists = path.is_file()

    print(f"configured_local_doc_path={settings.configured_local_doc_path}")
    print(f"resolved_local_doc_path={path}")
    print(f"local_rag_enabled={str(settings.local_rag_enabled).lower()}")
    print(f"local_doc_exists={str(exists).lower()}")
    print(f"local_doc_size_bytes={path.stat().st_size if exists else 0}")
    print(f"public_doc_lookup_enabled={str(settings.public_doc_lookup_enabled).lower()}")
    print(f"public_doc_urls_count={len(settings.public_doc_urls)}")
    print(f"public_doc_timeout_seconds={settings.public_doc_timeout_seconds}")
    if exists:
        text = path.read_text(encoding="utf-8-sig")
        lowered = text.casefold()
        for keyword in KEYWORDS:
            print(f"keyword_{keyword}={str(keyword.casefold() in lowered).lower()}")
    if not exists:
        print("WARNING: local document is missing")

    exit_code = 0
    for question in QUERIES:
        started = time.perf_counter()
        result = service.debug_retrieval(question)
        elapsed_ms = (time.perf_counter() - started) * 1000
        print(f"\nquery={question}")
        local = result["local"]
        public = result["public"]
        timings = result["timings_ms"]
        print(f"intent={result['detected_intent']}")
        print(f"chunks_total={local['chunks_count']} selected={len(local['selected_chunks'])}")
        for chunk in local["selected_chunks"]:
            print(f"- heading={chunk['heading']} score={chunk['score']} preview={chunk['preview']}")
        print(f"public_attempted={str(bool(public['urls_attempted'])).lower()}")
        if public["urls_attempted"]:
            print(f"public_urls_attempted={len(public['urls_attempted'])}")
        if public["selected_sources"]:
            print(f"public_sources_selected={len(public['selected_sources'])}")
        if public["errors"]:
            print(f"public_errors={public['errors']}")
        if not local["selected_chunks"]:
            print("WARNING: no local chunk found")
            exit_code = 1
        if result["combined_context_length"] >= settings.combined_context_max_chars:
            print("WARNING: combined context reached the configured maximum")
        if settings.public_doc_lookup_enabled and timings["public_docs"] > settings.public_doc_timeout_seconds * 1000:
            print("WARNING: public documentation lookup was slow")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
        print(f"timings_ms={timings}")
        print(f"elapsed_ms={elapsed_ms:.2f}")

    return exit_code if settings.local_rag_enabled else 0


if __name__ == "__main__":
    raise SystemExit(main())
