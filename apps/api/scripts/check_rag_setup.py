#!/usr/bin/env python3
"""Safe local RAG setup diagnostic. It never prints environment secrets."""

from __future__ import annotations

import sys
import time
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from neotel_api.config import get_settings  # noqa: E402
from neotel_api.services.chat import ChatService  # noqa: E402


QUERIES = (
    "O que é o STA?",
    "Como revogar um token GrIDsure?",
    "Como desbloquear token STA?",
    "Aplicação SAML não redireciona corretamente, o que validar?",
)


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
    if not exists:
        print("WARNING: local document is missing")

    exit_code = 0
    for question in QUERIES:
        started = time.perf_counter()
        result = service.debug_retrieval(question)
        elapsed_ms = (time.perf_counter() - started) * 1000
        print(f"\nquery={question}")
        print(f"chunks_total={result['local_chunks_count']} selected={len(result['selected_local_chunks'])}")
        for chunk in result["selected_local_chunks"]:
            print(f"- heading={chunk['heading']} score={chunk['score']} preview={chunk['preview']}")
        if not result["selected_local_chunks"]:
            print("WARNING: no local chunk found")
            exit_code = 1
        if result["combined_context_length"] >= settings.combined_context_max_chars:
            print("WARNING: combined context reached the configured maximum")
        if settings.public_doc_lookup_enabled and result["public_doc_ms"] > settings.public_doc_timeout_seconds * 1000:
            print("WARNING: public documentation lookup was slow")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
        print(f"elapsed_ms={elapsed_ms:.2f}")

    return exit_code if settings.local_rag_enabled else 0


if __name__ == "__main__":
    raise SystemExit(main())
