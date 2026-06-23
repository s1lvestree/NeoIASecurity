"""Manual smoke test for intent detection and fallback answer quality."""

from __future__ import annotations

import sys
import os
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))
os.environ.setdefault("BEDROCK_ENABLED", "false")
os.environ.setdefault("PUBLIC_DOC_LOOKUP_ENABLED", "false")

from neotel_api.config import get_settings  # noqa: E402
from neotel_api.services.chat import ChatService, classify_question_intent  # noqa: E402

QUESTIONS = [
    "O que é o STA?",
    "Para que serve o SafeNet Trusted Access?",
    "Como desbloquear token STA?",
    "Aplicação SAML não redireciona corretamente, o que validar?",
    "Quais métodos de autenticação o STA suporta?",
]
ALWAYS_FORBIDDEN = ["### CONTEXTO LOCAL", "### CONTEXTO PÚBLICO", "Resumo do contexto disponível"]


def main() -> int:
    service = ChatService(get_settings())
    failed = False
    for question in QUESTIONS:
        response = service.ask(question)
        intent = classify_question_intent(question)
        forbidden = list(ALWAYS_FORBIDDEN)
        if intent == "concept":
            forbidden.append("Token bloqueado")
            if "saml" not in question.lower():
                forbidden.append("Aplicação SAML")
        found = [item for item in forbidden if item.lower() in response.answer.lower()]
        failed = failed or bool(found)
        print(f"\nPergunta: {question}")
        print(f"Intent: {intent}")
        print(f"Mode: {response.mode}")
        print(f"Resposta:\n{response.answer}")
        print(f"Strings proibidas encontradas: {found or 'nenhuma'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
