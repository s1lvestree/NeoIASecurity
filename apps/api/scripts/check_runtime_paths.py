#!/usr/bin/env python3
"""Print safe runtime path diagnostics for local and Docker execution."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))
load_dotenv(API_ROOT / ".env", override=True)

from neotel_api.config import get_settings  # noqa: E402


def list_files(path: Path) -> list[str]:
    if not path.is_dir():
        return []
    return sorted(item.name for item in path.iterdir() if item.is_file())[:50]


def main() -> int:
    settings = get_settings()
    path = settings.local_rag_doc_path
    exists = path.is_file()
    print(f"cwd={Path.cwd()}")
    print(f"file_location={Path(__file__).resolve()}")
    print(f"configured_local_doc_path={settings.configured_local_doc_path}")
    print(f"resolved_local_doc_path={path}")
    print(f"local_doc_exists={str(exists).lower()}")
    print(f"local_doc_size_bytes={path.stat().st_size if exists else 0}")
    print(f"app_docs_files={list_files(Path('/app/docs'))}")
    print(f"apps_api_docs_files={list_files(Path('apps/api/docs'))}")
    print(f"api_root_docs_files={list_files(API_ROOT / 'docs')}")
    print(f"public_doc_lookup_enabled={str(settings.public_doc_lookup_enabled).lower()}")
    print(f"public_doc_urls_count={len(settings.public_doc_urls)}")
    return 0 if exists else 1


if __name__ == "__main__":
    raise SystemExit(main())
