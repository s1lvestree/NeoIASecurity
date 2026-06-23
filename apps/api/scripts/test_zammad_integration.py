from __future__ import annotations

import sys
import json
from pathlib import Path

from dotenv import load_dotenv


API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))
load_dotenv(API_ROOT / ".env", override=True)

from neotel_api.config import get_settings  # noqa: E402
from neotel_api.services.tickets import (  # noqa: E402
    create_zammad_ticket,
    ensure_zammad_customer,
    find_zammad_user_by_email,
    validate_zammad_auth,
    validate_zammad_group,
)


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    print(f"ZAMMAD_BASE_URL: {settings.zammad_base_url or '(não configurado)'}")
    print(f"ZAMMAD_GROUP: {settings.zammad_group or '(não configurado)'}")
    print(f"ZAMMAD_CUSTOMER_EMAIL: {settings.zammad_customer_email or '(não configurado)'}")
    print(f"ZAMMAD_API_TOKEN configurado: {'sim' if settings.zammad_api_token else 'não'}")
    print(f"ZAMMAD_API_TOKEN tamanho: {len(settings.zammad_api_token)}")
    if not settings.zammad_base_url:
        print("Erro: ZAMMAD_BASE_URL não configurado.")
        return 1
    if not settings.zammad_api_token:
        print("Erro: ZAMMAD_API_TOKEN não configurado.")
        return 1
    if not settings.zammad_group or not settings.zammad_customer_email:
        print("Erro: ZAMMAD_GROUP e ZAMMAD_CUSTOMER_EMAIL são obrigatórios.")
        return 1

    try:
        validate_zammad_auth(settings)
        print("Autenticação: OK")
        validate_zammad_group(settings, settings.zammad_group)
        print(f"Grupo encontrado: {settings.zammad_group}")
        existing_customer = find_zammad_user_by_email(
            settings, settings.zammad_customer_email
        )
        customer = ensure_zammad_customer(
            settings, settings.zammad_customer_email, settings.zammad_customer_name
        )
        customer_created = bool(customer.get("_neoia_created"))
        ticket = create_zammad_ticket(
            "Teste de integração do NeoIASecurity",
            "Chamado criado pelo script de validação da integração.",
        )
    except Exception as exc:
        safe_message = str(exc).replace(settings.zammad_api_token, "[REDACTED]")
        print(f"Erro na integração com Zammad: {safe_message}")
        detail = getattr(exc, "detail", None)
        if isinstance(detail, dict):
            safe_detail = json.dumps(detail, ensure_ascii=False).replace(
                settings.zammad_api_token, "[REDACTED]"
            )
            print(f"Diagnóstico: {safe_detail}")
        return 1

    print(f"Cliente ID: {customer.get('id')}")
    print(f"Cliente e-mail: {customer.get('email') or settings.zammad_customer_email}")
    print(f"Cliente criado automaticamente: {'sim' if customer_created else 'não'}")
    print(f"Ticket ID: {ticket['ticket_id']}")
    print(f"Ticket número: {ticket['ticket_number']}")
    print(f"Ticket URL: {ticket['ticket_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
